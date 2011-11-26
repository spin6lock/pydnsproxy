# -*- encoding: utf-8 -*-
#import gevent.monkey
#gevent.monkey.patch_all()
import struct
import logging
import Queue
import struct
from SocketServer import ThreadingUDPServer, BaseRequestHandler, UDPServer
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, timeout
import sys, os

from common import *

import domainpattern

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
        self.domestic_dnsserver = (DEF_DOMESTIC_DNS, DEF_PORT)
        self.tcp_socket = None 

    def extract_url(self, data):
        logger.debug("raw dns request:%s", data.encode('hex'))
        #pass 12 bytes
        data = data[12:]
        #extract the url
        url = []
        start = 0
        len = ord(data[start])
        print "len:", len
        while len != 0:
            part = str(data[start + 1:start + 1 + len])
            print part
            url.append(part)
            start = start + len + 1
            len = ord(data[start])
        url = '.'.join(url)
        logger.debug("requesting url:%s", url)
        return url

    def handle(self):
        data, client_socket = self.request
        url = self.extract_url(data)
        if domainpattern.is_match(url):
            logger.debug("match pattern, use remote dns")
            if DEF_CONNECTION == 'tcp':
                resp = self.tcp_response(data)
            else:
                resp = self._getResponse(data)
        else:
            logger.debug("doesn't match pattern, use local dns")
            resp = self.get_response_normal(data)
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
    def get_response_normal(self, data):
        """ get the DNS result from local DNS server """
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.connect(self.domestic_dnsserver)
        sock.sendall(data)
        resp = sock.recv(65535)
        sock.close()
        return resp

    @cache_wrapper
    def tcp_response(self, data):
        """ tcp request dns data """        
        resp = None
        while not resp:
          sock = self.get_tcp_sock()
          size_data = self.tcp_packet_head(data)
          sock.send(size_data + data)
          try:
            resp = sock.recv(1024)
            logger.debug("receive data:%s", resp.encode('hex'))
          except timeout:
            logger.debug("tcp socket timeout, throw away")
            sock = self.create_tcp_sock()
        self.release_tcp_sock(sock)
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
        global tcp_pool
        try:
          sock = tcp_pool.get(block=True, timeout=DEF_TIMEOUT)
        except Queue.Empty:
          logger.debug("tcp pool is empty, now create a new socket")
          sock = self.create_tcp_sock()
        return sock
    
    def release_tcp_sock(self, sock):
        global tcp_pool
        try:
          tcp_pool.put(sock, block=False)
        except Queue.Full:
          logger.debug("tcp pool is full, now throw away the oldest socket")
          old_sock = tcp_pool.get(block=False)
          old_sock.close()
          tcp_pool.put(sock, block=False)

    def create_tcp_sock(self):
        tcp_sock = socket(AF_INET, SOCK_STREAM)
        tcp_sock.connect((DEF_REMOTE_SERVER, DEF_PORT))
        tcp_sock.settimeout(5)
        return tcp_sock

if DEF_MULTITHREAD:
    class LocalDNSServer(ThreadingUDPServer):
        pass
else:
    class LocalDNSServer(UDPServer):
        pass

def main():
    global gl_remote_server
    global tcp_pool 
    tcp_pool = Queue.Queue()
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

if __name__ == '__main__':
    main()
