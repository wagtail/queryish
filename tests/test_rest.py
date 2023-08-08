from unittest import TestCase
import responses
from responses import matchers

from queryish.rest import APIQuerySet


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
