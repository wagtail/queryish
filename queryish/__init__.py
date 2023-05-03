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
            results = self.run_query()
            if isinstance(results, list):
                self._results = results
                for result in results:
                    yield result
            else:
                results_list = []
                for result in results:
                    results_list.append(result)
                    yield result
                self._results = results
        else:
            yield from self._results

    def count(self):
        if self._count is None:
            if self._results is not None:
                self._count = len(self._results)
            else:
                self._count = self.run_count()
        return self._count

    def __len__(self):
        # __len__ must run the full query
        if self._results is None:
            self._results = list(self.run_query())
        return len(self._results)

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
        elif isinstance(key, int):
            if key < 0:
                raise IndexError("Negative indexing is not supported")
            if self._results is None:
                self._results = list(self.run_query())
            return self._results[key]
        else:
            raise TypeError(
                "%r indices must be integers or slices, not %s"
                % (self.__class__.__name__, type(key).__name__)
            )
