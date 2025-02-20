from http.server import SimpleHTTPRequestHandler, HTTPServer
import os

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_GET(self):
        if self.path == "/":
            self.path = "/"  # List files
        return super().do_GET()

if __name__ == "__main__":
    port = 8000
    cwd = os.getcwd()
    print(f"🌍 Serving files from {cwd} at http://localhost:{port}/")
    
    server_address = ("", port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    print("✅ Server with CORS started!")
    httpd.serve_forever()
