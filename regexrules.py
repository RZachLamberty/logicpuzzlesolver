#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module: regexrules.py
Author: zlamberty
Created: 2015-12-16

Description:
    utility function for regex parsing of rules; used by the
    RulesFromText object in rule.py

Usage:
    <usage>

"""

import re

import rule

# ----------------------------- #
#   Module Constants            #
# ----------------------------- #


# ----------------------------- #
#   Main routine                #
# ----------------------------- #

class RegexRuleFunction(object):
    """ abstract class defining the api of all regex rule functions. These
        objects can be registered to RulesFromText objects and then used to
        parse lines. The basic gist, here, is that each object must have one
        method (__call__) that will take an arbitrary line of text and try to
        return a Rule object. This will require
            1. a basic regex
            2. a method to updating that regex based on context-specific values
               (a la string formatting; usually this will be sufficient but
               perhaps it becomes more complicated some day)
            3. a method to match lines (simple regex findall)
            4. a method to turn a match group into a Rule object

        The first three are pretty easily generalized; the fourth is the meat of
        it. Pass that fourth function in through the constructor for flexibility

    """
    def __init__(self, regex, m2rfunc=None):
        self.regex = regex
        if m2rfunc:
            self.match_to_rule = m2rfunc

    def __call__(self, line):
        try:
            return self.match_to_rule(self.get_matches(line))
        except:
            return None

    def update_regex(self, **params):
        self.regex = self.regex.format(**params)

    def get_matches(self, line):
        return re.search(self.regex, line).groups()

    def match_to_rule(self, match):
        raise NotImplementedError()


def simple_regex_rule(regex, f, keys):
    return RegexRuleFunction(
        regex=regex,
        m2rfunc=lambda match: rule.Rule(
            f, **{k: m for (k, m) in zip(keys, match) if k}
        )
    )


def comparison_rule(regex, f, keyorder):
    """ for the regex, a *match* here must have the following values:
            f1      - one filter
            f2      - the other filter
            mlf     - the comparison direction
            compCat - the category being compared
            offset  - the offset in the comparison (this is) [optional]

        regex       - the regex string that will yield the above match groups
        f           - the rule function (is_incremented or is_ordered)
        keyorder    - the order of the above match groups in the regex group

    """
    def foo(match):
        # comparison category
        params = {'compCat': match[keyorder.index('compCat')]}

        # which is big, which is small
        mlf = match[keyorder.index('mlf')]
        f1 = match[keyorder.index('f1')]
        f2 = match[keyorder.index('f2')]
        if mlf in ['more']:
            params['bigfilt'], params['smallfilt'] = f1, f2
        elif mlf in ['less', 'fewer']:
            params['bigfilt'], params['smallfilt'] = f2, f1
        else:
            msg = "mlf token {} doesn't tell us which filter value is larger"
            msg = msg.format(mlf)
            raise rule.RuleError(msg)

        # offset
        try:
            params['offset'] = int(match[keyorder.index('offset')])
        except ValueError:
            pass

        return rule.Rule(f, **params)
    return RegexRuleFunction(regex, m2rfunc=foo)


# remember, only one pass through, so keep harder regexes at the front
STANDARD_RULES = [
    # [A, B, ...] are all different
    # A = B (+ offset)
    comparison_rule(
        regex="({vals:})[ '][ a-zA-Z]*(\d+) (more|less|fewer) ({compcats:}) [ a-zA-Z]*({vals:})[ '.]",
        f=rule.is_incremented,
        keyorder=['f1', 'offset', 'mlf', 'compCat', 'f2'],
    ),
    # A > B (+ offset)
    # (A, B) is (C, D)
    # A is neither B nor C
    # A is either B or C
    simple_regex_rule(
        "({vals:})[ '][ a-zA-Z]*was either [ a-zA-Z]*({vals:})[ ''][ a-zA-Z]*or [ a-zA-Z]*({vals:})[ .]",
        rule.is_either_or, ['isfilt', 'eitherfilt', 'orfilt']
    ),
    # A is not B
    simple_regex_rule(
        "({vals:})[ '][ a-zA-Z]*(wasn't|didn't|isn't) [ a-zA-Z]*({vals:})[ .]",
        rule.is_diff, ['filt1', None, 'filt2']
    ),
    # A is B
    simple_regex_rule(
        "({vals:})[ '][ a-zA-Z]*({vals:})[ .]", rule.is_same, ['filt1', 'filt2']
    ),
]
