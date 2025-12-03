# from transport.message import Message

class AnalyzerManager:
    def __init__(self):
        self.analyzers = {}
        self.support = []

    def register_analyzer(self, name, analyzer):
        self.analyzers[name] = analyzer
        self.support.append(name)

    def analyze(self, data):
        pass