#!/usr/bin/env python3

import argparse
import os

from guessit import guessit



def walk(src, dst):
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
                            move(root, dst, d['type'], title)
                            break
                        else:
                            # We are moving a singular file, so we need to
                            # continue in the loop (no break)
                            move(os.path.join(root, f), dst, d['type'], title)
                    else:
                        ignored.add(f)
            except KeyError:
                continue


    print("Found {} movie titles and {} shows".format(len(titles['movie']), len(titles['episode'])))


def move(src, dst, type, title):
    # title = 'episode' or 'movie'. Adding s for plural.
    dst = os.path.join(dst, type + "s")
    if type == "episode":
        dst = os.path.join(dst, title)
    #print("{} -> {}/".format(src, dst))
    os.makedirs(dst, exist_ok=True)

    # touch the basename to simulate some moving
    import pathlib
    print(os.path.basename(src))
    pathlib.Path(os.path.basename(src)).touch()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dst")
    args = parser.parse_args()

    walk(args.src, args.dst)
