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
import os, threading
from gui import *
from socket import AF_INET, SOCK_STREAM, socket, error as socket_error
from protocol import tcp_send, tcp_receive, \
                     COMMAND, RESP, ACCESS, SEP, parse_query, \
                     SERVER_PORT, SERVER_INET_ADDR, close_socket


class Client(object):
    def __init__(self):
        self.s = None
        self.gui = None

    # Declare client socket and connecting
    def connect_to_server(self):
        s = socket(AF_INET, SOCK_STREAM)
        LOG.info('TCP Socket created and started connecting..')

        try:
            s.connect((SERVER_INET_ADDR, SERVER_PORT))
            self.s = s
            self.sync_user_id()
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
            tcp_send(self.s, COMMAND.NOTIFY_ABOUT_USER_ID, self.user_id)

            # Receive empty response about saving of user_id on the server
            _ = tcp_receive(self.s)

        # If the config was deleted or doesn't exist
        else:
            LOG.debug("Request to the server to generate a new user_id")
            tcp_send(self.s, COMMAND.GENERATE_USER_ID)

            # Get response from the server with user_id (_ is command/response)
            _, self.user_id = parse_query(tcp_receive(self.s))

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
        tcp_send(self.s, COMMAND.LIST_OF_ACCESIBLE_FILES)

        result, files = parse_query(tcp_receive(self.s))
        LOG.debug("Received response of available files")

        if result == RESP.OK:
            files = files.split(SEP)
        else:
            files = []

        return files

    def get_file_on_server(self, file_name):
        '''
        :param file_name: (string)
        :return: file content, if no errors
        '''
        LOG.debug("Request to server to get file")
        tcp_send(self.s, COMMAND.GET_FILE, file_name)

        resp_code, content = parse_query(tcp_receive(self.s))
        LOG.debug("Received response of getting file")

        return resp_code, content

    def create_new_file(self, file_name, access):
        '''
        :param file_name: name of file that should be created
        :param access: can be public or private (visible only for this client)
        :return: response code
        '''

        LOG.debug("Request to server to create a new file")
        data = file_name + SEP + access
        tcp_send(self.s, COMMAND.CREATE_NEW_FILE, data)

        response, _ = parse_query(tcp_receive(self.s))
        LOG.debug("Received response of creation of new file (code:%s" % response)

        return response

    def delete_file(self, file_name):
        '''
        :param file_name: file to delete (string)
        :return: result of the deletion file on the server
        '''
        LOG.debug("Request to server to delete file\"%s\"" % file_name)
        tcp_send(self.s, COMMAND.DELETE_FILE, file_name)

        # Receive response of deletion of the file
        result, files = parse_query(tcp_receive(self.s))
        LOG.debug("Received response of deletion file operation(code:%s)" % result)

        if result == RESP.OK:
            LOG.debug("File was successfully deleted on the server")

            # Delete local copy of the file
            try:
                os.remove(file_name)
                LOG.debug("Local copy of file was deleted successfully")
            except:
                LOG.debug("Local copy of file can't be found. But file was deleted on the server")
        elif result == RESP.PERMISSION_ERROR:
            LOG.debug("Client doesn't have permission to delete file \"%s\"" % file_name)
        elif result == RESP.FAIL:
            LOG.debug("Server couldn't delete requested file \"%s\"" % file_name)
            # LOG.debug("Client File \"%s\" was not deleted..." % file_name)

        return result


# Main part of client application
def start_gui(s, user_id):
    '''
    :param s: client socket (to communicate with a server)
    :return: -
    '''


    # List of accessible files
    files_to_edit = get_files_to_edit(s)
    # print(files_to_edit)


    # File deletion
    file_to_delete = "123.txt"
    del_res = delete_file(s, file_to_delete)


    # File creation
    # access = ACCESS.PUBLIC
    file_name, access = "new_file_3nd.txt", ACCESS.PRIVATE

    # Response on creation of new file
    new_file_res = create_new_file(s, file_name, access)

    if new_file_res == RESP.OK:
        LOG.info("Server created a new file successfully")

    elif new_file_res == RESP.FILE_ALREADY_EXISTS:
        LOG.error("File with requested name already exists")

    elif new_file_res == RESP.FAIL:
        LOG.error("Server couldn't create a new file with requested name")

    # TODO: Update file list in GUI if the result of file creation/deletion is OK, otherwise show error


    # TODO: Create asynchronous receiving to receive notification about file updating


    # Just testing R-R
    # tcp_send(s, "1|something")
    # resp = tcp_receive(s)
    # print "Response 1: %s, msg'len %s" % (resp, len(resp))
    #
    # # Test 2
    # tcp_send(s, "55|ccccccp")
    # print "Response 2: %s" % tcp_receive(s)
    #
    # # Test 3
    # tcp_send(s, "66|aaa")
    # print "Response 3: %s" % tcp_receive(s)


    # while True:
    #     print(2)

# def start_updater(user_id):
#     sock = __connect()
#     while True:
#         tcp_send(sock, COMMAND.WAITING_FOR_UPDATES)
#         res = tcp_receive(sock)
#         _, text = parse_query(res)
#         name_file, t = parse_query(text)


def main():
    root = Tkinter.Tk(className="Text editor (:")
    client = Client()

    # Connect until we connect to the server (limit 5 tries)
    try_num, tries_number = 0, 5
    while not client.s and try_num != tries_number:
        client.connect_to_server()
        try_num += 1

    # If connection is established, launch the gui
    if client.s:
        gui = GUI(root, client)
        client.gui = gui

        root.mainloop()

    # If user_id doesn't exist, server creates it.
    # Otherwise client notifies the server about its user_id
    # user_id = get_user_id(s)

    # # Start GUI and main program
    # start_gui(s, user_id)
    # updater_thread = threading.Thread(target=start_updater, args=(user_id,))
    # updater_thread.start()

    # Close socket it there're some problems
    if client.s:
        close_socket(client.s, "Close client socket.")
    print 'Terminating ...'


if __name__ == '__main__':
    main()
