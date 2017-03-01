import logging
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s %(levelname)s %(name)s:%(lineno)d] %(message)s')
logger = logging.getLogger("dns_forward")

from socket import socket, AF_INET, SOCK_DGRAM, timeout

from gevent.server import DatagramServer
from gevent import monkey
monkey.patch_all()

LISTEN_PORT = 53
TIMEOUT = 5
LOCAL_HOST = "0.0.0.0"
DOMESTIC_DNS = "10.16.0.1"
REMOTE_UDP_DNS_PORT = 53
TEST_SERVER_ADDR = "127.0.0.1" 
TEST_SERVER_PORT = 5300

class LocalDNSServer(DatagramServer):
    def handle(self, data, addr):
        resp = self.normal_response(data)
        logger.debug("finish")
        try:
            self.socket.sendto(resp, 0, addr)
        except StandardError as err:
            logging.debug(err)

    def normal_response(self, data):
        sock = socket(AF_INET, SOCK_DGRAM)  # socket for the remote DNS server
        sock.connect((DOMESTIC_DNS, REMOTE_UDP_DNS_PORT))
        new_sock = socket(AF_INET, SOCK_DGRAM)  # socket for the test DNS server
        new_sock.connect((TEST_SERVER_ADDR, TEST_SERVER_PORT))
        sock.sendall(data)
        new_sock.sendall(data)
        logger.debug("send to test server")
        try:
            resp = sock.recv(65535)
        except Exception, e:
            logging.debug('%s ignored.', e)
            return ''
        sock.close()
        return resp

def main():
    listener = LOCAL_HOST + ":" + str(LISTEN_PORT)
    dnsserver = LocalDNSServer(listener)
    dnsserver.serve_forever()


if __name__ == '__main__':
    main()
