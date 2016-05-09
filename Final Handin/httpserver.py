#!/usr/bin/env python
import os
import socket
import sys
import getopt
import baseUtility
import urllib2
from BaseHTTPServer import  HTTPServer, BaseHTTPRequestHandler
from SocketServer import BaseServer
import collections
import time

CACHE_MAX_VALUE = 7 * 1024 * 1024 # the maxmium cache in memory should be 6 MB and other 4 MB for program running
CACHE_DICTIONARY = collections.OrderedDict()
CURRENT_CACHE_SIZE = 0
class localCacheHelper:
    def __init__(self):
        pass
    @staticmethod
    def createCacheFolder():
        if not os.path.exists("localcache"):
            os.mkdir("localcache")
            print "debug: directory created "
        else:
            pass
    @staticmethod
    def calculateCurrentFileSize(folder_name):
        return sum(os.path.getsize(folder_name + "/" + filename) for filename in os.listdir(folder_name) if os.path.isfile(folder_name + "/" + filename))
    @staticmethod
    def isDiskQutaFull(response):
        current_size = localCacheHelper.calculateCurrentFileSize("localcache")
        print "debug: current_size ----------> {%d}"%current_size
        return (current_size + sys.getsizeof(response)) > (10 * 1024 * 1024 - 700 * 1024)
        
class HTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, origin, *args):
        
        #self.cache_c = collections.OrderedDict()
        #self.cache_size = 10;
        #self.cur_size = 0;
        self.origin = origin        
        BaseHTTPRequestHandler.__init__(self,*args)
    def do_GET(self):
        '''
        Cache Logic: LRU
        if path in cache 
              directly respond client with the response in memory
        if path not in cache
                    #check local cache
                    if path in disk cache
                            pickup the file from OS
                            send to client
                    else 
                         download resources from original server
                         calculate current dictionary size 
                         if current dictionary size < Max && (MAX - current_size) > len(response)
                              add download resources to cache
                         else 
                              # keep old elements in local 
                              save first cache elements to local ()
                                       if current folder size >  10 MB
                                          remove first local cache ( find file creation time)
                              remove cache in the memory 
                              add new response into memory cache 
        ''' 
        global CACHE_DICTIONARY, CURRENT_CACHE_SIZE,CACHE_MAX_VALUE
        if self.path not in CACHE_DICTIONARY.keys():
            try:
                # check whether file is on the disk
                server_file_path = os.pardir + self.path
                print "debug: \t %s"%server_file_path
                if os.path.exists(server_file_path):
                    with open(server_file_path) as page:
                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(page.read())
                else:
                    print "debug: original server name: ------>{%s}"%self.origin
                    new_request_URL = baseUtility.baseUtility.composeHTTPRequesURL(self.origin, 8080, self.path)
                    print "debug: new original Server URL: {%s}"%new_request_URL
                    response = urllib2.urlopen(new_request_URL)
                    response_Str = response.read()
                    print "debug: \r\n" + response_Str
                    print "debug: \r\n" + str(len(response_Str))
                    if CURRENT_CACHE_SIZE < CACHE_MAX_VALUE and (CACHE_MAX_VALUE - CURRENT_CACHE_SIZE) > len(response.read()):
                        print "debug: (%d,%d)"%(CURRENT_CACHE_SIZE,CACHE_MAX_VALUE)
                        CACHE_DICTIONARY[self.path] = response_Str
                        print "debug: \r\n" + response.read()
                        print "debug: \t memory cache dictionary: \t" + str(CACHE_DICTIONARY) 
                        CURRENT_CACHE_SIZE = len(response_Str) + len(self.path)
                        print "debug: \t current cache size: {%d}"%CURRENT_CACHE_SIZE
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(response_Str) 
                    else:
                        # get the oldest cache in memory and write it on the disk
                        oldest_cache_path = CACHE_DICTIONARY.items()[0][0]
                        print "debug: oldest cache path: %s" %oldest_cache_path
                        oldest_cache_response = CACHE_DICTIONARY.items()[0][1]
                        print "debug: oldest cache response: %s"%oldest_cache_response
                        self.saveToLocal(oldest_cache_path,oldest_cache_response)
                        # reset current dictionary size
                        CURRENT_CACHE_SIZE = CURRENT_CACHE_SIZE - len(oldest_cache_path) - len(oldest_cache_response)
                        # remove cache in memory 
                        del CACHE_DICTIONARY[oldest_cache_path]
                        print "debug: \n" + str(CACHE_DICTIONARY.keys())
                        # add new response in cache
                        CACHE_DICTIONARY[self.path] = response.read()
                        CURRENT_CACHE_SIZE = CURRENT_CACHE_SIZE + len(self.path) + len(self.responses)
                        
            except urllib2.HTTPError as httperror:
                self.send_error(httperror.code,httperror.reason)
                return 
            except urllib2.URLError as urlerror:
                self.send_error(urlerror)
                return 
            else:            
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(response.read())                
        else:          
            responds_in_memory = CACHE_DICTIONARY[self.path]
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(responds_in_memory)
            #respond_file.close()
    def saveToLocal(self, path, response):
        filename = os.pardir + path
        #direcory = os.path.dirname(filename)
        #if not os.path.exists(direcory):
            #os.makedirs(direcory)
        try:
            # judge the total size of the folder 
            # if total size > 10 MB 
            localCacheHelper.createCacheFolder()
            if not localCacheHelper.isDiskQutaFull(response):
                baseUtility.baseUtility.createFile(filename, response)
            else: 
                # remove the first cached file
                for filename in os.listdir("localcache"):
                    os.remove(filename)
        except IOError as e:
            # if quta is used up 
            #remove path from  web cache 
            #remove directory and files created in previous step
            # 
            if e.errno == errno.EDQUOT:
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
    
    def handler(*args):
        HTTPHandler(origin_server_name, *args)
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
