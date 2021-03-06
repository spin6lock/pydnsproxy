# -*- encoding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import logging
from socket import socket, AF_INET, SOCK_DGRAM, timeout

from common import DEBUG,LISTEN_PORT,AUTHORIZED_DNS_SERVER,\
    CONNECTION, TIMEOUT, LOCAL_HOST, \
    REMOTE_UDP_DNS_PORT, DOMESTIC_DNS

import domainpattern
import cache
from tcp_dns import TCP_Handle
from http_dns import HttpDnsHandle
from gevent.server import DatagramServer

log_format = '[%(asctime)s %(levelname)s %(name)s:%(lineno)d] %(message)s'
if DEBUG:
    logging.basicConfig(level=logging.DEBUG, format=log_format)
else:
    logging.basicConfig(filename="pydnsproxy.log", format=log_format)

logger = logging.getLogger('dns')


class LocalDNSServer(DatagramServer, TCP_Handle, HttpDnsHandle):
    def handle(self, data, addr):
        if CONNECTION == 'tcp':
            self.match_query = self.tcp_response
        elif CONNECTION == "http":
            self.match_query = self.http_response
        else:
            self.match_query = self.normal_response
        resp = self.match_query(data)
        try:
            self.socket.sendto(resp, 0, addr)
        except StandardError as err:
            logging.debug(err)

    def normal_response(self, data):
        labels, _ = cache.unpack_name(data, 12)
        logger.debug("udp resolv:%s", '.'.join(labels))
        sock = socket(AF_INET, SOCK_DGRAM)  # socket for the remote DNS server
        sock.connect((DOMESTIC_DNS, REMOTE_UDP_DNS_PORT))
        sock.sendall(data)
        sock.settimeout(5)
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
