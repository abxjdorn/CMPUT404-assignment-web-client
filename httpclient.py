#!/usr/bin/env python3
# coding: utf-8
# Copyright 2020 Abram Hindle, https://github.com/tywtyw2002, https://github.com/treedust, John Dorn
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

# This implements concepts from the HTTP 1.1 specification
# RFC 2616 (https://www.ietf.org/rfc/rfc2616.txt)

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse


DIAGNOSTIC = False


def dp(*args):
    if DIAGNOSTIC:
        print(*args)


def help():
    print("httpclient.py [GET/POST] [URL]\n")


class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body


    def __str__(self):
        if DIAGNOSTIC:
            return (
                    '= = = Status {} = = ='.format(self.code) + '\n' +
                    self.body
                )
        else:
            return self.body


class HTTPClient(object):
    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None


    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))


    def close(self):
        self.socket.close()


    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')


    def GET(self, url, args=None):
        return self._request('GET', url, args)


    def POST(self, url, args=None):
        return self._request('POST', url, args or {})


    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )


    def _request(self, method, url, args):
        print('URL: {}'.format(url))
        print('Args: {}'.format(args))

        hostname, port, path = self._decompose_url(url)

        host = self._lookup_host(hostname)
        dp('Connecting to {}:{} ({}:{})'.format(hostname, port, host, port))
        self.connect(hostname, port)

        encoded_request = self._encode_request(method, hostname, path, args)
        self.sendall(encoded_request)
        self.socket.shutdown(socket.SHUT_WR)
        response = self.recvall(self.socket)
        self.close()

        respline, headers, body = self._split_response(response)

        code = int(respline.split(' ')[1])
        return HTTPResponse(code, body)


    def _split_response(self, response):
        respline, rest = response.split('\r\n', 1)
        headers, body = rest.split('\r\n\r\n', 1)
        return respline, headers, body


    def _decompose_url(self, url):
        if not url.startswith('http://'):
            url = 'http://' + url

        parts = urllib.parse.urlparse(url)

        port = 80 if parts.port is None else parts.port
        path = parts.path or '/'
        if parts.query: path += '?' + parts.query
        return parts.hostname, port, path


    def _lookup_host(self, hostname):
        return socket.gethostbyname(hostname)


    def _encode_request(self, method, hostname, path, args):
        request_lines = [
                '{} {} HTTP/1.1'.format(method, path),
                'Host: {}'.format(hostname),
                'Connection: close',
                'Accept: */*',
            ]

        if args is not None:
            encoded_args = self._encode_args(args)
            request_lines.extend([
                    'Content-Length: {}'.format(len(encoded_args)),
                    'Content-Type: application/x-www-form-urlencoded',
                ])

        request_data = '\r\n'.join(request_lines) + '\r\n\r\n'
        if args:
            request_data +=  encoded_args

        print(bytes(request_data, encoding='utf-8'))

        return request_data


    def _encode_args(self, args):
        # This implements application/x-www-form-urlencoded encoding
        # approximately as per the description at
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/POST
        return ('&'.join(map(lambda k:
                    urllib.parse.quote(k) + '='
                    + urllib.parse.quote(args[k]),
                args.keys()
            )))


if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
