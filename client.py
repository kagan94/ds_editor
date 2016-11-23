#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Setup Python logging -------------------------------------------------------
import logging
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG,format=FORMAT)
LOG = logging.getLogger()
LOG.info('Client-side started working...')

# Imports----------------------------------------------------------------------
import ConfigParser as CP
import os
from threading import Thread, Condition, Lock
from gui import *
from socket import AF_INET, SOCK_STREAM, socket, error as socket_error
from protocol import client_files_dir, parse_get_file_response, pack_list,\
                     COMMAND, RESP, SEP, parse_query, SERVER_PORT, \
                     SERVER_INET_ADDR, close_socket, TERM_CHAR, BUFFER_SIZE


# Notifications from the server (used in async receiving, to recognize notification commands)
notification_commands = [notif for notif in COMMAND.NOTIFICATION.__dict__.values() if isinstance(notif, str)]


# If folder for client local files doesn't exist, then create it
if not os.path.exists(client_files_dir):
    os.makedirs(client_files_dir)


class Client(object):
    def __init__(self):
        self.s = None  # it's client socket
        self.gui = None

        self.__send_lock = Lock()  # Only one entity can send out at a time

        self.__rcv_sync_msgs_lock = Condition()  # To wait/notify on received
        self.__rcv_sync_msgs = []  # To collect the received responses
        self.__rcv_async_msgs_lock = Condition()
        self.__rcv_async_msgs = []  # To collect the received notifications


    # Declare client socket and connecting
    def connect_to_server(self):
        s = socket(AF_INET, SOCK_STREAM)
        LOG.info('TCP Socket created and started connecting..')

        try:
            s.connect((SERVER_INET_ADDR, SERVER_PORT))
            self.s = s
        except socket_error as (code, msg):
            if code == 10061:
                LOG.error('Socket error occurred. Server does not respond.')
            else:
                LOG.error('Socket error occurred. Error code: %s, %s' % (code, msg))
            self.s = None
        else:
            LOG.info('Connection is established successfully')

        return self.s

    def sync_user_id(self):
        '''
        Synchronize user_id
        :return: user_id (string)
        '''
        # Path to the config file
        current_path = os.path.abspath(os.path.dirname(__file__))
        config_file = current_path + "\\config.ini"

        # If the config exists, get the user_id from it
        if os.path.isfile(config_file):
            conf = CP.ConfigParser()
            conf.read(config_file)
            self.user_id = conf.get('USER_INFO', 'user_id')

            LOG.debug("Notify server about existing user_id")
            # tcp_send(self.s, COMMAND.NOTIFY_ABOUT_USER_ID, self.user_id)

            res, _ = self.__sync_request(COMMAND.NOTIFY_ABOUT_USER_ID, self.user_id)

            # Receive empty response about saving of user_id on the server
            # _ = tcp_receive(self.s)

        # If the config was deleted or doesn't exist
        else:
            LOG.debug("Request to the server to generate a new user_id")
            # tcp_send(self.s, COMMAND.GENERATE_USER_ID)

            # Get response from the server with user_id (_ is command/response)
            res, self.user_id = self.__sync_request(COMMAND.GENERATE_USER_ID)
            # print res, self.user_id
            # _, self.user_id = parse_query(tcp_receive(self.s))

            conf = CP.RawConfigParser()
            conf.add_section("USER_INFO")
            conf.set('USER_INFO', 'user_id', self.user_id)

            with open(config_file, 'w') as cf:
                conf.write(cf)

    def get_accessible_files(self):
        '''
        :return: list with file names that are possible to edit
        '''
        LOG.debug("Request to server to get list of accessible files to edit")

        # print "xxxxx"
        resp, files = self.__sync_request(COMMAND.LIST_OF_ACCESIBLE_FILES)
        # print resp, files
        # tcp_send(self.s, COMMAND.LIST_OF_ACCESIBLE_FILES)

        # result, files = parse_query(tcp_receive(self.s))
        LOG.debug("Received response of available files")

        if resp == RESP.OK:
            files = files.split(SEP)
        else:
            files = []

        return resp, files

    def get_file_on_server(self, file_name):
        '''
        :param file_name: (string)
        :return: response code and list of [am_i_owner(boolean), file_access(0/1), content(str)]
        '''
        LOG.debug("Request to server to get file")
        res, data = self.__sync_request(COMMAND.GET_FILE, file_name)
        response_data = parse_get_file_response(data)

        LOG.debug("Received response of getting file")

        return res, response_data

    def create_new_file(self, file_name, access):
        '''
        :param file_name: name of file that should be created
        :param access: can be public or private (visible only for this client)
        :return: response code
        '''

        LOG.debug("Request to server to create a new file")

        data = file_name + SEP + access
        resp_code, _ = self.__sync_request(COMMAND.CREATE_NEW_FILE, data)
        # tcp_send(self.s, COMMAND.CREATE_NEW_FILE, data)

        if resp_code == RESP.OK:
            file_path = os.path.join(client_files_dir, file_name)

            # Create a new empty file
            with open(file_path, 'w'):
                pass

        LOG.debug("Received response of creation of new file (code:%s" % resp_code)

        return resp_code

    def delete_file(self, file_name):
        '''
        :param file_name: file to delete (string)
        :return: result of the deletion file on the server
        '''
        global client_files_dir
        LOG.debug("Request to server to delete file\"%s\"" % file_name)
        # tcp_send(self.s, COMMAND.DELETE_FILE, file_name)

        resp_code, _ = self.__sync_request(COMMAND.DELETE_FILE, file_name)

        # Receive response of deletion of the file
        # result, _ = parse_query(tcp_receive(self.s))
        LOG.debug("Received response of deletion file operation(code:%s)" % resp_code)

        if resp_code == RESP.OK:
            LOG.debug("File was successfully deleted on the server")

            # Delete local copy of the file
            self.delete_local_file_copy(file_name)

        elif resp_code == RESP.PERMISSION_ERROR:
            LOG.debug("Client doesn't have permission to delete file \"%s\"" % file_name)
        elif resp_code == RESP.FAIL:
            LOG.debug("Server couldn't delete requested file \"%s\"" % file_name)

        return resp_code

    def update_file_on_server(self, file_name, change_type, pos, key=""):
        LOG.debug("Request to update file on server \"%s\", (change_type:%s, pos:%s)" % (file_name, change_type, pos))

        # Block window in GUI, until we receive a response
        self.gui.block_text_window()

        data = pack_list([file_name, change_type, pos, key])
        resp_code, _ = self.__sync_request(COMMAND.UPDATE_FILE, data)

        LOG.debug("Received response on updating file (code:%s)" % resp_code)

        # Unblock window in GUI, if response is OK.
        # Also update status bar
        self.gui.set_notification_status("change in file", resp_code)
        if resp_code == RESP.OK:
            self.gui.unblock_text_window()

        return resp_code

    def change_access_to_file(self, file_name, needed_access):
        '''
        :param file_name: (string)
        :param needed_access: (enum) 0 - public, 1 - private
        :return: response code from the server
        '''
        LOG.debug("Request to change the access to file \"%s\", (needed access:%s)"
                  % (file_name, needed_access))

        data = pack_list([file_name, needed_access])
        resp_code, _ = self.__sync_request(COMMAND.CHANGE_ACCESS_TO_FILE, data)

        LOG.debug("Received response on changing access to file (code:%s)" % resp_code)
        return resp_code

    def delete_local_file_copy(self, file_name):
        file_path = os.path.join(client_files_dir, file_name)

        # print file_path
        if os.path.isfile(file_path):
            os.remove(file_path)
            LOG.debug("Local copy of file was deleted successfully")
        else:
            LOG.debug("Local copy of file can't be found. But file was deleted on the server")

    # Sync/Async functions ============================================================================
    def __sync_request(self, command, data=""):
        '''Send request and wait for response'''
        with self.__send_lock:
            req = pack_list([command, data])

            if self.__tcp_send(req):
                with self.__rcv_sync_msgs_lock:

                    LOG.info("Waiting for response...")
                    while len(self.__rcv_sync_msgs) <= 0:
                        self.__rcv_sync_msgs_lock.wait()
                    LOG.info("Receieved response...")

                    response = self.__rcv_sync_msgs.pop()
                    result, data = parse_query(response)

                    return result, data
            return None

    def __tcp_send(self, msg):
        '''Append the terminate character to the data'''
        m = msg + TERM_CHAR
        # m = m.encode('utf-8')

        r = False
        try:
            self.s.sendall(m)
            r = True
        except KeyboardInterrupt:
            self.s.close()
            logging.info('Ctrl+C issued, terminating ...')
        except socket_error as e:
            if e.errno == 107:
                logging.warn('Server closed connection, terminating ...')
            else:
                logging.error('Connection error: %s' % str(e))
            self.s.close()
            logging.info('Disconnected')
        return r

    # Recognize different responses from server (can be notification or answer on requested command)
    def __sync_response(self, rsp):
        '''Collect the received response, notify waiting threads'''
        with self.__rcv_sync_msgs_lock:
            was_empty = len(self.__rcv_sync_msgs) <= 0
            self.__rcv_sync_msgs.append(rsp)

            if was_empty:
                self.__rcv_sync_msgs_lock.notifyAll()

    def __async_notification(self, msg):
        '''Collect the received server notifications, notify waiting threads'''
        with self.__rcv_async_msgs_lock:
            was_empty = len(self.__rcv_async_msgs) <= 0
            self.__rcv_async_msgs.append(msg)
            if was_empty:
                self.__rcv_async_msgs_lock.notifyAll()

    def __tcp_receive(self, buffer_size=BUFFER_SIZE):
        m = ''
        while 1:
            try:
                # Receive one block of data according to receive buffer size
                block = self.s.recv(buffer_size)
                m += block

            except socket_error as (code, msg):
                if code == 10054:
                    LOG.error('Server is not available.')
                else:
                    LOG.error('Socket error occurred. Error code: %s, %s' % (code, msg))
                return None

            if m.endswith(TERM_CHAR):
                break
        return m[:-len(TERM_CHAR)]

    # Main loops for threads (receive/sending) =========================================================
    def main_app_loop(self):
        '''Network Receiver/Message Processor loop'''
        LOG.info('Falling into receiver loop ...')
        while 1:
            m = self.__tcp_receive()

            if not m or len(m) <= 0:
                break

            # Check the received message
            command, data = parse_query(m)

            # Case: notification arrived
            if command in notification_commands:
                logging.debug('Server wants to notify me: %s' % m)
                self.__async_notification(m)

            # Case: response on requested command
            else:
                self.__sync_response(m)

    # Loop for iterating over received notifications
    def notifications_loop(self):
        logging.info('Falling into notifier loop ...')

        while True:
            # Wait if the we our asynchronous list is empty
            # When something will be received, we will start processing it
            with self.__rcv_async_msgs_lock:
                if len(self.__rcv_async_msgs) <= 0:
                    self.__rcv_async_msgs_lock.wait()

                # Fetch arrived message, and process it
                msg = self.__rcv_async_msgs.pop(0)
                notification, change = parse_query(msg)

                if notification == COMMAND.NOTIFICATION.UPDATE_FILE:
                    self.gui.notification_update_file(change)

                elif notification == COMMAND.NOTIFICATION.FILE_CREATION:
                    self.gui.notification_file_creation(change)

                elif notification == COMMAND.NOTIFICATION.FILE_DELETION:
                    self.gui.notification_file_deletion(change)

                elif notification == COMMAND.NOTIFICATION.CHANGED_ACCESS_TO_FILE:
                    self.gui.notification_changed_access_to_file(change)

            LOG.info('Server Notification: %s' % msg)


# Main part of client application
def main():
    root = Tkinter.Tk(className="Text editor (:")
    client = Client()

    # Try to connect until we exactly connect to the server (limit 5 tries)
    try_num, tries_number = 0, 5
    while not client.s and try_num != tries_number:
        client.connect_to_server()
        try_num += 1

    # If connection is established, launch the GUI
    if client.s:
        # Create 2 separate threads for asynchronous notifications and for main app
        main_app_thread = Thread(name='MainApplicationThread', target=client.main_app_loop)
        notifications_thread = Thread(name='NotificationsThread', target=client.notifications_loop)

        main_app_thread.start()
        notifications_thread.start()

        # Synchronize client id
        client.sync_user_id()

        gui = GUI(root, client)
        client.gui = gui

        # Launch GUI window
        root.mainloop()

        # Blocks until the thread finished the work.
        main_app_thread.join()
        notifications_thread.join()

    # Close socket it there're some problems
    if client.s:
        close_socket(client.s, "Close client socket.")
    print 'Terminating ...'


if __name__ == '__main__':
    main()
