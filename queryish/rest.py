import requests

from queryish import Queryish


class APISource(Queryish):
    def run_query(self):
        response_json = requests.get(
            self.base_url,
            headers={"Accept": "application/json"},
        ).json()
        if self.limit is None:
            stop = None
        else:
            stop = self.offset + self.limit
        return response_json[self.offset:stop]
