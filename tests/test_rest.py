from unittest import TestCase
import responses
from responses import matchers

from queryish.rest import APISource


class UnpaginatedCountryAPISource(APISource):
    base_url = "http://example.com/api/countries/"


class LimitOffsetPaginatedCountryAPISource(APISource):
    base_url = "http://example.com/api/countries/"
    pagination_style = "offset-limit"


class PageNumberPaginatedCountryAPISource(APISource):
    base_url = "http://example.com/api/countries/"
    pagination_style = "page-number"
    page_size = 2


class TestAPISource(TestCase):
    @responses.activate
    def test_fetch_unpaginated(self):
        responses.add(
            responses.GET, "http://example.com/api/countries/",
            body="""
                [
                    {
                        "name": "France",
                        "continent": "europe"
                    },
                    {
                        "name": "Germany",
                        "continent": "europe"
                    },
                    {
                        "name": "Italy",
                        "continent": "europe"
                    },
                    {
                        "name": "Japan",
                        "continent": "asia"
                    },
                    {
                        "name": "China",
                        "continent": "asia"
                    }
                ]
            """
        )

        self.assertEqual(UnpaginatedCountryAPISource().count(), 5)

        results = list(UnpaginatedCountryAPISource()[1:3])
        self.assertEqual(results, [
            {"name": "Germany", "continent": "europe"},
            {"name": "Italy", "continent": "europe"},
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
                            "name": "France",
                            "continent": "europe"
                        },
                        {
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
                            "name": "Italy",
                            "continent": "europe"
                        },
                        {
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
                            "name": "Italy",
                            "continent": "europe"
                        },
                        {
                            "name": "Japan",
                            "continent": "asia"
                        }
                    ]
                }
            """
        )

        self.assertEqual(LimitOffsetPaginatedCountryAPISource().count(), 5)

        full_results = list(LimitOffsetPaginatedCountryAPISource())
        self.assertEqual(full_results[2], {"name": "Italy", "continent": "europe"})

        partial_results = list(LimitOffsetPaginatedCountryAPISource()[2:4])
        self.assertEqual(partial_results, [
            {"name": "Italy", "continent": "europe"},
            {"name": "Japan", "continent": "asia"},
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
                            "name": "France",
                            "continent": "europe"
                        },
                        {
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
                            "name": "Italy",
                            "continent": "europe"
                        },
                        {
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
                            "name": "China",
                            "continent": "asia"
                        }
                    ]
                }
            """
        )

        self.assertEqual(PageNumberPaginatedCountryAPISource().count(), 5)

        full_results = list(PageNumberPaginatedCountryAPISource())
        self.assertEqual(full_results[2], {"name": "Italy", "continent": "europe"})

        partial_results = list(PageNumberPaginatedCountryAPISource()[2:4])
        self.assertEqual(partial_results, [
            {"name": "Italy", "continent": "europe"},
            {"name": "Japan", "continent": "asia"},
        ])
