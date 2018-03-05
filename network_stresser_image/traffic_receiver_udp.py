import socket
import argparse
from utils import *


def run(port, buffer_size, silent):
    """
    Listen on the given port for UDP traffic
    @param port: Port to listen on
    @param buffer_size: Size of the buffer used to accept data from the socket
    @param silent: Should logging output be suppressed
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ALL_IPS, port))
    print "Starting UDP server on port %d..." % (port,)
    while True:
        try:
            data, addr = sock.recvfrom(buffer_size)  # buffer size is 1024 bytes
            if not silent: log_receive("UDP", len(data))
        except KeyboardInterrupt:
            exit()
        except Exception:
            handle_exception()


parser = argparse.ArgumentParser(description='Receive UDP network traffic.')
parser.add_argument('--port', nargs='?', default=UDP_PORT, type=int,
                    help='Port of the server')
parser.add_argument('--buffer_size', nargs='?', default=MAX_BYTES, type=int,
                    help='UDP buffer size')
parser.add_argument('--silent', nargs='?', default=False, type=str2bool,
                    help='Suppress output')


if __name__ == "__main__":
    args = parser.parse_args()
    run(args.port, args.buffer_size, args.silent)

