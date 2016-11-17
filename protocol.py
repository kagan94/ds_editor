# Setup Python logging --------------------------------------------------------
import logging

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger()


# Info--------------------------------------------------------------------------
___NAME = "Protocol to the online document editor"
___VER = "0.0.1"

def __info():
    return '%s version %s' % (___NAME, ___VER)


# Imports----------------------------------------------------------------------
from socket import error as socket_error


# Extend our PYTHONPATH for working directory----------------------------------
from sys import path, argv, stdin
from os.path import abspath, sep
a_path = sep.join(abspath(argv[0]).split(sep)[:-1])
path.append(a_path)


# Common -----------------------------------------------------------------------
SERVER_PORT = 7778
SERVER_INET_ADDR = '127.0.0.1'

BUFFER_SIZE = 1024 # Receive not more than 1024 bytes per 1 msg
SEP = "|" # separate command and data in request
TIMEOUT = 5 # in seconds
TERM_CHAR = "|.|"


# "Enum" for commands
def enum(**vals):
    return type('Enum', (), vals)

COMMAND = enum(
    # From client to the Server
    GENERATE_USER_ID = '1',
    NOTIFY_ABOUT_USER_ID = '2',
    LIST_OF_ACCESIBLE_FILES = '3',
    DELETE_FILE = '4',
    # From Server to the client
    # RIGHT = 3,
    # LEFT = 4,
    # NONE = 0
)


# Responses
RESP = enum(
    OK = '0',
    FAIL = '1',
    PERMISSION_ERROR = '2',
    NOTIFY_ABOUT_USER_ID = '3', # notify server about user id
)

# Main functions ---------------------------------------------------------------
def tcp_send(sock, command, data=""):
    '''  TCP send request
    @param sock: TCP socket
    @param command: Command to the server/client
    @param data: The data to be sent
    '''
    # print "data to send: %s, len: %s" % (data, len(data))
    query = str(command) + SEP + str(data) + TERM_CHAR
    sock.send(query)
    return len(query)


def tcp_send_all(sock, data):
    '''
    @param sock: TCP socket
    @param data: The data to be sent
    '''
    # print "data to send: %s, len: %s" % (data, len(data))
    data += TERM_CHAR
    sock.sendall(data)
    return len(data)


def tcp_receive(sock, buffer_size=BUFFER_SIZE):
    '''
    :param sock: TCP socket
    :param buffer_size: max possible size of message per one receive call
    :return: message without terminate characters
    '''
    m = ''
    while 1:
        try:
            # Receive one block of data according to receive buffer size
            block = sock.recv(buffer_size)
            m += block
        except socket_error as (code, msg):
            if code == 10054:
                LOG.error('Server is not available.')
            else:
                LOG.error('Socket error occurred. Error code: %s, %s' % (code, msg))
            return None

        # print "received: %s, len: %s" % (block, len(block))
        # print m, TERM_CHAR, m.endswith(TERM_CHAR)

        # if m.endswith(TERM_CHAR) or len(block) <= 0:
        if m.endswith(TERM_CHAR):
            break
    return m[:-len(TERM_CHAR)]



def parse_query(raw_data):
    '''
    :param raw_data: string that may contain command and data
    :return: (command, data)
    '''
    # Split string by separator to get the command and data
    raw_data = raw_data.split(SEP)
    command, data = raw_data[0], "".join(raw_data[1:])
    return command, data


# def tcp_receive(sock, buffer_size=BUFFER_SIZE):
#     '''
#     :param sock: TCP socket
#     :param buffer_size: max possible size of receiving message
#     :return: message without terminate characters
#     '''
#     m = sock.recv(buffer_size)
#     return m[:-len(TERM_CHAR)]


def close_socket(sock, log_msg=""):
    # Check if the socket is closed disconnected already ( in case there can
    # be no I/O descriptor
    try:
        sock.fileno()
    except socket_error:
        LOG.debug('Socket closed already ...')
        return

    # Close socket, remove I/O descriptor
    sock.close()

    if len(log_msg) > 0:
        LOG.debug(log_msg)
