import copy
import re


class ObjectDoesNotExist(ValueError):
    pass


class MultipleObjectsReturned(ValueError):
    pass


class Queryish:
    does_not_exist_exception = ObjectDoesNotExist
    multiple_objects_returned_exception = MultipleObjectsReturned

    def __init__(self):
        self._results = None
        self._count = None
        self.start = 0
        self.stop = None
        self.filters = []
        self.filter_fields = None
        self.ordering = ()
        self.ordering_fields = None

    @property
    def offset(self):
        return self.start

    @property
    def limit(self):
        if self.stop is None:
            return None
        return self.stop - self.start

    def run_query(self):
        raise NotImplementedError

    def run_count(self):
        count = 0
        for i in self:
            count += 1
        return count

    def __iter__(self):
        if self._results is None:
            if self.start == self.stop:
                results = []
            else:
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
            elif self.start == self.stop:
                self._count = 0
            else:
                self._count = self.run_count()
        return self._count

    def __len__(self):
        # __len__ must run the full query
        if self._results is None:
            if self.start == self.stop:
                self._results = []
            else:
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
            raise self.does_not_exist_exception("No results found")
        elif len(results) > 1:
            raise self.multiple_objects_returned_exception("Multiple results found")
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

    def set_limits(self, start, stop):
        if (start is not None and start < 0) or (stop is not None and stop < 0):
            raise ValueError("Negative indexing is not supported")

        if stop is not None:
            if self.stop is not None:
                self.stop = min(self.stop, self.start + stop)
            else:
                self.stop = self.start + stop
        if start is not None:
            if self.stop is not None:
                self.start = min(self.stop, self.start + start)
            else:
                self.start = self.start + start

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step is not None:
                raise ValueError("%r does not support slicing with a step" % self.__class__.__name__)

            clone = self.clone()
            clone.set_limits(key.start, key.stop)
            if self._results:
                clone._results = self._results[key]
            return clone
        elif isinstance(key, int):
            if key < 0:
                raise IndexError("Negative indexing is not supported")
            if self._results is not None:
                return self._results[key]
            else:
                clone = self.clone()
                clone.set_limits(key, key + 1)
                return list(clone)[0]
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


class VirtualModelOptions:
    def __init__(self, model_name, fields, verbose_name, verbose_name_plural):
        self.model_name = model_name
        self.fields = fields
        self.verbose_name = verbose_name
        self.verbose_name_plural = verbose_name_plural
        self.app_label = 'QueryishVirtualApp'
        self.db_table = 'QueryishVirtualTable'
        self.hidden_fields = []
        self.private_fields = []
        self.concrete_fields =  self.fields
        self.many_to_many = []

    def get_fields(self, include_parents=True, include_hidden=False):
        """
        Return a list of fields associated to the model. By default, include
        forward and reverse fields, fields derived from inheritance, but not
        hidden fields. The returned fields can be changed using the parameters:

        - include_parents: include fields derived from inheritance
        - include_hidden:  include fields that have a related_name that
                           starts with a "+"
        """
        fields = []
        
        for field in self.fields:
            fields.append(self.get_field(field))
        return tuple(fields)

    def get_field(self,field_name):
        try:
            from django.db import models
            from django.core.exceptions import FieldDoesNotExist
            
            if field_name in self.fields:
                field = models.CharField()
                field.name = field_name
                field.attname = field_name
                field.verbose_name = field_name
                field.concrete = True
                return field
            raise FieldDoesNotExist('No "' + field_name+'" found')
        except ImportError:
            raise ImportError("django must be installed to use get_field")

    def get_parent_list(self):
        return []


class VirtualModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # Create custom exception classes for DoesNotExist and MultipleObjectsReturned
        attrs["DoesNotExist"] = type("DoesNotExist", (ObjectDoesNotExist,), {})
        attrs["MultipleObjectsReturned"] = type("MultipleObjectsReturned", (MultipleObjectsReturned,), {})

        model = super().__new__(cls, name, bases, attrs)
        meta = getattr(model, "Meta", None)

        if model.base_query_class:
            # construct a queryset subclass with a 'model' attribute
            # and any additional attributes defined on the Meta class
            dct = {
                "model": model,
                "does_not_exist_exception": model.DoesNotExist,
                "multiple_objects_returned_exception": model.MultipleObjectsReturned,
            }
            if meta:
                for attr in dir(meta):
                    # attr must be defined on base_query_class to be valid
                    if hasattr(model.base_query_class, attr) and not attr.startswith("_"):
                        dct[attr] = getattr(meta, attr)

            # create the queryset subclass
            model.query_class = type("%sQuerySet" % name, (model.base_query_class,), dct)

            # Make an `objects` attribute available on the class
            model.objects = model._default_manager = model.query_class()

        # construct a VirtualModelOptions instance to use as the _meta attribute
        verbose_name = getattr(meta, "verbose_name", None)
        if verbose_name is None:
            re_camel_case = re.compile(r"(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))")
            verbose_name = re_camel_case.sub(r" \1", name).strip().lower()

        model._meta = VirtualModelOptions(
            model_name=name.lower(),
            fields=getattr(meta, "fields", []),
            verbose_name=verbose_name,
            verbose_name_plural=getattr(meta, "verbose_name_plural", verbose_name + "s"),
        )

        return model


class VirtualModel(metaclass=VirtualModelMetaclass):
    base_query_class = None
    pk_field_name = "id"
    DoesNotExist = ObjectDoesNotExist
    MultipleObjectsReturned = MultipleObjectsReturned

    @classmethod
    def from_query_data(cls, data):
        return cls(**data)

    @classmethod
    def from_individual_data(cls, data):
        return cls.from_query_data(data)

    def __init__(self, **kwargs):
        for field in self._meta.fields:
            setattr(self, field, kwargs.get(field))
        self.pk = kwargs.get(self.pk_field_name)

    def __str__(self):
        return f"{self.__class__.__name__} object ({self.pk})"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {str(self)}>"

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        if self.pk is None:
            return other is self
        return self.pk == other.pk
