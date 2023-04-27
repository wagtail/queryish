class Queryish:
    def __init__(self):
        self._results = None

    def run_query(self):
        raise NotImplementedError

    def __iter__(self):
        if self._results is None:
            results = []
            for result in self.run_query():
                results.append(result)
                yield result
            self._results = results
        else:
            yield from self._results
