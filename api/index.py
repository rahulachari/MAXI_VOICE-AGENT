"""
JARVIS VoiceOS - Vercel Serverless Entrypoint
Serves API status and ensures zero-config compatibility with Vercel Python runtime.
"""

from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        response = {
            "status": "online",
            "name": "JARVIS VoiceOS API",
            "version": "1.0.0",
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))
