#! /usr/bin/python3
# -*- coding: utf-8 -*-
#
"""make mecab-ipadic-neologd deb package
"""

import argparse
import os
import sys
import logging
import glob

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

def get_dic_fname(git_dir):
    build_dir = os.path.join(git_dir, "build")
    if not os.path.isdir(build_dir):
        return None
    pat = os.path.join(build_dir, "mecab-ipadic-2.7.0-*-neologd-*")
    dir_list = glob.glob(pat)
    dir_list.sort()
    ret = os.path.join(dir_list[-1], "matrix.bin")
    return ret

def build_on_git(gitdir):
    cwd = pushd(gitdir)
    cmd = "./libexec/make-mecab-ipadic-neologd.sh"
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
    # git source code dir
    git_dir = os.path.join(args.work_dir, 'mecab-ipadic-neologd')

    # invoke git clone
    if os.path.exists(git_dir):
        logging.info("Directory %s exists, skip clone" % git_dir)
    else:
        git_clone(args.work_dir, args.depth)

    # build on git repo
    dic_fname = get_dic_fname(git_dir)
    if dic_fname is not None and os.path.exists(dic_fname):
        logging.info("Binary dic file %s exists, skip build" % dic_fname)
    else:
        build_on_git(git_dir)

if __name__ == '__main__':
    main()
