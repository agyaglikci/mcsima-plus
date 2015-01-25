#!/usr/bin/python

from optparse import OptionParser
from pinsim_log_parser import *
import os, sys, re, string, fpformat

usage  = "usage: %prog [options]"
parser = OptionParser(usage)

parser.add_option("--ticks_per_cycle", action="store", type="string", default="80", dest="ticks_per_cycle",
                  help="specify the number of ticks per cycle (default = 80)")
parser.add_option("--num_confs", action="store", type="string", default="4", dest="num_confs",
                  help="the number of configurations per app")
parser.add_option("--inputfile", action="store", type="string", default="input.list",  dest="inputfile",
                  help="input file specifying the location of the pin sim log files (default=input.list)")
parser.add_option("--outputprefix", action="store", type="string", default="out", dest="outputprefix",
                  help="the prefix of output eps files (default = out)")
parser.add_option("--chipkill", action="store_true", dest="chipkill", default=False,
                  help="apply chip kill memory power and energy numbers")
parser.add_option("--edpcomppostfix", action="store", type="string", default="", dest="edpcomppostfix",
                  help="energy-delay product comparison postfix (default = )")
(options, args) = parser.parse_args()



class LogList:
  def __init__(self, options):
    try:
      infile = open(options.inputfile, 'r')
    except IOError:
      print "cannot open "+options.inputfile
      sys.exit()

    self.num_apps          = 0
    self.num_confs_per_app = 0

    curr_app_class = ''
    curr_app       = ''
    curr_log       = ''
    curr_name      = ''
    curr_dir       = ''
    app_class      = []
    app            = []
    log            = []
    avg_only_app   = False
    for line in infile:
      if (line[0] != ' '):
        if len(app) > 0 and curr_app_class != '':
          app_class.append(curr_app_class)
          app_class.append(app)
          if avg_only_app == True:
            self.num_apps = self.num_apps + 1
          avg_only_app = False
        curr_app_class = line[:-1]
        app = []
      elif (line[1] != ' '):
        if len(log) > 0 and curr_app != '':
          app.append(curr_app)
          app.append(log)
        temp           = re.split('\s*', line[1:][:-1])
        curr_app       = temp[0]
        curr_dir       = temp[1]
        log = []
        if line[1] == '*':
          avg_only_app = True
        else:
          self.num_apps  = self.num_apps + 1
        self.num_confs_per_app = 0
      elif (line[2] != ' '):
        temp           = re.split('\s*', line[2:][:-1])
        curr_log       = curr_dir+temp[0]
        curr_md        = curr_dir+temp[1]
        stat           = Stat(MD(curr_md, 80))
        print curr_log
        stat.parse(curr_log, "/dev/null")
        compstat       = stat
        if options.edpcomppostfix != '' and stat.num_vmds_per_rank > 1:
          #comp_log = curr_dir+temp[0][:-4]+options.edpcomppostfix
          postfix_pos = temp[0].rfind('-')
          if temp[0][0:postfix_pos][-3:] == 'cfp':
            postfix_pos = postfix_pos - 4
          elif temp[0][0:postfix_pos][-4:] == 'cint':
            postfix_pos = postfix_pos - 5
          comp_log = curr_dir+temp[0][0:postfix_pos]+'-'+options.edpcomppostfix+temp[0][postfix_pos:]
          print comp_log
          compstat = Stat(MD(curr_md, 80))
          compstat.parse(comp_log, "/dev/null")
        log.append((curr_log, stat, compstat))
        self.num_confs_per_app = self.num_confs_per_app + 1

    if len(log) > 0 and curr_app != '':
      app.append(curr_app)
      app.append(log)
    if len(app) > 0 and curr_app_class != '':
      app_class.append(curr_app_class)
      app_class.append(app)

    self.class_app_log = app_class
    self.options       = options
    infile.close()


class StatList:
  def __init__(self, ll):  # ll = loglist
    self.ll = ll
    i = 0
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0
      while j < len(apps):
        app_name = apps[j]
        j = j + 1
        logs     = apps[j]
        j = j + 1
        for log in logs:
          print "----"
          print class_name + " / " + app_name + " / " + log[0] + " / " + str(log[1].num_vmds_per_rank)
          print "----"
          stat = Stat(80)
          stat.parse(log[0], "/dev/null")


class GnuplotDat:
  def __init__(self, ll):  # ll = loglist
    self.ll = ll

  def generate_ipc(self, chipkill = False):
    dat = ""
    
    i = 0
    array = []
    while i < self.ll.num_confs_per_app:
      per_conf = []
      per_conf.append("\"      \"")
      #if chipkill == False:
      #  if i == 0:
      #    per_conf.append("\"  {/Helvetica=11 noPD}\"")
      #  else:
      #    per_conf.append("\"  {/Helvetica=11 "+str(self.ll.class_app_log[1][1][i][1].num_vmds_per_rank)+"set}\"")
      #else:
      #  if i == 0:
      #    per_conf.append("\"  {/Helvetica=11 noPD}\"")
      #  elif self.ll.class_app_log[1][1][i][1].vmd_page_sz == '65536':
      #    per_conf.append("\"  {/Helvetica=11 36x4}\"")
      #  elif self.ll.class_app_log[1][1][i][1].vmd_page_sz == '16384':
      #    per_conf.append("\"  {/Helvetica=11 11x4}\"")
      #  else:
      #    per_conf.append("\"  {/Helvetica=11 7x8}\"")
      array.append(per_conf)
      i = i + 1

    i = 0
    num_apps = 0
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0

      k = 0
      ipc_sum = []
      avg_rd_latency_sum = []
      while k < self.ll.num_confs_per_app:
        k = k + 1
        ipc_sum.append(0.0)
        avg_rd_latency_sum.append(0.0)

      while j < len(apps):
        app_name = apps[j]
        j = j + 1
        logs     = apps[j]
        j = j + 1
        k = 0
        for log in logs:
          stat = log[1]
          if stat.num_ticks == 0:
            print app_name, log[0]
          curr_ipc  = 1.0*stat.num_instrs*stat.ticks_per_cycle/stat.num_ticks 
          curr_avg_rd_latency = 1.0*stat.total_mem_rd_time/stat.num_L1D_rd_accs/stat.ticks_per_cycle*16/24
          ipc_sum[k] = ipc_sum[k] + curr_ipc
          avg_rd_latency_sum[k] = avg_rd_latency_sum[k] + curr_avg_rd_latency
          if app_name[0] != '*':
            array[k].append(curr_ipc)  #IPC
            array[k].append(curr_avg_rd_latency) # average RD latency  -- y2 axis is scaled-down 
            array[k].append(k + (1 + self.ll.num_confs_per_app)*num_apps)
          k = k + 1
        if app_name[0] != '*':
          num_apps = num_apps + 1

      k = 0
      while k < self.ll.num_confs_per_app:
        array[k].append(ipc_sum[k]*2/len(apps))  #IPC
        array[k].append(avg_rd_latency_sum[k]*2/len(apps)) # average RD latency  -- y2 axis is scaled-down 
        array[k].append(k + (1 + self.ll.num_confs_per_app)*num_apps)
        k = k + 1
      num_apps = num_apps + 1
        

    for row in array:
      for element in row:
        dat = dat + str(element) + " "
      dat = dat + "\n"

    self.ipc_gnuplot_dat_str = dat

  def generate_energydelay(self, chipkill = False):
    dat = ""

    i = 0
    array = []
    while i < self.ll.num_confs_per_app:
      per_conf = []
      per_conf.append("\"      \"")
      #if chipkill == False:
      #  if i == 0:
      #    per_conf.append("\"  {/Helvetica=11 noPD}\"")
      #  else:
      #    per_conf.append("\"  {/Helvetica=11 "+str(self.ll.class_app_log[1][1][i][1].num_vmds_per_rank)+"set}\"")
      #else:
      #  if i == 0:
      #    per_conf.append("\"  {/Helvetica=11 noPD}\"")
      #  elif self.ll.class_app_log[1][1][i][1].vmd_page_sz == '65536':
      #    per_conf.append("\"  {/Helvetica=11 36x4}\"")
      #  elif self.ll.class_app_log[1][1][i][1].vmd_page_sz == '16384':
      #    per_conf.append("\"  {/Helvetica=11 11x4}\"")
      #  else:
      #    per_conf.append("\"  {/Helvetica=11 7x8}\"")
      array.append(per_conf)
      i = i + 1

    i = 0
    num_apps = 0
    
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0

      k = 0
      cpu_power_sum   = []
      mem_standby_sum = []
      mem_refresh_sum = []
      mem_dynamic_sum = []
      mem_io_sum      = []
      edp_sum         = []
      while k < self.ll.num_confs_per_app:
        k = k + 1
        cpu_power_sum.append(0.0)
        mem_standby_sum.append(0.0)
        mem_refresh_sum.append(0.0)
        mem_dynamic_sum.append(0.0)
        mem_io_sum.append(0.0)
        edp_sum.append(0.0)

      while j < len(apps):
        app_name = apps[j]
        j = j + 1
        logs     = apps[j]
        j = j + 1
        k = 0
        energy_delay = 0
        for log in logs:
          set = log[1].compute_energydelay(chipkill)
          cpu_power_sum[k] = cpu_power_sum[k] + set[0]
          mem_standby_sum[k] = mem_standby_sum[k] + set[1]
          mem_refresh_sum[k] = mem_refresh_sum[k] + set[2]
          mem_dynamic_sum[k] = mem_dynamic_sum[k] + set[3]
          mem_io_sum[k]      = mem_io_sum[k]      + set[4]
          if app_name[0] != '*':
            array[k].append(set[0])  # cpu power
            array[k].append(set[1])  # memory standby power
            array[k].append(set[2])  # memory refresh power
            array[k].append(set[3])  # memory dynamic power
            array[k].append(set[4])  # memory I/O     power
          if energy_delay == 0:
            energy_delay = set[5]
          edp_sum[k] = edp_sum[k] + (set[5]/energy_delay*50.0)
          print k, app_name, set[0], set[1], set[2], set[3], set[4], set[5]/energy_delay
          if app_name[0] != '*':
            array[k].append(set[5]/energy_delay*50.0)
            array[k].append(k + (1 + self.ll.num_confs_per_app)*num_apps)
          k = k + 1
        if app_name[0] != '*':
          num_apps = num_apps + 1

      k = 0
      while k < self.ll.num_confs_per_app:
        array[k].append(cpu_power_sum[k]*2/len(apps))
        array[k].append(mem_standby_sum[k]*2/len(apps))
        array[k].append(mem_refresh_sum[k]*2/len(apps))
        array[k].append(mem_dynamic_sum[k]*2/len(apps))
        array[k].append(mem_io_sum[k]*2/len(apps))
        array[k].append(edp_sum[k]*2/len(apps))
        array[k].append(k + (1 + self.ll.num_confs_per_app)*num_apps)
        k = k + 1
      num_apps = num_apps + 1
        
    for row in array:
      for element in row:
        dat = dat + str(element) + " "
      dat = dat + "\n"

    self.energydelay_gnuplot_dat_str = dat

  def generate_mempower(self, chipkill = False):
    dat = ""
    y2scale = 25
    if chipkill == True:
      y2scale = 40

    i = 0
    array = []
    while i < self.ll.num_confs_per_app:
      per_conf = []
      per_conf.append("\"      \"")
      #if chipkill == False:
      #  if i == 0:
      #    per_conf.append("\"  {/Helvetica=11 noPD}\"")
      #  else:
      #    per_conf.append("\"  {/Helvetica=11 "+str(self.ll.class_app_log[1][1][i][1].num_vmds_per_rank)+"set}\"")
      #else:
      #  if i == 0:
      #    per_conf.append("\"  {/Helvetica=11 noPD}\"")
      #  elif self.ll.class_app_log[1][1][i][1].vmd_page_sz == '65536':
      #    per_conf.append("\"  {/Helvetica=11 36x4}\"")
      #  elif self.ll.class_app_log[1][1][i][1].vmd_page_sz == '16384':
      #    per_conf.append("\"  {/Helvetica=11 11x4}\"")
      #  else:
      #    per_conf.append("\"  {/Helvetica=11 7x8}\"")
      array.append(per_conf)
      i = i + 1

    i = 0
    num_apps = 0
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0

      k = 0
      cpu_power_sum   = []
      mem_standby_sum = []
      mem_refresh_sum = []
      mem_dynamic_sum = []
      mem_io_sum      = []
      pdp_sum         = []
      while k < self.ll.num_confs_per_app:
        k = k + 1
        cpu_power_sum.append(0.0)
        mem_standby_sum.append(0.0)
        mem_refresh_sum.append(0.0)
        mem_dynamic_sum.append(0.0)
        mem_io_sum.append(0.0)
        pdp_sum.append(0.0)

      while j < len(apps):
        app_name = apps[j]
        j = j + 1
        logs     = apps[j]
        j = j + 1
        k = 0
        for log in logs:
          set = log[1].compute_energydelay(chipkill)
          cpu_power_sum[k]   = cpu_power_sum[k] + set[0]
          mem_standby_sum[k] = mem_standby_sum[k] + set[1]
          mem_refresh_sum[k] = mem_refresh_sum[k] + set[2]
          mem_dynamic_sum[k] = mem_dynamic_sum[k] + set[3]
          mem_io_sum[k]      = mem_io_sum[k]      + set[4]
          pdp_sum[k]         = pdp_sum[k]         + set[6]*y2scale
          if app_name[0] != '*':
            array[k].append(set[0])  # cpu power
            array[k].append(set[1])  # memory standby power
            array[k].append(set[2])  # memory refresh power
            array[k].append(set[3])  # memory dynamic power
            array[k].append(set[4])  # memory I/O     power
            array[k].append(set[6]*y2scale)  # memory power down percentage
            array[k].append(k + (1 + self.ll.num_confs_per_app)*num_apps)
          k = k + 1
        if app_name[0] != '*':
          num_apps = num_apps + 1

      k = 0
      while k < self.ll.num_confs_per_app:
        array[k].append(cpu_power_sum[k]*2/len(apps))
        array[k].append(mem_standby_sum[k]*2/len(apps))
        array[k].append(mem_refresh_sum[k]*2/len(apps))
        array[k].append(mem_dynamic_sum[k]*2/len(apps))
        array[k].append(mem_io_sum[k]*2/len(apps))
        array[k].append(pdp_sum[k]*2/len(apps))
        array[k].append(k + (1 + self.ll.num_confs_per_app)*num_apps)
        k = k + 1
      num_apps = num_apps + 1
        
    for row in array:
      for element in row:
        dat = dat + str(element) + " "
      dat = dat + "\n"

    self.mempower_gnuplot_dat_str = dat

  def generate_edpcomp(self, chipkill = False):
    dat = ""
    
    i = 0
    array = []
    while i < self.ll.num_confs_per_app:
      per_conf = []
      per_conf.append("\"      \"")
      #if chipkill == False:
      #  if i == 0:
      #    per_conf.append("\"  {/Helvetica=11 noPD}\"")
      #  else:
      #    per_conf.append("\"  {/Helvetica=11 "+str(self.ll.class_app_log[1][1][i][1].num_vmds_per_rank)+"set}\"")
      #else:
      #  per_conf.append("\"  {/Helvetica=11 conf"+str(i+1)+"}\"")
      array.append(per_conf)
      i = i + 1

    i = 0
    num_apps = 0
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0

      k = 0
      relativeEDP_sum = []
      while k < self.ll.num_confs_per_app:
        k = k + 1
        relativeEDP_sum.append(0.0)

      while j < len(apps):
        app_name = apps[j]
        j = j + 1
        logs     = apps[j]
        j = j + 1
        k = 0
        for log in logs:
          stat = log[1]
          compstat = log[2]
          if stat.num_ticks == 0 or compstat.num_ticks == 0:
            print app_name, log[0]
          edp = (stat.compute_energydelay(chipkill))[5]
          compedp = (compstat.compute_energydelay(chipkill))[5]
          relativeEDP_sum[k] = relativeEDP_sum[k] + 10*(edp-compedp)/edp
          if app_name[0] != '*':
            array[k].append(10*(edp-compedp)/edp)  #IPC
            array[k].append(k + (1 + self.ll.num_confs_per_app)*num_apps)
          k = k + 1
        if app_name[0] != '*':
          num_apps = num_apps + 1

      k = 0
      while k < self.ll.num_confs_per_app:
        array[k].append(relativeEDP_sum[k]*2/len(apps))  #IPC
        array[k].append(k + (1 + self.ll.num_confs_per_app)*num_apps)
        k = k + 1
      num_apps = num_apps + 1
        

    for row in array:
      for element in row:
        dat = dat + str(element) + " "
      dat = dat + "\n"

    self.edpcomp_gnuplot_dat_str = dat


class GnuplotCmd:
  def __init__(self, ll):  # ll = loglist
    self.ll = ll

  def generate_ipc(self, datfile_name, epsfile_name, chipkill = False):
    cmd = ""
    if chipkill == False:
      cmd = cmd + "set terminal postscript eps enhanced color \"Helvetica,11\" size 5.3in, 1.3in\n"
    else:
      cmd = cmd + "set terminal postscript eps enhanced color \"Helvetica,11\" size 5.3in, 1.3in\n"
    cmd = cmd + "set output \"" + epsfile_name + "\"\n"

    i = 0
    num_apps = 0
    num_apps_so_far_per_class = 0
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0
      while j < len(apps):
        app_name = apps[j]
        j = j + 2
        if app_name[0] != '*':
          cmd = cmd + "set label \"noPD\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)) + ", -0.5 rotate by 90 right\n"
          if chipkill is False:
            cmd = cmd + "set label \"1set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -0.5 rotate by 90 right\n"
            cmd = cmd + "set label \"2set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -0.5 rotate by 90 right\n"
            cmd = cmd + "set label \"4set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -0.5 rotate by 90 right\n"
            cmd = cmd + "set label \"8set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+4) + ", -0.5 rotate by 90 right\n"
          else:
            cmd = cmd + "set label \"36x4\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -0.5 rotate by 90 right\n"
            cmd = cmd + "set label \"11x4\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -0.5 rotate by 90 right\n"
            cmd = cmd + "set label \"7x8\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -0.5 rotate by 90 right\n"
          num_apps = num_apps + 1
      
      cmd = cmd + "set label \"noPD\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)) + ", -0.5 rotate by 90 right\n"
      if chipkill is False:
        cmd = cmd + "set label \"1set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -0.5 rotate by 90 right\n"
        cmd = cmd + "set label \"2set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -0.5 rotate by 90 right\n"
        cmd = cmd + "set label \"4set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -0.5 rotate by 90 right\n"
        cmd = cmd + "set label \"8set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+4) + ", -0.5 rotate by 90 right\n"
      else:
        cmd = cmd + "set label \"36x4\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -0.5 rotate by 90 right\n"
        cmd = cmd + "set label \"11x4\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -0.5 rotate by 90 right\n"
        cmd = cmd + "set label \"7x8\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -0.5 rotate by 90 right\n"
      num_apps = num_apps + 1
      if i < len(self.ll.class_app_log):
        cmd = cmd + "set arrow from " + str((self.ll.num_confs_per_app + 1)*num_apps - 1) + ",0 rto 0, -8 nohead\n"
      cmd = cmd + "set label \"" + class_name + "\" at " + str((self.ll.num_confs_per_app + 1)*(num_apps + num_apps_so_far_per_class - 1)/2) + ", -7.5\n"
      num_apps_so_far_per_class = num_apps

    cmd = cmd + "set arrow from -1,0 rto 0,-8 nohead\n"
    cmd = cmd + "set arrow from "+str(num_apps*(self.ll.num_confs_per_app + 1) - 1) + ",0 rto 0,-8 nohead\n"
    cmd = cmd + "set style histogram rowstacked\n"
    cmd = cmd + "set boxwidth 0.7 relative\n"
    cmd = cmd + "set style data histogram\n"
    cmd = cmd + "set xtics rotate by 90\n"
    cmd = cmd + "set tics nomirror\n"
    cmd = cmd + "set ytics out 0, 1, 10\n"
    cmd = cmd + "set border 11\n"
    cmd = cmd + "set y2label \"Cycle\"\n"
    cmd = cmd + "set xrange [ -1 : " + str(num_apps*(self.ll.num_confs_per_app + 1)-1) + " ]\n"
    #cmd = cmd + "set key enhanced top center vertical samplen 2\n"
    cmd = cmd + "set key horizontal at 40,17 samplen 2\n"
    cmd = cmd + "set yrange [ 0 : 16 ]\n"
    cmd = cmd + "set ylabel \"IPC\"\n"
    cmd = cmd + "set y2tics out\n"
    cmd = cmd + "# since we avg_rd_latency must be scaled\n"
    cmd = cmd + "set y2tics (\"0\" 0, \"3\" 2, \"6\" 4, \"9\" 6, \"12\" 8, \"15\" 10, \"18\" 12, \"21\" 14, \"24\" 16)\n"
    cmd = cmd + "set ytics  (\"0\" 0, \"2\" 2, \"4\" 4, \"6\" 6, \"8\" 8, \"10\" 10, \"12\" 12, \"14\" 14, \"16\" 16)\n"

    cmd = cmd + "set style line 3 lt -1 lc rgbcolor \"#ffffff\" pointtype 13 pointsize 0.7\n"
    cmd = cmd + "set style line 2 lt -1 lc rgbcolor \"#000000\" pointtype 13 pointsize 1.2\n"
    cmd = cmd + "set multiplot\n"
    cmd = cmd + "unset key\n"

    cmd = cmd + "plot "

    idx = 2
    i = 0
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0
      while j <= len(apps):
        if j == len(apps):
          app_name = 'average'
          j = j + 1
        else:
          app_name = apps[j]
          j = j + 1
          logs     = apps[j]
          j = j + 1

        if app_name[0] != '*':
          cmd = cmd + "newhistogram \"" + app_name + "\", '" + datfile_name + "' using "
          cmd = cmd + str(idx) + ":xtic(1) "
          if idx == 2:
            cmd = cmd + " title \"IPC\" "
          else: 
            cmd = cmd + " notitle "
          cmd = cmd + "with histogram fs solid 0.3 border -1 lt -1, \\\n"
          cmd = cmd + "                  '' using " + str(idx+2) + ":" + str(idx+1)
          if idx == 2:
            cmd = cmd + " title \"average read latency\" "
          else:
            cmd = cmd + " notitle "
          cmd = cmd + "with linespoints ls 2, \\\n"
          cmd = cmd + "                  '' using " + str(idx+2) + ":" + str(idx+1)
          cmd = cmd + " notitle with points ls 3"
          if j <= len(apps) or i < len(self.ll.class_app_log):
            cmd = cmd + ", \\\n"
          else:
            cmd = cmd + "\n"
          idx = idx + 3

    cmd = cmd + "unset xtics\n"
    cmd = cmd + "unset ytics\n"
    cmd = cmd + "unset y2tics\n"
    cmd = cmd + "set border 0\n"
    cmd = cmd + "unset xlabel\n"
    cmd = cmd + "unset ylabel\n"
    cmd = cmd + "unset y2label\n"
    cmd = cmd + "unset label\n"
    cmd = cmd + "unset arrow\n"
    cmd = cmd + "set key horiz nobox at .70,1.07\n"
    cmd = cmd + "set xrange [0:1]\n"
    cmd = cmd + "set yrange [0:1]\n"
    cmd = cmd + "plot x*0-1000 title \"IPC\" with filledcu fs solid 0.3 border -1 lt -1, \\\n"
    cmd = cmd + "     x*0-1000 title \"average read latency\" with linesp ls 2\n"

    self.ipc_gnuplot_cmd_str = cmd

  def generate_energydelay(self, datfile_name, epsfile_name, chipkill = False):
    cmd = ""
    if chipkill == True:
      cmd = cmd + "set terminal postscript eps enhanced color \"Helvetica,11\" size 5.3in, 1.8in\n"
    else:
      cmd = cmd + "set terminal postscript eps enhanced color \"Helvetica,11\" size 5.3in, 1.8in\n"
    cmd = cmd + "set output \"" + epsfile_name + "\"\n"

    i = 0
    num_apps = 0
    num_apps_so_far_per_class = 0
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0
      while j < len(apps):
        app_name = apps[j]
        j = j + 2
        if app_name[0] != '*':
          cmd = cmd + "set label \"noPD\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)) + ", -2 rotate by 90 right\n"
          if chipkill is False:
            cmd = cmd + "set label \"1set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -2 rotate by 90 right\n"
            cmd = cmd + "set label \"2set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -2 rotate by 90 right\n"
            cmd = cmd + "set label \"4set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -2 rotate by 90 right\n"
            cmd = cmd + "set label \"8set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+4) + ", -2 rotate by 90 right\n"
          else:
            cmd = cmd + "set label \"36x4\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -2 rotate by 90 right\n"
            cmd = cmd + "set label \"11x4\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -2 rotate by 90 right\n"
            cmd = cmd + "set label \"7x8\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -2 rotate by 90 right\n"
          num_apps = num_apps + 1
      
      cmd = cmd + "set label \"noPD\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)) + ", -2 rotate by 90 right\n"
      if chipkill is False:
        cmd = cmd + "set label \"1set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -2 rotate by 90 right\n"
        cmd = cmd + "set label \"2set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -2 rotate by 90 right\n"
        cmd = cmd + "set label \"4set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -2 rotate by 90 right\n"
        cmd = cmd + "set label \"8set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+4) + ", -2 rotate by 90 right\n"
      else:
        cmd = cmd + "set label \"36x4\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -2 rotate by 90 right\n"
        cmd = cmd + "set label \"11x4\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -2 rotate by 90 right\n"
        cmd = cmd + "set label \"7x8\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -2 rotate by 90 right\n"
      num_apps = num_apps + 1
      if i < len(self.ll.class_app_log):
        cmd = cmd + "set arrow from " + str((self.ll.num_confs_per_app + 1)*num_apps - 1) + ",0 rto 0, -28 nohead\n"
      cmd = cmd + "set label \"" + class_name + "\" at " + str((self.ll.num_confs_per_app + 1)*(num_apps + num_apps_so_far_per_class - 1)/2) + ", -24\n"
      num_apps_so_far_per_class = num_apps

    cmd = cmd + "set arrow from -1,0 rto 0,-28 nohead\n"
    cmd = cmd + "set arrow from "+str(num_apps*(self.ll.num_confs_per_app + 1) - 1) + ",0 rto 0,-27 nohead\n"
    cmd = cmd + "set style histogram rowstacked\n"
    cmd = cmd + "set boxwidth 0.7 relative\n"
    cmd = cmd + "set style data histogram\n"
    cmd = cmd + "set xtics rotate by 90\n"
    cmd = cmd + "set tics nomirror\n"
#    if chipkill == False:
    cmd = cmd + "set ytics out 0, 10, 90\n"
    cmd = cmd + "set key at 40,82 samplen 2\n"
    cmd = cmd + 'set y2tics ("0.0" 0, "0.2" 10, "0.4" 20, "0.6" 30, "0.8" 40, "1.0" 50, "1.2" 60, "1.4" 70, "1.6" 80)\n'
    cmd = cmd + "set yrange [ 0 : 82 ]\n"
#    else:
#      cmd = cmd + "set ytics out 0, 10, 100\n"
#      cmd = cmd + "set key at 40,102 samplen 2\n"
#      cmd = cmd + 'set y2tics ("0.0" 0, "0.2" 10, "0.4" 20, "0.6" 30, "0.8" 40, "1.0" 50, "1.2" 60, "1.4" 70, "1.6" 80)\n'
#      cmd = cmd + "set yrange [ 0 : 100 ]\n"

    cmd = cmd + "set border 11\n"
    cmd = cmd + "#set y2tics out 0, 20, 40 textcolor rgbcolor \"#FFFFFF\"\n"
    cmd = cmd + "set y2label \"Normalized energy*delay\"\n"
    cmd = cmd + "set xrange [ -1 : " + str(num_apps*(self.ll.num_confs_per_app + 1)-1) + " ]\n"
    cmd = cmd + "#set key enhanced autotitles columnhead box horizontal samplen 1\n"
    #cmd = cmd + "set key enhanced top right vertical samplen 2\n"
    cmd = cmd + "set ylabel \"System power (W)\"\n"
    cmd = cmd + "set y2tics out\n"
    cmd = cmd + "# since we avg_rd_latency must be scaled\n"
    #cmd = cmd + "unset key\n"
    cmd = cmd + "set grid y2tics back linetype 3 linewidth 2 linecolor \"#888888\", linewidth 0\n"
    cmd = cmd + "show grid\n"

    cmd = cmd + "set style line 3 lt -1 lc rgbcolor \"#bcf37c\" pointtype 13 pointsize 0.8\n"
    cmd = cmd + "set style line 2 lt -1 lc rgbcolor \"#000000\" pointtype 13 pointsize 1.4\n"
    cmd = cmd + "set style line 5 lt -1 lc rgbcolor \"#cccccc\" pointtype 16 pointsize 0.4\n"
    cmd = cmd + "set style line 4 lt -1 lc rgbcolor \"#000000\" pointtype 16 pointsize 0.8\n"
    cmd = cmd + "set multiplot\n"
    cmd = cmd + "unset key\n"

    cmd = cmd + "plot "

    idx = 2
    i = 0
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0
      while j <= len(apps):
        if j == len(apps):
          app_name = 'average'
          j = j + 1
        else:
          app_name = apps[j]
          j = j + 1
          logs     = apps[j]
          j = j + 1

        if app_name[0] != '*':
          cmd = cmd + "newhistogram \"" + app_name + "\", '" + datfile_name + "' using "
          cmd = cmd + str(idx) + ":xtic(1) "
          if idx == 2:
            cmd = cmd + " title \"processor\" "
          else: 
            cmd = cmd + " notitle "
          cmd = cmd + "with histogram fs solid 1 border -1 lt rgbcolor \"#0071b4\", \\\n"
          cmd = cmd + "                  '' using " + str(idx+1)
          if idx == 2:
            cmd = cmd + " title \"standby\" "
          else:
            cmd = cmd + " notitle "
          cmd = cmd + "with histograms fs solid 1 border -1 lt rgbcolor \"#ffffff\", \\\n"
          cmd = cmd + "                  '' using " + str(idx+2)
          if idx == 2:
            cmd = cmd + " title \"refresh\" "
          else:
            cmd = cmd + " notitle "
          cmd = cmd + "with histograms fs solid 1 border -1 lt rgbcolor \"#fdc643\", \\\n"
          cmd = cmd + "                  '' using " + str(idx+3)
          if idx == 2:
            cmd = cmd + " title \"access\" "
          else:
            cmd = cmd + " notitle "
          cmd = cmd + "with histograms fs solid 1 border -1 lt rgbcolor \"#b01c13\", \\\n"
          cmd = cmd + "                  '' using " + str(idx+4)
          if idx == 2:
            cmd = cmd + " title \"I/O\" "
          else:
            cmd = cmd + " notitle "
          cmd = cmd + "with histograms fs solid 1 border -1 lt rgbcolor \"#000000\", \\\n"
          cmd = cmd + "                  '' using " + str(idx+6) + ":" + str(idx+5)
          if idx == 2:
            cmd = cmd + " title \"normalized system energy*delay\" "
          else:
            cmd = cmd + " notitle "
          cmd = cmd + "with linespoints ls 2, \\\n"
          cmd = cmd + "                  '' using " + str(idx+6) + ":" + str(idx+5)
          cmd = cmd + " notitle with points ls 3"
          if j <= len(apps) or i < len(self.ll.class_app_log):
            cmd = cmd + ", \\\n"
          else:
            cmd = cmd + "\n"
          idx = idx + 7

    cmd = cmd + "unset xtics\n"
    cmd = cmd + "unset ytics\n"
    cmd = cmd + "unset y2tics\n"
    cmd = cmd + "set border 0\n"
    cmd = cmd + "unset xlabel\n"
    cmd = cmd + "unset ylabel\n"
    cmd = cmd + "unset y2label\n"
    cmd = cmd + "unset label\n"
    cmd = cmd + "unset arrow\n"
    cmd = cmd + "set key horiz nobox at .72,1.05\n"
    cmd = cmd + "set xrange [0:1]\n"
    cmd = cmd + "set yrange [0:1]\n"
    cmd = cmd + "plot x*0-1000 title \"processor\" with filledcu fs solid 1 border -1 lt rgbcolor \"#0071b4\", \\\n"
    cmd = cmd + "     x*0-1000 title \"standby\" with filledcu fs solid 1 border -1 lt rgbcolor \"#ffffff\", \\\n"
    cmd = cmd + "     x*0-1000 title \"refresh\" with filledcu fs solid 1 border -1 lt rgbcolor \"#fdc643\", \\\n"
    cmd = cmd + "     x*0-1000 title \"access\" with filledcu fs solid 1 border -1 lt rgbcolor \"#b01c13\", \\\n"
    cmd = cmd + "     x*0-1000 title \"I/O\" with filledcu fs solid 1 border -1 lt rgbcolor \"#000000\"\n"
    cmd = cmd + "set key horiz nobox at .95,1.05\n"
    cmd = cmd + "plot x*0-1000 title \"normalized energy*delay\" with linesp ls 2\n"

    self.energydelay_gnuplot_cmd_str = cmd

  def generate_mempower(self, datfile_name, epsfile_name, chipkill = False):
    cmd = ""
    label_yoffset = -12.0
    if chipkill == True:
      cmd = cmd + "set terminal postscript eps enhanced color \"Helvetica,11\" size 5.3in, 1.5in\n"
      label_yoffset = -19.0
    else:
      cmd = cmd + "set terminal postscript eps enhanced color \"Helvetica,11\" size 5.3in, 1.5in\n"
    cmd = cmd + "set output \"" + epsfile_name + "\"\n"

    i = 0
    num_apps = 0
    num_apps_so_far_per_class = 0
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0
      while j < len(apps):
        app_name = apps[j]
        j = j + 2
        if app_name[0] != '*':
          cmd = cmd + "set label \"noPD\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)) + ", -1 rotate by 90 right\n"
          if chipkill is False:
            cmd = cmd + "set label \"1set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -1 rotate by 90 right\n"
            cmd = cmd + "set label \"2set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -1 rotate by 90 right\n"
            cmd = cmd + "set label \"4set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -1 rotate by 90 right\n"
            cmd = cmd + "set label \"8set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+4) + ", -1 rotate by 90 right\n"
          else:
            cmd = cmd + "set label \"36x4\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -1 rotate by 90 right\n"
            cmd = cmd + "set label \"11x4\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -1 rotate by 90 right\n"
            cmd = cmd + "set label \"7x8\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -1 rotate by 90 right\n"
          num_apps = num_apps + 1
      
      cmd = cmd + "set label \"noPD\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)) + ", -1 rotate by 90 right\n"
      if chipkill is False:
        cmd = cmd + "set label \"1set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -1 rotate by 90 right\n"
        cmd = cmd + "set label \"2set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -1 rotate by 90 right\n"
        cmd = cmd + "set label \"4set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -1 rotate by 90 right\n"
        cmd = cmd + "set label \"8set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+4) + ", -1 rotate by 90 right\n"
      else:
        cmd = cmd + "set label \"36x4\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -1 rotate by 90 right\n"
        cmd = cmd + "set label \"11x4\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -1 rotate by 90 right\n"
        cmd = cmd + "set label \"7x8\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -1 rotate by 90 right\n"
      num_apps = num_apps + 1
      if i < len(self.ll.class_app_log):
        cmd = cmd + "set arrow from " + str((self.ll.num_confs_per_app + 1)*num_apps - 1) + ",0 rto 0, " + str(label_yoffset-1) + " nohead\n"
      cmd = cmd + "set label \"" + class_name + "\" at " + str((self.ll.num_confs_per_app + 1)*(num_apps + num_apps_so_far_per_class - 1)/2) + ", " + str(label_yoffset) + "\n"
      num_apps_so_far_per_class = num_apps

    cmd = cmd + "set arrow from -1,0 rto 0," + str(label_yoffset-1) + " nohead\n"
    cmd = cmd + "set arrow from "+str(num_apps*(self.ll.num_confs_per_app + 1) - 1) + ",0 rto 0," + str(label_yoffset-1) + " nohead\n"
    cmd = cmd + "set style histogram rowstacked\n"
    cmd = cmd + "set boxwidth 0.7 relative\n"
    cmd = cmd + "set style data histogram\n"
    cmd = cmd + "set xtics rotate by 90\n"
    cmd = cmd + "set tics nomirror\n"
    cmd = cmd + "set border 11\n"
    cmd = cmd + "#set y2tics out 0, 20, 40 textcolor rgbcolor \"#FFFFFF\"\n"
    cmd = cmd + "set y2label \"low-power mode fraction\"\n"
    cmd = cmd + "set xrange [ -1 : " + str(num_apps*(self.ll.num_confs_per_app + 1)-1) + " ]\n"
    cmd = cmd + "#set key enhanced autotitles columnhead box horizontal samplen 1\n"
    #cmd = cmd + "set key enhanced top right vertical samplen 2\n"
    if chipkill == False:
      cmd = cmd + "set key at 40,32 samplen 2\n"
      cmd = cmd + "set yrange [ 0 : 30 ]\n"
      cmd = cmd + "set ytics out 0, 5, 30\n"
      cmd = cmd + 'set y2tics ("0.0" 0, "0.2" 5, "0.4" 10, "0.6" 15, "0.8" 20, "1.0" 25)\n'
    else:
      cmd = cmd + "set key at 40,52 samplen 2\n"
      cmd = cmd + "set yrange [ 0 : 45 ]\n"
      cmd = cmd + "set ytics out 0, 5, 45\n"
      cmd = cmd + 'set y2tics ("0.0" 0, "0.2" 8, "0.4" 16, "0.6" 24, "0.8" 32, "1.0" 40)\n'

    cmd = cmd + "set ylabel \"Main memory power (W)\"\n"
    cmd = cmd + "set y2tics out\n"
    cmd = cmd + "# since we avg_rd_latency must be scaled\n"
    #cmd = cmd + "unset key\n"
    cmd = cmd + "set grid y2tics back linetype 3 linewidth 2 linecolor \"#888888\", linewidth 0\n"
    cmd = cmd + "show grid\n"

    cmd = cmd + "set style line 3 lt -1 lc rgbcolor \"#ccfb8c\" pointtype 13 pointsize 0.8\n"
    cmd = cmd + "set style line 2 lt -1 lc rgbcolor \"#000000\" pointtype 13 pointsize 1.4\n"
    cmd = cmd + "set style line 5 lt -1 lc rgbcolor \"#dddddd\" pointtype 16 pointsize 0.4\n"
    cmd = cmd + "set style line 4 lt -1 lc rgbcolor \"#000000\" pointtype 16 pointsize 0.8\n"
    cmd = cmd + "set multiplot\n"
    cmd = cmd + "unset key\n"

    cmd = cmd + "plot "

    idx = 2
    i = 0
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0
      while j <= len(apps):
        if j == len(apps):
          app_name = 'average'
          j = j + 1
        else:
          app_name = apps[j]
          j = j + 1
          logs     = apps[j]
          j = j + 1

        if app_name[0] != '*':
          cmd = cmd + "newhistogram \"" + app_name + "\", '" + datfile_name + "' using "
          cmd = cmd + str(idx+1) + ":xtic(1) "
          if idx == 2:
            cmd = cmd + " title \"standby\" "
          else:
            cmd = cmd + " notitle "
          cmd = cmd + "with histograms fs solid 1 border -1 lt rgbcolor \"#ffffff\", \\\n"
          cmd = cmd + "                  '' using " + str(idx+2)
          if idx == 2:
            cmd = cmd + " title \"refresh\" "
          else:
            cmd = cmd + " notitle "
          cmd = cmd + "with histograms fs solid 1 border -1 lt rgbcolor \"#fdc643\", \\\n"
          cmd = cmd + "                  '' using " + str(idx+3)
          if idx == 2:
            cmd = cmd + " title \"access\" "
          else:
            cmd = cmd + " notitle "
          cmd = cmd + "with histograms fs solid 1 border -1 lt rgbcolor \"#b01c13\", \\\n"
          cmd = cmd + "                  '' using " + str(idx+4)
          if idx == 2:
            cmd = cmd + " title \"I/O\" "
          else:
            cmd = cmd + " notitle "
          cmd = cmd + "with histograms fs solid 1 border -1 lt rgbcolor \"#000000\", \\\n"
          cmd = cmd + "                  '' using " + str(idx+6) + ":" + str(idx+5)
          if idx == 2:
            cmd = cmd + " title \"low-power mode fraction\" "
          else:
            cmd = cmd + " notitle "
          cmd = cmd + "with linespoints ls 4, \\\n"
          cmd = cmd + "                  '' using " + str(idx+6) + ":" + str(idx+5)
          cmd = cmd + " notitle with points ls 5"
          if j <= len(apps) or i < len(self.ll.class_app_log):
            cmd = cmd + ", \\\n"
          else:
            cmd = cmd + "\n"
          idx = idx + 7

    cmd = cmd + "unset xtics\n"
    cmd = cmd + "unset ytics\n"
    cmd = cmd + "unset y2tics\n"
    cmd = cmd + "set border 0\n"
    cmd = cmd + "unset xlabel\n"
    cmd = cmd + "unset ylabel\n"
    cmd = cmd + "unset y2label\n"
    cmd = cmd + "unset label\n"
    cmd = cmd + "unset arrow\n"
    cmd = cmd + "set key horiz nobox at .65,1.05\n"
    cmd = cmd + "set xrange [0:1]\n"
    cmd = cmd + "set yrange [0:1]\n"
    cmd = cmd + "plot x*0-1000 title \"standby\" with filledcu fs solid 1 border -1 lt rgbcolor \"#ffffff\", \\\n"
    cmd = cmd + "     x*0-1000 title \"refresh\" with filledcu fs solid 1 border -1 lt rgbcolor \"#fdc643\", \\\n"
    cmd = cmd + "     x*0-1000 title \"access\" with filledcu fs solid 1 border -1 lt rgbcolor \"#b01c13\", \\\n"
    cmd = cmd + "     x*0-1000 title \"I/O\" with filledcu fs solid 1 border -1 lt rgbcolor \"#000000\"\n"
    cmd = cmd + "set key horiz nobox at .87,1.05\n"
    cmd = cmd + "plot x*0-1000 title \"low-power mode fraction\" with linesp ls 4\n"

    self.mempower_gnuplot_cmd_str = cmd

  def generate_edpcomp(self, datfile_name, epsfile_name):
    cmd = ""
    cmd = cmd + "set terminal postscript eps enhanced color \"Helvetica,11\" size 5.3in, 0.9in\n"
    cmd = cmd + "set output \"" + epsfile_name + "\"\n"

    i = 0
    num_apps = 0
    num_apps_so_far_per_class = 0
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0
      while j < len(apps):
        app_name = apps[j]
        j = j + 2
        if app_name[0] != '*':
          cmd = cmd + "set label \"noPD\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)) + ", -1.5 rotate by 90 right\n"
          cmd = cmd + "set label \"1set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -1.5 rotate by 90 right\n"
          cmd = cmd + "set label \"2set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -1.5 rotate by 90 right\n"
          cmd = cmd + "set label \"4set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -1.5 rotate by 90 right\n"
          cmd = cmd + "set label \"8set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+4) + ", -1.5 rotate by 90 right\n"
          num_apps = num_apps + 1
      
      cmd = cmd + "set label \"noPD\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)) + ", -1.5 rotate by 90 right\n"
      cmd = cmd + "set label \"1set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+1) + ", -1.5 rotate by 90 right\n"
      cmd = cmd + "set label \"2set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+2) + ", -1.5 rotate by 90 right\n"
      cmd = cmd + "set label \"4set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+3) + ", -1.5 rotate by 90 right\n"
      cmd = cmd + "set label \"8set\" at " + str(num_apps*(self.ll.num_confs_per_app + 1)+4) + ", -1.5 rotate by 90 right\n"
      num_apps = num_apps + 1
      if i < len(self.ll.class_app_log):
        cmd = cmd + "set arrow from " + str((self.ll.num_confs_per_app + 1)*num_apps - 1) + ",0 rto 0, -3.6 nohead\n"
      cmd = cmd + "set label \"" + class_name + "\" at " + str((self.ll.num_confs_per_app + 1)*(num_apps + num_apps_so_far_per_class - 1)/2) + ", -3.7\n"
      num_apps_so_far_per_class = num_apps

    cmd = cmd + "set arrow from -1,0 rto 0,-3.6 nohead\n"
    cmd = cmd + "set arrow from "+str(num_apps*(self.ll.num_confs_per_app + 1) - 1) + ",0 rto 0,-3.6 nohead\n"
    cmd = cmd + "set style histogram rowstacked\n"
    cmd = cmd + "set boxwidth 0.7 relative\n"
    cmd = cmd + "set style data histogram\n"
    cmd = cmd + "set xtics out scale 0 rotate by 90\n"
    cmd = cmd + "set tics nomirror\n"
    cmd = cmd + "set ytics out 0, 1, 10\n"
    cmd = cmd + "set border 10\n"
    cmd = cmd + "set y2label textcolor rgbcolor \"#ffffff\"\n"
    cmd = cmd + "set y2label \"Percentage\"\n"
    cmd = cmd + "set xrange [ -1 : " + str(num_apps*(self.ll.num_confs_per_app + 1)-1) + " ]\n"
    cmd = cmd + "unset key\n"
    cmd = cmd + "set yrange [ -1.5 : 1.0 ]\n"
    cmd = cmd + "set ylabel \"Relative EDP\"\n"
    cmd = cmd + "set y2tics out 0, 20, 40 textcolor rgbcolor \"#ffffff\"\n"
    #cmd = cmd + "set ytics  (\"0%%\" 0, \"2\" 2, \"4\" 4, \"6\" 6, \"8\" 8, \"10\" 10, \"12\" 12, \"14\" 14, \"16\" 16)\n"
    cmd = cmd + "set ytics  (\"-15%%\" -1.5, \"-10%%\" -1, \"-5%%\" -0.5, \"0%%\" 0, \"5%%\" 0.5, \"10%%\" 1, \"15%%\" 1.5)\n"

    cmd = cmd + "set style line 3 lt -1 lc rgbcolor \"#ffffff\" pointtype 13 pointsize 0.7\n"
    cmd = cmd + "set style line 2 lt -1 lc rgbcolor \"#000000\" pointtype 13 pointsize 1.2\n"
    cmd = cmd + "set arrow from -1,0 to " + str(num_apps*(self.ll.num_confs_per_app + 1)-1) + ",0 nohead\n"

    cmd = cmd + "plot "

    idx = 2
    i = 0
    while i < len(self.ll.class_app_log):
      class_name = self.ll.class_app_log[i]
      i = i + 1
      apps       = self.ll.class_app_log[i]
      i = i + 1
      j = 0
      while j <= len(apps):
        if j == len(apps):
          app_name = 'average'
          j = j + 1
        else:
          app_name = apps[j]
          j = j + 1
          logs     = apps[j]
          j = j + 1

        if app_name[0] != '*':
          cmd = cmd + "newhistogram \"" + app_name + "\", '" + datfile_name + "' using "
          cmd = cmd + str(idx) + ":xtic(1) "
          if idx == 2:
            cmd = cmd + " title \"relative energy-delay product\" "
          else: 
            cmd = cmd + " notitle "
          cmd = cmd + "with histograms fs solid 1 border -1 lt rgbcolor \"#7030a0\""
          if j <= len(apps) or i < len(self.ll.class_app_log):
            cmd = cmd + ", \\\n"
          else:
            cmd = cmd + "\n"
          idx = idx + 2

    self.edpcomp_gnuplot_cmd_str = cmd


def write_to_file(file_name, string):
  try:
    file = open(file_name, 'w')
  except IOError:
    print "cannot open " + file_name
    sys.exit()

  file.write(string)
  file.close()


# main function
ipc_datfile_name = "ipc_datfile"
ipc_cmdfile_name = "ipc_cmdfile"
mem_datfile_name = "mem_datfile"
mem_cmdfile_name = "mem_cmdfile"
edp_datfile_name = "edp_datfile"
edp_cmdfile_name = "edp_cmdfile"
edpcomp_datfile_name = "edpcomp_datfile"
edpcomp_cmdfile_name = "edpcomp_cmdfile"

loglist    = LogList(options)
gnuplotcmd = GnuplotCmd(loglist)
gnuplotcmd.generate_ipc(ipc_datfile_name, options.outputprefix+"ipc.eps", options.chipkill)
gnuplotcmd.generate_mempower(mem_datfile_name, options.outputprefix+"mem.eps", options.chipkill)
gnuplotcmd.generate_energydelay(edp_datfile_name, options.outputprefix+"edp.eps", options.chipkill)
gnuplotcmd.generate_edpcomp(edpcomp_datfile_name, options.outputprefix+"edpcomp.eps")
gnuplotdat = GnuplotDat(loglist)
gnuplotdat.generate_ipc(options.chipkill)
gnuplotdat.generate_mempower(options.chipkill)
gnuplotdat.generate_energydelay(options.chipkill)
gnuplotdat.generate_edpcomp(options.chipkill)

write_to_file(ipc_datfile_name, gnuplotdat.ipc_gnuplot_dat_str)
write_to_file(ipc_cmdfile_name, gnuplotcmd.ipc_gnuplot_cmd_str)
os.system("gnuplot "+ipc_cmdfile_name)
os.system("ps2pdf "+options.outputprefix+"ipc.eps")
os.system("pdfcrop --margins 1 "+options.outputprefix+"ipc.pdf "+options.outputprefix+"ipc.pdf")

write_to_file(mem_datfile_name, gnuplotdat.mempower_gnuplot_dat_str)
write_to_file(mem_cmdfile_name, gnuplotcmd.mempower_gnuplot_cmd_str)
os.system("gnuplot "+mem_cmdfile_name)
os.system("ps2pdf "+options.outputprefix+"mem.eps")
os.system("pdfcrop --margins 1 "+options.outputprefix+"mem.pdf "+options.outputprefix+"mem.pdf")

write_to_file(edpcomp_datfile_name, gnuplotdat.edpcomp_gnuplot_dat_str)
write_to_file(edpcomp_cmdfile_name, gnuplotcmd.edpcomp_gnuplot_cmd_str)
os.system("gnuplot "+edpcomp_cmdfile_name)
os.system("ps2pdf "+options.outputprefix+"edpcomp.eps")
os.system("pdfcrop --margins 1 "+options.outputprefix+"edpcomp.pdf "+options.outputprefix+"edpcomp.pdf")

write_to_file(edp_datfile_name, gnuplotdat.energydelay_gnuplot_dat_str)
write_to_file(edp_cmdfile_name, gnuplotcmd.energydelay_gnuplot_cmd_str)
os.system("gnuplot "+edp_cmdfile_name)
os.system("ps2pdf "+options.outputprefix+"edp.eps")
os.system("pdfcrop --margins 1 "+options.outputprefix+"edp.pdf "+options.outputprefix+"edp.pdf")

