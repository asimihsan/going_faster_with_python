#!/usr/bin/env python

from __future__ import division

import os
import sys
import bz2
import contextlib
import re

# -------------------------------------------------------------------
#   Constants.
# -------------------------------------------------------------------
current_dir = os.path.abspath(os.path.join(__file__, os.pardir))
parent_dir = os.path.join(current_dir, os.pardir)
log_filepath = os.path.join(parent_dir, "utilities", "example.log.bz2")

re_log_line = re.compile("(.*?),(.*?),(.*)\n")
# -------------------------------------------------------------------

@profile
def main():
    cpu_usages = []
    with contextlib.closing(bz2.BZ2File(log_filepath)) as f_in:
        for line in f_in:
            process_line(line, cpu_usages)
    summarise(cpu_usages)

def summarise(cpu_usages):
    print "avg: %s" % (sum(cpu_usages) / len(cpu_usages), )

@profile
def process_line(line, cpu_usages):
    re_obj = re_log_line.search(line)
    try:
        elems = re_obj.groups()
    except:
        pass
    else:
        if elems[1] == "cpu_usage":
            cpu_usages.append(int(elems[2]))

if __name__ == "__main__":
    main()

