from transport.message import Message
from api.monitor import MonitorManager, get_default_filter
from api.analyzer import AnalyzerManager

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

"""
1. Transfer data.
2. Provide public interfaces for query (or request)
"""
class Processor:
    def __init__(self, monitor_manager: MonitorManager, analyzer_manager: AnalyzerManager, config: dict):
        self.monitor_manager = monitor_manager
        self.analyzer_manager = analyzer_manager
        self.config = config

    """
    wrap the data in a Message object and return it
    """
    def process(self, options: dict) -> Message:
        monitor_name = options.get("monitor", "pmacct")
        monitor = self.monitor_manager.monitors.get(monitor_name, None)
        if monitor_name == "pmacct":
            data_filter = get_default_filter()
            monitor.preprocess(options, data_filter=data_filter)
            msg = Message(monitor.data[0])
            return msg
        return None

    def analyze(self, options: dict, msg: Message) -> dict:
        # fake implementation
        self.analyzer_manager.analyze(msg)
        if msg is not None:
            return {"data": msg.payload}

    def run(self):
        print('Starting MoniLyzer server...')
        server = HTTPServer((self.config["host"], int(self.config["port"])), monilyzerHandler)
        server.injected_processor = self
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('Stopping MoniLyzer server...')
            server.server_close()

class monilyzerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse URL path and query string
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # Only accept /opt path
        if parsed_url.path != '/opt':
            self.send_error_response(400, "Invalid path. Expected: /opt")
            return
        
        # Extract options from query string (e.g., /opt?monitor=pmacct&hours=16800)
        if not query_params:
            self.send_error_response(400, "No query parameters provided. Expected: /opt?monitor=value&hours=value")
            return
        
        if "monitor" not in query_params or "hours" not in query_params:
            self.send_error_response(400, "Missing required parameters: monitor and hours")
            return
        
        try:
            options = {
                "monitor": query_params["monitor"][0],
                "hours": int(query_params["hours"][0])
            }
        except ValueError:
            self.send_error_response(400, "Invalid query parameters. Hours must be a valid integer")
            return
        
        # Send response status code and headers
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.end_headers()

        # Process and analyze
        processor = self.server.injected_processor
        msg = processor.process(options)
        resp = processor.analyze(options, msg)
        self.wfile.write(bytes(json.dumps(resp), "utf8"))

        return
    
    def send_error_response(self, code, message):
        """Send an error response with JSON body"""
        self.send_response(code)
        self.send_header('Content-type','application/json')
        self.end_headers()
        error_resp = {"error": message}
        self.wfile.write(bytes(json.dumps(error_resp), "utf8"))
