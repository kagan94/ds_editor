#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Setup Python logging -------------------------------------------------------
import logging

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger()


# Imports----------------------------------------------------------------------
from protocol import SERVER_PORT, SERVER_INET_ADDR, BUFFER_SIZE, SEP, close_socket, tcp_send, socket_receive_all, TERM_CHAR
from socket import AF_INET, SOCK_STREAM, socket, error as socket_error
import threading, os, time


# Main function ---------------------------------------------------

global lock
lock = threading.Lock()


def handler(c_socket):
    '''
    :param c_socket: client socket
    :return: -
    '''

    connection_n = threading.currentThread().getName().split("-")[1]
    LOG.debug("Client %s connected:" % connection_n)
    LOG.debug("Client's socket info: %s:%d’:" % c_socket.getsockname())

    dir_files = os.getcwd() + "\\files\\"

    # TODO: Create client id if not exist

    # # Receive
    # data = c_socket.recv(BUFFER_SIZE)
    # parse = data.split(SEP)
    #
    # print(parse[0], parse[1])

    # get request 1
    print(socket_receive_all(c_socket))

    # Request - response 1
    tcp_send(c_socket, "1|xxxx")
    print(socket_receive_all(c_socket))

    # Request - response 2
    tcp_send(c_socket, "2|notification")
    print(socket_receive_all(c_socket))

    # response 2
    tcp_send(c_socket, "5|Got it!")

    # while 1:

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