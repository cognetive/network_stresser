import argparse
from os import system
from utils import *

def run(python, iperf, tcp_receiver, udp_receiver, use_iperf, tcp_port, udp_port, buff_size, silent):
    """
    Initialise the TCP and UDP servers
    @param python: Path to Python binary
    @param tcp_receiver: Path to the TCP server Python script
    @param udp_receiver:  Path to the UDP server Python script
    @param tcp_port: TCP port to be used by the TCP server
    @param udp_port:  UDP port to be used by the UDP server
    @param buff_size: Size of the buffer to be used by the UDP server
    @param silent: Should logging output be suppressed
    """
    if use_iperf:
        system("{iperf} -s -p {tcp_port} &".format(**locals()))
        system("{iperf} -s -p {udp_port}".format(**locals()))
    else:
        system("{python} {tcp_receiver} --port={tcp_port} --silent={silent} &".format(**locals()))
        system("{python} {udp_receiver} --port={udp_port} --buffer_size={buff_size} --silent={silent}".format(**locals()))


parser = argparse.ArgumentParser(description='Receive network traffic.')
parser.add_argument('--python_bin', nargs='?', default=PYTHON_PATH, type=str,
                    help='location of python2.7')
parser.add_argument('--iperf_bin', nargs='?', default=IPERF_PATH, type=str,
                    help='location of iperf')
parser.add_argument('--tcp_receiver', nargs='?', type=str,
                    help='location of TCP receiver')
parser.add_argument('--udp_receiver', nargs='?', type=str,
                    help='location of UDP receiver')
parser.add_argument('--use_iperf', nargs='?', default=USE_IPERF, type=str2bool,
                    help='Use Iperf stresser')
parser.add_argument('--tcp_port', nargs='?', default=TCP_PORT, type=int,
                    help='TCP port of the server')
parser.add_argument('--udp_port', nargs='?', default=UDP_PORT, type=int,
                    help='UDP port of the server')
parser.add_argument('--buffer_size', nargs='?', default=BUFF_SIZE, type=int,
                    help='UDP buffer size')
parser.add_argument('--silent', nargs='?', default=False, type=str2bool,
                    help='Suppress output')


if __name__ == "__main__":
    args = parser.parse_args()
    run(
        args.python_bin, args.iperf_bin, args.tcp_receiver, args.udp_receiver, args.use_iperf,
        args.tcp_port, args.udp_port, args.buffer_size, args.silent
    )

