import sys
import os
from pathlib import Path

# Ensure the project directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import your FastAPI app from main.py
from main import app

# Namecheap cPanel uses Phusion Passenger (WSGI).
# a2wsgi bridges ASGI (FastAPI) to WSGI seamlessly.
try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)
except ImportError:
    # Fallback error message if dependencies are not yet installed in virtualenv
    def application(environ, start_response):
        status = '500 Internal Server Error'
        output = b"Dependencies not installed. Please install requirements in your virtualenv."
        response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]
