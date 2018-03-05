import sys
import socket
import random
import httplib
import argparse
from time import sleep
from utils import *
from datetime import datetime, timedelta


class trafficGenerator(object):
    def __init__(self, server, tcp_port, udp_port, max_bytes):
        """
        Initialize a traffic generator
        @param server: IP address of the server
        @param tcp_port: TCP port used by the server
        @param udp_port: UDP port used by the server
        @param max_bytes: Maximum number of bytes to be sent by the generator
        """
        self.server = server
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.max_bytes = max_bytes
        self.send_message = "{counter} {timestamp}\t\t\t {protocol} sending  {amount:05} bytes to {port:04}\t{dots}"
        self.receive_message = "{counter} {timestamp}\t {r.status} {r.reason} \t received {r_len:05} bytes from {src_port}\n"

    def get_data(self, amount):
        """
        Generate the given amount of data
        @param amount: The amount of data to generate
        @return: The generate data
        """
        return self.dots(amount), "X" * amount

    def dots(self, requested_amount):
        """
        Generate a string composed of '.', in a length that matched the requested amount of data, relative to the
            maximum amount of data possible
        @param requested_amount: The amount of data to be sent
        @return: The string of '.'
        """
        return int(round(requested_amount * 15.0 / self.max_bytes)) * "."

    def request_tcp(self, amount, counter, silent):
        """
        Send a TCP request of the given amount to the server
        @param amount: The amount of data to be sent
        @param counter: The index of the current request in the test
        @param silent: Should logging output be suppressed
        """
        dots, data = self.get_data(amount)
        port = self.tcp_port
        protocol = "TCP"

        conn = httplib.HTTPConnection(self.server, port)
        conn.request("POST", "/", data)
        timestamp = now()
        if not silent: print self.send_message.format(**locals())

        src_port = conn.sock.getsockname()[1]
        try:
            r = conn.getresponse()
            r_len = len(r.read())
            timestamp = now()
            if not silent: print self.receive_message.format(**locals())
        except Exception, e:
            print "Error occurred: %s" % (e.message,)

        conn.close()

    def request_udp(self, amount, counter, silent):
        """
        Send a UDP request of the given amount to the server
        @param amount: The amount of data to be sent
        @param counter: The index of the current request in the test
        @param silent: Should logging output be suppressed
        """
        dots, data = self.get_data(amount)
        port = self.udp_port
        protocol = "UDP"
        timestamp = now()
        if not silent: print self.send_message.format(**locals()) + "\n"

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data, (self.server, port))
        sock.close()


def main():
    """
    Generate network traffic based on user specified parameters
    """
    args = parser.parse_args()
    generator = trafficGenerator(args.server, args.tcp_port, args.udp_port, args.max_bytes)
    deadline = datetime.now()+timedelta(minutes=args.time)
    flows_counter = 0
    start_time = datetime.now()

    print "%s\tTEST STARTING: min_runtime=%.3fm min_flows=%d delay=%dms" %\
          (now(), args.time, args.num_of_flows, args.delay)
    try:
        while datetime.now() < deadline or flows_counter < args.num_of_flows:
            flows_counter += 1
            amount = random.randint(args.min_bytes, args.max_bytes)
            request_func =\
                generator.request_udp if (random.randint(1, 100) <= args.udp_percentage) else generator.request_tcp
            request_func(amount, flows_counter, args.silent)
            sleep(args.delay/1000.0)

    except KeyboardInterrupt:
        print "Exiting by user request..."

    total_runtime = (datetime.now() - start_time).total_seconds()
    flows_per_sec = flows_counter / total_runtime
    print "%s\tTEST COMPLETE: total_runtime=%.3fmin flows=%d flows_per_sec=%.3f" %\
          (now(), total_runtime/60.0, flows_counter, flows_per_sec)


parser = argparse.ArgumentParser(description='Generate network traffic as a stress test.')
parser.add_argument('--server', nargs='?', default=LOCALHOST,
                    help='IP address of the server')
parser.add_argument('--tcp_port', nargs='?', default=TCP_PORT, type=int,
                    help='TCP port of the server')
parser.add_argument('--udp_port', nargs='?', default=UDP_PORT, type=int,
                    help='UDP port of the server')
parser.add_argument('--udp_percentage', nargs='?', default=0, type=int,
                    help='The percentage of the flows to be created over UDP (0 to 100)')
parser.add_argument('--min_bytes', nargs='?', default=MIN_BYTES, type=int,
                    help='Minimum number of bytes to send')
parser.add_argument('--max_bytes', nargs='?', default=MAX_BYTES, type=int,
                    help='Maximum number of bytes to send')
parser.add_argument('--num_of_flows', nargs='?', default=0, type=int,
                    help='Minimum number of flows to generate')
parser.add_argument('--time', nargs='?', default=0, type=float,
                    help='Minimum length of time to generate traffic (in minutes)')
parser.add_argument('--delay', nargs='?', default=DELAY, type=int,
                    help='Delay between flows (in milliseconds)')
parser.add_argument('--silent', nargs='?', default=False, type=str2bool,
                    help='Suppress output')


if __name__ == "__main__":
    main()
