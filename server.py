#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Setup Python logging -------------------------------------------------------
import logging

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger()


# Imports----------------------------------------------------------------------
from protocol import SERVER_PORT, SERVER_INET_ADDR, tcp_send, tcp_receive, close_socket, \
                     COMMAND, RESP, ACCESS, CHANGE_TYPE, SEP, parse_query
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, socket, error as socket_error
import threading, os
from threading import Lock
import uuid  # for generating unique uuid
import ConfigParser as CP # for server settings

lock = threading.Lock()
changes = []

current_path = os.path.abspath(os.path.dirname(__file__))
config_file_path = os.path.join(current_path, "server_config.ini")
dir_files = os.path.join(os.getcwd(), "server_files")


# Functions to work with config -----------------------------------
def server_config_file():
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


def save_config(config):
    '''
    :param config: config object
    :return: -
    '''
    global config_file_path
    with open(config_file_path, 'w') as cf:
        config.write(cf)


def limited_files_from_config(user_id):
    global lock
    '''
    :param conf: config object
    :param user_id: (string)
    :return: list of limited files
    '''

    lock.acquire()
    config = server_config_file()
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


def is_user_owner_of_file(conf, file_name, user_id):
    '''
    :param conf: config object
    :param file_name: (string)
    :param user_id: (string)
    :return: (Boolean)
    '''
    try:
        files = conf.get("OWNERS_FILES", user_id).split(SEP)
        return file_name in files

    # If there's no owner of the file
    except:
        return True


# def user_has_access_to_file(conf, file_name, user_id):
#
#     if is_user_owner_of_file(conf, file_name, user_id) or ....:
#         return True
#
#     return False


def value_of_option_from_config(config, section, option):
    try:
        val = config.get(section, option)
    except:
        val = None
    return val


def remove_option_from_config(config, section, option):
    try:
        config.remove_option(section, option)
        LOG.info("Option(%s) was deleted successfully" % option)
    except:
        LOG.error("Option(%s) cannot be deleted" % option)




# Main functions -------------------------------------------------
def create_file(file_name, user_id, access):
    '''
    :param config: config object
    :param file_name: (string)
    :param user_id: (string)
    :param access: can be private or
    :return:
    '''
    lock.acquire()

    res = RESP.OK
    full_file_path = dir_files + "\\" + file_name
    config = server_config_file()

    if not os.path.isfile(full_file_path):
        # Create empty file
        with open(full_file_path, "w") as f:
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
        res = RESP.FILE_ALREADY_EXISTS

    # if there're some changes - save them
    save_config(config)
    lock.release()

    return res


def get_file_content(file_name, user_id):
    '''
    :param file_name: (string)
    :return: content from the file (string)
    '''
    global dir_files
    file_path = os.path.join(dir_files, file_name)
    limited_files = limited_files_from_config(user_id)
    content, resp = "", RESP.OK

    lock.acquire()

    if os.path.isfile(file_path):
        # Check user's permissions
        if file_name not in limited_files:
            with open(file_path, "r") as f:
                content = f.read()
        else:
            resp = RESP.PERMISSION_ERROR
    else:
        resp = RESP.FILE_DOES_NOT_EXIST

    lock.release()

    return resp, content


def update_file(file_name, change_type, pos, key=""):
    '''
    :param file_name: (string)
    :param change_type: (enum) can be DELETE/BACKSPACE/INSERT/ENTER
    :param pos: position of change in the text in format x.y
    :param key: (string) - optional, it's letter
    :return:
    '''
    global dir_files, changes, lock

    file_path = os.path.join(dir_files, file_name)
    resp = RESP.OK
    row, i = list(map(int, pos.split(".")))  # i-index(column)

    lock.acquire()

    # Add change from client into the queue "changes"
    change = [file_name, change_type, pos, key]
    changes.append(change)

    # Strategy:
    # We read existing file, make some changes, and save this file

    with open(file_path, "r") as f:
        lines = f.read().split("\n")

    # print "============="
    # print line, row, i, len(lines), lines, len(line)

    # Notice: row - 1 because in tkinter rows start from index "1"
    line = lines[row - 1]

    if change_type == CHANGE_TYPE.DELETE:
        # Case: Delete the next existing char
        if i + 1 <= len(line):
            lines[row - 1] = line[:i] + line[i + 1:]

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
        if i - 1 >= 0:
            lines[row - 1] = line[:i - 1] + line[i:]

        # Case: delete previous line if exist
        elif row - 1 > 0 and i - 1 < 0:
            lines[row - 2] += lines[row - 1]

            # Delete appended line
            lines.pop(row - 1)

    elif change_type == CHANGE_TYPE.ENTER:
        # Split text (if needed) and separate 2 lines
        head, tail = line[:i], line[i:]

        lines[row - 1] = head

        # Case: user pressed enter in the text
        if row < len(lines):
            lines.insert(row, tail)

        # Case: user pressed enter on the last line (maybe even not in the end of text)
        elif row == len(lines):
            lines.append(tail)

    elif change_type == CHANGE_TYPE.INSERT:
        lines[row - 1] = line[:i] + key + line[i:]

    # Write new changes into file
    with open(file_path, "w") as f:
        f.write("\n".join(lines))

    lock.release()

    return resp


def remove_file(file_path, user_id):
    global lock
    '''
    :param config: config object
    :param file_name: (string)
    :param user_id: (string)
    :return: result of deletion (enum)
    '''

    lock.acquire()

    file_name = os.path.basename(file_path)
    config = server_config_file()

    if is_user_owner_of_file(config, file_name, user_id):
        try:
            os.remove(file_path)

            # remove file from config
            remove_option_from_config(config, "OWNERS_FILES", file_name)

            # Remove file from limited files from config
            files = value_of_option_from_config(config, "LIMITED_FILES", user_id)
            files = files.split(SEP) if files else []

            if file_name in files:
                files.remove(file_name)
                config.set("LIMITED_FILES", user_id, SEP.join(files))

            resp = RESP.OK
        except:
            resp = RESP.FAIL
    else:
        resp = RESP.FILE_ALREADY_EXISTS

    save_config(config)
    lock.release()

    return resp


# Main handler ---------------------------------------------------
class EditSession(threading.Thread):

    def __init__(self, client_sock, client_sock_address):
        threading.Thread.__init__(self)
        self.__sock = client_sock
        self.__addr = client_sock_address
        self.__send_lock = Lock()
        self.__filename = None

    def notify(self, file_name, change_type, pos, key):
        if self.waiting_for_update:
            sending_data = SEP.join((file_name, change_type, pos, key))
            tcp_send(self.__sock, COMMAND.UPDATE_NOTIFICATION, sending_data)


    def run(self):
        global dir_files, lock

        current_thread = threading.current_thread()
        connection_n = current_thread.getName().split("-")[1]
        current_thread.socket = self.__sock

        LOG.debug("Client %s connected:" % connection_n)
        LOG.debug("Client's socket info: %s:%d’:" % self.__sock.getsockname())

        user_id = ""

        while True:
            command, data = parse_query(tcp_receive(self.__sock))
            LOG.debug("Client's request (%s) - %s|%s" % (self.__sock.getsockname(), command, data[:10] + "..."))

            current_thread.waiting_for_update = False

            if command == COMMAND.GENERATE_USER_ID:
                # make a unique user_id based on the host ID and current time
                user_id = uuid.uuid1()
                tcp_send(self.__sock, RESP.OK, user_id)
                LOG.debug("Server generated a new user_id (%s) and sent it to client" % user_id)

            elif command == COMMAND.NOTIFY_ABOUT_USER_ID:
                user_id = data
                LOG.debug("Client sent his existing user_id (%s)" % user_id)

                tcp_send(self.__sock, RESP.OK)
                LOG.debug("Empty request with acknowledgement about receiving user_id was sent to client")

            elif command == COMMAND.LIST_OF_ACCESIBLE_FILES:
                LOG.debug("Client requested to get a list of available files (client:%s...)" % user_id[:7])

                all_files = [f for f in os.listdir(dir_files) if os.path.isfile(os.path.join(dir_files, f))]
                limited_files = limited_files_from_config(user_id)
                available_files = set(all_files) - set(limited_files)

                tcp_send(self.__sock, RESP.OK, SEP.join(available_files))
                LOG.debug("List of available files was sent to client (:%s...)" % user_id[:7])

            elif command == COMMAND.GET_FILE:
                file_name = data
                LOG.debug("Client requested to get file \"%s\" (client:%s...)" % (file_name, user_id[:7]))

                resp, content = get_file_content(file_name, user_id)

                tcp_send(self.__sock, RESP.OK, content)
                LOG.debug("Response (code:%s) on getting requested file was sent to client (:%s...)" % (resp, user_id[:7]))

            elif command == COMMAND.CREATE_NEW_FILE:
                LOG.debug("Client requested to create a new file (client:%s...)" % user_id[:7])

                # print(data, SEP)
                file_name, access = data.split(SEP)
                resp = create_file(file_name, user_id, access)

                tcp_send(self.__sock, resp)
                LOG.debug("Response(code:%s) of file creation was sent to client (:%s...)" % (resp, user_id[:7]))

                # TODO: if response is OK and access is public, notify other clients

            elif command == COMMAND.DELETE_FILE:
                LOG.debug("Client requested to delete a file \"%s\" (client:%s...)" % (data, user_id[:7]))

                resp = remove_file(file_path=dir_files + data, user_id=user_id)

                tcp_send(self.__sock, resp)
                LOG.debug("Response(code:%s) of file deletion was sent to client (:%s...)" % (resp, user_id[:7]))

                # TODO: if response is OK, notify other clients

            elif command == COMMAND.UPDATE_FILE:
                LOG.debug("Client requested to update a file (client:%s...)" % user_id[:7])

                cleaned_data = data.split(SEP)
                file_name, change_type, pos = cleaned_data[:3]

                three_args_length = sum(len(s) for s in cleaned_data[:3]) + 3
                key = data[three_args_length:]

                print file_name, change_type, pos, key
                resp = update_file(file_name, change_type, pos, key)

                tcp_send(self.__sock, resp)
                LOG.debug("Response(code:%s) of change in file was sent to client (:%s...)" % (resp, user_id[:7]))

                for t in threading.enumerate():
                    if getattr(t, 'notify', False):
                        t.notify(file_name, change_type, pos, key)

            elif command == COMMAND.WAITING_FOR_UPDATES:
                current_thread.waiting_for_update = True

        close_socket(self.__sock, 'Close client socket.')



def main():
    LOG.info('Application started and server socket created')

    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 0)
    s.bind((SERVER_INET_ADDR, SERVER_PORT))

    # Socket in the listening state
    LOG.info("Waiting for a client connection...")

    # If we want to limit # of connections, then change 0 to # of possible connections
    s.listen(0)

    threads = []
    sessions = []
    while True:
        try:
            # Client connected
            client_socket, addr = s.accept()
            LOG.debug("New Client connected.")
            session = EditSession(client_socket, addr)
            sessions.append(session)
            session.start()

        except KeyboardInterrupt:
            LOG.info("Terminating by keyboard interrupt...")
            break
        except socket_error as err:
            LOG.error("Socket error - %s" % err)

    # Terminating application
    close_socket(s, 'Close server socket.')


if __name__ == '__main__':
    main()
