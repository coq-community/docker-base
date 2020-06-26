#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020  Érik Martin-Dorel
#
# Contributed under the terms of the MIT license,
# cf. <https://spdx.org/licenses/MIT.html>

from bash_formatter import BashLike
from datetime import datetime
import copy
import requests
import sys
import yaml
import json  # debug


debug = True


def dump(data):
    """Debug"""
    print(json.dumps(data, indent=4), file=sys.stderr, flush=True)


# def error(msg, flush=True):
#     print(msg, file=sys.stderr, flush=flush)
#     exit(1)

class Error(Exception):
    """Base class for exceptions in this module."""
    pass


def error(msg):
    raise Error(msg)


def uniqify(s):
    """Remove duplicates, without preserving the elements order."""
    return list(set(s))


def is_unique(s):
    """Check if the list s has no duplicate."""
    return len(s) == len(set(s))


def check_string(value, ident=None):
    if not isinstance(value, str):
        if ident:
            error("Error: expecting a string value, but was given '%s: %s'."
                  % (ident, value))
        else:
            error("Error: expecting a string value, but was given '%s'."
                  % value)


def eval_bashlike(template, matrix, defaults=None):
    b = BashLike()
    return b.format(template, matrix=matrix, defaults=defaults)


def get_build_date():
    """ISO 8601 UTC timestamp"""
    return datetime.utcnow().strftime("%FT%TZ")


def naive_url_encode(name):
    """https://gitlab.com/help/api/README.md#namespaced-path-encoding"""
    check_string(name)
    return name.replace('/', '%2F')


def get_url(url, headers=None, query=None):
    """Argument query can be 'commit.id'."""
    print('GET %s\n' % url, file=sys.stderr, flush=True)
    response = requests.get(url, headers=headers, params=None)
    if not response:
        error("Error!\nCode: %d\nText: %s"
              % (response.status_code, response.text))
    if not query:
        return response.text
    else:
        response = response.json()
        jpath = query.split('.')
        for step in jpath:
            response = response[step]
        return response


def get_commit(commit_api):
    """Get GitHub or GitLab SHA1 of a given branch."""
    fetcher = commit_api['fetcher']
    repo = commit_api['repo']
    branch = commit_api['branch']
    if fetcher == 'github':
        url = 'https://api.github.com/repos/%s/commits/%s' % (repo, branch)
        headers = {"Accept": "application/vnd.github.v3.sha"}
        query = None
    elif fetcher == 'gitlab':
        # https://gitlab.com/help/api/branches.md#get-single-repository-branch
        url = ('https://gitlab.com/api/v4/projects/%s/repository/branches/%s'
               % (naive_url_encode(repo), naive_url_encode(branch)))
        headers = None
        query = 'commit.id'
    else:
        error("Error: do not support 'fetcher: %s'" % fetcher)
    return get_url(url, headers, query)


def load_spec():
    """Parse the 'images.yml' file and return a dict."""
    images_filename = 'images.yml'
    with open(images_filename) as f:
        j = yaml.safe_load(f)
    return j


def product_build_matrix(matrix):
    """Get the list of dicts grouping 1 item per list mapped to matrix keys."""
    assert matrix
    old = [{}]
    res = []
    for key in matrix:
        for value in matrix[key]:
            for e in old:
                enew = copy.deepcopy(e)
                enew[key] = value
                res.append(enew)
        old = res
        res = []
    return old


def check_trim_relative_path(path):
    """Fail if path is absolute and remove leading './'."""
    check_string(path)
    if path[0] == '/':
        error("Error: expecting a relative path, but was given '%s'." % path)
    elif path[:2] == './':
        return path[2:]
    else:
        return path


def check_filename(filename):
    check_string(filename)
    if '/' in filename:
        error("Error: expecting a filename, but was given '%s'." % filename)


def eval_if(raw_condition, matrix):
    """Evaluate YAML condition.

    Supported forms:
        '{matrix[key]} == "string"'
        '{matrix[key]} != "string"'
        '"{matrix[key]}" == "string"'
        '"{matrix[key]}" != "string"'
    """
    # Conjunction
    if isinstance(raw_condition, list):
        for item_condition in raw_condition:
            e = eval_if(item_condition, matrix)
            if not e:
                return False
        return True
    elif raw_condition is None:
        return True

    check_string(raw_condition)
    equality = (raw_condition.find("==") > -1)
    inequality = (raw_condition.find("!=") > -1)
    if equality:
        args = raw_condition.split("==")
    elif inequality:
        args = raw_condition.split("!=")
    else:
        error("Unsupported condition: '%s'." % raw_condition)
    if len(args) != 2:
        error("Wrong number of arguments: '%s'." % raw_condition)
    a = eval_bashlike(args[0].strip().replace('"', ''), matrix)
    b = eval_bashlike(args[1].strip().replace('"', ''), matrix)
    if equality:
        return a == b
    else:
        return a != b


def get_list_dict_dockerfile_matrix_tags_args(json):
    """Get [{"path": "Dockerfile", "matrix": …, "tags": …, "args": …}, …]."""
    res = []
    images = json['images']
    for item in images:
        list_matrix = product_build_matrix(item['matrix'])
        dfile = item['dockerfile'] if 'dockerfile' in item else 'Dockerfile'
        check_filename(dfile)
        ctxt = check_trim_relative_path(item['build']['context'])
        dockerfile = '%s/%s' % (ctxt, dfile)
        raw_tags = item['build']['tags']
        raw_args = item['build']['args']
        for matrix in list_matrix:
            tags = []
            for tag_item in raw_tags:
                tag_template = tag_item['tag']
                tag_cond = tag_item['if'] if 'if' in tag_item else None
                if eval_if(tag_cond, matrix):
                    # otherwise skip the tag synonym
                    tag = eval_bashlike(tag_template, matrix)  # & defaults ?
                    tags.append(tag)
            defaults = {"build_date": get_build_date()}
            if 'commit_api' in item['build']:
                commit_api = item['build']['commit_api']
                defaults['commit'] = get_commit(commit_api)
            args = {}
            for arg_key in raw_args:
                arg_template = raw_args[arg_key]
                args[arg_key] = eval_bashlike(arg_template, matrix, defaults)
            newitem = {"path": dockerfile, "matrix": matrix,
                       "tags": tags, "args": args}
            res.append(newitem)
    if debug:
        dump(res)
    return res


def write_list_dockerfile(seq):
    """To be used on the value of get_list_dict_dockerfile_matrix_tags_args."""
    dockerfiles = uniqify(map(lambda e: e['path'], seq))
    print(dockerfiles)


def write_check_tags(seq):
    """To be used on the value of get_list_dict_dockerfile_matrix_tags_args."""
    res = []
    for e in seq:
        res.extend(e['tags'])
    print(res)
    if is_unique(res):
        print("OK: no duplicate tag found.", file=sys.stderr, flush=True)
    else:
        error("Error: there are some tags duplicates.")


def main(args):
    list_dict = get_list_dict_dockerfile_matrix_tags_args(load_spec())
    write_list_dockerfile(list_dict)
    write_check_tags(list_dict)


###############################################################################
# Test suite, cf. <https://docs.python-guide.org/writing/tests/>
# $ pip3 install pytest
# $ py.test bash_formatter.py

def test_get_commit():
    github = {"fetcher": "github", "repo": "coq/coq", "branch": "v8.0"}
    github_expected = "6aecb9a1fe3f9b027dfd702931298bc61d40b6d3"
    github_actual = get_commit(github)
    assert github_actual == github_expected
    gitlab = {"fetcher": "gitlab", "repo": "coq/coq", "branch": "v8.0"}
    gitlab_expected = "6aecb9a1fe3f9b027dfd702931298bc61d40b6d3"
    gitlab_actual = get_commit(gitlab)
    assert gitlab_actual == gitlab_expected


def shouldfail(lam):
    try:
        res = lam()
        print("Wrong outcome: '%s'" % res, file=sys.stderr, flush=True)
        assert False
    except Error:
        print('OK', file=sys.stderr, flush=True)


def test_check_trim_relative_path():
    assert check_trim_relative_path('./foo/bar') == 'foo/bar'
    assert check_trim_relative_path('bar/baz') == 'bar/baz'
    shouldfail(lambda: check_trim_relative_path('/etc'))


def test_eval_if():
    matrix1 = {"base": "latest", "coq": "dev"}
    matrix2 = {"base": "4.09.0-flambda", "coq": "dev"}
    assert eval_if('{matrix[base]}=="latest"', matrix1)
    assert eval_if('{matrix[base]} == "latest"', matrix1)
    assert eval_if(' "{matrix[base]}" == "latest"', matrix1)
    assert eval_if('{matrix[base]}!="latest"', matrix2)
    assert eval_if('{matrix[base]} != "latest"', matrix2)
    assert eval_if(' "{matrix[base]}" != "latest"', matrix2)


def test_is_unique():
    s = [1, 2, 4, 0, 4]
    assert not is_unique(s)
    s = uniqify(s)
    assert is_unique(s)


if __name__ == "__main__":
    main(sys.argv[1:])
