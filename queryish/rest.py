import requests

from queryish import Queryish


class APISource(Queryish):
    def __init__(self):
        super().__init__()
        self._responses = {}  # cache for API responses

    def run_query(self):
        response_json = self.fetch_api_response()
        if self.limit is None:
            stop = None
        else:
            stop = self.offset + self.limit
        return response_json[self.offset:stop]

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
