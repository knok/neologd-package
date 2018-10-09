#! /usr/bin/python3
# -*- coding: utf-8 -*-
#
"""make mecab-ipadic-neologd deb package
"""

import argparse
import os
import sys

neologd_url = "https://github.com/neologd/mecab-ipadic-neologd"

def pushd(newdir):
    cwd = os.path.abspath(".")
    os.chdir(newdir)
    return cwd

def popd(olddir):
    os.chdir(olddir)

def git_clone(workdir):
    cwd = pushd(workdir)
    os.system("git clone %s" % neologd_url)
    popd(cwd)

def get_args():
    p = argparse.ArgumentParser()
    p.add_argument('--work-dir', default='/var/tmp')
    args = p.parse_args()
    return args

def main():
    args = get_args()

if __name__ == '__main__':
    main()
