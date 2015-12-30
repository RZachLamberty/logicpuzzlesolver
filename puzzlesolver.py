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

import os

import categories
import puzzle
import rule
import rulelist


# ----------------------------- #
#   Module Constants            #
# ----------------------------- #

FCATS = os.path.join('config', 'test_categories.yaml')
#FRULES = os.path.join('config', 'test_rules.yaml')
FRULES = os.path.join('config', 'test_rules.txt')

# ----------------------------- #
#   Main routine                #
# ----------------------------- #

def main(numcat, numval):
    c = categories.CategoriesInteractive(numcat, numval)
    r = rulelist.RulesInteractive(c)
    p = puzzle.LogicPuzzle(c, r)
    p.solve()
    print p.results()


# ----------------------------- #
#   Command line                #
# ----------------------------- #

if __name__ == '__main__':
    main()
