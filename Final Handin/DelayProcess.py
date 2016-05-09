import os
import sys
import time
import struct
import socket
import urllib2
import threading
import operator

'''
 In this file, we will request delay from each replica server,
 and sort the replica serveres according to latency (short -> long)
'''
# this port used to retrieve delay info from replica server. The result will be returned by performanceMeasureServer service
MEASURE_DELAY_SERVER_PORT = 42314
# all replica server host names
replica_server_names = ["ec2-54-85-32-37.compute-1.amazonaws.com",
                                       "ec2-54-193-70-31.us-west-1.compute.amazonaws.com",
                                       "ec2-52-38-67-246.us-west-2.compute.amazonaws.com",
                                       "ec2-52-51-20-200.eu-west-1.compute.amazonaws.com",
                                       "ec2-52-29-65-165.eu-central-1.compute.amazonaws.com",
                                       "ec2-52-196-70-227.ap-northeast-1.compute.amazonaws.com",
                                       "ec2-54-169-117-213.ap-southeast-1.compute.amazonaws.com",
                                       "ec2-52-63-206-143.ap-southeast-2.compute.amazonaws.com",
                                       "ec2-54-233-185-94.sa-east-1.compute.amazonaws.com"
                                       ]
replica_host_IP_map = {"ec2-54-85-32-37.compute-1.amazonaws.com":"54.85.32.37",
                                      "ec2-54-193-70-31.us-west-1.compute.amazonaws.com":"54.193.70.31",
                                      "ec2-52-38-67-246.us-west-2.compute.amazonaws.com":"52.38.67.246",
                                      "ec2-52-51-20-200.eu-west-1.compute.amazonaws.com":"52.51.20.200",
                                      "ec2-52-29-65-165.eu-central-1.compute.amazonaws.com":"52.29.65.165",
                                      "ec2-52-196-70-227.ap-northeast-1.compute.amazonaws.com":"52.196.70.227",
                                      "ec2-54-169-117-213.ap-southeast-1.compute.amazonaws.com":"54.169.117.213",
                                      "ec2-52-63-206-143.ap-southeast-2.compute.amazonaws.com":"52.63.206.143",
                                      "ec2-54-233-185-94.sa-east-1.compute.amazonaws.com":"54.223.185.94",
                                       }
replica_IP_latency_map = {}
class createThreads(threading.Thread):
    def __init__(self,host_name,target_ip,execute_lock):
        threading.Thread.__init__(self)
        self.hostname = host_name
        self.client_ip = target_ip
        self.lock = execute_lock
    def run(self):
        # create a TCP socket to connect replica performanceMeasureServer service
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        '''
            might be optimized by cache replica IP
            if replica server IP has already in cache dictionary
            just directly pick up the IP in the cache 
            no need to get ip again 
        '''
        
        replica_server_ip = socket.gethostbyname(self.hostname)
        print replica_server_ip
        
        try: 
            print MEASURE_DELAY_SERVER_PORT
            sock.connect((replica_server_ip,MEASURE_DELAY_SERVER_PORT))
            sock.sendall(self.client_ip)
            latency = sock.recv(1024)
        except socket.error as e:
            print "error: Conneting to PerformanceMeasureServer service failed \n" + e.message
            latency = "9999" # if socket error, latency becomes infinity large
        finally:
            sock.close()
        print "debug: {IP -------> %s} \t {latency ---------> %s}"%(replica_server_ip,latency)
        with self.lock:
            replica_IP_latency_map.update({replica_server_ip:float(latency)})

def getMinLatencyFrmReplica(target_client_ip):
    '''
    sorted the Latency and return the least latency IP
    '''
    # this lock was used to prevent mutiple threads write to dictionary replica_IP_latency_map at the same time
    lock = threading.Lock()
    threads_pool = []
    start_time = time.time()
    for i in range(len(replica_server_names)):
        thread = createThreads(replica_server_names[i], target_client_ip, lock)
        #thread = createThreads("ec2-54-85-32-37.compute-1.amazonaws.com", target_client_ip, lock)
        thread.start()
        threads_pool.append(thread)
    for thread in threads_pool:
        thread.join(2)
    thread_time = (time.time() - start_time) * 1000 
    print "Threads running time -------> {%f}"%thread_time
    print str(replica_IP_latency_map)
    sorted_ips = sorted(replica_IP_latency_map.items(), key=operator.itemgetter(1))
    print "debug: \r\n" + str(sorted_ips)
    print "debug: best ip ------> {%s}"%sorted_ips[0][0]
    return sorted_ips[0][0]

if __name__=="__main__":
    getMinLatencyFrmReplica("129.10.117.100")