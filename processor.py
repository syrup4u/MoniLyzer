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
        path_parts = parsed_url.path.strip('/').split('/')
        query_params = parse_qs(parsed_url.query)
        
        # Try to extract options from path or query string
        options = {}
        
        # Try path parsing first (e.g., /pmacct/16800)
        if len(path_parts) >= 2 and path_parts[0] != '' and path_parts[1] != '':
            try:
                options["monitor"] = path_parts[0]
                options["hours"] = int(path_parts[1])
            except ValueError:
                self.send_error_response(400, "Invalid path format. Expected: /monitor/hours")
                return
        # Try query string parsing (e.g., ?monitor=pmacct&hours=16800)
        elif query_params:
            if "monitor" in query_params and "hours" in query_params:
                try:
                    options["monitor"] = query_params["monitor"][0]
                    options["hours"] = int(query_params["hours"][0])
                except ValueError:
                    self.send_error_response(400, "Invalid query parameters")
                    return
            else:
                self.send_error_response(400, "Missing required parameters: monitor and hours")
                return
        else:
            # No valid options provided
            self.send_error_response(400, "No options provided. Use path (/monitor/hours) or query string (?monitor=value&hours=value)")
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
