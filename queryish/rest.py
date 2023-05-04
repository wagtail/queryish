import requests

from queryish import Queryish


class APISource(Queryish):
    pagination_style = None

    def __init__(self):
        super().__init__()
        self._responses = {}  # cache for API responses

    def run_query(self):
        if self.pagination_style == "offset-limit":
            response_json = self.fetch_api_response(params={
                "offset": self.offset,
                "limit": self.limit,
            })
            return self.get_results_from_response(response_json)
        else:
            response_json = self.fetch_api_response()
            if self.limit is None:
                stop = None
            else:
                stop = self.offset + self.limit
            results = self.get_results_from_response(response_json)
            return results[self.offset:stop]

    def fetch_api_response(self, params=None):
        # construct a hashable key for the params
        if params is None:
            params = {}
        key = tuple(sorted(params.items()))
        if key not in self._responses:
            self._responses[key] = requests.get(
                self.base_url,
                params=params,
                headers={"Accept": "application/json"},
            ).json()
        return self._responses[key]

    def get_results_from_response(self, response):
        if self.pagination_style == "offset-limit":
            return response["results"]
        else:
            return response
