#! /usr/bin/env python
# -*- coding: utf-8 -*-

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
import os
from sys import path, argv
a_path = os.path.sep.join(os.path.abspath(argv[0]).split(os.path.sep)[:-1])
path.append(a_path)


# Local copies of files on the client side
current_path = os.path.abspath(os.path.dirname(__file__))
client_files_dir = os.path.join(current_path, "client_local_files")


# Common -----------------------------------------------------------------------
SERVER_PORT = 7778
SERVER_INET_ADDR = '127.0.0.1'

BUFFER_SIZE = 1024  # Receive not more than 1024 bytes per 1 msg
SEP = "|"  # separate command and data in request
TIMEOUT = 5  # in seconds
TERM_CHAR = "|.|"


# "Enum" for commands
def enum(**vals):
    return type('Enum', (), vals)

COMMAND = enum(
    # From client to the Server
    GENERATE_USER_ID='1',
    NOTIFY_ABOUT_USER_ID='2',
    LIST_OF_ACCESIBLE_FILES='3',
    CREATE_NEW_FILE='4',
    GET_FILE='5',
    DELETE_FILE='6',
    UPDATE_FILE='7',
    CHANGE_ACCESS_TO_FILE='8',

    # Notifications from the server
    NOTIFICATION=enum(
        UPDATE_FILE='9',
        FILE_CREATION='10',
        FILE_DELETION='11',
        CHANGED_ACCESS_TO_FILE='12'
    )
)


# Responses
RESP = enum(
    OK='0',
    FAIL='1',
    PERMISSION_ERROR='2', # in case of deletion of file
    FILE_ALREADY_EXISTS='3',
    FILE_DOES_NOT_EXIST='4',
    NOTIFY_ABOUT_USER_ID='5', # notify server about user id
)

# Access to the file
ACCESS = enum(
    PUBLIC='0',
    PRIVATE='1'
)

CHANGE_TYPE = enum(
    DELETE='0',
    BACKSPACE='1',
    ENTER='2',
    INSERT='3'
)


# Main functions ---------------------------------------------------------------
def error_code_to_string(err_code):
    '''
    :param err_code: code of the error
    :return: (string) defenition of the error
    '''
    global RESP

    err_text = ""

    if err_code == RESP.OK:
        err_text = "No errors"
    elif err_code == RESP.FAIL:
        err_text = "Bad result."
    elif err_code == RESP.PERMISSION_ERROR:
        err_text = "Permissions error."
    elif err_code == RESP.FILE_ALREADY_EXISTS:
        err_text = "Requested file already exists."
    elif err_code == RESP.FILE_DOES_NOT_EXIST:
        err_text = "Requested file doesn't exist."
    return err_text


def tcp_send(sock, command, data=""):
    '''  TCP send request
    @param sock: TCP socket
    @param command: Command to the server/client
    @param data: The data to be sent
    '''
    # print "data to send: %s, len: %s" % (data, len(data))
    query = str(command) + SEP + str(data) + TERM_CHAR
    # query = query.decode('utf-8')

    try:
        sock.sendall(query)
        return True
    except:
        return False


def tcp_receive(sock, buffer_size=BUFFER_SIZE):
    '''
    :param sock: TCP socket
    :param buffer_size: max possible size of message per one receive call
    :return: message without terminate characters
    '''
    m = ''
    while 1:
        try:
            # print "receive waiting.."
            # Receive one block of data according to receive buffer size
            block = sock.recv(buffer_size)
            # print repr(block)
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

    # m = m.decode('utf-8')
    return m[:-len(TERM_CHAR)]


def parse_query(raw_data):
    '''
    :param raw_data: string that may contain command and data
    :return: (command, data)
    '''
    # Split string by separator to get the command and data
    # print raw_data
    cleaned_data = raw_data.split(SEP)
    command, data = cleaned_data[0], raw_data[len(cleaned_data[0]) + 1:]
    return command, data


def close_socket(sock, log_msg=""):
    # Check if the socket is closed already
    # in this case there can be no I/O descriptor
    try:
        sock.fileno()
    except socket_error:
        LOG.debug('Socket closed already ...')
        return

    # Close socket, remove I/O descriptor
    sock.close()

    if len(log_msg) > 0:
        LOG.debug(log_msg)


# This function is used in gui.py, server.py
def parse_change(change, case_update_file=False):
    '''
    :param change: (string)
    :param case_update_file: (Boolean)
    :return: splitted given data by SEP
        Notice: In case case_update_file = True it will return:
        file_name(str), change_type(enum), pos(str, format "x.y"), key (str, optional argument)
    '''
    cleaned_data = change.split(SEP)

    if not case_update_file:
        return cleaned_data

    # Fix. Char "|" can also be written by user
    # That's why we need to split given data correctly
    else:
        file_name, change_type, pos = cleaned_data[:3]

        three_args_length = sum(len(s) for s in cleaned_data[:3]) + 3
        key = change[three_args_length:]

        return file_name, change_type, pos, key


# This function is used in client.py
# (need to parse get_file response)
# NOTICE: Content should not be splitted, because it may contain separator
def parse_get_file_response(raw_data):
    '''
    :param data: raw_data
    :return: am_i_owner (Boolean), file_access (enum), content (string)
    '''
    cleaned_data = raw_data.split(SEP)
    am_i_owner, file_access = cleaned_data[:2]

    two_args_length = sum(len(s) for s in cleaned_data[:2]) + 2
    content = raw_data[two_args_length:]

    return am_i_owner, file_access, content


# Used in both client.py/server.py
def pack_list(target_list):
    '''
    :param target_list: (list)
    :return: joined list elements by separator
    '''
    content = SEP.join(target_list)
    return content
