class DummyMetrics:
    def start(self, labels):
        return 0

    def stop(self, labels, start_time, attempts=1, error=None):
        pass
