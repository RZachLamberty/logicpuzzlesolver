#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module: rule.py
Author: zlamberty
Created: 2015-12-14

Description:
    logic puzzle rule class

Usage:
    <usage>

"""

import pandas as pd
import re
import sys
import yaml

import common

from collections import defaultdict


# ----------------------------- #
#   rule functions              #
# ----------------------------- #

# bulk rules
def clean_up(df):
    df2 = df.copy()
    df2 = is_only_remaining_pair(df2)
    df2 = mark_confirmed(df2)
    return df2


def is_only_remaining_pair(df):
    """ Here we check for any pair of cat:val-s that are the only non rejected
        combination. If we find any such pair, we update our df

    """
    df2 = df.copy()
    for col in common.category_columns(df2):
        othercols = [c for c in common.category_columns(df2) if c != col]
        for (colval, g) in df2[common.is_possible(df2)].groupby(col):
            for othercol in othercols:
                oval0 = g[othercol].iloc[0]
                if (g[othercol] == oval0).all():
                    # there is only one value of othercal for col
                    df2 = is_same(
                        common.catval_filter(col, colval),
                        common.catval_filter(othercol, oval0),
                        df2
                    )

    return df2


def mark_confirmed(df):
    df2 = df.copy()

    for col in common.category_columns(df2):
        for (colval, g) in df2[df2[common.STATUS] == common.UNSURE].groupby(col):
            if g.shape[0] == 1:
                # there is only 1 remaining row for this value
                df2.loc[g.index[0], common.STATUS] = common.CONFIRMED

    return df2


# simple yes / no
def is_diff(filt1, filt2, df):
    filt1 = common.force_filter(filt1)
    filt2 = common.force_filter(filt2)
    df2 = df.copy()
    df2.loc[filt1(df2) & filt2(df2), common.STATUS] = common.REJECTED
    return df2


def is_same(filt1, filt2, df):
    """ Reject all rows where
        cat1:elem1 != cat2:elem2

    """
    filt1 = common.force_filter(filt1)
    filt2 = common.force_filter(filt2)
    df2 = df.copy()
    df2.loc[filt1(df2) & (~filt2(df2)), common.STATUS] = common.REJECTED
    df2.loc[(~filt1(df2)) & filt2(df2), common.STATUS] = common.REJECTED
    return df2


# (n)either / (n)or
def is_either_or(isfilt, eitherfilt, orfilt, df):
    isfilt = common.force_filter(isfilt)
    eitherfilt = common.force_filter(eitherfilt)
    orfilt = common.force_filter(orfilt)

    df2 = df.copy()

    # we have one exclusion relation here
    df2 = is_diff(eitherfilt, orfilt, df)

    # reject all values which are is but not either or
    df2.loc[(isfilt(df2) & ~((eitherfilt(df2)) | (orfilt(df2)))), common.STATUS] = common.REJECTED

    return df2


def is_neither_nor(isfilt, neitherfilt, norfilt, df):
    isfilt = common.force_filter(isfilt)
    neitherfilt = common.force_filter(neitherfilt)
    norfilt = common.force_filter(norfilt)

    df2 = df.copy()

    # we have one exclusion relation here
    df2 = is_diff(neitherfilt, norfilt, df)

    # reject all values which are is but not either or
    df2.loc[(isfilt(df2) & ((neitherfilt(df2)) | (norfilt(df2)))), common.STATUS] = common.REJECTED

    return df2


def pair_is_pair(filt11, filt12, filt21, filt22, df):
    """ this is really just four either-or statements """
    df2 = df.copy()
    df2 = is_either_or(filt11, filt21, filt22, df2)
    df2 = is_either_or(filt12, filt21, filt22, df2)
    df2 = is_either_or(filt21, filt11, filt12, df2)
    df2 = is_either_or(filt22, filt11, filt12, df2)
    return df2


# ordering
def is_ordered(compCat, bigfilt, smallfilt, df, offset=0):
    """ general equation is
        compCat(bigCat:bigElem) > compCat(smallCat:smallElem) + offset

        we also know, from this, that bigCat:bigElem != smallCat:smallElem

    """
    compCat = common.comparison_category(compCat, df)
    bigfilt = common.force_filter(bigfilt)
    smallfilt = common.force_filter(smallfilt)

    df2 = df.copy()

    # take care of the != clause first
    df2 = is_diff(bigfilt, smallfilt, df2)

    # all vals of bigCat must be > the minium val of smallCat
    minSmall = df2[smallfilt(df2)][compCat].min()
    df2.loc[
        bigfilt(df2) & (df2[compCat] <= (minSmall + offset)),
        common.STATUS
    ] = common.REJECTED

    # all vals of smallCat must be < the largest val of bigCat
    maxBig = df2[bigfilt(df2)][compCat].max()
    df2.loc[
        smallfilt(df2) & (df2[compCat] >= (maxBig - offset)),
        common.STATUS
    ] = common.REJECTED

    return df2


def is_incremented(compCat, bigfilt, smallfilt, df, offset=0):
    """ general equation is
        compCat(bigCat:bigElem) = compCat(smallCat:smallElem) + offset

        Same as is_ordered, but eq instead of gt

        if bigfilt or smallfilt are strings instead of lambdas, turn them
        into lambdas with the val_filter function

        we also know, from this, that bigCat:bigElem != smallCat:smallElem
    """
    compCat = common.comparison_category(compCat, df)
    bigfilt = common.force_filter(bigfilt)
    smallfilt = common.force_filter(smallfilt)

    df2 = df.copy()

    # take care of the != clause first
    df2 = is_diff(bigfilt, smallfilt, df2)

    # possible values
    small = df2[smallfilt(df2)][compCat].unique()
    big = df2[bigfilt(df2)][compCat].unique()

    # find impossible values (small values with no corresponding big; vice versa)
    badsmall = set(small).difference(big - offset)
    badbig = set(big).difference(small + offset)

    # drop impossible values
    df2.loc[smallfilt(df2) & (df2[compCat].isin(badsmall)), common.STATUS] = common.REJECTED
    df2.loc[bigfilt(df2) & (df2[compCat].isin(badbig)), common.STATUS] = common.REJECTED

    return df2


# similarity group requirements
def similarity_group_updates(filtlist, df):
    """ we are given a list of filters. Each filter specifies a distinct
        similarity group, so any rows which exist in more than one filter
        group can be rejected. An example:

        [A:a, B:b]

            A    B   common.STATUS
            a    a   unknown
            a    b   unknown --> rejected
            b    a   unknown
            b    b   unknown

    """
    filtlist = map(common.force_filter, filtlist)
    df2 = df.copy()

    for (filt1, filt2) in itertools.combinations(filtlist, 2):
        df2.loc[filt1(df2) & filt2(df2), common.STATUS] = common.REJECTED

    return df2


# ----------------------------- #
#   rule objects                #
# ----------------------------- #

class Rule(object):
    def __init__(self, f, **params):
        self.f = f
        self.params = params

    def __call__(self, df):
        return self.f(df=df, **self.params)


class YamlRule(Rule, yaml.YAMLObject):
    yaml_tag = u'!Rule'


def rule_func_constructor(loader, node):
    value = loader.construct_scalar(node)
    return getattr(sys.modules[__name__], value)


yaml.add_constructor(u'!foo', rule_func_constructor)
