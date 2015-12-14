#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module: categories.py
Author: zlamberty
Created: 2015-12-14

Description:
    Class for list of categories objects

Usage:
    <usage>

"""

import itertools
import pandas as pd
import yaml

import common


# ----------------------------- #
#   category class              #
# ----------------------------- #

class Categories(list):
    def __init__(self, numcats, numvals):
        raise NotImplementedError()

    def get_categories(self):
        raise NotImplementedError()

    @property
    def names(self):
        return [_.name for _ in self]

    @property
    def dts(self):
        return [_.dtype for _ in self]

    def possibilities(self):
        df = pd.DataFrame(
            data=list(itertools.product(*self)),
            columns=self.names
        )

        # set dtypes
        for (col, dt) in zip(self.names, self.dts):
            df.loc[:, col] = df[col].astype(dt)

        df.loc[:, common.STATUS] = common.UNSURE

        return df


class CategoriesInteractive(Categories):
    def __init__(self, numcats, numvals):
        self.categories = []
        self.numcats = numcats
        self.numvals = numvals
        self.get_categories()

    def get_categories(self):
        for i in range(self.numcats):
            name = raw_input("\ncategory name: ")
            vals = [raw_input("\t> ") for i in range(self.numvals)]
            dt = common.get_datatype_interactive(indent="\t")

            if dt == common.MONTHTYPE:
                vals = map(common.monthify, vals)

            self.append(pd.Series(data=vals, name=name, dtype=dt))


class CategoriesFromYaml(Categories):
    def __init__(self, f):
        self.get_categories(f)

    def get_categories(self, f):
        with open(f, 'r') as fcat:
            cats = yaml.load(fcat)
        for (name, d) in cats.items():
            vals = d['values']
            dt = d.get('type', 'category')

            if dt == common.MONTHTYPE:
                vals = map(common.monthify, vals)

            self.append(pd.Series(data=vals, name=name, dtype=dt))
