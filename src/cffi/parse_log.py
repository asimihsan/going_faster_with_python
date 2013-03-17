#!/usr/bin/env python

from __future__ import division

import os
import sys
import bz2
import contextlib

# -------------------------------------------------------------------
#   Constants.
# -------------------------------------------------------------------
current_dir = os.path.abspath(os.path.join(__file__, os.pardir))
parent_dir = os.path.join(current_dir, os.pardir)
log_filepath = os.path.join(parent_dir, "utilities", "example.log.bz2")
# -------------------------------------------------------------------

import _cffi_parse_log
process_line = _cffi_parse_log._make_ffi_process_line()

def main():
    with contextlib.closing(bz2.BZ2File(log_filepath)) as f_in:
        cpu_usages = map(process_line, f_in)
    summarise(cpu_usages)

def summarise(cpu_usages):
    print "avg: %s" % (sum(cpu_usages) / len(cpu_usages), )

if __name__ == "__main__":
    main()

