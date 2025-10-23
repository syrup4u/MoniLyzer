from transport.message import Message
from api.monitor import MonitorManager, get_default_filter
from api.analyzer import AnalyzerManager

from http.server import HTTPServer, BaseHTTPRequestHandler
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
    # TODO: path parsing
    def do_GET(self):
        # Send response status code and headers
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.end_headers()

        # test: process and analyze
        processor = self.server.injected_processor
        options = {"monitor": "pmacct", "hours": 16800}
        msg = processor.process(options)
        resp = processor.analyze(options, msg)
        self.wfile.write(bytes(json.dumps(resp), "utf8"))

        return
