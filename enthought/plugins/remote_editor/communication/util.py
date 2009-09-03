# Standard library imports
from errno import EINTR
import os
import select
import socket
from subprocess import Popen
import sys

# ETS imports
from enthought.etsconfig.api import ETSConfig

# An obscure ASCII character that we used as separators in socket streams
MESSAGE_SEP = chr(7) # 'bell' character

# The location of the server lock file and the communication log
LOCK_PATH = os.path.join(ETSConfig.application_data, 
                         'remote_editor_server.lock')
LOG_PATH = os.path.join(ETSConfig.application_data, 'remote_editor_server.log')


def spawn_independent(command, shell=False):
    """ Given a command suitable for 'Popen', open the process such that if this
        process is killed, the spawned process survives.
    """
    if sys.platform == 'win32':
        if isinstance(command, basestring):
            command = 'start /b ' + command
        else:
            command.insert(0, 'start')
            command.insert(1, '/b')
        Popen(command, shell=True)
    else:
        pid = os.fork()
        if pid:
            return
        else:
            os.setpgrp()
            Popen(command, shell=shell)
            sys.exit(0)


def get_server_port():
    """ Reads the server port from the lock file. If the file does not exist
        returns -1.
    """
    if os.path.exists(LOCK_PATH):
        f = open(LOCK_PATH, 'r')
        try:
            return int(f.read().strip())
        finally:
            f.close()
    else:
        return -1


def accept_no_intr(sock):
    """ Call sock.accept such that if it is interrupted by an EINTR
        ("Interrupted system call") signal or a KeyboardInterrupt exception, it
        is re-called.
    """
    while True:
        try:
            return sock.accept()
        except socket.error, err:
            if err[0] != EINTR:
                raise
        except KeyboardInterrupt:
            pass


def send(sock, command, arguments=''):
    """ Send a command with arguments (both strings) through a socket. This
        information is encoded with length information to ensure that everything
        is received.
    """
    sent, total = 0, 0
    msg = command + MESSAGE_SEP + arguments
    msg = str(len(msg)) + MESSAGE_SEP + msg
    length = len(msg)
    while total < length:
        msg = msg[sent:]
        sent = sock.send(msg)
        if not sent:
            raise socket.error
        total += sent


def send_port(port, command, arguments='', timeout=None):
    """ A send a command to a port. Convenience function that uses 'send'.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if timeout is not None:
        sock.settimeout(timeout)
    errno = sock.connect_ex(('localhost', port))
    if errno:
        sock.close()
        return False
    
    try:
        send(sock, command, arguments)
    except socket.error:
        return False
    finally:
        try:
            sock.shutdown(socket.SHUT_WR)
        except:
            pass
    return True

    
def receive(sock):
    """ Receive a command with arguments from a socket that was previously sent
        information with 'send'.
    """    
    index = -1
    chunk, length = '', ''
    received = False

    while not received:
        # Use select to query the socket for activity before calling sock.recv.
        # Choose a timeout of 60 seconds for now.
        readers, writers, in_error = select.select([sock], [], [], 60)

        for rsock in readers:
            while index == -1:
                length += chunk
                chunk = rsock.recv(4096)
                if not chunk:
                    raise socket.error
                index = chunk.find(MESSAGE_SEP)
            length = int(length + chunk[:index])

            msg = chunk[index+1:]
            while len(msg) < length:
                chunk = rsock.recv(length - len(msg))
                if not chunk:
                    raise socket.error
                msg += chunk
            received = True

    command, sep, arguments = msg.partition(MESSAGE_SEP)
    return command, arguments
