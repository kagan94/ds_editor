# Setup Python logging --------------------------------------------------------
import logging

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger()

# Common
SERVER_PORT = 7778
SERVER_INET_ADDR = '127.0.0.1'

# Receive not more than 1024 bytes per 1 msg
BUFFER_SIZE = 1024
SEP = "|"
TIMEOUT = 5 # seconds
TERM_CHAR = "|.|"






# Imports----------------------------------------------------------------------
from socket import SHUT_WR, SHUT_RD
from socket import socket, AF_INET, SOCK_STREAM
from socket import error as soc_err
from exceptions import Exception

# extend our PYTHONPATH for working directory
from sys import path, argv, stdin
from os.path import abspath, sep
a_path = sep.join(abspath(argv[0]).split(sep)[:-1])
path.append(a_path)


# TERM_CHAR = "\n"
TEMP_DIR = "D:/temp_dir/"



# Server vars
# Do the file flush when the file size equals the "flush_size"
# needs to not keep a huge amount of the data in RAM (we just save it from time to time)
FLUSH_SIZE = BUFFER_SIZE  * 100


# Commands --------------------------------------------------------------------
COMMAND_CHECK_FILE_EXISTENCE = "check_file_existence"
COMMAND_CHECK_SPACE_FOR_FILE = "check_space_for_file"
COMMAND_GET_LIST_OF_FILES = "get_list_of_files"
COMMAND_DOWNLOAD_FILE = "download_file"

# Responses--------------------------------------------------------------------
__RSP_OK = '0'
__RSP_FAIL = '1'


# Info--------------------------------------------------------------------------
___NAME = "Protocol to file uploading/downloading"
___VER = "0.0.1"


def __info():
    return '%s version %s' % (___NAME, ___VER)


def prepare_query(command, data = ""):
    # Command structure (ex: command:data\n)

    return ACTION_SEP.join((command, data))


def send_query(s, query):
    # s - socket

    LOG.debug("Query to send: %s" % query)
    s.send(query + TERM_CHAR)


def parse_query(raw_data):
    # Return: (command, data)

    # remove term charm from the end
    raw_data = raw_data[:-len(TERM_CHAR)]

    return raw_data.split(ACTION_SEP)


def tcp_send(sock, data):
    '''
    @param sock: TCP socket, used to send/receive
    @param data: The data to be sent
    '''
    # print "data to send: %s, len: %s" % (data, len(data))
    data += TERM_CHAR
    sock.send(data)
    return len(data)


def socket_receive(sock, buffer_size=BUFFER_SIZE):
    return sock.recv(buffer_size)


def socket_receive_all(sock, buffer_size=BUFFER_SIZE):
    m = ''
    while 1:
        # Receive one block of data according to receive buffer size
        block = sock.recv(buffer_size)
        # stop receiving once the first empty block was received
        m += block
        # print "received: %s, len: %s" % (block, len(block))
        if len(block) <= 0 or m.endswith(TERM_CHAR):
            # print "BREAK"
            break
    return m[:-len(TERM_CHAR)]


def tcp_receive_single_and_parse(socket):
    # receive request, and detect the command from client socket
    # return: command, data

    data = socket.recv(BUFFER_SIZE)
    return parse_query(data)


def close_socket(sock, log_msg=""):
    # Check if the socket is closed disconnected already ( in case there can
    # be no I/O descriptor
    try:
        sock.fileno()
    except soc_err:
        LOG.debug('Socket closed already ...')
        return

    # Close socket, remove I/O descriptor
    sock.close()

    if len(log_msg) > 0:
        LOG.debug(log_msg)
