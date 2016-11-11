#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Setup Python logging -------------------------------------------------------
import logging
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG,format=FORMAT)
LOG = logging.getLogger()
LOG.info('Client-side started working...')

# Imports----------------------------------------------------------------------
from protocol import socket_receive_all, TERM_CHAR, SERVER_PORT,SERVER_INET_ADDR, BUFFER_SIZE, SEP, close_socket, socket_receive, tcp_send
from socket import AF_INET, SOCK_STREAM, socket, error as socket_error




# Declare client socket and connecting
def __connect():
    s = socket(AF_INET, SOCK_STREAM)

    try:
        s.connect((SERVER_INET_ADDR, SERVER_PORT))
    except socket_error as (code, msg):
        if code == 10061:
            LOG.error('Socket error occurred. Server does not respond.')
        else:
            LOG.error('Socket error occurred. Error code: %s, %s' % (code, msg))
        return None

    LOG.info('TCP Socket created and start connecting..')
    return s


# Main part of client application
def start_gui(s):
    '''
    :param s: client socket (to communicate with a server)
    :return: -
    '''

    # TODO: Check id and send to the server
    # id is given by the server. If not exist, server creates it and it to the client



    # R-R
    tcp_send(s, "1|something")
    resp = socket_receive_all(s)
    print "Response 1: %s, msg'len %s" % (resp, len(resp))

    # try:
    #     answer = socket_receive(s)
    #     res = answer.split(SEP)
    #
    #     print(res)
    # except socket_error as (code, msg):
    #     if code == 10054:
    #         LOG.error('Server is not available.')
    #     else:
    #         LOG.error('Socket error occurred. Error code: %s, %s' % (code, msg))
    #     return None


    # Test 2
    tcp_send(s, "55|ccccccp")
    print "Response 2: %s" % socket_receive_all(s)

    # Test 3
    tcp_send(s, "66|aaa")
    print "Response 3: %s" % socket_receive_all(s)


    # while True:
    #     print(2)


def main():
    s = __connect()

    # If socked was not created, then exit
    if s is None: return

    # Start GUI and main program
    start_gui(s)

    # Close socket it there're some problems
    close_socket(s, "Close client socket.")

    # Wait for user input before terminating application
    # raw_input('Press Enter to terminate ...')
    print 'Terminating ...'


if __name__ == '__main__':
    main()