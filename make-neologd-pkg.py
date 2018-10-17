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
import tempfile
import shutil
import subprocess

neologd_url = "https://github.com/neologd/mecab-ipadic-neologd"
VERSION = "0.1"

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

def get_commit(git_dir, date):
    cwd = pushd(git_dir)
    cmd = "git rev-list master -n 1 --first-parent".split()
    cmd.append("--before=%s" % date)
    output = subprocess.check_output(cmd)
    popd(cwd)
    return output[:-1]

def git_checkout(git_dir, commit):
    cwd = pushd(git_dir)
    cmd = "git checkout".split()
    cmd.append(commit)
    subprocess.check_call(cmd)
    popd(cwd)
    return

def git_get_lastdate(git_dir):
    cwd = pushd(git_dir)
    cmd = 'git log -1 --format=%cd --date=short'.split()
    date = subprocess.check_output(cmd)
    return date[:-1]

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

def binary_debian_files(rootdir, debian_version):
    # compat
    fname = os.path.join(rootdir, 'compat')
    with open(fname, 'w') as f:
        f.write("9\n")
    # README.Debian
    fname = os.path.join(rootdir, 'README.debian')
    with open(fname, 'w') as f:
        f.write("""mecab-ipadic-neologd for Debian
---------------------------------------------
mecab-ipadic-NEologd is customized system dictionary for MeCab.

This dictionary includes many neologisms (new word), which are
extracted from many language resources on the Web.

When you analyze the Web documents, it's better to use this system
dictionary and default one (ipadic) together.

You can use the dictionary with -d /var/lib/mecab/dic/ipadic-neologd
argument.
""")
    # control
    fname = os.path.join(rootdir, 'control')
    with open(fname, 'w') as f:
        f.write("""Source: mecab-ipadic-neologd
Section: text
Priority: optional
Build-Depends: debhelper (>= 10)
Build-Depends-Indep: mecab-utils (>= 0.93), curl, git, libmecab-dev, xz-utils
Maintainer: Natural Language Processing Japanese <team+pkgnlpja@tracker.debian.org>
Uploaders: NOKUBI Takatsugu <knok@daionet.gr.jp>
Standards-Version: 4.1.5
Homepage: https://github.com/neologd/mecab-ipadic-neologd

Package: mecab-ipadic-neologd
Architecture: any
Pre-Depends: dpkg
Depends: ${misc:Depends}, mecab (>= 0.93)
Description: Neologism dictionay for MeCab (binary format)
 mecab-ipadic-NEologd is customized system dictionary for MeCab.
 This dictionary includes many neologisms (new word), which are
 extracted from many language resources on the Web.
 When you analyze the Web documents, it's better to use this
 system dictionary and default one (ipadic) together.

Package: mecab-ipadic-neologd-csv
Architecture: all
Pre-Depends: dpkg
Depends: ${misc:Depends}, mecab (>= 0.93)
Description: Neologism dictionay for MeCab (csv format)
 The dictionary source csv files derived from the original ipadic.
""")
    # rules
    fname = os.path.join(rootdir, 'rules')
    with open(fname, 'w') as f:
        f.write('''#!/usr/bin/make -f
#
%:
	dh $@
''')
    # changelog
    fname = os.path.join(rootdir, 'changelog')
    with open(fname, 'w') as f:
        f.write("""mecab-ipadic-neologd (0.0.0.1~%s-1) unstable; urgency=medium

  * packaged by make-neologd-pkg.py (%s)

 -- NOKUBI Takatsugu <knok@daionet.gr.jp>  Wed, 10 Oct 2018 11:38:33 +0900
""" % (debian_version, VERSION))
    # install
    fname = os.path.join(rootdir, 'mecab-ipadic-neologd.install')
    with open(fname, 'w') as f:
        f.write('var/lib/mecab/dic/ipadic-neologd/*')
    fname = os.path.join(rootdir, 'mecab-ipadic-neologd-csv.install')
    with open(fname, 'w') as f:
        f.write('usr/share/mecab/dic/ipadic-neologd/*')

def copy_bin_files(git_dir, debian_dir):
    dic_dir = get_dic_fname(git_dir)
    dic_dir = os.path.dirname(dic_dir)
    # copy binary dictionary files
    ## make package dir
    bin_dist = os.path.join(debian_dir, "../var/lib/mecab/dic/ipadic-neologd")
    os.makedirs(bin_dist, exist_ok=True)
    ## copy files
    ### .bin
    pat = os.path.join(dic_dir, "*.bin")
    files = glob.glob(pat)
    for fname in files:
        shutil.copy(fname, bin_dist)
    ### .dic
    pat = os.path.join(dic_dir, "*.dic")
    files = glob.glob(pat)
    for fname in files:
        shutil.copy(fname, bin_dist)
    ### dicrc
    fname = os.path.join(dic_dir, "dicrc")
    shutil.copy(fname, bin_dist)
    
def copy_csv_files(git_dir, debian_dir):
    dic_dir = get_dic_fname(git_dir)
    dic_dir = os.path.dirname(dic_dir)
    # copy csv dictionary files
    ## make package dir
    bin_dist = os.path.join(debian_dir, "../usr/share/mecab/dic/ipadic-neologd")
    os.makedirs(bin_dist, exist_ok=True)
    ## copy files
    ### .csv
    pat = os.path.join(dic_dir, "*.csv")
    files = glob.glob(pat)
    for fname in files:
        shutil.copy(fname, bin_dist)
    ### dicrc
    fname = os.path.join(dic_dir, "dicrc")
    shutil.copy(fname, bin_dist)

def run_dpkg_buildpackage(pkg_dir):
    cwd = pushd(pkg_dir)
    cmd = "dpkg-buildpackage -b -uc -us"
    os.system(cmd)
    popd(cwd)

def copy_deb(temp_dir):
    cwd = pushd(temp_dir)
    pat = "mecab-ipadic-neologd*.deb"
    files = glob.glob(pat)
    for fname in files:
        shutil.copy(fname, cwd)
    popd(cwd)

def make_pkg_binary(work_dir, git_dir, date_str):
    with tempfile.TemporaryDirectory(dir=work_dir) as td:
        pkg_dir = os.path.join(td, "mecab-ipadic-neologd-%s" % date_str)
        os.makedirs(pkg_dir)
        deb_dir = os.path.join(pkg_dir, 'debian')
        os.makedirs(deb_dir)
        binary_debian_files(deb_dir, date_str)
        copy_bin_files(git_dir, deb_dir)
        copy_csv_files(git_dir, deb_dir)
        run_dpkg_buildpackage(pkg_dir)
        copy_deb(td)

def get_args():
    p = argparse.ArgumentParser()
    p.add_argument('--work-dir', default='/var/tmp')
    p.add_argument('--depth', default=-1, type=int)
    p.add_argument('--date', default=None,
                   help='specify checkout version by date string (YYYY-MM-DD)')
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

    # get version or date
    if args.date is not None:
        ch = get_commit(git_dir, args.date)
        ver_date = args.date
        git_checkout(git_dir, ch)
    else:
        ver_date = git_get_lastdate(git_dir)

    # build on git repo
    dic_fname = get_dic_fname(git_dir)
    if dic_fname is not None and os.path.exists(dic_fname):
        logging.info("Binary dic file %s exists, skip build" % dic_fname)
    else:
        build_on_git(git_dir)
        dic_fname = get_dic_fname(git_dir)

    # build debian binary package
    date_str = dic_fname[:-11] # remove /matrix
    date_str = date_str[-8:] # remove prefix
    make_pkg_binary(args.work_dir, git_dir, date_str)

if __name__ == '__main__':
    main()
