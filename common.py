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

import pandas as pd


# ----------------------------- #
#   Module Constants            #
# ----------------------------- #

STATUS = 'status'
CONFIRMED, REJECTED, UNSURE = 'confirmed', 'rejected', 'unsure'
MONTHTYPE = pd._period.Period


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


def monthify(x):
    return pd.tseries.period.Period('{}-{:0>2}'.format(NOW.year, int(x)))


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
