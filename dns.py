# -*- encoding: utf-8 -*-
import logging
import struct
from SocketServer import ThreadingUDPServer, BaseRequestHandler, UDPServer
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, timeout
import sys, os
from common import *

gl_remote_server = None

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig()
logger = logging.getLogger("dns")
    
def cache_wrapper(func, cache={}):
    def cache_func(self, data):
        resp = cache.get(data)
        if not resp:
            resp = func(self, data)
            cache[data] = resp
        return resp
    if DEF_CACHE:
        return cache_func      
    else:
        return func

class LocalDNSHandler(BaseRequestHandler):
    def setup(self):
        global gl_remote_server
        if not gl_remote_server:
            remote_server = DEF_REMOTE_SERVER
        else:
            remote_server = gl_remote_server
        self.dnsserver = (remote_server, DEF_PORT)
        self.tcp_socket = None 

    def handle(self):
        data, client_socket = self.request
        if DEF_CONNECTION == 'tcp':
            resp = self.tcp_response(data)
        else:
            resp = self._getResponse(data)
        try:
          client_socket.sendto(resp, 0, self.client_address)
        except StandardError as err:
          logger.debug(err)

    @cache_wrapper
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

    @cache_wrapper
    def tcp_response(self, data):
        """ tcp request dns data """        
        sock = self.get_tcp_sock()
        size_data = self.tcp_packet_head(data)
        sock.send(size_data + data)
        resp = sock.recv(1024)
        logger.debug("receive data:%s", resp.encode('hex'))
        sock.close()
        return self.packet_body(resp)

    def tcp_packet_head(self, data):
        size = len(data)
        size_data = struct.pack('!H', size)
        logger.debug("head data len: %d", size)
        logger.debug("head data: %s", size_data.encode('hex'))
        return size_data

    def packet_body(self, data):
        size = struct.unpack('!H', data[0:2])[0]
        logger.debug("response package size: %d", size)
        logger.debug("len of response: %d", len(data))
        return data[2:2 + size]

    def get_tcp_sock(self):
        tcp_sock = socket(AF_INET, SOCK_STREAM)
        tcp_sock.connect((DEF_REMOTE_SERVER, DEF_PORT))
        tcp_sock.settimeout(5)
        return tcp_sock

class LocalDNSServer(ThreadingUDPServer):
    pass

def main():
    global gl_remote_server
    try:
        if hasattr(sys, 'frozen'):
            dir = os.path.dirname(sys.executable)
        else:
            dir = os.path.dirname(__file__)
        confFile = os.path.join(dir, DEF_CONF_FILE)
        f = open(confFile, 'r')
        dns = f.read().split('=')
        f.close()
        if len(dns) == 2:
            if dns[0].strip().lower() == 'dns':
                gl_remote_server = dns[1].strip()
            else:
                pass
    except:
        pass
    dnsserver = LocalDNSServer((DEF_LOCAL_HOST, DEF_PORT), LocalDNSHandler)
    dnsserver.serve_forever()
    tcp_sock.close()

if __name__ == '__main__':
    main()
