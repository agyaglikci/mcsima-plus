#!/usr/bin/python

from optparse import OptionParser
from pinsim_log_parser import *
import sys, re, string, fpformat

usage = "usage: %prog [options]"
parser = OptionParser(usage)
parser.add_option("--mdfile", action="store", type="string", default="/dev/null", dest="mdfile",
                  help="specify the machine description file (default = /dev/null)")
parser.add_option("--logfile", action="store", type="string", default="md.out", dest="logfile",
                  help="specify the log file (default = md.out)")
parser.add_option("--ipcfile", action="store", type="string", default="/dev/null", dest="ipcfile",
                  help="specify the output ipc trace file (default = /dev/null)")
parser.add_option("--simple", action="store_true", dest="simple", default=False,
                  help="printout only IPC, Xbar BW, and MC BW")
parser.add_option("--ticks_per_cycle", action="store", type="string", default="80", dest="ticks_per_cycle",
                  help="specify the number of ticks per cycle (default = 80, valid only if mdfile == /dev/null")
(options, args) = parser.parse_args()

#md   = MD(options.mdfile, options.ticks_per_cycle)
md   = MD(options.logfile, options.ticks_per_cycle)
stat = Stat(md)
stat.parse(options.logfile, options.ipcfile)
if options.simple == True:
  edp = stat.compute_energydelay()
  stat.show_simple(str(edp[5]))
else:
  stat.show()

edp = stat.compute_energydelay()
print "EDP = " + str(edp[5])
