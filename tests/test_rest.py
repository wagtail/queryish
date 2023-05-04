from unittest import TestCase
import responses

from queryish.rest import APISource


class UnpaginatedCountryAPISource(APISource):
    base_url = "http://example.com/api/countries/"


class LimitOffsetPaginatedCountryAPISource(APISource):
    base_url = "http://example.com/api/countries/"
    pagination_style = "offset-limit"


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
        results = list(UnpaginatedCountryAPISource()[1:3])
        self.assertEqual(results, [
            {"name": "Germany", "continent": "europe"},
            {"name": "Italy", "continent": "europe"},
        ])

    @responses.activate
    def test_fetch_limit_offset_paginated(self):
        responses.add(
            responses.GET, "http://example.com/api/countries/?limit=2&offset=2",
            body="""
                {
                    "count": 5,
                    "next": "http://localhost:8000/api/countries/?limit=2&offset=4",
                    "previous": "http://localhost:8000/api/countries/?limit=2",
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
        results = list(LimitOffsetPaginatedCountryAPISource()[2:4])
        self.assertEqual(results, [
            {"name": "Italy", "continent": "europe"},
            {"name": "Japan", "continent": "asia"},
        ])
