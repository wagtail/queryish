from unittest import TestCase
import responses

from queryish.rest import APISource


class CountryAPISource(APISource):
    base_url = "http://example.com/api/countries/"



class TestAPISource(TestCase):
    @responses.activate
    def test_fetch(self):
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
        results = list(CountryAPISource()[1:3])
        self.assertEqual(results, [
            {"name": "Germany", "continent": "europe"},
            {"name": "Italy", "continent": "europe"},
        ])
