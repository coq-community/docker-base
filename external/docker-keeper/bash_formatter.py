#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2024  Érik Martin-Dorel
#
# Contributed under the terms of the MIT license,
# cf. <https://spdx.org/licenses/MIT.html>

from string import Formatter
import functools
import _string
import re


def translate(glob, greedy=False):
    """Translate a simple glob expression to a (non-anchored) regexp."""
    qmark = '.'
    if greedy:
        star = '.*'
    else:
        star = '.*?'

    inner = lambda s: qmark.join(map(re.escape, s.split('?')))  # noqa: E731

    return star.join(map(inner, glob.split('*')))


def translate_prefix(glob, greedy=False):
    """Translate a simple glob expression to a (left)anchored regexp."""
    return '^' + translate(glob, greedy)


def reverse(text):
    return text[::-1]


class BashLike(Formatter):
    """Refine string.format(dict), allowing {var[bash-like-patterns]}.

    In particular:
    {var[0:7]}
    {var[%.*]}
    {var[%%.*]}
    {var[//glob/str]}
    """
    # New implementation of
    # <https://github.com/python/cpython/blob/919f0bc/Lib/string.py#L267-L280>:
    def get_field(self, field_name, args, kwargs):
        first, rest = _string.formatter_field_name_split(field_name)

        obj = self.get_value(first, args, kwargs)

        for is_attr, i in rest:
            if is_attr:
                # hide private fields
                if i.startswith('_'):
                    obj = ''
                else:
                    obj = getattr(obj, i)
            else:
                mslice = re.match('^([0-9]+):([0-9]+)$', i)
                msuffixgreedy = re.match('^%%(.+)$', i)
                msuffix = re.match('^%(.+)$', i)  # to test after greedy
                mprefixgreedy = re.match('^##(.+)$', i)
                mprefix = re.match('^#(.+)$', i)
                msed = re.match('^//([^/]+)/(.*)$', i)
                mprefixjoin = re.match('^/#/(.*)$', i)  # useful on a list var
                msuffixjoin = re.match('^/%/(.*)$', i)  # useful on a list var
                if mslice:
                    a, b = map(int, mslice.groups())
                    obj = obj[a:b]
                elif msuffixgreedy:
                    suffix = msuffixgreedy.groups()[0]
                    prefix = translate_prefix(reverse(suffix), True)
                    obj = reverse(re.sub(prefix, '', reverse(obj), count=1))
                elif msuffix:
                    suffix = msuffix.groups()[0]
                    prefix = translate_prefix(reverse(suffix), False)
                    obj = reverse(re.sub(prefix, '', reverse(obj), count=1))
                elif mprefixgreedy:
                    prefix = mprefixgreedy.groups()[0]
                    prefix = translate_prefix(prefix, True)
                    obj = re.sub(prefix, '', obj, count=1)
                elif mprefix:
                    prefix = mprefix.groups()[0]
                    prefix = translate_prefix(prefix, False)
                    obj = re.sub(prefix, '', obj, count=1)
                elif msed:
                    glob, dest = msed.groups()
                    regexp = translate(glob, True)
                    obj = re.sub(regexp, dest, obj, count=0)
                elif mprefixjoin:
                    addprefix = mprefixjoin.groups()[0]
                    if obj:
                        if isinstance(obj, list):
                            obj = functools.reduce(lambda res, e:
                                                   res + addprefix + str(e),
                                                   obj, '')
                        else:
                            obj = addprefix + str(obj)
                    else:
                        obj = ''
                elif msuffixjoin:
                    addsuffix = msuffixjoin.groups()[0]  # no need for reverse
                    if obj:
                        if isinstance(obj, list):
                            obj = functools.reduce(lambda res, e:
                                                   res + str(e) + addsuffix,
                                                   obj, '')
                        else:
                            obj = str(obj) + addsuffix
                    else:
                        obj = ''
                else:
                    obj = obj[i]

        return obj, first


###############################################################################
# Test suite, cf. <https://docs.python-guide.org/writing/tests/>
# $ pip3 install pytest
# $ py.test bash_formatter.py

class Dummy():
    _val = None
    pub = None

    def __init__(self, val, pub):
        self._val = val
        self.pub = pub


def test_reverse():
    assert reverse('12345') == '54321'


def test_translate():
    assert translate('?????678-*.txt') == '.....678\\-.*?\\.txt'
    assert translate('?????678-*.txt', True) == '.....678\\-.*\\.txt'


def test_BashLike():
    b = BashLike()
    assert b.format('A{var[2:4]}Z', var='abcde') == 'AcdZ'
    assert b.format('{s[0:7]}', s='1234567890abcdef') == '1234567'
    assert b.format('{s[%.*]}', s='8.10.0') == '8.10'
    assert b.format('{s[%%.*]}', s='8.10.0') == '8'
    assert b.format('{s[%???]}', s='3.14159') == '3.14'
    assert b.format('{obj.pub}', obj=Dummy(4, 12)) == '12'
    assert b.format('{obj._val}', obj=Dummy(4, 12)) == ''
    assert b.format('V{matrix[coq][//-/+]}', matrix={'coq': '8.12-alpha'}) == \
        'V8.12+alpha'
    assert b.format('{s[#*>]}', s="string->int->char") == 'int->char'
    assert b.format('{s[##*>]}', s="string->int->char") == 'char'
    assert b.format('{s[%-*]}', s="string->int->char") == 'string->int'
    assert b.format('{s[%%-*]}', s="string->int->char") == 'string'
    assert b.format('{lst[/#/;]}', lst=[]) == ''
    assert b.format('{s[/#/;]}', s="dev") == ';dev'
    assert b.format('{lst[/#/;]}', lst=['5.0']) == ';5.0'
    assert b.format('{lst[/#/;]}', lst=[1, 2, 4]) == ';1;2;4'
    assert b.format('{s[/#/;][#;]}', s="dev") == 'dev'
    assert b.format('{lst[/#/;][#;]}', lst=['5.0']) == '5.0'
    assert b.format('{lst[/#/;][#;]}', lst=[1, 2, 4]) == '1;2;4'
    assert b.format('{lst[/#/,ocaml-][#,]}', lst=['4.14', '5.0']) == \
        'ocaml-4.14,ocaml-5.0'
    assert b.format('{lst[/%/;]}', lst=[]) == ''
    assert b.format('{s[/%/;]}', s="dev") == 'dev;'
    assert b.format('{lst[/%/;]}', lst=['5.0']) == '5.0;'
    assert b.format('{lst[/%/;]}', lst=[1, 2, 4]) == '1;2;4;'
    assert b.format('{s[/%/;][%;]}', s="dev") == 'dev'
    assert b.format('{lst[/%/;][%;]}', lst=['5.0']) == '5.0'
    assert b.format('{lst[/%/;][%;]}', lst=[1, 2, 4]) == '1;2;4'
    assert b.format('{lst[/%/-flambda,][%,]}', lst=['4.14', '5.0']) == \
        '4.14-flambda,5.0-flambda'
