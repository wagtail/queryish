class Queryish:
    def run_query(self):
        raise NotImplementedError

    def __iter__(self):
        yield from self.run_query()
