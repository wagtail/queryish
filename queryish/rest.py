import requests

from queryish import Queryish


class APISource(Queryish):
    pagination_style = None

    def __init__(self):
        super().__init__()
        self._responses = {}  # cache for API responses

    def get_filters_as_query_dict(self):
        params = {}
        for key, val in self.filters:
            if key in params:
                if isinstance(params[key], list):
                    params[key].append(val)
                else:
                    params[key] = [params[key], val]
            else:
                params[key] = val
        return params

    def run_query(self):
        params = self.get_filters_as_query_dict()

        if self.pagination_style == "offset-limit":
            offset = self.offset
            limit = self.limit
            returned_result_count = 0

            while True:
                # continue fetching pages of results until we reach either
                # the end of the result set or the end of the slice
                response_json = self.fetch_api_response(params={
                    "offset": offset,
                    "limit": limit,
                    **params,
                })
                results_page = self.get_results_from_response(response_json)
                for result in results_page:
                    yield result
                    returned_result_count += 1
                    if limit is not None and returned_result_count >= limit:
                        return
                if len(results_page) == 0 or offset + len(results_page) >= response_json["count"]:
                    # we've reached the end of the result set
                    return

                offset += len(results_page)
                if limit is not None:
                    limit -= len(results_page)
        elif self.pagination_style == "page-number":
            offset = self.offset
            limit = self.limit
            returned_result_count = 0

            while True:
                # continue fetching pages of results until we reach either
                # the end of the result set or the end of the slice
                page = 1 + offset // self.page_size
                response_json = self.fetch_api_response(params={
                    "page": page,
                    **params,
                })
                results_page = self.get_results_from_response(response_json)
                results_page_offset = offset % self.page_size
                for result in results_page[results_page_offset:]:
                    yield result
                    returned_result_count += 1
                    if self.limit is not None and returned_result_count >= self.limit:
                        return
                if len(results_page) == 0 or offset + len(results_page) >= response_json["count"]:
                    # we've reached the end of the result set
                    return

                offset += len(results_page)
                if limit is not None:
                    limit -= len(results_page)
        else:
            response_json = self.fetch_api_response(params=params)
            if self.limit is None:
                stop = None
            else:
                stop = self.offset + self.limit
            results = self.get_results_from_response(response_json)
            yield from results[self.offset:stop]

    def run_count(self):
        params = self.get_filters_as_query_dict()

        if self.pagination_style == "offset-limit" or self.pagination_style == "page-number":
            if self.pagination_style == "offset-limit":
                params["limit"] = 1
            else:
                params["page"] = 1

            response_json = self.fetch_api_response(params=params)
            count = response_json["count"]
            # count is the full result set without considering slicing;
            # we need to adjust it to the slice
            if self.limit is not None:
                count = min(count, self.limit)
            count = max(0, count - self.offset)
            return count

        else:
            # default to standard behaviour of getting all results and counting them
            return super().run_count()

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
        if self.pagination_style == "offset-limit" or self.pagination_style == "page-number":
            return response["results"]
        else:
            return response
