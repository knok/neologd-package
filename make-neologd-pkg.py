#! /usr/bin/python3
# -*- coding: utf-8 -*-
#
"""make mecab-ipadic-neologd deb package
"""

import argparse
import os
import sys
import logging

neologd_url = "https://github.com/neologd/mecab-ipadic-neologd"

def pushd(newdir):
    cwd = os.path.abspath(".")
    os.chdir(newdir)
    return cwd

def popd(olddir):
    os.chdir(olddir)

def git_clone(workdir, depth):
    cwd = pushd(workdir)
    cmd = "git clone %s" % neologd_url
    if depth > 0:
        cmd += " --depth %d" % depth
    os.system(cmd)
    popd(cwd)

def get_args():
    p = argparse.ArgumentParser()
    p.add_argument('--work-dir', default='/var/tmp')
    p.add_argument('--depth', default=-1, type=int)
    args = p.parse_args()
    return args

def main():
    args = get_args()
    git_dir = os.path.join(args.work_dir, 'mecab-ipadic-neologd')
    if os.path.exists(git_dir):
        logging.info("Directory %s exists, skip clone" % git_dir)
    else:
        git_clone(args.work_dir, args.depth)

if __name__ == '__main__':
    main()
