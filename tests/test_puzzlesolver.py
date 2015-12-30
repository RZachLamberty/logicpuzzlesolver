#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module: test_puzzlesolver.py
Author: zlamberty
Created: 2015-12-19

Description:
    tests for the puzzlesolver module

Usage:
    <usage>

"""

import unittest2 as unittest

import categories
import puzzle
import rule
import rulelist


# ----------------------------- #
#   Module Constants            #
# ----------------------------- #

CONF = 'conf'


def test_main(fcats=FCATS, frules=FRULES):
    c = categories.CategoriesFromYaml(fcats)
    r = rulelist.RulesFromFile(frules, c)
    p = puzzle.LogicPuzzle(c, r)
    p.solve()
    print p.results()
