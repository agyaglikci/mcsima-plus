#!/usr/bin/python

from optparse import OptionParser
from subprocess import Popen
import os, sys, re, string, fpformat, math, subprocess, time

usage  = "usage: %prog [options]"
parser = OptionParser(usage)


parser.add_option("--infile", action="store", type="string", default="in.py", dest="infile",
                  help="input file, default = in.py")
parser.add_option("--max_active_process", action="store", type="int", default=4, dest="max_active_process",
                  help="maximum active process, default = 4")
parser.add_option("--base_dir", action="store", type="string", default="", dest="base_dir",
                  help="baseline directory, default = ")
parser.add_option("--common_prefix", action="store", type="string", default="pinbin -t mypthreadtool -mdfile", dest="common_prefix",
                  help="common prefix of each pin run, default = pinbin -t mypthreadtool -mdfile")
(options, args) = parser.parse_args()


try:
  infile = open(options.infile, 'r')
except IOError:
  print "cannot open " + options.infile
  sys.exit()


active_processes = []
cmd_cwd = ''
out_dir = ''
base_dir = options.base_dir

while True:
  # first, check if we have enough processes
  #for process in active_processes:
  try:
    for process in active_processes[:]:
      if process.poll() != None:
        active_processes.remove(process)
        print "Process [pid = " + str(process.pid) + "] finished"

    while len(active_processes) < options.max_active_process and infile.closed == False:
      line = infile.readline()
      temp = re.split('\s*', line)

      if len(line) == 0:
        infile.close()
        break
      elif len(temp) <= 0 or len(line) <= 1 or string.find(line, '#') >= 0:
        continue
      elif line[0] != ' ':
        cmd_cwd = base_dir + temp[0]
        out_dir = base_dir + temp[1]
      else:
        cmd = line[string.find(line, temp[2]):]
        if cmd[-1] == '\n':
          cmd = cmd[:-1]
        cmd = options.common_prefix + cmd + ' > ' + out_dir + temp[1]
        active_processes.append(Popen([cmd], cwd=cmd_cwd, shell=True))
        print "Process [pid = "+str(active_processes[-1].pid)+"] started -- " + out_dir + temp[1]

    time.sleep(1)
    if len(active_processes) == 0:
      break

  except KeyboardInterrupt:
    os.killpg(os.getpgrp(), 9)
    for process in active_processes:
      print "Process [pid = " + str(process.pid) + "] killed"
      os.kill(process.pid, 9)
    sys.exit()

sys.exit()

