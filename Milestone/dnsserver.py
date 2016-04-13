# DNS packet format:
# https://tools.ietf.org/html/rfc1035
#	 +---------------------+
#	 |		Header	   |
#	 +---------------------+
#	 |	   Question	  | the question for the name server
#	 +---------------------+
#	 |		Answer	   | RRs answering the question
#	 +---------------------+
#	 |	  Authority	  | RRs pointing toward an authority
#	 +---------------------+
#	 |	  Additional	 | RRs holding additional information
#	 +---------------------+
#
# Header section format:
#   0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |					  ID					   |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |QR|   Opcode  |AA|TC|RD|RA|   Z	|   RCODE   |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |					QDCOUNT					|
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |					ANCOUNT					|
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |					NSCOUNT					|
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |					ARCOUNT					|
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#
# Question section format
#   0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |											   |
# /					 QNAME					 /
# /											   /
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |					 QTYPE					 |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |					 QCLASS					|
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#
# Answer, authority, additional sections format:
#   0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |											   |
# /											   /
# /					  NAME					 /
# |											   |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |					  TYPE					 |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |					 CLASS					 |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |					  TTL					  |
# |											   |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |				   RDLENGTH					|
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--|
# /					 RDATA					 /
# /											   /
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+

import SocketServer
import sys, socket, struct
import argparse
#import mapping

DEFAULT_REPLICA = '54.174.6.90'

class DNS_Packet():
	def pack_packet(self, ip):
		self.ancount = 1
		self.flags = 0x8180
		header = struct.pack('>HHHHHH', self.id, self.flags, self.qdcount, self.ancount, self.nscount, self.arcount)

		'''
		question = ''.join(chr(len(x)) + x for x in self.qname.split('.'))
		question += '\x00'
		question += struct.pack('>HH', self.qtype, self.qclass)
		'''

		ans_name = 0xC00C
		ans_type = 0x0001
		ans_class = 0x0001
		ans_ttl = 60
		ans_len = 4
		answer = struct.pack('>HHHLH4s', ans_name, ans_type, ans_class, ans_ttl, ans_len, socket.inet_aton(ip));

		packet = header + self.question_data + answer
		return packet

	def unpack_packet(self, data):
		[self.id, self.flags, self.qdcount, self.ancount, self.nscount, self.arcount] = struct.unpack('>HHHHHH', data[:12])

		self.question_data = data[12:]
		[self.qtype, self.qclass] = struct.unpack('>HH', self.question_data[-4:])
		qname = self.question_data[:-4]
		pointer = 0
		temp = []
		try:
			while True:
				content = ord(qname[pointer])
				if content == 0:
					break
				pointer += 1
				temp.append(qname[pointer:pointer + content])
				pointer += content
			self.qname = '.'.join(temp)
		except:
			self.qname = 'cs5700cdn.example.com'
		print self.qname

class DNS_Request_Handler(SocketServer.BaseRequestHandler):
	def handle(self):
		global port 
		data = self.request[0].strip()
		socket = self.request[1]
		packet = DNS_Packet()
		packet.unpack_packet(data)

		print 'ID: %X \tFlags: %.4X' % (packet.id, packet.flags)
		print 'QdCount: %d\tAnCount: %d' % (packet.qdcount, packet.ancount)
		print 'client address: ', self.client_address[0]
		print 'qtype:%s' %(packet.qtype)	# query type, should be 1
		print 'qclass:%s' %(packet.qclass)
		print 'qname:%s' %(packet.qname)

		if packet.qtype == 2:

			'''
		if packet.qtype == 1 and packet.qname == self.server.hostname:

			
			replica_ip = mapping.get_replica(self.client_address[0], port)

			if replica_ip:
				response = packet.pack_packet(replica_ip)
				socket.sendto(data, self.client_address)
				print 'Got replica IP %s for %s from cache' %(replica_ip, self.client_address[0])

			else:
				replica_ip = mapping.replica_find(self.client_address[0], 50000)
				response = packet.pack_packet(replica_ip)
				socket.sendto(response, self.client_address)
				print 'Got replica IP %s for %s from finding' %(replica_ip, self.client_address[0])
			'''
			response = packet.pack_packet(DEFAULT_REPLICA)
			socket.sendto(response, self.client_address)
			print 'Use DEFAULT_REPLICA %s for %s' %(DEFAULT_REPLICA, self.client_address[0])

		else:			
			pass

class DNS_Server(SocketServer.UDPServer):
	def __init__(self, hostname, server_address, handler_class = DNS_Request_Handler):
		SocketServer.UDPServer.__init__(self, server_address, handler_class)
		self.hostname = hostname
		return

def main(port, hostname):
	server = DNS_Server(hostname, ('', port))
	server.serve_forever()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(add_help = False)
	parser.add_argument('-p', '--port', required = True, type = int, help = 'port for the DNS server')
	parser.add_argument('-n', '--hostname', required = True, type = str, help = 'cdn specific name')
	args = parser.parse_args()
	port = args.port
	hostname = args.hostname
	main(port, hostname)


