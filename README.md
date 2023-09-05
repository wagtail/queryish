# queryish

A Python library for constructing queries on arbitrary data sources following Django's QuerySet API.

## Motivation

Django's QuerySet API is a powerful tool for constructing queries on a database. It allows you to compose queries incrementally, with the query only being executed when the results are needed:

```python
books = Book.objects.all()
python_books = books.filter(topic='python')
latest_python_books = python_books.order_by('-publication_date')[:5]
print(latest_python_books)  # Query is executed here
```

This pattern is a good fit for building web interfaces for listing data, as it allows filtering, ordering and pagination to be handled as separate steps.

We may often be required to implement similar interfaces for data taken from sources other than a database, such as a REST API or a search engine. In these cases, we would like to have a similarly rich API for constructing queries to these data sources. Even better would be to follow the QuerySet API as closely as possible, so that we can take advantage of ready-made tools such as [Django's generic class-based views](https://docs.djangoproject.com/en/stable/topics/class-based-views/) that are designed to work with this API.

_queryish_ is a library for building wrappers around data sources that replicate the QuerySet API, allowing you to work with the data in the same way that you would with querysets and models.

## Installation

Install using pip:

```bash
pip install queryish
```

## Usage - REST APIs

_queryish_ provides a base class `queryish.rest.APIModel` for wrapping REST APIs. By default, this follows the out-of-the-box structure served by [Django REST Framework](https://www.django-rest-framework.org/), but various options are available to customise this.

```python
from queryish.rest import APIModel

class Party(APIModel):
    class Meta:
        base_url = "https://demozoo.org/api/v1/parties/"
        fields = ["id", "name", "start_date", "end_date", "location", "country_code"]
        pagination_style = "page-number"
        page_size = 100

    def __str__(self):
        return self.name
```

The resulting class has an `objects` property that supports the usual filtering, ordering and slicing operations familiar from Django's QuerySet API, although these may be limited by the capabilities of the REST API being accessed.

```python
>>> Party.objects.count()
4623
>>> Party.objects.filter(country_code="GB")[:10]
<PartyQuerySet [<Party: 16 Bit Show 1991>, <Party: Acorn User Show 1991>, <Party: Anarchy Easter Party 1992>, <Party: Anarchy Winter Conference 1991>, <Party: Atari Preservation Party 2007>, <Party: Commodore Computer Club UK 1st Meet>, <Party: Commodore Show 1987>, <Party: Commodore Show 1988>, <Party: Deja Vu 1998>, <Party: Deja Vu 1999>]>
>>> Party.objects.get(name="Nova 2023")
<Party: Nova 2023>
```

Methods supported include `all`, `count`, `filter`, `order_by`, `get`, `first`, and `in_bulk`. The result set can be sliced at arbitrary indices - these do not have to match the pagination supported by the underlying API. `APIModel` will automatically make multiple API requests as required.

The following attributes are available on `APIModel.Meta`:

* `base_url`: The base URL of the API from where results can be fetched.
* `pk_field_name`: The name of the primary key field. Defaults to `"id"`. Lookups on the field name `"pk"` will be mapped to this field.
* `detail_url`: A string template for the URL of a single object, such as `"https://demozoo.org/api/v1/parties/%s/"`. If this is specified, lookups on the primary key and no other fields will be directed to this URL rather than `base_url`.
* `fields`: A list of field names defined in the API response that will be copied to attributes of the returned object.
* `pagination_style`: The style of pagination used by the API. Recognised values are `"page-number"` and `"offset-limit"`; all others (including the default of `None`) indicate no pagination.
* `page_size`: Required if `pagination_style` is `"page-number"` - the number of results per page returned by the API.
* `page_query_param`: The name of the URL query parameter used to specify the page number. Defaults to `"page"`.
* `offset_query_param`: The name of the URL query parameter used to specify the offset. Defaults to `"offset"`.
* `limit_query_param`: The name of the URL query parameter used to specify the limit. Defaults to `"limit"`.
* `ordering_query_param`: The name of the URL query parameter used to specify the ordering. Defaults to `"ordering"`.

To accommodate APIs where the returned JSON does not map cleanly to the intended set of model attributes, the class methods `from_query_data` and `from_individual_data` on `APIModel` can be overridden:

```python
class Pokemon(APIModel):
    class Meta:
        base_url = "https://pokeapi.co/api/v2/pokemon/"
        detail_url = "https://pokeapi.co/api/v2/pokemon/%s/"
        fields = ["id", "name"]
        pagination_style = "offset-limit"
        verbose_name_plural = "pokemon"

    @classmethod
    def from_query_data(cls, data):
        """
        Given a record returned from the listing endpoint (base_url), return an instance of the model.
        """
        # Records within the listing endpoint return a `url` field, from which we want to extract the ID
        return cls(
            id=int(re.match(r'https://pokeapi.co/api/v2/pokemon/(\d+)/', data['url']).group(1)),
            name=data['name'],
        )

    @classmethod
    def from_individual_data(cls, data):
        """
        Given a record returned from the detail endpoint (detail_url), return an instance of the model.
        """
        return cls(
            id=data['id'],
            name=data['name'],
        )

    def __str__(self):
        return self.name
```

## Customising the REST API queryset class

The `objects` attribute of an `APIModel` subclass is an instance of `queryish.rest.APIQuerySet` which initially consists of the complete set of records. As with Django's QuerySet, methods such as `filter` return a new instance.

It may be necessary to subclass `APIQuerySet` and override methods in order to support certain API responses. For example, the base implementation expects unpaginated API endpoints to return a list as the top-level JSON object, and paginated API endpoints to return a dict with a `results` item. If the API you are working with returns a different structure, you can override the `get_results_from_response` method to extract the list of results from the response:

```python
from queryish.rest import APIQuerySet

class TreeQuerySet(APIQuerySet):
    base_url = "https://api.data.amsterdam.nl/v1/bomen/stamgegevens/"
    pagination_style = "page-number"
    page_size = 20
    http_headers = {"Accept": "application/hal+json"}

    def get_results_from_response(self, response):
        return response["_embedded"]["stamgegevens"]
```

`APIQuerySet` subclasses can be instantiated independently of an `APIModel`, but results will be returned as plain JSON values:

```python
>>> TreeQuerySet().filter(jaarVanAanleg=1986).first()
{'_links': {'schema': 'https://schemas.data.amsterdam.nl/datasets/bomen/dataset#stamgegevens', 'self': {'href': 'https://api.data.amsterdam.nl/v1/bomen/stamgegevens/1101570/', 'title': '1101570', 'id': 1101570}, 'gbdBuurt': {'href': 'https://api.data.amsterdam.nl/v1/gebieden/buurten/03630980000211/', 'title': '03630980000211', 'identificatie': '03630980000211'}}, 'id': 1101570, 'gbdBuurtId': '03630980000211', 'geometrie': {'type': 'Point', 'coordinates': [115162.72, 485972.68]}, 'boomhoogteklasseActueel': 'c. 9 tot 12 m.', 'jaarVanAanleg': 1986, 'soortnaam': "Salix alba 'Chermesina'", 'stamdiameterklasse': '0,5 tot 1 m.', 'typeObject': 'Gekandelaberde boom', 'typeSoortnaam': 'Bomen', 'soortnaamKort': 'Salix', 'soortnaamTop': 'Wilg (Salix)'}
```

This can be overridden by defining a `model` attribute on the queryset, or overriding the `get_instance` / `get_individual_instance` methods. To use a customised queryset with an `APIModel`, define the `base_query_class` attribute on the model class:

```python
class Tree(APIModel):
    base_query_class = TreeQuerySet
    class Meta:
        fields = ["id", "geometrie", "boomhoogteklasseActueel", "jaarVanAanleg", "soortnaam", "soortnaamKort"]

# >>> Tree.objects.filter(jaarVanAanleg=1986).first()
# <Tree: Tree object (1101570)>
```

## Other data sources

_queryish_ is not limited to REST APIs - the base class `queryish.Queryish` can be used to build a QuerySet-like API around any data source. At minimum, this requires defining a `run_query` method that returns an iterable of records that is filtered, ordered and sliced according to the queryset's attributes. For example, a queryset implementation that works from a simple in-memory list of objects might look like this:

```python
from queryish import Queryish

class CountryQuerySet(Queryish):
    def run_query(self):
        countries = [
            {"code": "nl", "name": "Netherlands"},
            {"code": "de", "name": "Germany"},
            {"code": "fr", "name": "France"},
            {"code": "gb", "name": "United Kingdom"},
            {"code": "us", "name": "United States"},
        ]

        # Filter the list of countries by `self.filters` - a list of (key, value) tuples
        for (key, val) in self.filters:
            countries = [c for c in countries if c[key] == val]

        # Sort the list of countries by `self.ordering` - a tuple of field names
        countries.sort(key=lambda c: [c.get(field, None) for field in self.ordering])

        # Slice the list of countries by `self.offset` and `self.limit`. `offset` is always numeric
        # and defaults to 0 for an unsliced list; `limit` is either numeric or None (denoting no limit).
        return countries[self.offset : self.offset + self.limit if self.limit else None]
```

Subclasses will also typically override the method `run_count`, which returns the number of records in the queryset accounting for any filtering and slicing. If this is not overridden, the default implementation will call `run_query` and count the results.
