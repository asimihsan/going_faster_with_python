import os
import sys
import bz2
from string import Template
import contextlib
import datetime
import random

# ------------------------------------------------------------------
#   Constants.
# ------------------------------------------------------------------
current_dir = os.path.abspath(os.path.join(__file__, os.pardir))
log_filepath = os.path.join(current_dir, "example.log.bz2")
log_line_template = Template("${epoch},${metric},${value}\n")
epoch = datetime.datetime(1970,1,1)
epoch_start = int((datetime.datetime.now() - epoch).total_seconds())
number_of_log_lines = 5 * 1000 * 1000
# ------------------------------------------------------------------

def main():
    with contextlib.closing(bz2.BZ2File(log_filepath, "w")) as f_out:
        current_epoch = epoch_start
        metric = "cpu_usage"
        for i in xrange(number_of_log_lines):
            line = log_line_template.substitute(epoch = current_epoch,
                                                metric = metric,
                                                value = random.randint(0, 100))
            f_out.write(line)
            current_epoch += 1

if __name__ == "__main__":
    main()
