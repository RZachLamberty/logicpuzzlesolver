#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module: puzzle.py
Author: zlamberty
Created: 2015-12-12

Description:
    Puzzle class

Usage:
    <usage>

"""

import pandas as pd

import common
import rule


# ----------------------------- #
#   Module Constants            #
# ----------------------------- #

# ----------------------------- #
#   Main class                  #
# ----------------------------- #

class LogicPuzzleError(Exception):
    pass


class LogicPuzzle(object):
    def __init__(self, categories, rules, maxsolveattempts=10):
        self.categories = categories
        self.rules = rules
        self.history = []
        self._df = pd.DataFrame()
        self._solve_attempts = 0
        self.maxsolveattempts = maxsolveattempts
        self.df = self.categories.possibilities()

    @property
    def df(self):
        """ the dataframe of possibilities; property'd so we can keep history """
        return self._df

    @df.setter
    def df(self, df):
        self.history.append(self._df.copy())
        self._df = df

    @property
    def poss(self):
        return self.df[common.is_possible(self.df)]

    def undo(self):
        self._df = self.history.pop()

    def solve(self):
        while not self.solved():
            self._solve_attempts += 1
            self.apply_rules()
            self.df = rule.clean_up(self.df)
            if self.maxsolveattempts and (self._solve_attempts >= self.maxsolveattempts):
                raise LogicPuzzleError("reached maximum number of solution iterations")

    def apply_rules(self):
        for rule in self.rules:
            self.df = rule(self.df)

    def solved(self):
        return self.df[self.df[common.STATUS] == common.UNSURE].empty

    def results(self):
        return self.df[self.df[common.STATUS] == common.CONFIRMED]
