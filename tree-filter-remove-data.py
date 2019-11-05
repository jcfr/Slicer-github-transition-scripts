#!/usr/bin/env python3.5

import hashlib
import os
import shutil
import subprocess

from collections import OrderedDict


def main():

    with open('/tmp/candidates', 'r') as fp:
        candidates = fp.read().splitlines()

    removed_filename = 'GIT_MIGRATION_DATA_REMOVED.txt'
    shutil.copyfile('/tmp/' + removed_filename, removed_filename)

    removed_filenames = OrderedDict()
    with open(removed_filename, 'r') as fp:
        for line in fp.read().splitlines():
            removed_filenames[line.split("  ")[1]] = line.split("  ")[0]

    for candidate in candidates:

        if not os.path.exists(candidate) or os.path.isdir(candidate):

            # If candidate does NOT exist and is found in removed_filenames, remove it
            # as there is no need to keep track of it.
            if candidate in removed_filenames:
                del removed_filenames[candidate]

            continue

        with open(candidate, "rb") as f:
            bytes = f.read() # read entire file as bytes
            sha256 = hashlib.sha256(bytes).hexdigest();

        sha256_and_filename = sha256 + "  " + candidate
        removed_filenames[candidate] = sha256

        filename = os.path.split(candidate)[1]
        shutil.move(candidate, '/tmp/Slicer4Migration-extracted-data/' + filename + '_' + sha256)

    removed_filenames = OrderedDict(sorted(removed_filenames.items()))

    with open(removed_filename, 'w') as fp:
        for filename, sha256 in removed_filenames.items():
            fp.write(sha256 + "  " + filename + "\n")

    shutil.copyfile(removed_filename, '/tmp/' + removed_filename)

if __name__ == '__main__':
    main()

