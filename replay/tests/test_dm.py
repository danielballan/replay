from __future__ import (absolute_import, division,
                        unicode_literals, print_function)
import six
import numpy as np
import time
from replay.pipeline.pipeline import DataMuggler, ColSpec, Unalignable
from datetime import datetime
from nose.tools import assert_true, assert_equal
from numpy.testing import assert_array_equal
from nose.tools import assert_raises, make_decorator


def use_fs_dec(func):
    """
    A decorator to run a test with and with out fs

    func : function
        The signature must be f(use_fs)
    """
    def wrapper():
        for use_fs in [True, False]:
            yield func, use_fs

    return make_decorator(func)(wrapper)


def test_empty_DM():
    dm = DataMuggler([])
    assert_equal(len(dm.keys()), 0)


def test_maxframes():
    col_list = [('a', 'ffill', 0),
                ('b', 'ffill', 1),
                ('c', 'ffill', 2)]

    dm = DataMuggler(col_list, max_frames=5, use_pims_fs=False)
    assert_equal(3, dm.ncols)

    for j in range(12):
        ts = datetime.now()
        data_dict = {'a': j, 'b': np.ones(2) * j,
                     'c': np.ones((2, 2)) * j}

        dm.append_data(ts, data_dict)

        a = dm.get_values('a', [])[1]['a']
        b = dm.get_values('b', [])[1]['b']
        c = dm.get_values('c', [])[1]['c']

        assert_equal(len(a), j+1)
        assert_equal(a[-1], j)
        print(len(b))
        assert_true(len(b) <= 5)
        assert_equal(int(np.mean(b[-1])), j)
        assert_true(len(c) <= 5)
        assert_equal(int(np.mean(c[-1])), j)


@use_fs_dec
def test_get_row(use_fs):
    col_list = [('a', 'ffill', 0),
                ('b', 'ffill', 1),
                ('c', 'ffill', 2)]

    dm = DataMuggler(col_list, use_pims_fs=use_fs)
    assert_equal(3, dm.ncols)
    ts_list = []
    for j in range(12):
        ts = datetime.now()
        ts_list.append(ts)
        data_dict = {'a': j, 'b': np.ones(2) * j,
                     'c': np.ones((2, 2)) * j}

        dm.append_data(ts, data_dict)

    print(dm._dataframe)

    for j, ts in enumerate(ts_list):
        res = dm.get_row(ts, ['a', 'b', 'c'])
        assert_equal(res['a'], j)
        assert_array_equal(res['b'], np.ones(2) * j)
        assert_array_equal(res['c'], np.ones((2, 2)) * j)


@use_fs_dec
def test_get_col(use_fs):
    col_list = [('a', 'ffill', 0),
                ('b', 'ffill', 1),
                ('c', 'ffill', 2)]

    dm = DataMuggler(col_list, use_pims_fs=use_fs)
    assert_equal(3, dm.ncols)

    for j in range(12):
        ts = datetime.now()
        data_dict = {'b': np.ones(2) * j,
                     'c': np.ones((2, 2)) * j}

        if j % 2:
            data_dict['a'] = j
        dm.append_data(ts, data_dict)

    ts_lst, col_vals = dm.get_column('a')
    target_vals = [j * 2 + 1 for j in range(6)]
    assert_array_equal(col_vals, target_vals)

    ts_lst, col_vals = dm.get_column('b')
    for j, cv in zip(range(12), col_vals):
        assert_array_equal(np.ones(2) * j, cv)

    assert_raises(ValueError, dm.get_column, 'aardvark')


@use_fs_dec
def test_last_val(use_fs):
    col_list = [('a', 'ffill', 0),
                ('b', 'ffill', 1),
                ('c', 'ffill', 2)]

    dm = DataMuggler(col_list, use_pims_fs=use_fs)
    ts_list = []
    for j in range(12):
        ts = datetime.now()
        ts_list.append(ts)
        data_dict = {'a': j, 'b': np.ones(2) * j,
                     'c': np.ones((2, 2)) * j}

        dm.append_data(ts, data_dict)

        t, res = dm.get_last_value('a', ['b', 'c'])
        assert_equal(ts, t)
        for k in data_dict:
            assert_array_equal(res[k], data_dict[k])


@use_fs_dec
def test_get_times(use_fs):
    col_list = [('a', 'ffill', 0),
                ('b', 'ffill', 1),
                ('c', 'ffill', 2)]

    dm = DataMuggler(col_list, use_pims_fs=use_fs)
    ts_list = []
    for j in range(12):
        ts = datetime.now()
        ts_list.append(ts)
        data_dict = {'a': j, 'b': np.ones(2) * j,
                     'c': np.ones((2, 2)) * j}

        dm.append_data(ts, data_dict)
    res_ts = dm.get_times('a')
    assert_equal(ts_list, list(res_ts))


def test_bad_col_append():
    col_list = [('a', 'ffill', 0),
                ('b', 'ffill', 1),
                ('c', 'ffill', 2)]

    dm = DataMuggler(col_list)

    bad_dict = {'aardvark': 42}
    assert_raises(ValueError, dm.append_data, datetime.now(), bad_dict)


def test_colspec():
    assert_raises(ValueError, ColSpec, 'a', 'ffill', -1)
    assert_raises(ValueError, ColSpec, 'a', 'aardvark', 1)


def test_props():
    col_list = [(chr(j), vf, j - 97) for
                j, vf in enumerate(ColSpec.valid_fill_methods, start=97)]

    dm = DataMuggler(col_list)

    fill_dict = {chr(j): vf for
                j, vf in enumerate(ColSpec.valid_fill_methods, start=97)}

    assert_equal(fill_dict, dm.col_fill_rules)

    dim_dict = {chr(j): j-97 for j, vf
                in enumerate(ColSpec.valid_fill_methods, start=97)}

    assert_equal(dim_dict, dm.col_dims)


def test_align_against():
    col_list = [('a', 'ffill', 0),
                ('b', 'ffill', 0),
                ('c', 'ffill', 0),
                ('d', None, 0)]

    dm = DataMuggler(col_list)
    dm.append_data(datetime.now(), {'a': -1, 'd': -1})
    for j in range(12):
        ts = datetime.now()
        data_dict = {'c': j}
        if j % 2:
            data_dict['a'] = j
        if j % 3:
            data_dict['b'] = j

        dm.append_data(ts, data_dict)

    ab_dict = dm.align_against('a', ['b', 'd'])
    assert_equal({'a': True, 'b': False, 'd': False},
                 ab_dict)

    ba_dict = dm.align_against('b', ['a'])
    assert_equal({'a': True, 'b': True}, ba_dict)

    d_dict = dm.align_against('d')
    assert_equal(d_dict,
                 {'a': True, 'b': False, 'c': False, 'd': True})

    assert_raises(ValueError, dm.align_against, 'aardvark')


def test_unique_keys():
    col_list = [('a', 'ffill', 0),
                ('a', 'ffill', 0),
                ('c', 'ffill', 0),
                ('d', None, 0)]

    assert_raises(ValueError, DataMuggler, col_list)


def test__non_scalar_lookup_fail():
    col_list = [('a', 'ffill', 0),
                ('b', 'ffill', 0)]

    dm = DataMuggler(col_list)

    ts = datetime.now()
    data_dict = {'a': 1, 'b': 1}
    dm.append_data(ts, data_dict)

    ts = datetime.now()
    data_dict = {'b': 2}
    dm.append_data(ts, data_dict)

    assert_raises(Unalignable, dm._listify_output, dm._dataframe)


def test_add_column():
    col_list = [('a', 'ffill', 0),
                ('b', 'ffill', 0)]

    new_col = ('c', None, 0)
    dm = DataMuggler(col_list)
    assert_equal(2, dm.ncols)
    dm.add_column(new_col)
    assert_equal(3, dm.ncols)

    assert_equal(set(['a', 'b', 'c']), set(dm.keys()))

    assert_raises(ValueError, dm.add_column, new_col)


def test_add_column_data():
    col_list = [('a', 'ffill', 0),
                ('b', 'ffill', 1)]

    dm = DataMuggler(col_list)
    assert_equal(2, dm.ncols)

    for j in range(5):
        ts = datetime.now()
        data_dict = {'a': j, 'b': np.ones(2) * j}

        dm.append_data(ts, data_dict)

    new_col = ('c', None, 2)
    dm.add_column(new_col)
    assert_equal(3, dm.ncols)
    for j in range(5, 10):
        ts = datetime.now()
        data_dict = {'a': j, 'b': np.ones(2) * j,
                     'c': np.ones((2, 2)) * j}

        dm.append_data(ts, data_dict)

        a = dm.get_values('a', [])[1]['a']
        b = dm.get_values('b', [])[1]['b']
        c = dm.get_values('c', [])[1]['c']

        assert_equal(len(a), j+1)
        assert_equal(len(b), j+1)
        assert_equal(len(c), j+1 - 5)
        assert_equal(a[-1], j)
        assert_equal(int(np.mean(b[-1])), j)
        assert_equal(int(np.mean(c[-1])), j)


@use_fs_dec
def test_bulk_add(use_pims_fs):
    N = 5
    a_data = list(np.rollaxis((np.ones((2, 2)).reshape(2, 2, 1) *
                               np.arange(N).reshape(1, 1, -1)), 2, 0))

    b_data = list(np.rollaxis((np.ones((2, 2)).reshape(2, 2, 1) *
                               np.arange(N)[::-1].reshape(1, 1, -1)), 2, 0))

    data_dict = {'a': a_data, 'b': b_data}
    ts = []
    for j in range(N):
        ts.append(datetime.now())
        time.sleep(.1)

    col_list = [('a', 'ffill', 2),
                ('b', 'ffill', 2)]
    dm = DataMuggler(col_list, use_pims_fs=use_pims_fs)
    cached_dd = dict(data_dict)
    dm.append_data(ts, data_dict)
    assert_equal(cached_dd, data_dict)

    ts, a_res = dm.get_column('a')
    for l, r in zip(a_data, a_res):
        assert_array_equal(l, r)

    ts, b_res = dm.get_column('b')
    for l, r in zip(b_data, b_res):
        assert_array_equal(l, r)
