from unittest import TestCase

from queryish import Queryish


run_query_calls = []
run_count_calls = []


class CounterQuerySetWithoutCount(Queryish):
    def __init__(self, max_count=10):
        super().__init__()
        self.max_count = max_count

    def _get_real_limits(self):
        start = min(self.start, self.max_count)
        if self.stop is not None:
            stop = min(self.stop, self.max_count)
        else:
            stop = self.max_count

        return (start, stop)

    def run_query(self):
        run_query_calls.append((self.start, self.stop))
        start, stop = self._get_real_limits()
        for i in range(start, stop):
            yield i

    def clone(self, **kwargs):
        clone = super().clone(**kwargs)
        return clone


class CounterQuerySet(CounterQuerySetWithoutCount):
    def run_count(self):
        run_count_calls.append((self.start, self.stop))
        start, stop = self._get_real_limits()
        return stop - start

    def clone(self, **kwargs):
        clone = super().clone(**kwargs)
        return clone


class TestQueryish(TestCase):
    def setUp(self):
        run_query_calls.clear()
        run_count_calls.clear()

    def test_get_results_as_list(self):
        qs = CounterQuerySet()
        self.assertEqual(list(qs), list(range(0, 10)))
        self.assertEqual(run_query_calls, [(0, None)])

    def test_all(self):
        qs = CounterQuerySet()
        self.assertEqual(list(qs.all()), list(range(0, 10)))
        self.assertEqual(run_query_calls, [(0, None)])

    def test_query_is_only_run_once(self):
        qs = CounterQuerySet()
        list(qs)
        list(qs)
        self.assertEqual(run_query_calls, [(0, None)])

    def test_count_uses_results_by_default(self):
        qs = CounterQuerySetWithoutCount()
        self.assertEqual(qs.count(), 10)
        self.assertEqual(qs.count(), 10)
        self.assertEqual(run_query_calls, [(0, None)])

    def test_count_does_not_use_results_when_run_count_provided(self):
        qs = CounterQuerySet()
        self.assertEqual(qs.count(), 10)
        self.assertEqual(qs.count(), 10)
        self.assertEqual(run_count_calls, [(0, None)])
        self.assertEqual(run_query_calls, [])

    def test_count_uses_results_when_available(self):
        qs = CounterQuerySet()
        list(qs)
        self.assertEqual(qs.count(), 10)
        self.assertEqual(qs.count(), 10)
        self.assertEqual(run_count_calls, [])
        self.assertEqual(run_query_calls, [(0, None)])

    def test_count_on_empty_slice(self):
        qs = CounterQuerySet()[3:3]
        self.assertEqual(qs.count(), 0)
        self.assertEqual(run_count_calls, [])
        self.assertEqual(run_query_calls, [])

    def test_len_does_not_use_count(self):
        qs = CounterQuerySet()
        self.assertEqual(len(qs), 10)
        self.assertEqual(run_count_calls, [])
        self.assertEqual(run_query_calls, [(0, None)])

    def test_len_on_empty_slice(self):
        qs = CounterQuerySet()[3:3]
        self.assertEqual(len(qs), 0)
        self.assertEqual(run_count_calls, [])
        self.assertEqual(run_query_calls, [])

    def test_slicing(self):
        qs = CounterQuerySet()[1:3]
        self.assertEqual(qs.offset, 1)
        self.assertEqual(qs.limit, 2)
        self.assertEqual(list(qs), [1, 2])
        self.assertEqual(run_query_calls, [(1, 3)])

    def test_slicing_without_start(self):
        qs = CounterQuerySet()[:3]
        self.assertEqual(qs.offset, 0)
        self.assertEqual(qs.limit, 3)
        self.assertEqual(list(qs), [0, 1, 2])
        self.assertEqual(run_query_calls, [(0, 3)])

    def test_slicing_without_stop(self):
        qs = CounterQuerySet()[3:]
        self.assertEqual(qs.offset, 3)
        self.assertEqual(qs.limit, None)
        self.assertEqual(list(qs), [3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(run_query_calls, [(3, None)])

    def test_empty_slice(self):
        qs = CounterQuerySet()[3:3]
        self.assertEqual(qs.offset, 3)
        self.assertEqual(qs.limit, 0)
        self.assertEqual(list(qs), [])
        self.assertEqual(run_query_calls, [])

    def test_iter_on_empty_slice(self):
        qs = CounterQuerySet()[3:3]
        results = []
        for item in qs:
            results.append(item)
        self.assertEqual(results, [])
        self.assertEqual(run_query_calls, [])

    def test_multiple_slicing(self):
        qs1 = CounterQuerySet()
        qs2 = qs1[1:9]
        self.assertEqual(qs2.offset, 1)
        self.assertEqual(qs2.limit, 8)
        qs3 = qs2[2:4]
        self.assertEqual(qs3.offset, 3)
        self.assertEqual(qs3.limit, 2)

        self.assertEqual(list(qs3), [3, 4])
        self.assertEqual(run_query_calls, [(3, 5)])

    def test_multiple_slicing_without_start(self):
        qs1 = CounterQuerySet()
        qs2 = qs1[1:9]
        self.assertEqual(qs2.offset, 1)
        self.assertEqual(qs2.limit, 8)
        qs3 = qs2[:4]
        self.assertEqual(qs3.offset, 1)
        self.assertEqual(qs3.limit, 4)

        self.assertEqual(list(qs3), [1, 2, 3, 4])
        self.assertEqual(run_query_calls, [(1, 5)])

    def test_multiple_slicing_without_stop(self):
        qs1 = CounterQuerySet()
        qs2 = qs1[1:9]
        self.assertEqual(qs2.offset, 1)
        self.assertEqual(qs2.limit, 8)
        qs3 = qs2[2:]
        self.assertEqual(qs3.offset, 3)
        self.assertEqual(qs3.limit, 6)

        self.assertEqual(list(qs3), [3, 4, 5, 6, 7, 8])
        self.assertEqual(run_query_calls, [(3, 9)])

    def test_multiple_slicing_is_limited_by_first_slice(self):
        qs1 = CounterQuerySet()
        qs2 = qs1[1:3]
        self.assertEqual(qs2.offset, 1)
        self.assertEqual(qs2.limit, 2)
        qs3 = qs2[1:10]
        self.assertEqual(qs3.offset, 2)
        self.assertEqual(qs3.limit, 1)

        self.assertEqual(list(qs3), [2])
        self.assertEqual(run_query_calls, [(2, 3)])

    def test_slice_reuses_results(self):
        qs1 = CounterQuerySet()
        list(qs1)
        qs2 = qs1[1:9]
        self.assertEqual(list(qs2), [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(run_query_calls, [(0, None)])

    def test_disjoint_slices(self):
        qs1 = CounterQuerySet()
        qs2 = qs1[2:4]
        qs3 = qs2[3:5]
        self.assertEqual(qs3.start, 4)
        self.assertEqual(qs3.stop, 4)
        self.assertEqual(list(qs3), [])
        self.assertEqual(run_query_calls, [])

    def test_indexing(self):
        qs = CounterQuerySet()
        self.assertEqual(qs[1], 1)
        self.assertEqual(run_query_calls, [(1, 2)])
        self.assertEqual(qs[2], 2)
        self.assertEqual(run_query_calls, [(1, 2), (2, 3)])

    def test_indexing_after_fetch(self):
        qs = CounterQuerySet()
        list(qs)
        self.assertEqual(qs[1], 1)
        self.assertEqual(run_query_calls, [(0, None)])
        self.assertEqual(qs[2], 2)
        self.assertEqual(run_query_calls, [(0, None)])

    def test_indexing_after_slice(self):
        qs = CounterQuerySet()[1:5]
        self.assertEqual(qs[1], 2)
        self.assertEqual(run_query_calls, [(2, 3)])
        self.assertEqual(qs[2], 3)
        self.assertEqual(run_query_calls, [(2, 3), (3, 4)])

    def test_indexing_after_slice_and_fetch(self):
        qs = CounterQuerySet()[1:5]
        list(qs)
        self.assertEqual(qs[1], 2)
        self.assertEqual(run_query_calls, [(1, 5)])
        self.assertEqual(qs[2], 3)
        self.assertEqual(run_query_calls, [(1, 5)])

    def test_indexing_out_of_range(self):
        qs = CounterQuerySet()
        with self.assertRaises(IndexError):
            qs[20]
        self.assertEqual(run_query_calls, [(20, 21)])

    def test_indexing_out_of_range_after_slice(self):
        qs = CounterQuerySet()[3:8]
        with self.assertRaises(IndexError):
            qs[6]
        self.assertEqual(run_query_calls, [])

    def test_invalid_index_type(self):
        qs = CounterQuerySet()
        with self.assertRaises(TypeError):
            qs['a']

    def test_repr(self):
        qs = CounterQuerySet()
        self.assertEqual(repr(qs), "<CounterQuerySet [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]>")
        qs = CounterQuerySet(max_count=30)
        self.assertEqual(
            repr(qs),
            "<CounterQuerySet [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, '...(remaining elements truncated)...']>"
        )

    def test_first(self):
        qs = CounterQuerySet()
        self.assertEqual(qs.first(), 0)
        self.assertEqual(qs[20:30].first(), None)
