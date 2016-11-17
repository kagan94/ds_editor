#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Setup Python logging -------------------------------------------------------
import logging

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger()


# Imports----------------------------------------------------------------------
from protocol import SERVER_PORT, SERVER_INET_ADDR, tcp_send, tcp_receive, tcp_send_all, close_socket, \
                     COMMAND, RESP, SEP, parse_query
from socket import AF_INET, SOCK_STREAM, socket, error as socket_error
import threading, os
import uuid  # for generating unique uuid
import ConfigParser as CP # for server settings

global lock
lock = threading.Lock()
current_path = os.path.abspath(os.path.dirname(__file__))
config_file_path = current_path + "\\server_config.ini"


def server_config_file():
    '''
    :return: config object
    '''
    global config_file_path, lock
    lock.acquire()

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

    lock.release()
    return conf


def limited_files_from_config(conf, user_id):
    '''
    :param conf: config object
    :param user_id: (string)
    :return: list of limited files
    '''
    try:
        return [file_name for (file_name, owner) in conf.items('LIMITED_FILES') if owner != user_id]
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
        owner_id = conf.get('LIMITED_FILES', file_name)
        return owner_id == user_id

    # If there's no owner of the file
    except:
        return True


def remove_option_from_config(config, section, option):
    try:
        config.remove_option(section, option)
        LOG.info("Option(%s) was deleted successfully" % option)
    except:
        LOG.error("Option(%s) cannot be deleted" % option)


def remove_file(config, file_path, user_id):
    '''
    :param config: config object
    :param file_name: (string)
    :param user_id: (string)
    :return: result of deletion (enum)
    '''
    file_name = os.path.basename(file_path)

    if is_user_owner_of_file(config, file_name, user_id):
        try:
            os.remove(file_path)

            # remove file from config
            remove_option_from_config(config, "OWNERS_FILES", file_name)
            remove_option_from_config(config, "LIMITED_FILES", file_name)

            resp = RESP.OK
        except:
            resp = RESP.FAIL
    else:
        resp = RESP.PERMISSION_ERROR

    return resp


# Main function ---------------------------------------------------
def handler(c_socket):
    '''
    :param c_socket: client socket
    :return: -
    '''

    connection_n = threading.currentThread().getName().split("-")[1]
    LOG.debug("Client %s connected:" % connection_n)
    LOG.debug("Client's socket info: %s:%d’:" % c_socket.getsockname())

    user_id = ""
    dir_files = os.getcwd() + "\\files\\"
    conf = server_config_file()

    while 1:
        command, data = parse_query(tcp_receive(c_socket))
        LOG.debug("Client's request (%s) - %s|%s" % (c_socket.getsockname(), command, data[:10] + "..."))

        if command == COMMAND.GENERATE_USER_ID:
            # make a unique user_id based on the host ID and current time
            user_id = uuid.uuid1()
            tcp_send(c_socket, RESP.OK, user_id)
            LOG.debug("Server generated a new user_id (%s) and sent it to the client" % user_id)

        elif command == COMMAND.NOTIFY_ABOUT_USER_ID:
            user_id = data
            LOG.debug("Client sent his existing user_id (%s)" % user_id)

            tcp_send(c_socket, RESP.OK)
            LOG.debug("Empty request with acknowledgement about receiving user_id was sent to the client")

        elif command == COMMAND.LIST_OF_ACCESIBLE_FILES:
            LOG.debug("Client requested to get a list of available files (client:%s...)" % user_id[:7])

            all_files = [f for f in os.listdir(dir_files) if os.path.isfile(os.path.join(dir_files, f))]
            limited_files = limited_files_from_config(conf, user_id)
            available_files = set(all_files) - set(limited_files)

            tcp_send(c_socket, RESP.OK, SEP.join(available_files))
            LOG.debug("List of available files was sent to the client (:%s...)" % user_id[:7])

        elif command == COMMAND.DELETE_FILE:
            LOG.debug("Client requested to delete a file \"%s\" (client:%s...)" % (data, user_id[:7]))

            lock.acquire()
            resp = remove_file(config=conf, file_path=dir_files + data, user_id=user_id)
            lock.release()

            tcp_send(c_socket, resp)
            LOG.debug("Response(code:%s) of file deletion was sent to the client (:%s...)" % (resp, user_id[:7]))

    # # Receive
    # data = c_socket.recv(BUFFER_SIZE)
    # parse = data.split(SEP)
    #
    # print(parse[0], parse[1])

    # get request 1
    # print(tcp_receive(c_socket))
    #
    # # Request - response 1
    # tcp_send(c_socket, "1|xxxx")
    # print(tcp_receive(c_socket))
    #
    # # Request - response 2
    # tcp_send(c_socket, "2|notification")
    # print(tcp_receive(c_socket))
    #
    # # response 2
    # tcp_send(c_socket, "5|Got it!")

    # lock.acquire()
    # # Do something
    # client_socket.send(BUFFER_SIZE)
    # lock.acquire()
    # # lock.release()

    close_socket(c_socket, 'Close client socket.')



def main():
    LOG.info('Application started and server socket created')

    s = socket(AF_INET, SOCK_STREAM)
    s.bind((SERVER_INET_ADDR, SERVER_PORT))

    # Socket in the listening state
    LOG.info("Waiting for a client connection...")
    # If we want to limit # of connections, then change 0 to # of possible connections
    s.listen(0)

    threads = []

    while 1:
        # Client connected
        client_socket, addr = s.accept()
        LOG.debug("New Client connected.")

        # For each connection create a new thread
        t = threading.Thread(target=handler, args=(client_socket,))
        threads.append(t)
        t.start()

        # TODO: if server wants, break while

    # Terminating application
    close_socket(s, 'Close server socket.')


if __name__ == '__main__':
    main()