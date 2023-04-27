from unittest import TestCase

from queryish import Queryish


class CounterSourceWithoutCount(Queryish):
    def __init__(self):
        super().__init__()
        self.run_query_call_count = 0

    def _get_real_limits(self):
        start = min(self.offset, 10)
        if self.limit is not None:
            stop = min(self.offset + self.limit, 10)
        else:
            stop = 10

        return (start, stop)

    def run_query(self):
        self.run_query_call_count += 1
        start, stop = self._get_real_limits()
        for i in range(start, stop):
            yield i


class CounterSource(CounterSourceWithoutCount):
    def __init__(self):
        super().__init__()
        self.run_count_call_count = 0

    def run_count(self):
        self.run_count_call_count += 1
        start, stop = self._get_real_limits()
        return stop - start


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

    def test_count_uses_results_by_default(self):
        qs = CounterSourceWithoutCount()
        self.assertEqual(qs.count(), 10)
        self.assertEqual(qs.count(), 10)
        self.assertEqual(qs.run_query_call_count, 1)

    def test_count_does_not_use_results_when_run_count_provided(self):
        qs = CounterSource()
        self.assertEqual(qs.count(), 10)
        self.assertEqual(qs.count(), 10)
        self.assertEqual(qs.run_count_call_count, 1)
        self.assertEqual(qs.run_query_call_count, 0)

    def test_len_uses_count(self):
        qs = CounterSource()
        self.assertEqual(len(qs), 10)
        self.assertEqual(qs.run_count_call_count, 1)
        self.assertEqual(qs.run_query_call_count, 0)

    def test_slicing(self):
        qs = CounterSource()[1:3]
        self.assertEqual(qs.offset, 1)
        self.assertEqual(qs.limit, 2)
        self.assertEqual(list(qs), [1, 2])
        self.assertEqual(qs.run_query_call_count, 1)

    def test_slicing_without_start(self):
        qs = CounterSource()[:3]
        self.assertEqual(qs.offset, 0)
        self.assertEqual(qs.limit, 3)
        self.assertEqual(list(qs), [0, 1, 2])
        self.assertEqual(qs.run_query_call_count, 1)

    def test_slicing_without_stop(self):
        qs = CounterSource()[3:]
        self.assertEqual(qs.offset, 3)
        self.assertEqual(qs.limit, None)
        self.assertEqual(list(qs), [3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(qs.run_query_call_count, 1)

    def test_multiple_slicing(self):
        qs1 = CounterSource()
        qs2 = qs1[1:9]
        self.assertEqual(qs2.offset, 1)
        self.assertEqual(qs2.limit, 8)
        qs3 = qs2[2:4]
        self.assertEqual(qs3.offset, 3)
        self.assertEqual(qs3.limit, 2)

        self.assertEqual(list(qs3), [3, 4])
        self.assertEqual(qs1.run_query_call_count, 0)
        self.assertEqual(qs2.run_query_call_count, 0)
        self.assertEqual(qs3.run_query_call_count, 1)

    def test_multiple_slicing_without_start(self):
        qs1 = CounterSource()
        qs2 = qs1[1:9]
        self.assertEqual(qs2.offset, 1)
        self.assertEqual(qs2.limit, 8)
        qs3 = qs2[:4]
        self.assertEqual(qs3.offset, 1)
        self.assertEqual(qs3.limit, 4)

        self.assertEqual(list(qs3), [1, 2, 3, 4])
        self.assertEqual(qs1.run_query_call_count, 0)
        self.assertEqual(qs2.run_query_call_count, 0)
        self.assertEqual(qs3.run_query_call_count, 1)

    def test_multiple_slicing_without_stop(self):
        qs1 = CounterSource()
        qs2 = qs1[1:9]
        self.assertEqual(qs2.offset, 1)
        self.assertEqual(qs2.limit, 8)
        qs3 = qs2[2:]
        self.assertEqual(qs3.offset, 3)
        self.assertEqual(qs3.limit, 6)

        self.assertEqual(list(qs3), [3, 4, 5, 6, 7, 8])
        self.assertEqual(qs1.run_query_call_count, 0)
        self.assertEqual(qs2.run_query_call_count, 0)
        self.assertEqual(qs3.run_query_call_count, 1)
