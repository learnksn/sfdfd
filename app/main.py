import http.server, os
os.chdir('/workspace')
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=8000, bind='0.0.0.0')
