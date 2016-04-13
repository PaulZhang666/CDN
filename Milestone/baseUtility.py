import sys
import os
import time
import urlparse
import socket
import json
import re
import simplejson

class baseUtility:
    def __init__(self):
        pass
    @staticmethod
    def composeHTTPRequesURL(server_name, serve_port, resource_path):
        return "http://" + server_name + ":" + str(serve_port) + resource_path
    @staticmethod
    def getHostName(url):
        return urlparse.urlparse(url).netloc.split(":")[0] 
    @staticmethod
    def getPortNumber(url):
        port = 80
        split_URL = urlparse.urlparse(url).netloc.split(":")
        if split_URL and len(split_URL) >= 2:
            port = int(split_URL[1])
            
        return port 
    @staticmethod
    def getHTTPResponse(url):
        host = baseUtility.getHostName(url)
        port = baseUtility.getPortNumber(url)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        header = HTTP.GETRequest(url)
        sock.send(header)
        response = baseUtility.recieve(sock)
        http_header, http_body = HTTP.responseSplit(response)
        return http_body
    @staticmethod
    def getRequestPath(_url):
        _path = urlparse.urlparse(_url).path
        if not _path:
            path = "/wiki/Main_Page"
        path = _path
        return path   
    @staticmethod
    def createFile(filename,_data):
        try:
            downloadfile = open(filename, 'w')
            downloadfile.write(_data)
        except IOError as e:
            raise e
        finally:
            downloadfile.close()        
    @staticmethod
    def recieve(_socket):
        responseBody = ' '
        response = _socket.recv(4096)
        header, body = HTTP.responseSplit(response)
        responseBody += response
        if HTTP.isResponseChunked(header):
            if "\r\n0\r\n" in body:
                return responseBody
            while True:
                tmpResponse = str(_socket.recv(4096))
                #if "<h2>Extra Credit</h2>" in tmpResponse:
                    #print tmpResponse
                if (tmpResponse[0] == "0"):
                    break
                elif ("\n0\r\n" in tmpResponse):
                    responseBody += tmpResponse
                    break
                else:
                    responseBody += tmpResponse
            return responseBody
        elif  HTTP.isContentLength(header):
            data_pos = responseBody.find(HTTP.CRLF)+ 4
            data_recv_len = len(responseBody[data_pos:])
            content_len = HTTP.getContentLength(header)
    
            required_data_len = content_len - data_recv_len
    
            if required_data_len == 0:
                return responseBody
            while required_data_len != 0:
                tmp = _socket.recv(4096)
                responseBody += tmp 
                required_data_len -= len(tmp)
            return responseBody
        else: 
            return ""
        
        
class HTTP:
    CRLF = "\r\n\r\n"
    def __init__(self):
        pass
    @staticmethod
    def GETRequest(_url):
        urlStr = urlparse.urlparse(_url)
        host = urlStr.netloc
        if not host:
            host = _url
        if not _url:
            path = "/"
        path = urlStr.path 
        if host == _url:
            path = "/"
        getHeader = [
                "GET %s HTTP/1.1\r\n" %path,
                "Host: %s\r\n" % host,
                "User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0\r\n",
                "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n",
                "Accept-Language: en-US,en;q=0.5\r\n",
                "Referer: %s\r\n"%_url,
                "Connection: keep-alive",          
        ]  
        return "".join(getHeader) + HTTP.CRLF
    
    @staticmethod
    def responseSplit(_response):
        httpHeader,delimiter,body = _response.partition(HTTP.CRLF)
        return (httpHeader, body) 
    
    @staticmethod
    def extractStatusCode(_responseHeader):
        if not _responseHeader:
            print "Response Header is empty"
            exit(0)
        tagLines = _responseHeader.split('\n')
        statusCode = tagLines[0].split(' ')[2]
        return statusCode
    
    @staticmethod
    def isStatus200(_responseHeader):
        statusCode = HTTP.extractStatusCode(_responseHeader)
        if statusCode.startswith('2'):
            return True
        return False
    @staticmethod
    def isResponseChunked( responseHeader):
        if "Transfer-Encoding: chunked" in responseHeader:
            return True
        return False
    @staticmethod
    def isContentLength( header):
        if ("Content-Length:" in header):
            return True
        return False
    @staticmethod
    def getContentLength(_header):
        lengthPatternStr = "Content-Length: (.*?)$"
        lengthPattern = re.compile(lengthPatternStr)
        length = re.findall(lengthPattern, _header)
        
        if len(length) == 0:
            return 0
        return int(length[0]) 

class IPGeo:
    API_URL = "http://ip-api.com/json/"
    def __init__(self, IP):
        self.ip = IP 
        self.getGeoIP()
    
    def getGeoIP(self):
        # free geo IP API
        # http://ip-api.com/json
        url = self.API_URL + self.ip
        response = baseUtility.getHTTPResponse(url)
        parsed_json = json.loads(response)
        
        self.status = parsed_json['status']
        self.country = parsed_json['country']
        self.countryCode = parsed_json['countryCode']
        self.region = parsed_json['region']
        self.regionName = parsed_json['regionName']
        self.city = parsed_json['city']
        self.zipcode = parsed_json['zip']
        self.latitude = parsed_json['lat']
        self.longitude = parsed_json['lon']
        self.timezone = parsed_json['timezone']
        self.ispname = parsed_json['isp']
        self.org = parsed_json['org']
        self.asnum = parsed_json['as']
        self.query = parsed_json['query']
        
    def toString(self):
        return ("status: {%s}\n" % self.status
                     + "country: {%s} \n" % self.country
                     + "countryCode: {%s} \n" % self.countryCode
                     + "region: {%s} \n" % self.region
                     + "region Name: {%s} \n" % self.regionName
                     + "city: {%s} \n" % self.city
                     + "zip: {%s} \n" % self.zipcode
                     + "latitude: {%f}\n" % self.latitude
                     + "longitude: {%f}\n" % self.longitude
                     + "timezone: {%s}\n" % self.timezone
                     + "isp: {%s}\n" % self.ispname
                     + "organization: {%s}\n" % self.org
                     + "AS number: {%s}\n" % self.asnum
                     + "query: {%s}\n" % self.query                     
                     )

if __name__ == "__main__":
    ipgeo = IPGeo("54.215.216.108")
    print ipgeo.toString()
    print "jaja"