#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module: common.py
Author: zlamberty
Created: 2015-12-14

Description:
    common utility functions for logic solver routines

Usage:
    <usage>

"""

import datetime
import functools
import pandas as pd


# ----------------------------- #
#   Module Constants            #
# ----------------------------- #

STATUS = 'status'
CONFIRMED, REJECTED, UNSURE = 'confirmed', 'rejected', 'unsure'

NOW = datetime.datetime.now()
MONTHTYPE = pd._period.Period


# ----------------------------- #
#   common error                #
# ----------------------------- #

class CommonError(Exception):
    pass


# ----------------------------- #
#   date type munging           #
# ----------------------------- #

def get_datatype_interactive(indent):
    dt = raw_input('{}datatype (i, f, m, or leave blank for category): '.format(indent))
    if dt in ('i', 'int'):
        return int
    elif dt in ('f', 'float'):
        return float
    elif dt in ('m', 'month'):
        return MONTHTYPE
    else:
        return 'category'


# ----------------------------- #
#   months are special          #
# ----------------------------- #

JAN = (1, '1', 'ja', 'jan', 'january')
FEB = (2, '2', 'f', 'fe', 'feb', 'february')
MAR = (3, '3', 'mar', 'march')
APR = (4, '4', 'ap', 'apr', 'april')
MAY = (5, '5', 'may')
JUN = (6, '6', 'jun', 'june')
JUL = (7, '7', 'jul', 'july')
AUG = (8, '8', 'au', 'aug', 'august')
SEP = (9, '9', 'se', 'sep', 'sept', 'september')
OCT = (10, '10', 'o', 'oc', 'oct', 'october')
NOV = (11, '11', 'n', 'no', 'nov', 'november')
DEC = (12, '12', 'd', 'de', 'dec', 'december')


class MonthifyError(Exception):
    pass


def to_month(x):
    return pd.tseries.period.Period('{}-{:0>2}'.format(NOW.year, x))


MONTHS = {
    JAN: to_month(1),
    FEB: to_month(2),
    MAR: to_month(3),
    APR: to_month(4),
    MAY: to_month(5),
    JUN: to_month(6),
    JUL: to_month(7),
    AUG: to_month(8),
    SEP: to_month(9),
    OCT: to_month(10),
    NOV: to_month(11),
    DEC: to_month(12),
}


def monthify(x):
    try:
        try:
            x = x.lower()
        except:
            pass

        for (k, m) in MONTHS.items():
            if x in k:
                return m

        raise MonthifyError()
    except:
        raise MonthifyError('could not convert month value "{}" to int'.format(x))


# ----------------------------- #
#   common filters              #
# ----------------------------- #

def force_filter(f):
    return val_filter(f) if isinstance(f, (basestring, int, MONTHTYPE)) else f


def catval_filter(cat, val, onlyPoss=True):
    return lambda df: (is_possible(df) | (not onlyPoss)) & (df[cat] == val)


def val_filter(val, onlyPoss=True):
    """ just a lax version of above -- doesn't care about category """
    return lambda df: (is_possible(df) | (not onlyPoss)) & (df.isin([val]).any(axis=1))


def is_possible(df):
    return ~(df[STATUS] == REJECTED)


def category_columns(df):
    return [c for c in df.columns if c != STATUS]


def comparison_category(compCat, df):
    """ compCat *should* be a column name. If it is, great. If it is a
        singular version of a category name, we'll call that good enough

    """
    if compCat in df.columns:
        return compCat
    elif '{}s'.format(compCat) in df.columns:
        return '{}s'.format(compCat)
    else:
        msg = "Cannot find a column name that matches comparison category {}"
        msg = msg.format(compCat)
        raise CommonError(msg)

# ----------------------------- #
#   memoize decorator           #
# ----------------------------- #

class memoized(object):
    """ cache the return value of a method

        This class is meant to be used as a decorator of methods. The return
        value from a given method invocation will be cached on the instance
        whose method was invoked. All arguments passed to a method decorated
        with memoize must be hashable.

        If a memoized method is invoked directly on its class the result will
        not be cached. Instead the method will be invoked like a static method:
        class Obj(object):
            @memoize
            def add_to(self, arg):
                return self + arg
        Obj.add_to(1) # not enough arguments
        Obj.add_to(1, 2) # returns 3, result is not cached

        Ripped shamelessly from
        http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/

    """
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self.func
        return partial(self, obj)

    def __call__(self, *args, **kw):
        obj = args[0]

        try:
            cache = obj.__cache
        except AttributeError:
            cache = obj.__cache = {}

        key = (self.func, args[1:], frozenset(kw.items()))

        try:
            res = cache[key]
        except KeyError:
            res = cache[key] = self.func(*args, **kw)

        return res
