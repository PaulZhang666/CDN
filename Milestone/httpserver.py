#!/usr/bin/env python
import os
import socket
import sys
import getopt
import baseUtility
import urllib2
from BaseHTTPServer import  HTTPServer, BaseHTTPRequestHandler
from SocketServer import BaseServer


class HTTPHandler(BaseHTTPRequestHandler):
    #SEND_HEADER = ('Content-type', 'text/plain')
    def __init__(self, origin, web_cache, *args):
        self.origin = origin
        self.cache = web_cache
        BaseHTTPRequestHandler.__init__(self,*args)
    def do_GET(self):
        # judge whether the path is in cache
        # if path not in cache
        # try download it from its original server
        # and save to HTTP server 
        # if path in cache
        # response the file to the client 
        if self.path not in self.cache:
            try:                
                new_request_URL = baseUtility.baseUtility.composeHTTPRequesURL(self.origin, 8080, self.path)
                response = urllib2.urlopen(new_request_URL)
                #new_request_URL = baseUtility.baseUtility.getRequestPath(new_request_URL)
                #print new_request_URL
                #response = baseUtility.baseUtility.getHTTPResponse(new_request_URL)
                # download file to HTTP server
                #self.saveToLocal(self.path, response)
                
            except urllib2.HTTPError as httperror:
                self.send_error(httperror.reason)
                return 
            except urllib2.URLError as urlerror:
                self.send_error(urlerror)
                return 
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(response.read())                
            #self.cache.append(self.path)
        else:
            respond_file = open(os.pardir + self.path)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(respond_file.read())
            respond_file.close()
    def saveToLocal(self, path, response):
        filename = os.pardir + path
        direcory = os.path.dirname(filename)
        if not os.path.exists(direcory):
            os.makedirs(direcory)
        try:
            baseUtility.baseUtility.createFile(filename, response)
            self.cache.append(path)
        except IOError as e:
            # if quta is used up 
            #remove path from  web cache 
            #remove directory and files created in previous step
            # 
            if e.errno == errno.EDQUOT:
                self.cache.remove(path)
                os.remove(filename)
        else:
            raise e 
class server(BaseServer):
    def __init__(self, server_address, handler_class):
        BaseServer.__init__(self, server_address, handler_class)
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM )
        self.server_bind()
        self.listen()
    def server_bind(self):
        #allow reuse address
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.server_address)
    def listen(self):
        # listen the particular port to wait services
        # 5 is the suggestted HTTP queue size
        self.sock.listen(5)
    #def serveforever(self):
        #self.serve_forever(self)
def startServer(port, origin_server_name):
    WEB_CACHE = []
    def handler(*args):
        HTTPHandler(origin_server_name, WEB_CACHE,*args)
    httpserver = HTTPServer(('', port), handler)
    httpserver.serve_forever()
    
def main(args):
    opts, argvs = getopt.getopt(args, "p:o:")
    for opt, arg in opts:
        if opt == "-p":
            port = int(arg)
        elif opt =="-o":
            name = arg
        else:
            exit("Use Guide: %s -p [port] -o [origin]" % args[0])
    startServer(port,name)
if __name__ == "__main__":
    main(sys.argv[1:])