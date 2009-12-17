# -*- encoding: utf-8 -*-
from socket import *

class DNSProxy:
    def __init__(self, dnsserver):
        self.dnsserver = (dnsserver, 53)
        hostip = 'localhost'
        print 'DNS server start on %s.' % hostip
        self.host = (hostip, 53)

    def _getResponse(self, data):
        "Send client's DNS request (data) to remote DNS server, and return its response."
        sock = socket(AF_INET, SOCK_DGRAM) # socket for server
        sock.connect(self.dnsserver)
        sock.sendall(data)
        sock.settimeout(5)
        try:
            rspdata = sock.recv(65535)
        except Exception, e:
            print e, 'ignored.'
            return 1
        # "delicious food" for GFW:
        while 1:
            sock.settimeout(0.1)
            try:
                rspdata = sock.recv(65535)
            except timeout:
                break
        sock.close()
        return rspdata

    def run(self):
        """Get client's DNS request,
           send it to _getResponse(),
           recieve the return data,
           send it back to client."""
        sock = socket(AF_INET, SOCK_DGRAM) # socket for client
        sock.bind(self.host)
        while 1:
            try:
                data, address = sock.recvfrom(65535)
            except Exception, e:
                print e, 'ignored.'
                continue
            data = self._getResponse(data)
            if data != 1:
                try:
                    sock.sendto(data, address)
                except Exception, e:
                    print e, 'ignored.'
                    continue
        sock.close()

if __name__ == '__main__':
    try:
        f = open('dnsserver.conf', 'r')
        dns = f.read().split('=')
        f.close()
        if len(dns) == 2:
            dns = dns[1].strip()
    except:
        dns = '202.102.134.68'
    proxy = DNSProxy(dns)
    proxy.run()