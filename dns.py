# -*- encoding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import logging
from socket import socket, AF_INET, SOCK_DGRAM, timeout

from common import DEBUG,LISTEN_PORT,AUTHORIZED_DNS_SERVER,\
    DEF_CONNECTION, DEF_TIMEOUT, DEF_LOCAL_HOST, \
    REMOTE_UDP_DNS_PORT, DEF_DOMESTIC_DNS  

import domainpattern
import cache
from tcp_dns import TCP_Handle
from gevent.server import DatagramServer

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(filename="pydnsproxy.log")

logger = logging.getLogger('dns')
class LocalDNSServer(DatagramServer, TCP_Handle):
    def handle(self, data, addr):
        if DEF_CONNECTION == 'tcp':
          self.match_query = self.tcp_response
        else:
          self.match_query = self.normal_response
        url = self.extract_url(data)
        resp = self.match_query(data)
        try:
            self.socket.sendto(resp, 0, addr)
        except StandardError as err:
            logging.debug(err)

    #@cache.memorized_domain
    def normal_response(self, data):
        sock = socket(AF_INET, SOCK_DGRAM) # socket for the remote DNS server
        sock.connect((DEF_DOMESTIC_DNS, REMOTE_UDP_DNS_PORT))
        sock.sendall(data)
        try:
            resp = sock.recv(65535)
        except Exception, e:
            logging.debug('%s ignored.', e)
            return ''
        sock.close()
        return resp

    @cache.memorized_domain
    def get_response_normal(self, data):
        """ get the DNS result from local DNS server """
        logging.debug("normal dns req")
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.connect(self.normal_dns_server)
        sock.sendall(data)
        sock.settimeout(5)
        resp = ""
        try:
          resp = sock.recv(65535)
          logging.debug("normal dns reply:%s", resp.encode("hex"))
        except Exception as err:
          logging.debug('%s ignored', err.message)
        sock.close()
        return resp

def main():
    listener = DEF_LOCAL_HOST +":"+ str(LISTEN_PORT)
    dnsserver = LocalDNSServer(listener)
    dnsserver.serve_forever()

if __name__ == '__main__':
    main()
