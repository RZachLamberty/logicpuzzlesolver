#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module: rulelist.py
Author: zlamberty
Created: 2015-12-16

Description:
    class object, basically just a smart list of rule objects

Usage:
    <usage>

"""

import re
import yaml

import common
import rule

from collections import defaultdict
from regexrules import STANDARD_RULES

# ----------------------------- #
#   rules (lists of rule objs)  #
# ----------------------------- #

class RuleError(Exception):
    pass


class Rules(list):
    funcmap = {
        1: {'desc': 'A is B', 'func': rule.is_same, 'params': ['filt1', 'filt2']},
        2: {'desc': 'A is not B', 'func': rule.is_diff, 'params': ['filt1', 'filt2']},
        3: {'desc': 'A is either B or C', 'func': rule.is_either_or, 'params': ['isfilt', 'eitherfilt', 'orfilt']},
        4: {'desc': 'A is neither B nor C', 'func': rule.is_neither_nor, 'params': ['isfilt', 'neitherfilt', 'norfilt']},
        5: {'desc': '(A, B) is (C, D)', 'func': rule.pair_is_pair, 'params': ['filt11', 'filt12', 'filt21', 'filt22']},
        6: {'desc': 'A > B (+ offset)', 'func': rule.is_ordered, 'params': ['compCat', 'bigfilt', 'smallfilt', 'offset']},
        7: {'desc': 'A = B (+ offset)', 'func': rule.is_incremented, 'params': ['compCat', 'bigfilt', 'smallfilt', 'offset']},
        8: {'desc': '[A, B, ...] are all different', 'func': rule.similarity_group_updates, 'listparams': ['filtlist']},
    }

    def __init__(self):
        raise NotImplementedError()

    def get_rules(self):
        raise NotImplementedError()

    def make_lookup(self, categories=None):
        self.lookup = {}
        try:
            for cat in categories:
                self.lookup[str(cat.name)] = cat.name
                if str(cat.name).endswith('s'):
                    self.lookup[str(cat.name)[:-1]] = cat.name
                self.lookup.update({str(v): v for v in cat.values})
                # month rev lookup gets builtin
                if cat.isin(common.MONTHS.values()).any():
                    for (strs, v) in common.MONTHS.items():
                        self.lookup.update({s: v for s in strs})
        except:
            pass


class RulesFromYaml(Rules):
    def __init__(self, fyaml):
        self.f = fyaml
        self.get_rules()

    def get_rules(self):
        with open(self.f, 'rb') as f:
            self += yaml.load(f)


class RulesFromText(Rules):
    """ the big one -- can we do regex matching on rules? """
    def __init__(self, rulelines, categories, regexes=STANDARD_RULES):
        self._rulelines = [rl.lower() for rl in rulelines]
        self._categories = categories
        self._regexes = regexes
        self._update_regexes()
        self.get_rules()
        self.smart_lookup_ify()

    def get_rules(self):
        for ruleline in self._rulelines:
            rule = self.try_all_regexes(ruleline)
            self.append(rule)

    def try_all_regexes(self, ruleline):
        for regexfunc in self._regexes:
            matchrule = regexfunc(ruleline)
            if matchrule:
                return matchrule
        print ruleline
        L = len(self._regexes)
        raise RuleError("No match found among our {} regexes".format(L))

    def smart_lookup_ify(self):
        """ for all the rules we have now collected, we should have params.
            The values in those params should be replaced, if possible, with
            their associated self.lookup values

        """
        self.make_lookup(self._categories)
        for rule in self:
            rule.params = {
                k: self.lookup.get(v, v) for (k, v) in rule.params.items()
            }

    # properties; mostly for formatting regex strings
    @property
    @common.memoized
    def vals(self):
        return {str(v): cat.name for cat in self._categories for v in cat.values}

    @property
    @common.memoized
    def valsRegex(self):
        return '|'.join(self.vals.keys())

    @property
    @common.memoized
    def verbs(self):
        vbs = defaultdict(set)
        for line in self._rulelines:
            verbvals = re.findall(
                'who (\w+) [ a-zA-Z]*({vals:})'.format(vals=self.valsRegex),
                line
            )
            for (verb, catval) in verbvals:
                vbs[self.vals[catval]].add(verb)
                if verb.endswith('ed'):
                    vbs[self.vals[catval]].add(verb[:-2])
        return vbs

    @property
    @common.memoized
    def verbsRegex(self):
        return '|'.join(self.verbs.keys())

    @property
    @common.memoized
    def verbVals(self):
        vv = []
        for (catname, verbs) in self.verbs.items():
            vals = {k for (k, v) in self.vals.items() if v == catname}
            vv.append([verbs, vals])
        return vv

    @property
    @common.memoized
    def compcats(self):
        cc = {}
        for catname in self._categories.names:
            cc[catname] = catname
            if catname.endswith('s'):
                cc[catname[:-1]] = catname
        return cc

    @property
    @common.memoized
    def compcatsRegex(self):
        return '|'.join(self.compcats.keys())

    @property
    def fstr(self):
        return {
            'vals': self.valsRegex,
            'verbs': self.verbsRegex,
            'compcats': self.compcatsRegex,
        }

    def _update_regexes(self):
        for regex in self._regexes:
            regex.update_regex(**self.fstr)


class RulesFromFile(RulesFromText):
    def __init__(self, fname, categories, regexes=STANDARD_RULES):
        self.fname = fname
        with open(self.fname, 'rb') as f:
            lines = [line.strip() for line in f.readlines()]
        super(RulesFromFile, self).__init__(
            rulelines=lines, categories=categories, regexes=regexes
        )


class RulesFromTextInteractive(RulesFromText):
    def __init__(self, categories, regexes=STANDARD_RULES):
        lines = []
        print "Enter rules (leave blank to exit):"
        while True:
            line = raw_input("\trule: ")
            if line:
                lines.append(line)
            else:
                break
        super(RulesFromTextInteractive, self).__init__(
            rulelines=lines, categories=categories, regexes=regexes
        )


class RulesInteractive(Rules):
    def __init__(self, categories):
        self.make_lookup(categories)
        self.get_rules()

    def get_rules(self):
        # now actually make the rules
        rules = []
        while True:
            paramnames = []
            listparamnames = []
            ruletype = raw_input(
                "\nWhat type of rule is this?"
                + "".join(
                    '\n\t{} - {}'.format(i, d['desc'])
                    for (i, d) in self.funcmap.items()
                )
                + "\n\t  - (leave blank to exit)"
                + "\n\n\t> "
            )
            if not ruletype:
                break

            try:
                d = self.funcmap[int(ruletype)]
                f = d['func']
                pnames = d.get('params', [])
                listpnames = d.get('listparams', [])
                params = self.get_rule_kwargs_interactive(pnames, listpnames)
                self.append(Rule(f, **params))
            except KeyError:
                print "\ninvalid value, try again\n"
                continue

            raise NotImplementedError("Not finished with this function yet!")
            rules.append([f, ])

    def get_rule_kwargs_interactive(self, pnames, listpnames):
        """ pnames is a list of parameters that expect only one value;
            listpnames expects a list. Self.Lookup is a reverse lookup
            dictionary of str repr values --> df values

        """
        print "\n\tgetting parameters (leave any blank for defaults)"
        params = {}
        for pname in pnames:
            val = raw_input("\t\t{}: ".format(pname))
            if val:
                try:
                    val = self.lookup[val]
                except KeyError:
                    val = self.type_update_interactive([val], indent="\t\t\t")[0]
                params[pname] = val

        for pname in listpnames:
            print "\t\t{}: ".format(pname)
            params[pname] = []
            while True:
                val = raw_input("\t\t\t> ")
                if val:
                    try:
                        val = self.lookup[val]
                    except:
                        val = self.type_update_interactive([val], indent="\t\t\t\t")[0]
                    params[pname].append(val)
                else:
                    break

        return params

    def type_update_interactive(self, vals, indent="\t\t"):
        valtype = raw_input("{}special type (int, float, month, or blank): ".format(indent))
        if valtype == 'int':
            vals = map(int, vals)
        elif valtype == 'float':
            vals = map(float, vals)
        elif valtype == 'month':
            vals = map(common.monthify, vals)

        return vals
