import copy


class ObjectPropertyMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # Make an `objects` attribute available on the class
        subclass = super().__new__(cls, name, bases, attrs)
        subclass.objects = subclass()
        return subclass


class Queryish(metaclass=ObjectPropertyMetaclass):
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

    def first(self):
        results = list(self[:1])
        try:
            return results[0]
        except IndexError:
            return None

    def all(self):
        return self

    @property
    def ordered(self):
        return bool(self.ordering)

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step is not None:
                raise ValueError("%r does not support slicing with a step" % self.__class__.__name__)

            # Adjust the requested start/stop values to be relative to the full queryset
            absolute_start = (key.start or 0) + self.offset
            if key.stop is None:
                absolute_stop = None
            else:
                absolute_stop = key.stop + self.offset

            # find the absolute stop value corresponding to the current limit
            if self.limit is None:
                current_absolute_stop = None
            else:
                current_absolute_stop = self.offset + self.limit

            if absolute_stop is None:
                final_absolute_stop = current_absolute_stop
            elif current_absolute_stop is None:
                final_absolute_stop = absolute_stop
            else:
                final_absolute_stop = min(current_absolute_stop, absolute_stop)

            if final_absolute_stop is None:
                new_limit = None
            else:
                new_limit = final_absolute_stop - absolute_start

            clone = self.clone(offset=absolute_start, limit=new_limit)
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

    def __repr__(self):
        items = list(self[:21])
        if len(items) > 20:
            items[-1] = "...(remaining elements truncated)..."
        return "<%s %r>" % (self.__class__.__name__, items)
