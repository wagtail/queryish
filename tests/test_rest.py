import re
from unittest import TestCase
import responses
from responses import matchers

from queryish.rest import APIModel, APIQuerySet


class CountryAPIQuerySet(APIQuerySet):
    base_url = "http://example.com/api/countries/"
    filter_fields = ["id", "name", "continent"]
    ordering_fields = ["id", "name", "continent"]


class UnpaginatedCountryAPIQuerySet(CountryAPIQuerySet):
    pass


class LimitOffsetPaginatedCountryAPIQuerySet(CountryAPIQuerySet):
    pagination_style = "offset-limit"


class PageNumberPaginatedCountryAPIQuerySet(CountryAPIQuerySet):
    pagination_style = "page-number"
    page_size = 2


class Country(APIModel):
    class Meta:
        base_url = "http://example.com/api/countries/"
        fields = ["id", "name", "continent"]

    def __str__(self):
        return self.name


class Pokemon(APIModel):
    class Meta:
        base_url = "https://pokeapi.co/api/v2/pokemon/"
        detail_url = "https://pokeapi.co/api/v2/pokemon/%d/"
        fields = ["id", "name"]
        pagination_style = "offset-limit"

    @classmethod
    def from_query_data(cls, data):
        return cls(
            id=int(re.match(r'https://pokeapi.co/api/v2/pokemon/(\d+)/', data['url']).group(1)),
            name=data['name'],
        )

    @classmethod
    def from_individual_data(cls, data):
        return cls(
            id=data['id'],
            name=data['name'],
        )

    def __str__(self):
        return self.name


class TestAPIQuerySet(TestCase):
    @responses.activate
    def test_fetch_unpaginated(self):
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            body="""
                [
                    {
                        "id": 1,
                        "name": "France",
                        "continent": "europe"
                    },
                    {
                        "id": 2,
                        "name": "Germany",
                        "continent": "europe"
                    },
                    {
                        "id": 3,
                        "name": "Italy",
                        "continent": "europe"
                    },
                    {
                        "id": 4,
                        "name": "Japan",
                        "continent": "asia"
                    },
                    {
                        "id": 5,
                        "name": "China",
                        "continent": "asia"
                    }
                ]
            """
        )

        self.assertEqual(UnpaginatedCountryAPIQuerySet().count(), 5)

        results = UnpaginatedCountryAPIQuerySet()[1:3]
        self.assertFalse(results.ordered)
        self.assertEqual(list(results), [
            {"id": 2, "name": "Germany", "continent": "europe"},
            {"id": 3, "name": "Italy", "continent": "europe"},
        ])

    @responses.activate
    def test_fetch_limit_offset_paginated(self):
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"limit": 1})],
            body="""
                {
                    "count": 5,
                    "next": "http://example.com/api/countries/?limit=1&offset=1",
                    "previous": null,
                    "results": [
                        {
                            "id": 1,
                            "name": "France",
                            "continent": "europe"
                        }
                    ]
                }
            """
        )

        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"offset": 0})],
            body="""
                {
                    "count": 5,
                    "next": "http://example.com/api/countries/?limit=2&offset=2",
                    "previous": null,
                    "results": [
                        {
                            "id": 1,
                            "name": "France",
                            "continent": "europe"
                        },
                        {
                            "id": 2,
                            "name": "Germany",
                            "continent": "europe"
                        }
                    ]
                }
            """
        )

        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"offset": 2})],
            body="""
                {
                    "count": 5,
                    "next": "http://example.com/api/countries/?limit=2&offset=4",
                    "previous": "http://example.com/api/countries/?limit=2",
                    "results": [
                        {
                            "id": 3,
                            "name": "Italy",
                            "continent": "europe"
                        },
                        {
                            "id": 4,
                            "name": "Japan",
                            "continent": "asia"
                        }
                    ]
                }
            """
        )

        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"offset": 4})],
            body="""
                {
                    "count": 5,
                    "next": null,
                    "previous": "http://example.com/api/countries/?limit=2&offset=2",
                    "results": [
                        {
                            "id": 5,
                            "name": "China",
                            "continent": "asia"
                        }
                    ]
                }
            """
        )

        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"limit": 2, "offset": 2})],
            body="""
                {
                    "count": 5,
                    "next": "http://example.com/api/countries/?limit=2&offset=4",
                    "previous": "http://example.com/api/countries/?limit=2",
                    "results": [
                        {
                            "id": 3,
                            "name": "Italy",
                            "continent": "europe"
                        },
                        {
                            "id": 4,
                            "name": "Japan",
                            "continent": "asia"
                        }
                    ]
                }
            """
        )

        self.assertEqual(LimitOffsetPaginatedCountryAPIQuerySet().count(), 5)

        full_results = list(LimitOffsetPaginatedCountryAPIQuerySet())
        self.assertEqual(full_results[2], {"id": 3, "name": "Italy", "continent": "europe"})

        partial_results = list(LimitOffsetPaginatedCountryAPIQuerySet()[2:4])
        self.assertEqual(partial_results, [
            {"id": 3, "name": "Italy", "continent": "europe"},
            {"id": 4, "name": "Japan", "continent": "asia"},
        ])

    @responses.activate
    def test_fetch_page_number_paginated(self):
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"page": 1})],
            body="""
                {
                    "count": 5,
                    "next": "http://example.com/api/countries/?page=2",
                    "previous": null,
                    "results": [
                        {
                            "id": 1,
                            "name": "France",
                            "continent": "europe"
                        },
                        {
                            "id": 2,
                            "name": "Germany",
                            "continent": "europe"
                        }
                    ]
                }
            """
        )
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"page": 2})],
            body="""
                {
                    "count": 5,
                    "next": "http://example.com/api/countries/?page=3",
                    "previous": "http://example.com/api/countries/",
                    "results": [
                        {
                            "id": 3,
                            "name": "Italy",
                            "continent": "europe"
                        },
                        {
                            "id": 4,
                            "name": "Japan",
                            "continent": "asia"
                        }
                    ]
                }
            """
        )
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"page": 3})],
            body="""
                {
                    "count": 5,
                    "next": null,
                    "previous": "http://example.com/api/countries/?page=2",
                    "results": [
                        {
                            "id": 5,
                            "name": "China",
                            "continent": "asia"
                        }
                    ]
                }
            """
        )

        self.assertEqual(PageNumberPaginatedCountryAPIQuerySet().count(), 5)

        full_results = list(PageNumberPaginatedCountryAPIQuerySet())
        self.assertEqual(full_results[2], {"id": 3, "name": "Italy", "continent": "europe"})

        partial_results = list(PageNumberPaginatedCountryAPIQuerySet()[2:4])
        self.assertEqual(partial_results, [
            {"id": 3, "name": "Italy", "continent": "europe"},
            {"id": 4, "name": "Japan", "continent": "asia"},
        ])

    @responses.activate
    def test_filter(self):
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"continent": "asia"})],
            body="""
                [
                    {
                        "id": 4,
                        "name": "Japan",
                        "continent": "asia"
                    },
                    {
                        "id": 5,
                        "name": "China",
                        "continent": "asia"
                    }
                ]
            """
        )
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({})],
            body="""
                [
                    {
                        "id": 1,
                        "name": "France",
                        "continent": "europe"
                    },
                    {
                        "id": 2,
                        "name": "Germany",
                        "continent": "europe"
                    },
                    {
                        "id": 3,
                        "name": "Italy",
                        "continent": "europe"
                    },
                    {
                        "id": 4,
                        "name": "Japan",
                        "continent": "asia"
                    },
                    {
                        "id": 5,
                        "name": "China",
                        "continent": "asia"
                    }
                ]
            """
        )

        all_results = UnpaginatedCountryAPIQuerySet()
        results = all_results.filter(continent="asia")
        self.assertEqual(results.count(), 2)
        # filter should not affect the original queryset
        self.assertEqual(all_results.count(), 5)
        self.assertEqual(list(results), [
            {"id": 4, "name": "Japan", "continent": "asia"},
            {"id": 5, "name": "China", "continent": "asia"},
        ])

    @responses.activate
    def test_multiple_filters(self):
        # multiple filters should be ANDed together
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"continent": "asia", "name": "Japan"})],
            body="""
                [
                    {
                        "id": 4,
                        "name": "Japan",
                        "continent": "asia"
                    }
                ]
            """
        )

        results = UnpaginatedCountryAPIQuerySet().filter(continent="asia", name="Japan")
        self.assertEqual(results.count(), 1)
        self.assertEqual(list(results), [{"id": 4, "name": "Japan", "continent": "asia"}])

        # filters can also be chained
        results = UnpaginatedCountryAPIQuerySet().filter(continent="asia").filter(name="Japan")
        self.assertEqual(results.count(), 1)
        self.assertEqual(list(results), [{"id": 4, "name": "Japan", "continent": "asia"}])

    @responses.activate
    def test_filter_by_field_alias(self):
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"id": 4})],
            body="""
                [
                    {
                        "id": 4,
                        "name": "Japan",
                        "continent": "asia"
                    }
                ]
            """
        )

        results = UnpaginatedCountryAPIQuerySet().filter(pk=4)
        self.assertEqual(results.count(), 1)
        self.assertEqual(list(results), [{"id": 4, "name": "Japan", "continent": "asia"}])

    @responses.activate
    def test_ordering(self):
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"continent": "asia", "ordering": "name"})],
            body="""
                [
                    {
                        "id": 5,
                        "name": "China",
                        "continent": "asia"
                    },
                    {
                        "id": 4,
                        "name": "Japan",
                        "continent": "asia"
                    }
                ]
            """
        )

        results = UnpaginatedCountryAPIQuerySet().filter(continent="asia").order_by("name")
        self.assertTrue(results.ordered)
        self.assertEqual(results.count(), 2)
        self.assertEqual(list(results), [
            {"id": 5, "name": "China", "continent": "asia"},
            {"id": 4, "name": "Japan", "continent": "asia"},
        ])

    @responses.activate
    def test_get(self):
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"name": "France"})],
            body="""
                [
                    {
                        "id": 1,
                        "name": "France",
                        "continent": "europe"
                    }
                ]
            """
        )

        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"name": "Wakanda"})],
            body="""
                []
            """
        )

        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"continent": "europe"})],
            body="""
                [
                    {
                        "id": 1,
                        "name": "France",
                        "continent": "europe"
                    },
                    {
                        "id": 2,
                        "name": "Germany",
                        "continent": "europe"
                    },
                    {
                        "id": 3,
                        "name": "Italy",
                        "continent": "europe"
                    }
                ]
            """
        )

        self.assertEqual(
            UnpaginatedCountryAPIQuerySet().get(name="France"),
            {"id": 1, "name": "France", "continent": "europe"}
        )
        with self.assertRaises(ValueError):
            UnpaginatedCountryAPIQuerySet().get(name="Wakanda")

        with self.assertRaises(ValueError):
            UnpaginatedCountryAPIQuerySet().get(continent="europe")


class TestAPIModel(TestCase):
    @responses.activate
    def test_query(self):
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            match=[matchers.query_param_matcher({"continent": "europe", "ordering": "-name"})],
            body="""
                [
                    {
                        "id": 3,
                        "name": "Italy",
                        "continent": "europe"
                    },
                    {
                        "id": 2,
                        "name": "Germany",
                        "continent": "europe"
                    },
                    {
                        "id": 1,
                        "name": "France",
                        "continent": "europe"
                    }
                ]
            """
        )

        results = Country.objects.filter(continent="europe").order_by("-name")
        self.assertEqual(results.count(), 3)
        self.assertIsInstance(results[0], Country)
        country_names = [country.name for country in results]
        self.assertEqual(country_names, ["Italy", "Germany", "France"])
        self.assertEqual(repr(results[0]), "<Country: Italy>")
        self.assertEqual(str(results[0]), "Italy")

    @responses.activate
    def test_instance_from_query_data(self):
        responses.add(
            responses.GET, "https://pokeapi.co/api/v2/pokemon/",
            match=[matchers.query_param_matcher({"offset": "0", "limit": "1"})],
            body="""
                {"count":1281,"next":"https://pokeapi.co/api/v2/pokemon/?offset=1&limit=1","previous":null,"results":[{"name":"bulbasaur","url":"https://pokeapi.co/api/v2/pokemon/1/"}]}
            """
        )
        result = Pokemon.objects.first()
        self.assertEqual(result.name, "bulbasaur")
        self.assertEqual(result.id, 1)

    @responses.activate
    def test_instance_from_detail_lookup(self):
        responses.add(
            responses.GET, "https://pokeapi.co/api/v2/pokemon/3/",
            body="""
                {"name":"venusaur", "id":3}
            """
        )
        result = Pokemon.objects.get(id=3)
        self.assertEqual(result.name, "venusaur")
        self.assertEqual(result.id, 3)


    @responses.activate
    def test_in_bulk(self):
        responses.add(
            responses.GET, "https://pokeapi.co/api/v2/pokemon/3/",
            body="""
                {"name":"venusaur", "id":3}
            """
        )
        responses.add(
            responses.GET, "https://pokeapi.co/api/v2/pokemon/6/",
            body="""
                {"name":"charizard", "id":6}
            """
        )
        result = Pokemon.objects.in_bulk([3, 6])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[3].name, "venusaur")
        self.assertEqual(result[3].id, 3)
        self.assertEqual(result[6].name, "charizard")
        self.assertEqual(result[6].id, 6)
