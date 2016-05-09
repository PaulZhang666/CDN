#/#!/usr/bin/env python
import os 
import commands
import socket
import SocketServer
import time

'''
In this server, we want to monitor the replica server's delay and load,
DNS server will request these info to make decision of best replica server

'''
class tools:
    def __init__(self):
        pass
    @staticmethod
    def getServerLatency(ipaddr):
        '''
        in this function, we use scamper to get the latency statistic  from ping command 
        and. we will ping 4 times and get the avg delay with the standev delay.
        lower standev delay means the network is more stable
        '''
        # ping 1 times and get the last line of the scamper output
        #yifanzhang@ip-172-31-7-167:~$ scamper -c 'ping -c 1' -i 129.10.117.100 | awk END{print $4}
        #round-trip min/avg/max/stddev = 12.530/12.782/12.905/0.147 ms
        command = "scamper -c 'ping -c 1' -i " + ipaddr+"|awk 'END{print $4}'" 
        outputs = commands.getoutput(command)
        if  outputs:
            [minimum,avg,maxmium,stddev] = outputs.split('/')
            return avg
        else:
            print ("Please  check network connections and rerun this program!")
            return ""
        
class MeasureHandler(SocketServer.BaseRequestHandler):
    '''
    handle the request comes from DNS server 
    '''
    def handle(self):
        '''
        server get the client IP 
        send avg_delay and standev_delay to client server (DNS server)
        '''
        target_ip = self.request.recv(1024).strip()
        print "debug: \n Client IP address: %s"%target_ip
        avg_delay = tools.getServerLatency(target_ip)
        print "avg delay: {%s} "%(avg_delay)
 
        if not avg_delay:
            avg_delay = "9999"
        self.request.sendall(avg_delay)
        
class MeasurementServer:
    def __init__(self,port):
        self.port = port
    def startMesurementServer(self):
        server = SocketServer.TCPServer(('',self.port), MeasureHandler)
        server.serve_forever()
        
if __name__ == "__main__":
    port = 42314 
    server = MeasurementServer(port)
    server.startMesurementServer()
    #tools.getServerLatency("129.10.117.100")
         
        
        
        
        
