from unittest import TestCase

from queryish import Queryish


class CounterSource(Queryish):
    def __init__(self):
        super().__init__()
        self.run_query_call_count = 0

    def run_query(self):
        self.run_query_call_count += 1
        for i in range(0, 10):
            yield i


class TestQueryish(TestCase):
    def test_get_results_as_list(self):
        qs = CounterSource()
        self.assertEqual(list(qs), list(range(0, 10)))
        self.assertEqual(qs.run_query_call_count, 1)

    def test_query_is_only_run_once(self):
        qs = CounterSource()
        list(qs)
        list(qs)
        self.assertEqual(qs.run_query_call_count, 1)
