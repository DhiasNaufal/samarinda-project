# # Run in a separate thread so it doesn't block PyQt
# def run_server():
#     threading.Thread(target=start_server, args=(".",), daemon=True).start()

"""
  v2
"""
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        # return super().translate_path(path)
        """ Restrict access to only allowed directories """
        # Get the requested file's absolute path
        root_dir = os.getcwd()
        requested_path = os.path.normpath(os.path.join(root_dir, path.lstrip("/")))

        # Check if the requested path is inside an allowed directory
        for allowed_dir in ["assets", "data", "output"]:
            allowed_path = os.path.join(root_dir, allowed_dir)
            if requested_path.startswith(allowed_path):
                return requested_path
        
        # If not allowed, return a 403 Forbidden response
        self.send_error(403, "Forbidden")
        return None
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        # self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type, Accept')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        return super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def start_server(directory, port=8000):
    os.chdir(directory)
    handler = CustomHTTPRequestHandler
    httpd = HTTPServer(("localhost", port), handler)
    print(f"Server started at http://localhost:{port}")
    print(f"Serving files from: {os.getcwd()}")
    print("Press Ctrl+C to stop the server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")

if __name__ == "__main__":
    # You can change this to your directory
    directory = "."  # Current directory
    port = 8000
    start_server(directory, port)
