class AnalyzerManager:
    def __init__(self):
        self.analyzers = {}
        self.support = []

    def register_analyzer(self, name, analyzer):
        self.analyzers[name] = analyzer
        self.support.append(name)

    def analyze(self, name, message):
        if name not in self.analyzers:
            raise KeyError(f"Analyzer '{name}' not registered")
        analyzer = self.analyzers[name]
        # Delegate to analyzer implementation's analyze method
        return analyzer.analyze(message)
