#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Setup Python logging -------------------------------------------------------
import logging

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger()


# Imports----------------------------------------------------------------------
from protocol import SERVER_PORT, SERVER_INET_ADDR, tcp_send, tcp_receive, tcp_send_all, close_socket, \
                     COMMAND, RESP, parse_query
from socket import AF_INET, SOCK_STREAM, socket, error as socket_error
import threading, os, time
import uuid  # for generating unique uuid


global lock
lock = threading.Lock()


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

    while 1:
        # TODO: Create client id if not exist

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

    # # Receive
    # data = c_socket.recv(BUFFER_SIZE)
    # parse = data.split(SEP)
    #
    # print(parse[0], parse[1])

    # get request 1
    print(tcp_receive(c_socket))

    # Request - response 1
    tcp_send(c_socket, "1|xxxx")
    print(tcp_receive(c_socket))

    # Request - response 2
    tcp_send(c_socket, "2|notification")
    print(tcp_receive(c_socket))

    # response 2
    tcp_send(c_socket, "5|Got it!")

    # lock.acquire()
    # # Do something
    # client_socket.send(BUFFER_SIZE)
    # lock.release()

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