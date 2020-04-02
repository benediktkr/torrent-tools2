#!/usr/bin/env python3

import argparse
import shutil
import os
import pathlib

from guessit import guessit
from colorama import Fore, Style

Yellow = Fore.YELLOW
Green = Fore.GREEN
RESET_ALL = Style.RESET_ALL
CACHE_FILE="/tmp/ttsort.list"

RSYNC_LOCKFILE = "/tmp/tt-rsync.lock"

def touch(path):
    return pathlib.Path(path).touch()

def sort(src, dst, cp, dry_run=False, verbose=False):
    titles = {'episode': set(), 'movie': set()}
    ignored = set()
    qs = ['720p', '1080p']

    for root, dirs, files in os.walk(src):
        for f in files:
            d = guessit(f)
            try:
                if d['type'] in ["movie", "episode"]:
                    if d.get('screen_size') in qs:
                        # Sometimes it's all lowercase, so pulling it
                        # out and .title().
                        title = d['title'].title()
                        titles[d['type']].add(title)

                        # Check if the file live in a parent dir with the
                        # same title. If so, we want to move the whole dir
                        #   root = parent dir
                        #   f = video filename (usually has more info)
                        guess_basename = guessit(os.path.basename(root))
                        if guess_basename['title'].title() == title:
                            # This means we're moving the entire parent dir
                            # so there's no need to continue with the rest
                            r = move(root, dst, d['type'], title, cp, dry_run)
                            if verbose or "skipped" not in r:
                                print("{}: {}".format(r, root.split("/")[-1]))

                            break
                        else:
                            # We are moving a singular file, so we need to
                            # continue in the loop (no break)
                            src = os.path.join(root, f)
                            r = move(src, dst, d['type'], title, cp, dry_run)
                            if verbose:
                                print("{}: {}".format(r, src.split("/")[-1]))
                    else:
                        ignored.add(f)
            except KeyError:
                ignored.add(f)


    if verbose and False:
        print("Ignored files:")
        for ign in ignored:
            print("* {}".format(ign))

    # print("Found {} movie titles and {} shows".format(
    #     len(titles['movie']),
    #     len(titles['episode']))
    # )


def in_cache(name):
    try:
        with open(CACHE_FILE, 'r') as f:
            return name in [l.rstrip() for l in f]
    except FileNotFoundError:
        return False

def add_cache(name):
    mode = "a" if os.path.exists(CACHE_FILE) else "w"
    with open(CACHE_FILE, 'a') as f:
        f.write(name + "\n")

def move(src, dst, type, title, cp=False, dry_run=False):
    src2 = src.split('/')[-1]
    # to avoid spinning up platter disk
    if in_cache(src2):
        return Yellow + "skipped (cache)" + RESET_ALL

    # title = 'episode' or 'movie'. Adding s for plural.
    dst = os.path.join(dst, type + "s")
    if type == "episode":
        dst = os.path.join(dst, title)
    os.makedirs(dst, exist_ok=True)

    if not dry_run:
        if cp:
            if os.path.exists(os.path.join(dst, src2)):
                add_cache(src2)
                return Yellow + "skipped" + RESET_ALL
            # copy2 preserves metadata
            try:
                # if its a file
                shutil.copy2(src, dst)
                add_cache(src2)
                return Green + "copied" + RESET_ALL
            except IsADirectoryError:
                # if its a dir
                shutil.copytree(src, os.path.join(dst, src2))
                add_cache(src2)
                return Green + "copied" + RESET_ALL
        else:
            shutil.move(src, dst)
            return Green + "moved" + RESET_ALL

    if dry_run:
        # touch the basename to simulate some moving
        pathlib.Path(os.path.join(dst, os.path.basename(src))).touch()
        return "dry_run"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dst")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--cp", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if os.path.exists(RSYNC_LOCKFILE):
        print("{} exists, exiting")
        raise SystemExit(2)

    sort(args.src, args.dst, args.cp, args.dry_run, args.verbose)
