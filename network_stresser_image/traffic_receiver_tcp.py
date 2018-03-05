import argparse
from utils import *
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


SILENT = False


class Serve(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        self._set_headers()
        self.wfile.write("<html><body><h1>received</h1></body></html>")

    def log_message(self, format, *args):
        content_len = int(self.headers.getheader('content-length', 0))
        if not SILENT: log_receive("TCP", content_len)


def run(port, silent):
    """
    Listen on the given port for TCP traffic
    @param port: Port to listen on
    @param silent: Should logging output be suppressed
    """
    server_class = HTTPServer
    handler_class = Serve
    global SILENT
    SILENT = silent

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print "Starting TCP server on port %d..." % (port,)
    while True:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            exit()
        except Exception:
            handle_exception()


parser = argparse.ArgumentParser(description='Receive TCP network traffic.')
parser.add_argument('--port', nargs='?', default=TCP_PORT, type=int,
                    help='Port of the server')
parser.add_argument('--silent', nargs='?', default=False, type=str2bool,
                    help='Suppress output')


if __name__ == "__main__":
    args = parser.parse_args()
    run(args.port, args.silent)

