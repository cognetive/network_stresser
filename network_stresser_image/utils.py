import sys, traceback
from datetime import datetime

USE_IPERF = False
TCP_PORT = 80
UDP_PORT = 8080
ALL_IPS = "0.0.0.0"
LOCALHOST = "127.0.0.1"
MIN_BYTES = 100
MAX_BYTES = 1000
BUFF_SIZE = 2000
NUM_OF_FLOWS = 1000
DELAY = 1000 # in milliseconds
IPERF_PATH = "/usr/bin/iperf"
PYTHON_PATH = "/usr/bin/python2.7"

def log_receive(protocol, bytes):
    print "%s\t%s\treceived %d bytes\n" % (now(), protocol, bytes)

def now():
    """
    Print the current time
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

def str2bool(v):
    """
    Convert string to boolean value
    @param v: The string to convert
    @return: A boolean value matching the given string
    @raise: argparse.ArgumentTypeError if the string does not match any value which can be interpreted as boolean
    """
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def handle_exception():
    print "An exception occurred:"
    print '-' * 60
    traceback.print_exc(file=sys.stdout)
    print '-' * 60