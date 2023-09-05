from functools import cached_property
import requests

from queryish import Queryish, VirtualModel


class APIQuerySet(Queryish):
    base_url = None
    detail_url = None
    pagination_style = None
    pk_field_name = "id"
    limit_query_param = "limit"
    offset_query_param = "offset"
    page_query_param = "page"
    ordering_query_param = "ordering"
    model = None
    page_size = None
    http_headers = {"Accept": "application/json"}

    def __init__(self):
        super().__init__()
        self._responses = {}  # cache for API responses

    @cached_property
    def filter_field_aliases(self):
        return {"pk": self.pk_field_name}

    def filter_is_valid(self, key, val):
        if key in self.filter_field_aliases:
            key = self.filter_field_aliases[key]
        return super().filter_is_valid(key, val)

    def get_filters_as_query_dict(self):
        params = {}
        for key, val in self.filters:
            # map key to the real API field name, if present in filter_field_aliases
            key = self.filter_field_aliases.get(key, key)

            if key in params:
                if isinstance(params[key], list):
                    params[key].append(val)
                else:
                    params[key] = [params[key], val]
            else:
                params[key] = val
        return params

    def get_instance(self, val):
        if self.model:
            return self.model.from_query_data(val)
        else:
            return val

    def get_individual_instance(self, val):
        if self.model:
            return self.model.from_individual_data(val)
        else:
            return val

    def get_detail_url(self, pk):
        return self.detail_url % pk

    def run_query(self):
        params = self.get_filters_as_query_dict()

        if list(params.keys()) == [self.pk_field_name] and self.detail_url:
            # if the only filter is the pk, we can use the detail view
            # to fetch the single instance
            yield self.get_individual_instance(self.fetch_api_response(
                url=self.get_detail_url(params[self.pk_field_name]),
            ))
            return

        if self.ordering:
            params[self.ordering_query_param] = ",".join(self.ordering)

        if self.pagination_style == "offset-limit":
            offset = self.offset
            limit = self.limit
            returned_result_count = 0

            while True:
                # continue fetching pages of results until we reach either
                # the end of the result set or the end of the slice
                response_json = self.fetch_api_response(params={
                    self.offset_query_param: offset,
                    self.limit_query_param: limit,
                    **params,
                })
                results_page = self.get_results_from_response(response_json)
                for result in results_page:
                    yield self.get_instance(result)
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
                    self.page_query_param: page,
                    **params,
                })
                results_page = self.get_results_from_response(response_json)
                results_page_offset = offset % self.page_size
                for result in results_page[results_page_offset:]:
                    yield self.get_instance(result)
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
            for item in results[self.offset:stop]:
                yield self.get_instance(item)

    def run_count(self):
        params = self.get_filters_as_query_dict()

        if self.pagination_style == "offset-limit" or self.pagination_style == "page-number":
            if self.pagination_style == "offset-limit":
                params[self.limit_query_param] = 1
            else:
                params[self.page_query_param] = 1

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

    def fetch_api_response(self, url=None, params=None):
        # construct a hashable key for the params
        if url is None:
            url = self.base_url

        if params is None:
            params = {}
        key = tuple([url] + sorted(params.items()))
        if key not in self._responses:
            self._responses[key] = requests.get(
                url,
                params=params,
                headers=self.http_headers,
            ).json()
        return self._responses[key]

    def get_results_from_response(self, response):
        if self.pagination_style == "offset-limit" or self.pagination_style == "page-number":
            return response["results"]
        else:
            return response

    def in_bulk(self, id_list=None, field_name="pk"):
        return {
            id: self.get(**{field_name: id})
            for id in (id_list or [])
        }


class APIModel(VirtualModel):
    base_query_class = APIQuerySet
