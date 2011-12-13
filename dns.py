# -*- encoding: utf-8 -*-
import logging
from SocketServer import ThreadingUDPServer, BaseRequestHandler, UDPServer
from socket import socket, AF_INET, SOCK_DGRAM, timeout

from common import DEF_MULTITHREAD, DEBUG, DEF_DNS_IF_MATCH_PATTERN, DEF_PORT, \
    DEF_CONNECTION, DEF_TIMEOUT, DEF_LOCAL_HOST, DEF_DNS_IF_DOESNT_MATCH

import domainpattern
import cache
from tcp_dns import TCP_Handle

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig()
    file_handler = logging.FileHandler('pydnsproxy.log', 'a')
    logging.root.addHandler(file_handler)
logger = logging.getLogger("dns")

class LocalDNSHandler(BaseRequestHandler, TCP_Handle):
    def setup(self):
        if DEF_CONNECTION == 'tcp':
          self.match_query = self.tcp_response
        else:
          self.match_query = self._getResponse
        self.query_with_no_match = self.get_response_normal
        self.tcp_dns_server = DEF_DNS_IF_MATCH_PATTERN
        self.normal_dns_server = (DEF_DNS_IF_DOESNT_MATCH, DEF_PORT)
        self.dnsserver = (DEF_DNS_IF_MATCH_PATTERN, DEF_PORT)

    def handle(self):
        data, client_socket = self.request
        url = self.extract_url(data)
        if domainpattern.is_match(url):
            logger.debug("match pattern, use dns:%s", DEF_DNS_IF_MATCH_PATTERN)
            resp = self.match_query(data)
        else:
            logger.debug("doesn't match pattern, use dns:%s", DEF_DNS_IF_DOESNT_MATCH)
            resp = self.query_with_no_match(data)
        try:
            client_socket.sendto(resp, 0, self.client_address)
        except StandardError as err:
            logger.debug(err)

    @cache.memorized_domain
    def _getResponse(self, data):
        "Send client's DNS request (data) to remote DNS server, and return its response."
        sock = socket(AF_INET, SOCK_DGRAM) # socket for the remote DNS server
        sock.connect(self.dnsserver)
        sock.sendall(data)
        sock.settimeout(5)
        try:
            rspdata = sock.recv(65535)
        except Exception, e:
            logger.debug('%s ignored.', e)
            return ''
        # "delicious food" for GFW:
        while 1:
            sock.settimeout(DEF_TIMEOUT)
            try:
                rspdata = sock.recv(65535)
            except timeout:
                break
        sock.close()
        return rspdata

    @cache.memorized_domain
    def get_response_normal(self, data):
        """ get the DNS result from local DNS server """
        logger.debug("normal dns req")
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.connect(self.normal_dns_server)
        sock.sendall(data)
        sock.settimeout(5)
        try:
          resp = sock.recv(65535)
          logger.debug("normal dns reply:%s", resp.encode("hex"))
        except Exception as err:
          logger.debug('%s ignored', err.message)
        sock.close()
        return resp

if DEF_MULTITHREAD:
    class LocalDNSServer(ThreadingUDPServer):
        pass
else:
    class LocalDNSServer(UDPServer):
        pass

def main():
    dnsserver = LocalDNSServer((DEF_LOCAL_HOST, DEF_PORT), LocalDNSHandler)
    dnsserver.serve_forever()

if __name__ == '__main__':
    main()
