from unittest import TestCase

from queryish import Queryish


class CounterSourceWithoutCount(Queryish):
    def __init__(self, max_count=10):
        super().__init__()
        self.max_count = max_count
        self.run_query_call_count = 0

    def _get_real_limits(self):
        start = min(self.offset, self.max_count)
        if self.limit is not None:
            stop = min(self.offset + self.limit, self.max_count)
        else:
            stop = self.max_count

        return (start, stop)

    def run_query(self):
        self.run_query_call_count += 1
        start, stop = self._get_real_limits()
        for i in range(start, stop):
            yield i

    def clone(self, **kwargs):
        clone = super().clone(**kwargs)
        clone.run_query_call_count = 0
        return clone


class CounterSource(CounterSourceWithoutCount):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.run_count_call_count = 0

    def run_count(self):
        self.run_count_call_count += 1
        start, stop = self._get_real_limits()
        return stop - start

    def clone(self, **kwargs):
        clone = super().clone(**kwargs)
        clone.run_count_call_count = 0
        return clone


class TestQueryish(TestCase):
    def test_objects(self):
        self.assertEqual(CounterSource.objects.count(), 10)

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

    def test_count_uses_results_when_available(self):
        qs = CounterSource()
        list(qs)
        self.assertEqual(qs.count(), 10)
        self.assertEqual(qs.count(), 10)
        self.assertEqual(qs.run_count_call_count, 0)
        self.assertEqual(qs.run_query_call_count, 1)

    def test_len_does_not_use_count(self):
        qs = CounterSource()
        self.assertEqual(len(qs), 10)
        self.assertEqual(qs.run_count_call_count, 0)
        self.assertEqual(qs.run_query_call_count, 1)

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

    def test_slice_reuses_results(self):
        qs1 = CounterSource()
        list(qs1)
        qs2 = qs1[1:9]
        self.assertEqual(list(qs2), [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(qs1.run_query_call_count, 1)
        self.assertEqual(qs2.run_query_call_count, 0)

    def test_indexing(self):
        qs = CounterSource()
        self.assertEqual(qs[1], 1)
        self.assertEqual(qs.run_query_call_count, 1)
        self.assertEqual(qs[2], 2)
        self.assertEqual(qs.run_query_call_count, 1)

    def test_indexing_after_slice(self):
        qs = CounterSource()[1:5]
        self.assertEqual(qs[1], 2)
        self.assertEqual(qs.run_query_call_count, 1)
        self.assertEqual(qs[2], 3)
        self.assertEqual(qs.run_query_call_count, 1)

    def test_invalid_index_type(self):
        qs = CounterSource()
        with self.assertRaises(TypeError):
            qs['a']

    def test_repr(self):
        qs = CounterSource()
        self.assertEqual(repr(qs), "<CounterSource [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]>")
        qs = CounterSource(max_count=30)
        self.assertEqual(
            repr(qs),
            "<CounterSource [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, '...(remaining elements truncated)...']>"
        )

    def test_first(self):
        qs = CounterSource()
        self.assertEqual(qs.first(), 0)
        self.assertEqual(qs[20:30].first(), None)
