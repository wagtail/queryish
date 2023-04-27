from unittest import TestCase

from queryish import Queryish


class CounterSource(Queryish):
    def run_query(self):
        for i in range(0, 10):
            yield i


class TestQueryish(TestCase):
    def test_get_results_as_list(self):
        qs = CounterSource()
        self.assertEqual(list(qs), list(range(0, 10)))
