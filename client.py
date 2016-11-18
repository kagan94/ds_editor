#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Setup Python logging -------------------------------------------------------
import logging
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG,format=FORMAT)
LOG = logging.getLogger()
LOG.info('Client-side started working...')

# Imports----------------------------------------------------------------------
from protocol import tcp_send, tcp_receive, \
                     COMMAND, RESP, ACCESS, SEP, parse_query, \
                     SERVER_PORT, SERVER_INET_ADDR, close_socket
from socket import AF_INET, SOCK_STREAM, socket, error as socket_error
import ConfigParser as CP, os



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


def get_user_id(s):
    '''
    :param s: socket
    :return: user_id (string)
    '''
    # Path to the config file
    current_path = os.path.abspath(os.path.dirname(__file__))
    config_file = current_path + "\\config.ini"

    # If the config exists, get the user_id from it
    if os.path.isfile(config_file):
        conf = CP.ConfigParser()
        conf.read(config_file)
        user_id = conf.get('USER_INFO', 'user_id')

        LOG.debug("Notify server about existing user_id")
        tcp_send(s, COMMAND.NOTIFY_ABOUT_USER_ID, user_id)

        # Receive empty response about saving of user_id on the server
        _ = tcp_receive(s)

    # If the config was deleted or doesn't exist
    else:
        LOG.debug("Request to the server to generate a new user_id")
        tcp_send(s, COMMAND.GENERATE_USER_ID)

        # Get response from the server with user_id (_ is command/response)
        _, user_id = parse_query(tcp_receive(s))

        conf = CP.RawConfigParser()
        conf.add_section("USER_INFO")
        conf.set('USER_INFO', 'user_id', user_id)

        with open(config_file, 'w') as cf:
            conf.write(cf)

    return user_id


def get_files_to_edit(s):
    '''
    :param s: socket
    :return: list with file names that are possible to edit
    '''
    LOG.debug("Request to the server to get list of accessible files to edit")
    tcp_send(s, COMMAND.LIST_OF_ACCESIBLE_FILES)

    result, files = parse_query(tcp_receive(s))
    LOG.debug("Received response of available files")

    if result == RESP.OK:
        files = files.split(SEP)
    else:
        files = []

    return files


def create_new_file(s, file_name, access):
    '''
    :param s: socket
    :param file_name: name of file that should be created
    :param access: can be public or private (visible only for this client)
    :return: response code
    '''

    LOG.debug("Request to the server to create a new file")
    data = file_name + SEP + access
    tcp_send(s, COMMAND.CREATE_NEW_FILE, data)

    response, _ = parse_query(tcp_receive(s))
    LOG.debug("Received response of creation of new file (code:%s" % response)

    return response


def delete_file(s, file_name):
    '''
    :param s: socket
    :param file_name: file to delete (string)
    :return: result of the deletion file on the server
    '''
    LOG.debug("Request to the server to delete file\"%s\"" % file_name)
    tcp_send(s, COMMAND.DELETE_FILE, file_name)

    # Receive response of deletion of the file
    result, files = parse_query(tcp_receive(s))
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
def start_gui(s):
    '''
    :param s: client socket (to communicate with a server)
    :return: -
    '''

    # If user_id doesn't exist, server creates it.
    # Otherwise client notifies the server about its user_id
    user_id = get_user_id(s)


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

    #
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