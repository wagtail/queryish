import copy

class Queryish:
    def __init__(self):
        self._results = None
        self._count = None
        self.offset = 0
        self.limit = None

    def run_query(self):
        raise NotImplementedError

    def run_count(self):
        count = 0
        for i in self:
            count += 1
        return count

    def __iter__(self):
        if self._results is None:
            results = []
            for result in self.run_query():
                results.append(result)
                yield result
            self._results = results
        else:
            yield from self._results

    def count(self):
        if self._count is None:
            self._count = self.run_count()
        return self._count

    def __len__(self):
        return self.count()

    def clone(self, **kwargs):
        clone = copy.copy(self)
        clone._results = None
        clone._count = None
        for key, value in kwargs.items():
            setattr(clone, key, value)
        return clone

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step is not None:
                raise ValueError("%r does not support slicing with a step" % self.__class__.__name__)

            new_offset = self.offset + (key.start or 0)
            if key.stop is None:
                # no new limit imposed, but need to adjust any existing limit to account for the new offset
                if self.limit is None:
                    new_limit = None
                else:
                    new_limit = self.limit - (key.start or 0)
            else:
                # new limit imposed
                new_limit = key.stop - (key.start or 0)

            clone = self.clone(offset=new_offset, limit=new_limit)
            if self._results:
                clone._results = self._results[key]
            return clone
        else:
            raise NotImplementedError("%r does not support indexing" % self.__class__.__name__)
