import sys
import socket
import random
import httplib
import argparse
from time import sleep
from utils import *
from datetime import datetime, timedelta
from os import system
import multiprocessing

def do_request_tcp(lst):
    server,port,data,silent=lst
    try:
        conn = httplib.HTTPConnection(server, port,timeout=1)
        conn.request("POST", "/", data)
    except Exception, ex:
        conn.close()
        return 0
    timestamp = now()
    if not silent: print self.send_message.format(**locals())

    src_port = conn.sock.getsockname()[1]
    try:
        r = conn.getresponse()
        r_len = len(r.read())
        timestamp = now()
        if not silent: print self.receive_message.format(**locals())
    except Exception, e:
        conn.close()
        return 0
    return 1
    conn.close()


class trafficGenerator(object):
    def __init__(self, server, iperf, iperf_bandwidth, iperf_threads, tcp_port, udp_port, max_bytes):
        """
        Initialize a traffic generator
        @param server: IP address of the server
        @param tcp_port: TCP port used by the server
        @param udp_port: UDP port used by the server
        @param max_bytes: Maximum number of bytes to be sent by the generator
        """
        self.server = server
        self.iperf = iperf
        self.iperf_bandwidth = iperf_bandwidth
        self.iperf_threads = iperf_threads
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.max_bytes = max_bytes
        self.send_message = "{counter} {timestamp}\t\t\t {protocol} sending  {amount:05} bytes to port {port:04}\t{dots}"
        self.send_iperf_message = "{counter} {timestamp}\t\t\t {protocol} bandwidth {iperf_bandwidth} threads {iperf_threads} to port {port:04}"
        self.receive_message = "{counter} {timestamp}\t {r.status} {r.reason} \t received {r_len:05} bytes from port {src_port}\n"

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
        serv=self.server
        #lst=[[serv, port, data,silent]]*100
        lst=[serv, port, data,silent]
        #pool=multiprocessing.Pool(100)
        #results=pool.map(do_request_tcp,lst)
        sum=do_request_tcp(lst)
        #pool.close()
        #pool.join()   
        #sum=0
        #for x in results:
        #    sum+=x 
        return sum


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

    def request_iperf_udp(self, amount, counter, silent):
        self.request_iperf("IPERF UDP", self.udp_port, amount, counter, silent, "-u")
        
    def request_iperf_tcp(self, amount, counter, silent):
        self.request_iperf("IPERF TCP", self.tcp_port, amount, counter, silent, "")

    def request_iperf(self, protocol, port, amount, counter, silent, extraflags):
        """
        Send an iPerf UDP request of the given amount to the server
        @param amount: The amount of data to be sent
        @param counter: The index of the current request in the test
        @param silent: Should logging output be suppressed
        """
        dots, data = self.get_data(amount)
        iperf = self.iperf
        server = self.server
        iperf_threads = self.iperf_threads
        iperf_bandwidth = self.iperf_bandwidth
        timestamp = now()
        if not silent: print self.send_iperf_message.format(**locals()) + "\n"

        system("{iperf} -c {server} {extraflags} -p {port} -b {iperf_bandwidth} -P {iperf_threads}".format(**locals()))
        

def main():
    """
    Generate network traffic based on user specified parameters
    """
    args = parser.parse_args()
    generator = trafficGenerator(args.server, args.iperf_bin, args.iperf_bandwidth, args.iperf_threads, args.tcp_port, args.udp_port, args.max_bytes )
    deadline = datetime.now()+timedelta(minutes=args.time)
    flows_counter = 0
    sleep(5)
    start_time = datetime.now()

    print "%s\tTEST STARTING: max_desired_runtime=%.3fm, desired_flows=%d, delay=%dms" %\
          (now(), args.time, args.num_of_flows, args.delay)
    try:
        while datetime.now() < deadline and flows_counter < args.num_of_flows:
            amount = random.randint(args.min_bytes, args.max_bytes)
            if args.use_iperf:
                request_func =\
                    generator.request_iperf_udp if (random.randint(1, 100) <= args.udp_percentage) else generator.request_iperf_tcp
            else:
                request_func =\
                    generator.request_udp if (random.randint(1, 100) <= args.udp_percentage) else generator.request_tcp
            if args.use_iperf:
                request_func(amount,flows_counter,args.silent)
            else:
                flows_counter+=request_func(amount,flows_counter,args.silent)
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
parser.add_argument('--iperf_bin', nargs='?', default=IPERF_PATH, type=str,
                    help='location of iperf')
parser.add_argument('--use_iperf', nargs='?', default=USE_IPERF, type=str2bool,
                    help='Use Iperf stresser')
parser.add_argument('--iperf_bandwidth', nargs='?', default=IPERF_BANDWIDTH, type=str,
                    help='iPerf bandwidth (0=unlimited)')
parser.add_argument('--iperf_threads', nargs='?', default=IPERF_THREADS, type=int,
                    help='Number of iperf threads')
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
