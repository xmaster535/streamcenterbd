from http.server import BaseHTTPRequestHandler
import requests

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # আপনার GitHub-এর Raw JSON লিঙ্কটি এখানে দিন
        github_raw_url = "https://raw.githubusercontent.com/xmaster535/streamcenterbd/refs/heads/main/strmcntr_cache.json"
        
        response = requests.get(github_raw_url)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.content)
        return
