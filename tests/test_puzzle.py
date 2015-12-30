#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module: test_puzzle.py
Author: zlamberty
Created: 2015-12-19

Description:
    test the puzzle class

Usage:
    <usage>

"""

import os
import pandas as pd
import unittest

import categories
import rulelist
import puzzle


CONFIG = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'config'
)
FMT = os.path.join(CONFIG, '{num:0>3.0f}.{ftype:}.{ext:}')


class TestLogicPuzzle(unittest.TestCase):
    def __init__(self, num, *args, **kwargs):
        self.num = num
        self.fcatyaml = FMT.format(num=self.num, ftype='categories', ext='yaml')
        self.fruleyaml = FMT.format(num=self.num, ftype='rules', ext='yaml')
        self.fruletxt = FMT.format(num=self.num, ftype='rules', ext='txt')
        self.fsolyaml = FMT.format(num=self.num, ftype='solution', ext='yaml')
        self.fsoltxt = FMT.format(num=self.num, ftype='solution', ext='txt')
        self.fsolcsv = FMT.format(num=self.num, ftype='solution', ext='csv')
        super(TestLogicPuzzle, self).__init__(*args, **kwargs)

    def setUp(self):
        self.c = categories.CategoriesFromYaml(self.fcatyaml)
        self.r = rulelist.RulesFromFile(self.fruletxt, self.c)
        self.p = puzzle.LogicPuzzle(self.c, self.r)

    def test_solve(self):
        self.p.solve()
        a = self.p.solution
        a = a.reset_index()
        b = pd.read_csv(self.fsolcsv)
        self.assertEqual(a, b)


if __name__ == '__main__':
    unittest.main()
