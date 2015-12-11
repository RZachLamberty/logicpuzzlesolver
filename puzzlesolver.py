#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module: puzzlesolver.py
Author: zlamberty
Created: 2015-12-09

Description:
    solver of logic puzzles

Usage:
    <usage>

"""

import datetime
import itertools
import pandas as pd


# ----------------------------- #
#   Module Constants            #
# ----------------------------- #

STATUS = 'status'
CONFIRMED, REJECTED, UNSURE = 'confirmed', 'rejected', 'unsure'
NOW = datetime.datetime.now()
MONTHTYPE = pd._period.Period


# ----------------------------- #
#   rules                       #
# ----------------------------- #

# bulk updates
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
    for col in category_columns(df2):
        othercols = [c for c in category_columns(df2) if c != col]
        for (colval, g) in df2[is_possible(df2)].groupby(col):
            for othercol in othercols:
                vc = g[othercol].value_counts()
                if vc.shape[0] == 1:
                    # there is only one value of othercal for col
                    df2 = is_same(
                        catval_filter(col, colval),
                        catval_filter(othercol, g.iloc[0][othercol]),
                        df2
                    )

    return df2


def mark_confirmed(df):
    df2 = df.copy()

    for col in category_columns(df2):
        for (colval, g) in df2[df2[STATUS] == UNSURE].groupby(col):
            if g.shape[0] == 1:
                # there is only 1 remaining row for this value
                df2.loc[g.index[0], STATUS] = CONFIRMED

    return df2


# simple yes / no
def is_diff(filt1, filt2, df):
    filt1 = force_filter(filt1)
    filt2 = force_filter(filt2)
    df2 = df.copy()
    df2.loc[filt1(df2) & filt2(df2), STATUS] = REJECTED
    return df2


def is_same(filt1, filt2, df):
    """ Reject all rows where
        cat1:elem1 != cat2:elem2

    """
    filt1 = force_filter(filt1)
    filt2 = force_filter(filt2)
    df2 = df.copy()
    df2.loc[filt1(df2) & (~filt2(df2)), STATUS] = REJECTED
    df2.loc[(~filt1(df2)) & filt2(df2), STATUS] = REJECTED
    return df2


# (n)either / (n)or
def is_either_or(isfilt, eitherfilt, orfilt, df):
    isfilt = force_filter(isfilt)
    eitherfilt = force_filter(eitherfilt)
    orfilt = force_filter(orfilt)

    df2 = df.copy()

    # we have one exclusion relation here
    df2 = is_diff(eitherfilt, orfilt, df)

    # reject all values which are is but not either or
    df2.loc[(isfilt(df2) & ~((eitherfilt(df2)) | (orfilt(df2)))), STATUS] = REJECTED

    return df2


def is_neither_nor(isfilt, neitherfilt, norfilt, df):
    isfilt = force_filter(isfilt)
    neitherfilt = force_filter(neitherfilt)
    norfilt = force_filter(norfilt)

    df2 = df.copy()

    # we have one exclusion relation here
    df2 = is_diff(neitherfilt, norfilt, df)

    # reject all values which are is but not either or
    df2.loc[(isfilt(df2) & ((neitherfilt(df2)) | (norfilt(df2)))), STATUS] = REJECTED

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
    bigfilt = force_filter(bigfilt)
    smallfilt = force_filter(smallfilt)

    df2 = df.copy()

    # take care of the != clause first
    df2 = is_diff(bigfilt, smallfilt, df2)

    # all vals of bigCat must be > the minium val of smallCat
    minSmall = df2[smallfilt(df2)][compCat].min()
    df2.loc[
        bigfilt(df2) & (df2[compCat] <= (minSmall + offset)),
        STATUS
    ] = REJECTED

    # all vals of smallCat must be < the largest val of bigCat
    maxBig = df2[bigfilt(df2)][compCat].max()
    df2.loc[
        smallfilt(df2) & (df2[compCat] >= (maxBig - offset)),
        STATUS
    ] = REJECTED

    return df2


def is_incremented(compCat, bigfilt, smallfilt, df, offset=0):
    """ general equation is
        compCat(bigCat:bigElem) = compCat(smallCat:smallElem) + offset

        Same as is_ordered, but eq instead of gt

        if bigfilt or smallfilt are strings instead of lambdas, turn them
        into lambdas with the val_filter function

        we also know, from this, that bigCat:bigElem != smallCat:smallElem
    """
    bigfilt = force_filter(bigfilt)
    smallfilt = force_filter(smallfilt)

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
    df2.loc[smallfilt(df2) & (df2[compCat].isin(badsmall)), STATUS] = REJECTED
    df2.loc[bigfilt(df2) & (df2[compCat].isin(badbig)), STATUS] = REJECTED

    return df2


# similarity group requirements
def similarity_group_updates(filtlist, df):
    """ we are given a list of filters. Each filter specifies a distinct
        similarity group, so any rows which exist in more than one filter
        group can be rejected. An example:

        [A:a, B:b]

            A    B   STATUS
            a    a   unknown
            a    b   unknown --> rejected
            b    a   unknown
            b    b   unknown

    """
    filtlist = map(force_filter, filtlist)
    df2 = df.copy()

    for (filt1, filt2) in itertools.combinations(filtlist, 2):
        df2.loc[filt1(df2) & filt2(df2), STATUS] = REJECTED

    return df2


# ----------------------------- #
#   solutions                   #
# ----------------------------- #

def puzzle_is_solved(df):
    return df[df[STATUS] == UNSURE].empty


def puzzle_results(df):
    return df[df[STATUS] == CONFIRMED]


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


# ----------------------------- #
#   Main routine                #
# ----------------------------- #

def test_df():
    """ docstring """
    years = pd.Series(data=[1964, 1968, 1972, 1976], name='years')
    names = pd.Series(data=['Deb Daniels', 'Edna Evitz', 'Fay Ferguson', 'Norma Nolan'], name='names')
    topics = pd.Series(data=['astronomy', 'bioengineering', 'economics', 'physics'], name='category')

    categories = [years, names, topics]

    return pd.DataFrame(
        data=[
            {'year': y, 'name': n, 'category': c, STATUS: UNSURE}
            for (y, n, c) in itertools.product(*categories)
        ],
        columns=['year', 'name', 'category', 'status']
    )


def test_rules():
    return [
        [
            is_ordered,
            {
                'compCat': 'year',
                'bigfilt': 'Norma Nolan',
                'smallfilt': 'bioengineering',
            }
        ],
        [
            is_incremented,
            {
                'compCat': 'year',
                'bigfilt': 'physics',
                'smallfilt': 'bioengineering',
                'offset': 8,
            }
        ],
        [
            is_same,
            {
                'filt1': 'Edna Evitz',
                'filt2': 'physics',
            }
        ],
        [
            similarity_group_updates,
            {
                'filtlist': [
                    'Fay Ferguson',
                    1964,
                    1976,
                    'astronomy'
                ],
            }
        ]
    ]


def make_puzzle(numcats, numvals):
    """ interactive function for making the puzzle """
    categories = []
    for i in range(numcats):
        name = raw_input("\ncategory name: ")
        vals = [raw_input("\t> ") for i in range(numvals)]
        dt = get_datatype_interactive(indent="\t")

        if dt == MONTHTYPE:
            vals = map(monthify, vals)

        categories.append(pd.Series(data=vals, name=name, dtype=dt))

    catnames = [_.name for _ in categories]
    dts = [_.dtype for _ in categories]

    df = pd.DataFrame(
        data=list(itertools.product(*categories)),
        columns=catnames
    )

    # set dtypes
    for (col, dt) in zip(df, dts):
        df.loc[:, col] = df[col].astype(dt)

    df.loc[:, STATUS] = UNSURE

    return df


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


def type_update_interactive(vals, indent):
    valtype = raw_input("{}special type (int, float, month, monthdelta, or blank): ".format(indent))
    if valtype == 'int':
        vals = map(int, vals)
    elif valtype == 'float':
        vals = map(float, vals)
    elif valtype == 'month':
        vals = map(monthify, vals)
    elif valtype == 'monthdelta':
        vals = [monthify(v, delta=True) for v in vals]

    return vals


def make_rules(df):
    """ interactive function for building the rules """
    # make the up-casting smart by letting it know what values are possible
    # ahead of time
    rev = {}
    for col in df.columns:
        rev[str(col)] = col
        for val in df[col].unique():
            rev[str(val)] = val

    # now actually make the rules
    rules = []
    while True:
        paramnames = []
        listparamnames = []
        ruletype = raw_input(
            "\nWhat type of rule is this?"
            "\n\t1 - A is B"
            "\n\t2 - A is not B"
            "\n\t3 - A is either B or C"
            "\n\t4 - A is neither B nor C"
            "\n\t5 - (A, B) is (C, D)"
            "\n\t6 - A > B (+ delta)"
            "\n\t7 - A = B (+ delta)"
            "\n\t8 - [A, B, C, D, and E] are all different"
            "\n\t  - (leave blank to exit)"
            "\n\n\t> "
        )
        if not ruletype:
            break
        elif ruletype == '1':
            f = is_same
            paramnames = ['filt1', 'filt2']
        elif ruletype == '2':
            f = is_diff
            paramnames = ['filt1', 'filt2']
        elif ruletype == '3':
            f = is_either_or
            paramnames = ['isfilt', 'eitherfilt', 'orfilt']
        elif ruletype == '4':
            f = is_neither_nor
            paramnames = ['isfilt', 'neitherfilt', 'norfilt']
        elif ruletype == '5':
            f = pair_is_pair
            paramnames = ['filt11', 'filt12', 'filt21', 'filt22']
        elif ruletype == '6':
            f = is_ordered
            paramnames = ['compCat', 'bigfilt', 'smallfilt', 'offset']
        elif ruletype == '7':
            f = is_incremented
            paramnames = ['compCat', 'bigfilt', 'smallfilt', 'offset']
        elif ruletype == '8':
            f = similarity_group_updates
            listparamnames = ['filtlist']
        else:
            print "\ninvalid value, try again\n"
            continue

        rules.append([f, get_params_interactive(paramnames, listparamnames, rev)])

    return rules


def get_params_interactive(paramnames=[], listparamnames=[], rev={}):
    """ paramnames is a list of parameters that expect only one value;
        listparamnames expects a list. Rev is a reverse lookup dictionary
        of str repr values --> df values

    """
    print "\n\tgetting parameters (leave any blank for defaults)"
    params = {}
    for paramname in paramnames:
        val = raw_input("\t\t{}: ".format(paramname))
        if val:
            try:
                val = rev[val]
            except KeyError:
                val = type_update_interactive([val], indent="\t\t\t")[0]
            params[paramname] = val

    for paramname in listparamnames:
        print "\t\t{}: ".format(paramname)
        params[paramname] = []
        while True:
            val = raw_input("\t\t\t> ")
            if val:
                try:
                    val = rev[val]
                except KeyError:
                    val = type_update_interactive([val], indent="\t\t\t\t")[0]
                params[paramname].append(val)
            else:
                break

    return params


def apply_rules(df, rules):
    df2 = df.copy()

    for (f, kwargs) in rules:
        df2 = f(df=df2, **kwargs)

    return df2


def solve(df, rules):
    while not puzzle_is_solved(df):
        df = apply_rules(df, rules)
        df = clean_up(df)

    return df


def main():
    #df = test_df()
    #rules = test_rules()

    df = make_puzzle()
    rules = make_rules()

    df = solve(df, rules)

    print puzzle_results(df)

    return df


# ----------------------------- #
#   Command line                #
# ----------------------------- #

if __name__ == '__main__':
    main()
