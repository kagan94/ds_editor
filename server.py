#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Setup Python logging -------------------------------------------------------
import logging

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger()


# Imports----------------------------------------------------------------------
from protocol import SERVER_PORT, SERVER_INET_ADDR, tcp_send, tcp_receive, close_socket, \
                     COMMAND, RESP, ACCESS, CHANGE_TYPE, SEP, parse_change, parse_query, \
                     pack_list
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, socket, error as socket_error
import os, threading
import codecs  # encoding library
import uuid  # for generating unique uuid
import ConfigParser as CP  # for server settings


# Set encoding to utf-8 to understand ASCII symbols ---------------
# import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')


lock = threading.Lock()

current_path = os.path.abspath(os.path.dirname(__file__))
config_file_path = os.path.join(current_path, "server_config.ini")
dir_files = os.path.join(os.getcwd(), "server_files")


# If folder for server copies of files doesn't exist, then create it
if not os.path.exists(dir_files):
    os.makedirs(dir_files)


def value_of_option_from_config(config, section, option):
    try:
        val = config.get(section, option)
    except:
        val = None
    return val


class Server(object):
    def __init__(self):
        ''' Initialize "sessions" queue to collect client sessions '''
        self.sessions = []
        self.notifications = []

    def main_loop(self):
        ''' Main server loop. There server accepts clients and collect them into the session queue '''
        LOG.info('Application started and server socket created')

        s = socket(AF_INET, SOCK_STREAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 0)
        try:
            s.bind((SERVER_INET_ADDR, SERVER_PORT))
        except socket_error as (code, msg):
            if code == 10048:
                LOG.error("Server already started working..")
            return

        # Socket in the listening state
        LOG.info("Waiting for a client connection...")

        # If we want to limit # of connections, then change 0 to # of possible connections
        s.listen(0)

        while True:
            try:
                # Client connected
                client_socket, addr = s.accept()
                LOG.debug("New Client connected.")

                session = ClientSession(client_socket, addr, server=self)
                self.sessions.append(session)
                session.start()

            except KeyboardInterrupt:
                LOG.info("Terminating by keyboard interrupt...")
                break
            except socket_error as err:
                LOG.error("Socket error - %s" % err)

        # Terminating application
        close_socket(s, 'Close server socket.')

    # Functions to work with config -----------------------------------
    def server_config_file(self):
        '''
        :return: config object
        '''
        global config_file_path

        # Case 1: config exists
        if os.path.isfile(config_file_path):
            conf = CP.ConfigParser()
            conf.read(config_file_path)

        # Case 2: Config was deleted or doesn't exist
        else:
            conf = CP.RawConfigParser()
            conf.add_section("LIMITED_FILES")
            conf.add_section("OWNERS_FILES")

            with open(config_file_path, 'w') as cf:
                conf.write(cf)
        return conf

    def save_config(self, config):
        '''
        :param config: config object
        :return: -
        '''
        global config_file_path
        with open(config_file_path, 'w') as cf:
            config.write(cf)

    def limited_files_from_config(self, user_id):
        global lock
        '''
        :param conf: config object
        :param user_id: (string)
        :return: list of limited files
        '''

        lock.acquire()
        config = self.server_config_file()
        lock.release()

        try:
            limited_files = []
            for (owner_id, files) in config.items('LIMITED_FILES'):
                if owner_id != user_id:
                    for file_name in files.split(SEP):
                        limited_files.append(file_name)
            return limited_files
        except:
            return []

    def is_user_owner_of_file(self, config, file_name, user_id):
        '''
        :param conf: config object
        :param file_name: (string)
        :param user_id: (string)
        :return: (Boolean)
        '''
        try:
            files = config.get("OWNERS_FILES", user_id).split(SEP)
            return file_name in files
        # If there's no owner of the file
        except:
            return True

    def get_file_access(self, config, file_name):
        '''
        :param config: config object
        :param file_name: (string)
        :return: access to the file (enum). 0-Public, 1-Private
        '''
        # If file is in "limited files" section, then it's private
        for (owner_id, files) in config.items('LIMITED_FILES'):
            if file_name in files.split(SEP):
                return ACCESS.PRIVATE
        return ACCESS.PUBLIC

    def remove_option_from_config(self, config, section, option):
        try:
            config.remove_option(section, option)
            LOG.info("Option(%s) was deleted successfully" % option)
        except:
            LOG.error("Option(%s) cannot be deleted" % option)


    # Main functions -------------------------------------------------
    def create_file(self, file_name, user_id, access):
        '''
        :param file_name: (string)
        :param user_id: (string)
        :param access: can be public or private
        :return: response code
        '''
        global dir_files, lock

        lock.acquire()

        resp_code = RESP.OK
        file_path = os.path.join(dir_files, file_name)
        config = self.server_config_file()

        if not os.path.isfile(file_path):
            # Create empty file
            with open(file_path, "w") as f:
                pass

            # Writing in config
            try:
                user_files = config.get("OWNERS_FILES", user_id)
                config.set("OWNERS_FILES", user_id, user_files + SEP + file_name)
            except:
                config.set("OWNERS_FILES", user_id, file_name)

            # If file is only visible to the user
            if access == ACCESS.PRIVATE:
                try:
                    limited_files = config.get("LIMITED_FILES", user_id)
                    config.set("LIMITED_FILES", user_id, limited_files + SEP + file_name)
                except:
                    config.set("LIMITED_FILES", user_id, file_name)
        else:
            resp_code = RESP.FILE_ALREADY_EXISTS

        # if there're some changes - save them
        self.save_config(config)
        lock.release()

        return resp_code

    def get_file_content(self, file_name, user_id):
        '''
        :param file_name: (string)
        :param user_id: (string)
        :return: content from the file (string)
        '''
        global dir_files

        file_path = os.path.join(dir_files, file_name)
        limited_files = self.limited_files_from_config(user_id)
        content, resp_code = "", RESP.OK

        lock.acquire()
        config = self.server_config_file()

        if os.path.isfile(file_path):
            # Check user's permissions
            if file_name not in limited_files:
                with open(file_path, "r") as f:
                    content = f.read()
            else:
                resp_code = RESP.PERMISSION_ERROR
        else:
            resp_code = RESP.FILE_DOES_NOT_EXIST

        am_i_owner = self.is_user_owner_of_file(config, file_name, user_id)
        am_i_owner = "1" if am_i_owner else "0"

        file_access = self.get_file_access(config, file_name)

        lock.release()

        sending_data = pack_list([am_i_owner, file_access, content])
        return resp_code, sending_data

    def update_file(self, file_name, change_type, pos, key=""):
        '''
        :param file_name: (string)
        :param change_type: (enum) can be DELETE/BACKSPACE/INSERT/ENTER
        :param pos: position of change in the text in format x.y
        :param key: (string) - optional, it's letter
        :return:
        '''
        global dir_files, lock

        file_path = os.path.join(dir_files, file_name)
        resp = RESP.OK
        row, column = tuple(map(int, pos.split(".")))  # pos is tuple(row, column)

        # decode symbol to avoid problems with encoding
        key = key.decode("utf-8")

        lock.acquire()

        # Strategy:
        # We read existing file, make some changes, and save this file

        with codecs.open(file_path, "r", "utf-8") as f:
            lines = f.read()
            lines = lines.split("\n")

        # print "============="
        # print line, row, i, len(lines), lines, len(line)

        # Notice: row - 1 because in tkinter rows start from index "1"
        line = lines[row - 1]

        if change_type == CHANGE_TYPE.DELETE:
            # Case: Delete the next existing char
            if column + 1 <= len(line):
                lines[row - 1] = line[:column] + line[column + 1:]

            # Case: need to delete \n and append next line
            else:
                # Next line might not exist, that's why check it
                try:
                    next_line = lines[row]
                except IndexError:
                    next_line = None

                # Append next line to previous line
                if next_line is not None:
                    lines[row - 1] += next_line
                    lines.pop(row)  # delete appended line

        elif change_type == CHANGE_TYPE.BACKSPACE:
            # Case: delete previous character
            if column - 1 >= 0:
                lines[row - 1] = line[:column - 1] + line[column:]

            # Case: delete previous line if exist
            elif row - 1 > 0 and column - 1 < 0:
                lines[row - 2] += lines[row - 1]

                # Delete appended line
                lines.pop(row - 1)

        elif change_type == CHANGE_TYPE.ENTER:
            # Split text (if needed) and separate 2 lines
            head, tail = line[:column], line[column:]

            lines[row - 1] = head

            # Case: user pressed enter in the text
            if row < len(lines):
                lines.insert(row, tail)

            # Case: user pressed enter on the last line (maybe even not in the end of text)
            elif row == len(lines):
                lines.append(tail)

        elif change_type == CHANGE_TYPE.INSERT:
            lines[row - 1] = line[:column] + key + line[column:]

        # Write new changes into file
        with codecs.open(file_path, "w", "utf-8") as f:
            content = "\n".join(lines)
            f.write(content)

        lock.release()

        return resp

    def change_access_to_file(self, user_id, file_name, needed_access):
        '''
        :param user_id: (string)
        :param file_name: (string)
        :param needed_access: (enum)
        :return: response code
        '''
        global lock

        resp_code = RESP.OK

        lock.acquire()
        config = self.server_config_file()

        # Only owner can edit the access of the file
        if self.is_user_owner_of_file(config, file_name, user_id):
            files = value_of_option_from_config(config, "LIMITED_FILES", user_id)
            files = files.split(SEP) if files else []

            # Access to the file should be public
            if needed_access == ACCESS.PUBLIC:
                # Make access public by removing file from limited files
                if file_name in files:
                    files.remove(file_name)

            # Access to the file should be private
            else:
                # Add file to limited files (means file is private)
                if file_name not in files:
                    files.append(file_name)

            config.set("LIMITED_FILES", user_id, pack_list(files))
            self.save_config(config)

        # User wants to change access, but he/she is not owner of the file
        else:
            resp_code = RESP.PERMISSION_ERROR

        lock.release()

        return resp_code

    def remove_file(self, file_name, user_id):
        global dir_files, lock
        '''
        :param file_name: (string)
        :param user_id: (string)
        :return: response code (enum)
        '''
        file_path = os.path.join(dir_files, file_name)
        resp_code = RESP.OK

        lock.acquire()
        config = self.server_config_file()

        if self.is_user_owner_of_file(config, file_name, user_id):
            try:
                os.remove(file_path)

                # remove file from config
                self.remove_option_from_config(config, "OWNERS_FILES", file_name)

                # Remove file from limited files from config
                files = value_of_option_from_config(config, "LIMITED_FILES", user_id)
                files = files.split(SEP) if files else []

                if file_name in files:
                    files.remove(file_name)
                    config.set("LIMITED_FILES", user_id, pack_list(files))
            except:
                resp_code = RESP.FAIL
        else:
            resp_code = RESP.FILE_ALREADY_EXISTS

        self.save_config(config)
        lock.release()

        return resp_code

    def notify_other_clients(self):
        '''Function to notify other clients about changes'''

        while self.notifications:
            # Each change was packed in the following format [command, [arg1, arg2, arg_n]]
            change = self.notifications.pop(0)
            command = change.pop(0)
            change = change[0]

            for t in self.sessions:
                # print t.name
                t.notify(command, change)


# Main handler ---------------------------------------------------
class ClientSession(threading.Thread):
    def __init__(self, client_sock, client_sock_address, server):
        threading.Thread.__init__(self)
        self.server = server  # Server functions

        self.__sock = client_sock
        self.__addr = client_sock_address
        self.__send_lock = threading.Lock()
        self.__filename = None
        self.notify_me = True

    # Add notification into the notification queue
    def add_notification(self, change):
        '''
            All active user will receive notification, except initializer
        :param change: (list) [command, [info_about_changes]]
        '''
        self.notify_me = False
        self.server.notifications.append(change)

    def run(self):
        global dir_files, lock

        current_thread = threading.current_thread()
        connection_n = current_thread.getName().split("-")[1]
        current_thread.socket = self.__sock

        LOG.debug("Client %s connected:" % connection_n)
        LOG.debug("Client's socket info : %s:%d:" % self.__sock.getsockname())

        user_id = ""

        while True:
            msg = tcp_receive(self.__sock)
            resp_code, sending_data = RESP.OK, ""

            # Msg received successfully
            if msg:
                command, data = parse_query(msg)
                LOG.debug("Client's request (%s) - %s|%s" % (self.__sock.getsockname(), command, data[:10] + "..."))

            # Case: some problem with receiving data
            else:
                LOG.debug("Client(%s) closed the connection" % connection_n)
                break

            if command == COMMAND.GENERATE_USER_ID:
                # make a unique user_id based on the host ID and current time
                user_id = uuid.uuid1()

                resp_code, sending_data = RESP.OK, user_id
                LOG.debug("Server generated a new user_id (%s) and sent it to client" % user_id)

            elif command == COMMAND.NOTIFY_ABOUT_USER_ID:
                user_id = data
                LOG.debug("Client sent his existing user_id (%s)" % user_id)

                resp_code = RESP.OK
                LOG.debug("Empty request with acknowledgement about receiving user_id was sent to client")

            elif command == COMMAND.LIST_OF_ACCESIBLE_FILES:
                LOG.debug("Client requested to get a list of available files (client:%s...)" % user_id[:7])

                all_files = [f for f in os.listdir(dir_files) if os.path.isfile(os.path.join(dir_files, f))]
                limited_files = self.server.limited_files_from_config(user_id)
                available_files = set(all_files) - set(limited_files)

                resp_code, sending_data = RESP.OK, pack_list(available_files)
                LOG.debug("List of available files was sent to client (:%s...)" % user_id[:7])

            elif command == COMMAND.GET_FILE:
                file_name = data
                LOG.debug("Client requested to get file \"%s\" (client:%s...)" % (file_name, user_id[:7]))

                resp_code, sending_data = self.server.get_file_content(file_name, user_id)
                LOG.debug("Response (code:%s) on getting requested file was sent to client (:%s...)" % (resp_code, user_id[:7]))

            elif command == COMMAND.CREATE_NEW_FILE:
                LOG.debug("Client requested to create a new file (client:%s...)" % user_id[:7])

                # print(data, SEP)
                file_name, access = data.split(SEP)

                resp_code = self.server.create_file(file_name, user_id, access)
                LOG.debug("Response(code:%s) of file creation was sent to client (:%s...)" % (resp_code, user_id[:7]))

                # If access is public and result of file creation is OK, then notify other clients
                if access == ACCESS.PUBLIC and resp_code == RESP.OK:
                    change = [COMMAND.NOTIFICATION.FILE_CREATION, [file_name]]
                    self.add_notification(change)

            elif command == COMMAND.DELETE_FILE:
                LOG.debug("Client requested to delete a file \"%s\" (client:%s...)" % (data, user_id[:7]))

                file_name = data

                resp_code = self.server.remove_file(file_name, user_id=user_id)
                LOG.debug("Response(code:%s) of file deletion was sent to client (:%s...)" % (resp_code, user_id[:7]))

                # If response is OK, notify other clients about deletion of this file
                if resp_code == RESP.OK:
                    change = [COMMAND.NOTIFICATION.FILE_DELETION, [file_name]]
                    self.add_notification(change)

            elif command == COMMAND.UPDATE_FILE:
                LOG.debug("Client requested to update a file (client:%s...)" % user_id[:7])

                file_name, change_type, pos, key = parse_change(data, case_update_file=True)

                resp_code = self.server.update_file(file_name, change_type, pos, key)
                LOG.debug("Response(code:%s) of change in file was sent to client (:%s...)" % (resp_code, user_id[:7]))

                # Add change from client into the queue "changes"
                change = [COMMAND.NOTIFICATION.UPDATE_FILE, [file_name, change_type, pos, key]]
                self.add_notification(change)

            elif command == COMMAND.CHANGE_ACCESS_TO_FILE:
                LOG.debug("Client requested to update a file (client:%s...)" % user_id[:7])

                file_name, needed_access = parse_query(data)

                resp_code = self.server.change_access_to_file(user_id, file_name, needed_access)
                LOG.debug("Response(code:%s) of change in file was sent to client (:%s...)" % (resp_code, user_id[:7]))

                # If response is OK, notify other clients about deletion of this file
                if resp_code == RESP.OK:
                    change = [COMMAND.NOTIFICATION.CHANGED_ACCESS_TO_FILE, [file_name, needed_access]]
                    self.add_notification(change)

            # Send response on requested command
            res = tcp_send(self.__sock, resp_code, sending_data)

            # Trigger notify_clients function (if there're some changes in the queue, it will process them)
            self.server.notify_other_clients()

            # Case: some problem with receiving data
            if not res:
                LOG.debug("Client(%s, %s) closed the connection" % self.__sock.getsockname())
                break

        close_socket(self.__sock, 'Close client socket.')

    def notify(self, command, change):
        # Send notifications to all other users except the master
        if self.notify_me:
            sending_data = pack_list(change)
            tcp_send(self.__sock, command, sending_data)

        # Set current thread to "receive notifications" state
        self.notify_me = True


def main():
    server = Server()
    server.main_loop()


if __name__ == '__main__':
    main()
