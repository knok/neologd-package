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
VERSION = "0.2"

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

def git_newest(git_dir):
    cwd = pushd(git_dir)
    cmd = "git fetch origin".split()
    subprocess.call(cmd)
    cmd = "git reset --hard origin/master".split()
    subprocess.check_call(cmd)
    popd(cwd)

def get_commit(git_dir, date):
    cwd = pushd(git_dir)
    cmd = "git rev-list master -n 1 --first-parent".split()
    cmd.append("--before=%s" % date)
    output = subprocess.check_output(cmd)
    popd(cwd)
    return output[:-1].decode()

def git_checkout(git_dir, commit):
    cwd = pushd(git_dir)
    cmd = "git checkout".split()
    cmd.append(commit)
    subprocess.check_call(cmd)
    popd(cwd)
    return

def clean_git_build_dir(git_dir):
    cwd = pushd(git_dir)
    # get build/mecab-ipadic-$ver-$date
    dirs = glob.glob("build/mecab-ipadic-*-*")
    for d in dirs:
        if os.path.isdir(d):
            shutil.rmtree(d)
    popd(cwd)
    return

def git_get_lastdate(git_dir):
    cwd = pushd(git_dir)
    cmd = 'git log -1 --format=%cd --date=short'.split()
    date = subprocess.check_output(cmd)
    popd(cwd)
    return date[:-1].decode()

def get_dic_fname(git_dir):
    build_dir = os.path.join(git_dir, "build")
    if not os.path.isdir(build_dir):
        return None
    pat = os.path.join(build_dir, "mecab-ipadic-2.7.0-*-neologd-*")
    dir_list = glob.glob(pat)
    if len(dir_list) == 0:
        return None
    dir_list.sort()
    ret = os.path.join(dir_list[-1], "matrix.bin")
    return ret

def build_on_git(gitdir):
    cwd = pushd(gitdir)
    cmd = ["./bin/install-mecab-ipadic-neologd", "-y"]
    subprocess.check_call(cmd)
    popd(cwd)

def binary_debian_files(rootdir, debian_version, upstream_date):
    # compat
    fname = os.path.join(rootdir, 'compat')
    with open(fname, 'w') as f:
        f.write("9\n")
    # README.Debian
    fname = os.path.join(rootdir, 'README.debian')
    with open(fname, 'w') as f:
        f.write("""mecab-ipadic-neologd-%s for Debian
---------------------------------------------
mecab-ipadic-NEologd is customized system dictionary for MeCab.

This dictionary includes many neologisms (new word), which are
extracted from many language resources on the Web.

When you analyze the Web documents, it's better to use this system
dictionary and default one (ipadic) together.

You can use the dictionary with 
-d /var/lib/mecab/dic/ipadic-neologd-%s argument.
        """ % (upstream_date, upstream_date))
    # control
    fname = os.path.join(rootdir, 'control')
    with open(fname, 'w') as f:
        f.write("""Source: mecab-ipadic-neologd-%s
Section: text
Priority: optional
Build-Depends: debhelper (>= 10)
Build-Depends-Indep: mecab-utils (>= 0.93), curl, libmecab-dev
Maintainer: Natural Language Processing Japanese <team+pkgnlpja@tracker.debian.org>
Uploaders: NOKUBI Takatsugu <knok@daionet.gr.jp>
Standards-Version: 4.1.5
Homepage: https://github.com/neologd/mecab-ipadic-neologd

Package: mecab-ipadic-neologd-%s
Architecture: any
Pre-Depends: dpkg
Depends: ${misc:Depends}, mecab (>= 0.93)
Description: Neologism dictionay for MeCab (binary format)
 mecab-ipadic-NEologd is customized system dictionary for MeCab.
 This dictionary includes many neologisms (new word), which are
 extracted from many language resources on the Web.
 When you analyze the Web documents, it's better to use this
 system dictionary and default one (ipadic) together.

Package: mecab-ipadic-neologd-csv-%s
Architecture: all
Pre-Depends: dpkg
Depends: ${misc:Depends}, mecab (>= 0.93)
Description: Neologism dictionay for MeCab (csv format)
 The dictionary source csv files derived from the original ipadic.
        """ % (upstream_date, upstream_date, upstream_date))
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
        f.write("""mecab-ipadic-neologd-%s (0.0.0.1~%s-1) unstable; urgency=medium

  * packaged by make-neologd-pkg.py (%s)

 -- NOKUBI Takatsugu <knok@daionet.gr.jp>  Wed, 10 Oct 2018 11:38:33 +0900
""" % (upstream_date, debian_version, VERSION))
    # install
    fname = os.path.join(rootdir, 'mecab-ipadic-neologd-%s.install' % upstream_date)
    with open(fname, 'w') as f:
        f.write('var/lib/mecab/dic/ipadic-neologd-%s/*' % upstream_date)
    fname = os.path.join(rootdir, 'mecab-ipadic-neologd-csv-%s.install' % upstream_date)
    with open(fname, 'w') as f:
        f.write('usr/share/mecab/dic/ipadic-neologd-%s/*' % upstream_date)

def copy_bin_files(git_dir, debian_dir, upstream_date):
    dic_dir = get_dic_fname(git_dir)
    dic_dir = os.path.dirname(dic_dir)
    # copy binary dictionary files
    ## make package dir
    bin_dist = os.path.join(debian_dir, "../var/lib/mecab/dic/ipadic-neologd-%s" % upstream_date)
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
    
def copy_csv_files(git_dir, debian_dir, upstream_date):
    dic_dir = get_dic_fname(git_dir)
    dic_dir = os.path.dirname(dic_dir)
    # copy csv dictionary files
    ## make package dir
    bin_dist = os.path.join(debian_dir, "../usr/share/mecab/dic/ipadic-neologd-%s" % upstream_date)
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

def make_pkg_binary(work_dir, git_dir, date_str, ver_date):
    with tempfile.TemporaryDirectory(dir=work_dir) as td:
        pkg_dir = os.path.join(td, "mecab-ipadic-neologd-%s" % ver_date)
        os.makedirs(pkg_dir)
        deb_dir = os.path.join(pkg_dir, 'debian')
        os.makedirs(deb_dir)
        binary_debian_files(deb_dir, date_str, ver_date)
        copy_bin_files(git_dir, deb_dir, ver_date)
        copy_csv_files(git_dir, deb_dir, ver_date)
        run_dpkg_buildpackage(pkg_dir)
        copy_deb(td)

def get_args():
    p = argparse.ArgumentParser()
    p.add_argument('--work-dir', default='/var/tmp')
    p.add_argument('--depth', default=-1, type=int)
    p.add_argument('--date', '-d', default=None,
                   help='specify checkout version by date string (YYYY-MM-DD)')
    p.add_argument('--commit', '-c', default=None,
                   help="specify commit hash")
    p.add_argument('--newest', '-n', default=False, action="store_true",
                   help="update git repo to newest")
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

    # newest or get version or specify by date
    if args.newest:
        git_newest(git_dir)
        ver_date = git_get_lastdate(git_dir)
        clean_git_build_dir(git_dir)
    elif args.commit is not None:
        git_checkout(git_dir, args.commit)
        ver_date = git_get_lastdate(git_dir)
        clean_git_build_dir(git_dir)
    elif args.date is not None:
        ch = get_commit(git_dir, args.date)
        ver_date = args.date
        git_checkout(git_dir, ch)
        clean_git_build_dir(git_dir)
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
    make_pkg_binary(args.work_dir, git_dir, date_str, ver_date)

if __name__ == '__main__':
    main()
