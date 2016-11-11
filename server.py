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



def main_old(s, cs):
    # receive request, and detect the command
    command, data = tcp_receive_single_and_parse(client_socket)
    LOG.debug("Request is received. Start to proceed the command...")

    # Case 1: File uploading
    if command in [COMMAND_CHECK_FILE_EXISTENCE]:
        # Step 1
        # Check file existence before uploading

        full_file_name = TEMP_DIR + data

        res = __RSP_OK if not os.path.isfile(full_file_name) else __RSP_FAIL

        client_socket.send(res)
        LOG.debug("The response of check on file existence was sent to the client.")

        if res != __RSP_OK:
            LOG.info("Requested file exists in the temp folder.")
            return

        LOG.info("Requested file does not exist in the temp folder.")

        # Step 2
        # Check free memory space, before uploading

        # Receive request from the client
        _, needed_memory = tcp_receive_single_and_parse(client_socket)

        res = __RSP_OK if check_necessary_usage(needed_memory, TEMP_DIR) else __RSP_FAIL

        client_socket.send(res)
        LOG.debug("The response of check of the free memory space was sent to the client.")

        if res != __RSP_OK:
            LOG.info("The free space in the folder is not enough to save the file.")
            return

        tf = open(full_file_name, "wb")
        LOG.debug("Temporary file \"%s\" was created." % tf.name)

        # Step 3
        # Uploading the file
        data, received_data = None, b""
        flush_count = 1
        res = __RSP_OK

        try:
            # Receive the file
            while data != "":
                data = client_socket.recv(BUFFER_SIZE)
                received_data += data

                # Calculate when we should flush the file
                flush_num = int(float(getsizeof(received_data)) / float(FLUSH_SIZE))

                if flush_num == flush_count:
                    tf.flush()

                    LOG.debug("File was flushed. Flush #%s." % flush_count)
                    flush_count += 1

            LOG.debug('Received %s bytes and saved in the file.' % getsizeof(received_data))
            tf.write(received_data)

            tf.close()
            LOG.debug('Temp file was successfully saved and closed.')

        except socket_error as (code, msg):
            res = __RSP_FAIL

            LOG.error('Socket error occurred. Error code: %s, %s' % (code, msg))

            os.remove(tf.name)
            LOG.info('Temporary file was removed.')

        # Send back the result of file uploading
        client_socket.send(res)

    # # Case 2: File downloading
    # elif command == COMMAND_DOWNLOAD_FILE:
    #     full_file_name = TEMP_DIR + data
    #     res = b""
    #
    #     if not os.path.isfile(full_file_name):
    #         LOG.error("The file to download does not exist. (Empty request will be sent)")
    #     else:
    #         # Read and send the file
    #         with open(full_file_name, "rb") as f:
    #             res = f.read()
    #
    #         LOG.debug("Send the file to the client.")
    #
    #     tcp_send(client_socket, res)
    #
    # # Case 3: Get list of files in temp folder
    # elif command == COMMAND_GET_LIST_OF_FILES:
    #     res = os.listdir(TEMP_DIR)
    #     res = "\n".join(res)
    #
    #     LOG.debug("Send list of all files in the temp folder.")
    #     client_socket.sendall(res)



def handler(c_socket):
    '''
    :param c_socket: client socket
    :return: -
    '''

    connection_n = threading.currentThread().getName().split("-")[1]
    LOG.debug("Client %s connected:" % connection_n)
    LOG.debug("Client's socket info: %s:%d’:" % c_socket.getsockname())

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