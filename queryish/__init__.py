import copy

class Queryish:
    def __init__(self):
        self._results = None
        self._count = None
        self.offset = 0
        self.limit = None
        self.filters = []
        self.filter_fields = None
        self.ordering = ()
        self.ordering_fields = None

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
                self._results = results_list
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
        clone.filters = self.filters.copy()
        for key, value in kwargs.items():
            setattr(clone, key, value)
        return clone

    def filter_is_valid(self, key, val):
        if self.filter_fields is not None and key not in self.filter_fields:
            return False
        return True

    def filter(self, **kwargs):
        clone = self.clone()
        for key, val in kwargs.items():
            if self.filter_is_valid(key, val):
                clone.filters.append((key, val))
            else:
                raise ValueError("Invalid filter field: %s" % key)
        return clone

    def ordering_is_valid(self, key):
        if self.ordering_fields is not None and key not in self.ordering_fields:
            return False
        return True

    def order_by(self, *args):
        ordering = []
        for key in args:
            if self.ordering_is_valid(key):
                ordering.append(key)
            else:
                raise ValueError("Invalid ordering field: %s" % key)
        return self.clone(ordering=tuple(ordering))

    def get(self, **kwargs):
        results = list(self.filter(**kwargs)[:2])
        if len(results) == 0:
            raise ValueError("No results found")
        elif len(results) > 1:
            raise ValueError("Multiple results found")
        else:
            return results[0]

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
