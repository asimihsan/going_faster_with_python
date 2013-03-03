#!/usr/bin/env python

from __future__ import division

import os
import sys
import subprocess
import psutil
from optparse import OptionParser
import signal
import time
from collections import namedtuple
import scipy.stats as stats
import numpy

from twisted.internet import protocol, reactor
from twisted.internet.task import LoopingCall

from pprinttable import pprinttable

# ------------------------------------------------------------------
#   Constants.
# ------------------------------------------------------------------
DEFAULT_RUNCOUNT = 5
APP_NAME = "measureproc"
# ------------------------------------------------------------------

# -----------------------------------------------------------------------------
#   Logging.
# -----------------------------------------------------------------------------
import logging
import logging.handlers
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)
# -----------------------------------------------------------------------------

class RunMeasurement(object):
    __slots__ = ('rss_max', 'user', 'system', 'clock')

    def __init__(self, rss_max=None, user=None, system=None, clock=None):
        self.rss_max = rss_max
        self.user = user
        self.system = system
        self.clock = clock

    def __str__(self):
        return "RunMeasurement {rss_max=%s, user=%s, system=%s, clock=%s}" % \
            (self.rss_max, self.user, self.system, self.clock)

    def __repr__(self):
        return str(self)

def summarise_results(results):
    Row = namedtuple('Row', ['metric', 'min', 'Q1', 'median', 'Q2', 'max'])
    table_data = []
    for metric in ["clock", "user", "system", "rss_max"]:
        data = [getattr(datum, metric) for datum in results]
        minimum = min(data)
        percentile_25 = stats.scoreatpercentile(data, 25)
        median = stats.scoreatpercentile(data, 50)
        percentile_75 = stats.scoreatpercentile(data, 25)
        maximum = max(data)
        format_string = "%.2f"
        table_data.append(Row(metric = metric,
                              min = format_string  % minimum,
                              Q1 = format_string % percentile_25,
                              median = format_string % median,
                              Q2 = format_string % percentile_75,
                              max = format_string % maximum))
    print "Summary of %s runs" % len(results)
    pprinttable(table_data)

class MeasureProtocol(protocol.ProcessProtocol):
    INTERVAL = 0.1

    def __init__(self,
                 args = None,
                 current_iteration = 1,
                 maximum_iterations = DEFAULT_RUNCOUNT,
                 measurements = None):
        self.args = args
        if not measurements:
            self.measurements = []
        else:
            self.measurements = measurements
        self.current_iteration = current_iteration
        self.maximum_iterations = maximum_iterations
        self.run_measurement = None

    def connectionMade(self):
        # Process starting.
        self.start = time.time()
        self.process_obj = psutil.Process(self.transport.pid)
        self.measure_call = LoopingCall(self.measure)
        self.measure_call.start(self.INTERVAL)

    def measure(self):
        try:
            cpu_times = self.process_obj.get_cpu_times()
            user = cpu_times.user
            system = cpu_times.system
            memory_info = self.process_obj.get_memory_info()
            rss = memory_info.rss / (1024 * 1024)
        except psutil.error.AccessDenied:
            pass
        else:
            if not self.run_measurement:
                self.run_measurement = RunMeasurement()
            self.run_measurement.user = user
            self.run_measurement.system = system
            self.run_measurement.rss_max = max(self.run_measurement.rss_max, rss)

    def outReceived(self, data):
        logger.debug("[stdout] %s" % data.strip())

    def errReceived(self, data):
        logger.debug("[stderr] %s" % data.strip())

    def processEnded(self, status):
        # Process stopping.
        if hasattr(self, "measure_call") and self.measure_call:
            self.measure_call.stop()
        self.stop = time.time()
        self.run_measurement.clock = self.stop - self.start
        self.measurements.append(self.run_measurement)
        logger.debug("[%s] measurement: %s" % (self.current_iteration, self.run_measurement))

        if self.current_iteration >= self.maximum_iterations:
            summarise_results(self.measurements)
            reactor.stop()
        else:
            measure_protocol = MeasureProtocol(args = self.args,
                                               current_iteration = self.current_iteration + 1,
                                               maximum_iterations = self.maximum_iterations,
                                               measurements = self.measurements)
            reactor.spawnProcess(measure_protocol, self.args[0], self.args)

def parse_args():
    usage = "measureproc.py scriptfile [arg] ..."
    parser = OptionParser(usage=usage)
    parser.allow_interspersed_args = False
    parser.add_option("-v", action="store_true", default=False, dest="verbose")
    (options, args) = parser.parse_args()
    return (parser, options, args)

def main():
    (parser, options, args) = parse_args()
    if len(args) == 0:
        parser.print_usage()
        sys.exit(1)
    if options.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("verbose logging enabled.")

    # ---------------------------------------------------------------
    #   Terminate the Twisted reactor on a signal.
    # ---------------------------------------------------------------
    def signal_handler(signum, stackframe):
        reactor.callFromThread(reactor.stop)
    signal.signal(signal.SIGINT, signal_handler)
    # ---------------------------------------------------------------

    # ---------------------------------------------------------------
    #   Spawn the process specified when the reactor starts.
    #
    #   We want to run it up to the run count, and after the final
    #   iteration summarise the findings.
    # ---------------------------------------------------------------
    measure_protocol = MeasureProtocol(args = args)
    reactor.spawnProcess(measure_protocol, args[0], args)
    # ---------------------------------------------------------------

    reactor.run()

if __name__ == "__main__":
    main()
