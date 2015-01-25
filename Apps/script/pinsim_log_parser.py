#!/usr/bin/python

from optparse import OptionParser
import sys, re, string, fpformat


class MD:
  mdparams = { }
  def __init__(self, mdfile, ticks_per_cycle):

    # parse mdfile
    if mdfile == "/dev/null":
      self.ticks_per_cycle = int(ticks_per_cycle)
      self.max_ipc         = 16
      self.num_ranks_per_MC    = 1
      self.num_vmds_per_rank   = 1
      self.mini_rank           = 'false'
      self.vmd_page_sz         = '16384'

    else:
      try:
        mdfile = open(mdfile, 'r')
      except IOError:
        print "cannot open "+mdfile
        sys.exit()

      for line in mdfile:
        line = re.sub('#.*', '', line)  # remove comments
        temp = re.split('\s*', line)
        if len(temp) >= 3:
          self.mdparams[temp[0]] = temp[2]

      self.ticks_per_cycle = int(self.mdparams['pts.l1i$.process_interval'])
      self.max_ipc = int(self.mdparams['pts.num_hthreads']) / int(self.mdparams['pts.num_hthreads_per_l1$'])
      self.num_ranks_per_MC = int(self.mdparams['pts.mc.num_ranks_per_mc'])
      self.num_vmds_per_rank = int(self.mdparams['pts.mc.num_vmds_per_rank'])
      self.mini_rank         = self.mdparams['pts.mc.mini_rank']
      self.vmd_page_sz       = self.mdparams['pts.mc.vmd_page_sz']


class Stat:
  def __init__(self, md):
    self.md = md
    self.ticks_per_cycle   = md.ticks_per_cycle
    self.max_ipc           = md.max_ipc
    self.num_ranks_per_MC  = md.num_ranks_per_MC
    self.num_vmds_per_rank = md.num_vmds_per_rank
    self.mini_rank         = md.mini_rank
    self.vmd_page_sz       = md.vmd_page_sz
    self.num_ticks = 0
    self.num_instrs      = 0
    self.num_hthreads    = 0
    self.num_br_misses   = 0
    self.num_branches    = 0
    self.num_nacks       = 0
    self.xbar_accs       = 0
    self.num_L1I_accs    = 0
    self.num_L1I_misses  = 0
    self.num_L1I_ev_coh  = 0
    self.num_L1I_coh_accs = 0
    self.num_L1D_rd_accs   = 0
    self.num_L1D_rd_misses = 0
    self.num_L1D_wr_accs   = 0
    self.num_L1D_wr_misses = 0
    self.num_L1D_ev_coh    = 0
    self.num_L1D_ev_cap    = 0
    self.num_L1D_coh_accs  = 0
    self.num_TLBD_accs     = 0
    self.num_TLBD_misses   = 0
    self.num_TLBI_accs     = 0
    self.num_TLBI_misses   = 0
    self.num_L2_rd_accs   = 0
    self.num_L2_rd_misses = 0
    self.num_L2_wr_accs   = 0
    self.num_L2_wr_misses = 0
    self.num_L2_ev_coh    = 0
    self.num_L2_ev_cap    = 0
    self.num_L2_coh_accs  = 0
    self.num_MC_rds       = 0
    self.num_MC_wrs       = 0
    self.num_MC_acts      = 0
    self.num_MC_pres      = 0
    self.num_RBoL_hits    = 0
    self.num_RBoL_misses  = 0
    self.num_DRAM_pages   = 0
    self.num_Dir_i_to_tr  = 0
    self.num_Dir_e_to_tr  = 0
    self.num_Dir_s_to_tr  = 0
    self.num_Dir_m_to_tr  = 0
    self.num_Dir_m_to_i   = 0
    self.num_Dir_tr_to_i  = 0
    self.num_Dir_tr_to_e  = 0
    self.num_Dir_tr_to_s  = 0
    self.num_Dir_tr_to_m  = 0
    self.num_Dir_nacks    = 0
    self.num_Dir_bypass   = 0
    self.num_Dir_evict    = 0
    self.num_Dir_invalidate = 0
    self.num_Dir_from_mc  = 0
    self.num_Dir_cache_acc  = 0
    self.num_Dir_cache_miss = 0
    self.num_cond_broadcast = 0
    self.num_cond_signal    = 0
    self.num_cond_wait      = 0
    self.num_lock           = 0
    self.num_trylock        = 0
    self.num_barrier        = 0
    self.num_instrs_spin    = 0
    self.num_x87_ops        = 0
    self.num_call_ops       = 0
    self.total_mem_wr_time  = 0
    self.total_mem_rd_time  = 0
    self.active_pd_time     = 0
    self.num_MCs            = 0
    self.cycles   = []
    self.instrs   = []

  def parse(self, logfile, ipcfile):
    # parse logfile
    try:
      logfile = open(logfile, 'r')
    except IOError:
      print "cannot open "+logfile
      sys.exit()
    
    for line in logfile:
      if re.search("^  -- ",line) != None and re.search("^  -- \[",line) == None:
        line = line[5:]
        temp = re.split('\s*', line)
        if line[0:3] == 'HTH':
          self.num_hthreads = self.num_hthreads + 1
          self.num_br_misses = self.num_br_misses + int(temp[7][1:][:-1])
          self.num_branches  = self.num_branches  + int(temp[8][:-1])
          self.num_nacks     = self.num_nacks     + int(temp[13][:-1])
          self.num_x87_ops   = self.num_x87_ops   + int(temp[16][:-1])
          self.num_call_ops  = self.num_call_ops  + int(temp[19][:-1])
          if (len(temp) >= 28):
            self.total_mem_wr_time = self.total_mem_wr_time + int(temp[25][:-1])
            self.total_mem_rd_time = self.total_mem_rd_time + int(temp[28])
        elif line[0:3] == 'NoC':
          if temp[9][-1] == ')':
            self.xbar_accs = int(temp[7][1:][:-1]) + int(temp[8][:-1]) + int(temp[9][:-1])
          else:
            self.xbar_accs = int(temp[7][1:][:-1]) + int(temp[8][:-1]) + int(temp[9][:-2])
        elif line[0:4] == 'L1$I':
          if temp[2] == 'RD':
            self.num_L1I_accs   = self.num_L1I_accs   + int(temp[7][:-1])
            self.num_L1I_misses = self.num_L1I_misses + int(temp[6][1:][:-1])
          elif temp[2] == '(ev_coherency,)':
            self.num_L1I_ev_coh = self.num_L1I_ev_coh + int(temp[6][1:][:-1])
            self.num_L1I_coh_accs = self.num_L1I_coh_accs + int(temp[7][:-1])
        elif line[0:4] == 'L1$D':
          if temp[2] == 'RD':
            self.num_L1D_rd_misses = self.num_L1D_rd_misses + int(temp[6][1:][:-1])
            self.num_L1D_rd_accs   = self.num_L1D_rd_accs   + int(temp[7][:-1])
          elif temp[2] == 'WR':
            self.num_L1D_wr_misses = self.num_L1D_wr_misses + int(temp[6][1:][:-1])
            self.num_L1D_wr_accs   = self.num_L1D_wr_accs   + int(temp[7][:-1])
          elif temp[2] != 'awake':
            self.num_L1D_ev_coh    = self.num_L1D_ev_coh    + int(temp[8][1:][:-1])
            self.num_L1D_ev_cap    = self.num_L1D_ev_cap    + int(temp[9][:-1])
            self.num_L1D_coh_accs  = self.num_L1D_coh_accs  + int(temp[10][:-1])
        elif line[0:4] == 'TLBI':
          self.num_TLBI_misses = self.num_TLBI_misses + int(temp[5][1:][:-1])
          self.num_TLBI_accs   = self.num_TLBI_accs   + int(temp[6][:-1])
        elif line[0:4] == 'TLBD':
          self.num_TLBD_misses = self.num_TLBD_misses + int(temp[5][1:][:-1])
          self.num_TLBD_accs   = self.num_TLBD_accs   + int(temp[6][:-1])
        elif line[0:4] == 'L2$ ':
          if temp[3] == 'RD':
            self.num_L2_rd_misses = self.num_L2_rd_misses + int(temp[7][1:][:-1])
            self.num_L2_rd_accs   = self.num_L2_rd_accs   + int(temp[8][:-1])
          elif temp[3] == 'WR':
            self.num_L2_wr_misses = self.num_L2_wr_misses + int(temp[7][1:][:-1])
            self.num_L2_wr_accs   = self.num_L2_wr_accs   + int(temp[8][:-1])
          elif temp[3][:3] == '(ev':
            self.num_L2_ev_coh    = self.num_L2_ev_coh    + int(temp[9][1:][:-1])
            self.num_L2_ev_cap    = self.num_L2_ev_cap    + int(temp[10][:-1])
            self.num_L2_coh_accs  = self.num_L2_coh_accs  + int(temp[11][:-1])
        elif line[0:4] == 'MC  ':
          self.num_MCs     = self.num_MCs + 1
          self.num_MC_rds  = self.num_MC_rds  + int(temp[8][1:][:-1])
          self.num_MC_wrs  = self.num_MC_wrs  + int(temp[9][:-1])
          self.num_MC_acts = self.num_MC_acts + int(temp[10][:-1])
          self.num_MC_pres = self.num_MC_pres + int(temp[11][:-2])
          self.num_RBoL_hits    = self.num_RBoL_hits   + int(temp[34][1:][:-1])
          self.num_RBoL_misses  = self.num_RBoL_misses + int(temp[35][:-2])
          self.num_DRAM_pages   = self.num_DRAM_pages  + int(temp[36])
          if len(temp) >= 20:
            self.active_pd_time = self.active_pd_time + int(temp[19])
        elif line[0:4] == 'Dir ':
          if temp[3] == '(i->tr,':
            self.num_Dir_i_to_tr  = self.num_Dir_i_to_tr + int(temp[13][1:][:-1])
            self.num_Dir_e_to_tr  = self.num_Dir_e_to_tr + int(temp[14][:-1])
            self.num_Dir_s_to_tr  = self.num_Dir_s_to_tr + int(temp[15][:-1])
            self.num_Dir_m_to_tr  = self.num_Dir_m_to_tr + int(temp[16][:-1])
            self.num_Dir_m_to_i   = self.num_Dir_m_to_i  + int(temp[17][:-1])
            self.num_Dir_tr_to_i  = self.num_Dir_tr_to_i + int(temp[18][:-1])
            self.num_Dir_tr_to_e  = self.num_Dir_tr_to_e + int(temp[19][:-1])
            self.num_Dir_tr_to_s  = self.num_Dir_tr_to_s + int(temp[20][:-1])
            self.num_Dir_tr_to_m  = self.num_Dir_tr_to_m + int(temp[21][:-1])
          else:
            self.num_Dir_nacks   = self.num_Dir_nacks   + int(temp[13][1:][:-1])
            self.num_Dir_bypass  = self.num_Dir_bypass  + int(temp[14][:-1])
            self.num_Dir_evict   = self.num_Dir_evict   + int(temp[15][:-1])
            self.num_Dir_invalidate = self.num_Dir_invalidate + int(temp[16][:-1])
            self.num_Dir_from_mc = self.num_Dir_from_mc + int(temp[17][:-1])
            self.num_Dir_cache_acc     = self.num_Dir_cache_acc     + int(temp[18][:-1])
            self.num_Dir_cache_miss = self.num_Dir_cache_miss + int(temp[19][:-1])
        elif re.search("global event queue : at cycle", line) != None:
          self.num_ticks = int(temp[7])
        elif re.search("total number of fetched instructions", line) != None:
          self.num_instrs = int(temp[6])
        elif line[0:5] == '(cond':
          self.num_cond_broadcast = self.num_cond_broadcast + int(temp[7][1:][:-1])
          self.num_cond_signal    = self.num_cond_signal    + int(temp[8][:-1])
          self.num_cond_wait      = self.num_cond_wait      + int(temp[9][:-1])
          self.num_lock           = self.num_lock           + int(temp[10][:-1])
          self.num_trylock        = self.num_trylock        + int(temp[11][:-1])
          self.num_barrier        = self.num_barrier        + int(temp[12][:-1])
      elif ipcfile != '/dev/null' and re.search("\sinstructions are fetched so", line) != None:
        temp = re.split('\s*', line[6:].lstrip())
        self.cycles.append(int(temp[0][:-1]) / self.ticks_per_cycle)
        self.instrs.append(int(temp[2]))
      elif re.search("\sis killed", line) != None:
        temp = re.split('\s*', line[6:].lstrip())
        self.num_instrs_spin      = self.num_instrs_spin    + int(temp[21][:-1])

    if ipcfile != '/dev/null':
      try:
        ipcfile = open(ipcfile, 'w')
      except IOError:
        print "cannot open "+ipcfile
        sys.exit()
    
      subsampling = False
      i = 0
      if len(self.cycles) > 10000:
        subsampling = True
      prev_cycle = 0
      prev_instr = 0
      for curr_cycle in self.cycles:
        if i%10 == 0 or subsampling == False:
          curr_instr = self.instrs.pop(0)
          curr_ipc   = 1.0 * (curr_instr - prev_instr) / (curr_cycle - prev_cycle)
          ipcfile.write(str(curr_instr/10.0**9)+' '+str(curr_ipc)+' '+str(1.0*curr_instr/curr_cycle)+' '+str(curr_cycle/10.0**6)+'\n')
          prev_cycle = curr_cycle
          prev_instr = curr_instr
        else:
          self.instrs.pop(0)
        i = i + 1

      sys.exit()

  def compute_energydelay(self, chipkill = False):
    # compute power and energy delay product
    IFQ                 = 0.05095
    IRF                 = 0.00337
    FRF                 = 0.00943
    EXU                 = 0.02829
    FPU                 = 0.22135
    LSQ                 = 0.02560
    Pipeline            = 0.07677
    Bypass              = 0.04026
    Dec                 = 0.02312
    DCL                 = 0.00925
    Thread_inst_sel     = 0.00647
    Core_CLK            = 0.05025
    l1i_rd_dyn          = 0.090558  # nJ
    l1i_wr_dyn          = 0.089246  # nJ
    l1i_rd_dyn_tag      = 0.000506  # nJ
    l1i_wr_dyn_tag      = 0.000490  # nJ
    itlb                = 0.08600
    l1d_rd_dyn          = 0.093471  # nJ
    l1d_wr_dyn          = 0.093035  # nJ
    l1d_rd_dyn_tag      = 0.001995  # nJ
    l1d_wr_dyn_tag      = 0.001728  # nJ
    dtlb                = 0.08600
    missb              = 0.00792
    fillb              = 0.01359
    prefetchb          = 0.01783
    dwbb                = 0.01359
    l2_rd_dyn           = 0.178028  # nJ
    l2_wr_dyn           = 0.152407  # nJ
    l2_rd_dyn_tag       = 0.004730  # nJ
    l2_wr_dyn_tag       = 0.003089  # nJ
    L2_mfbuffer_dyn     = 0.03937*2
    L2_prefetchbuffer_dyn = 0.03937
    L2_WBB_dyn          = 0.03937
    Local_xbar_dyn      = 0.624
    l2_main_xbar_rd_dyn = 0.528053  # nJ
    l2_main_xbar_wr_dyn = 0.599783  # nJ
    dir_dyn             = (0.00178 + 0.00126 + 0.00756 + 0.00843) #nJ
    main_rd_dyn         = 0.243*36 #14.20243*0.3 # nJ
    main_wr_dyn         = 0.255*36 #15.57213*0.3 # nJ
    main_act_dyn        = (0.112+1.067)*36 #15.57213*0.7 # nJ
    l1i_leak            = 0.00482*16  # W
    iprefetchb_leak     = 0.001199*16
    itlb_leak           = 0.016731*16
    l1d_leak            = 0.00887*16  # W
    dtlb_leak           = 0.016731*16
    miss_leak          = 0.000869*16
    fillb_leak         = 0.000715*16
    dprefetchb_leak     = 0.001199*16
    dwbb_leak           = 0.000715*16
    EXU_leak            = 0.0167*16
    FPU_leak            = 0.111375*16

    
    l2_leak             = 0.185*4  # W
    dir_leak            = 0.0866*4 # W
    Local_xbar_leak     = 0.11737*4
    l2_main_xbar_leak   = 0.107703  # W
    intra_dir_dyn       = 0.25453
    MC_logic_dyn        = 0.55712
    MC_logic_leak       = 0.06891*4
    metal_wire          = 9.44167
    main_standby        = 0.008895*8*36  # W
    main_refresh        = 0.000554*8*36  # W
    bus                 = 0.953674  # nJ
    clk                 = 0.5       # ns
    max_cpu_power       = 30.84     # W
    pd_power_scale      = 0.2
    bus_act             = 0         # nJ
    bus_rd              = 0         # nJ
    bus_wr              = 0         # nJ
    if chipkill == False:
      # assume x9 DRAM chips
      main_rd_dyn       = 0.333*8    # nJ
      main_wr_dyn       = 0.531*8    # nJ
      main_act_dyn      = (0.114+1.068)*8  # nJ
      main_standby      = 0.095672*8 # W
      main_refresh      = 0.00912*8  # W
      if self.num_ranks_per_MC == 1:
        bus_act         = 1.5*1.5 * (7 + 19) * 1.3 * (102*0.1 + 2*(1 + 8/self.num_vmds_per_rank)) / 1000 # nJ
        bus_rd          = bus_act + 12.04 * 512 / 2000 # nJ
        bus_wr          = bus_act +  8.02 * 512 / 2000 # nJ
      elif self.num_ranks_per_MC == 2:
        bus_act         = 1.5*1.5 * (7 + 19) * 1.3 * (102*0.1 + 2*(2 + 8/self.num_vmds_per_rank)) / 1000 # nJ
        bus_rd          = bus_act + 21.82 * 512 / 2000 # nJ
        bus_wr          = bus_act + 31.74 * 512 / 2000 # nJ
      elif self.num_ranks_per_MC == 4:
        bus_act         = 1.5*1.5 * (7 + 19) * 1.3 * (102*0.1 + 2*(4 + 8/self.num_vmds_per_rank)) / 1000 # nJ
        bus_rd          = bus_act + 42.51 * 512 / 2000 # nJ
        bus_wr          = bus_act + 72.80 * 512 / 2000 # nJ
      if self.mini_rank == 'true':
        bus_rd += 12.04 * 512 / 2000
        bus_wr +=  8.02 * 512 / 2000
    else:
      if self.vmd_page_sz == '65536':
        # 36 chip Chipkill (x4 DRAM chips)  -- actually 35 chips are enough (1 VMD, 2 ranks)
        main_rd_dyn     = 0.151*35 #0.243*35   # nJ
        main_wr_dyn     = 0.248*35 #0.255*35   # nJ
        main_act_dyn    = (0.099 + 1.067)*35 #(0.112 + 1.067)*35  # nJ
        main_standby    = 0.07116*35  # W
        main_refresh    = 0.004432*35 # W
        bus_act         = 1.5*1.5 * (7 + 18) * 1.3 * (102*0.1 + 2*(4 + 16)) / 1000 # nJ
        bus_rd          = bus_act + 42.51 * 512 / 2000 # nJ
        bus_wr          = bus_act + 72.80 * 512 / 2000 # nJ
      elif self.vmd_page_sz == '16384':
        # 11 chip Chipkill (x4 DRAM chips) (2 VMD, 4 ranks)
        main_rd_dyn     = 0.151*11*2 #0.243*11*2   # nJ
        main_wr_dyn     = 0.248*11*2 #0.255*11*2   # nJ
        main_act_dyn    = (0.099 + 1.067)*11*2 #(0.112 + 1.067)*11*2  # nJ
        main_standby    = 0.07116*11*2  # W
        main_refresh    = 0.004432*11*2 # W
        bus_act         = 1.5*1.5 * (7 + 18) * 1.3 * (102*0.1 + 2*(4 + 11)) / 1000 # nJ
        bus_rd          = bus_act + 42.51 * 512 / 2000 # nJ
        bus_wr          = bus_act + 72.80 * 512 / 2000 # nJ
      else:
        #  7 chip ChipKill (x8 DRAM chips) (2 VMD, 4 ranks)
        main_rd_dyn     = 0.333*7*2   # nJ
        main_wr_dyn     = 0.531*7*2   # nJ
        main_act_dyn    = (0.114 + 1.068)*7*2  # nJ
        main_standby    = 0.095672*7*2  # W
        main_refresh    = 0.00912*7*2 # W
        bus_act         = 1.5*1.5 * (7 + 19) * 1.3 * (102*0.1 + 2*(4 + 7)) / 1000 # nJ
        bus_rd          = bus_act + 42.51 * 512 / 2000 # nJ
        bus_wr          = bus_act + 72.80 * 512 / 2000 # nJ

    curr_cycle          = 1.0*self.num_ticks/self.ticks_per_cycle
    ipc                 = 1.0*self.num_instrs/curr_cycle
    duty                = 1.0*ipc/self.max_ipc
    Top_wire            = metal_wire*duty
    Core_wire           = 0.50*Top_wire
    L2_wire             = 0.25*Top_wire
    Xbar_wire           = 0.0*Top_wire
    MC_wire             = 0.20*Top_wire
    Router_wire         = 0.05*Top_wire
    IFU_wire            = 0.33*Core_wire
    LSU_wire            = 0.33*Core_wire
    EXU_wire            = 0.33*Core_wire

    IRFp = IRF*self.num_instrs*3 /(clk * curr_cycle)
    ALUp = EXU*self.num_instrs   /(clk * curr_cycle)
    FRFp = FRF*self.num_x87_ops*4/(clk * curr_cycle)
    FPUp = FRFp + FPU * self.num_x87_ops/(clk * curr_cycle)
    Bypassp = Bypass*self.num_instrs/(clk * curr_cycle)
    Decp = Dec*self.num_instrs/(clk * curr_cycle)
    DCLp = DCL*self.num_instrs/(clk * curr_cycle)
    TH_INST_SELp= Thread_inst_sel*self.num_instrs/(clk * curr_cycle)
    Pipelinep =Pipeline*duty*self.num_instrs/(clk * curr_cycle)
    IFQp = IFQ*self.num_instrs/(clk * curr_cycle)
    CLKp = Core_CLK*self.num_instrs/(clk * curr_cycle)

    cpu_power = IRFp + ALUp + FRFp + FPUp + Bypassp + Decp + DCLp 
    cpu_power = cpu_power + TH_INST_SELp + Pipelinep + IFQp + CLKp

    #cpu_power           = max_cpu_power * (1 + 1*ipc/self.max_ipc)/(1 + 1)
    cpu_power           = cpu_power + (self.num_L1I_accs + self.num_L1I_ev_coh) * (itlb + l1i_rd_dyn + l1i_rd_dyn_tag) / (clk * curr_cycle)
    cpu_power           = cpu_power + (self.num_L1I_coh_accs- self.num_L1I_ev_coh) * l1i_rd_dyn_tag / (clk * curr_cycle)
    cpu_power           = cpu_power + (self.num_L1D_rd_accs + self.num_L1D_ev_coh + self.num_L1D_ev_cap) * (dtlb + l1d_rd_dyn + l1d_rd_dyn_tag) / (clk * curr_cycle)
    cpu_power           = cpu_power + (self.num_L1D_ev_coh + self.num_L1D_ev_cap) * dwbb / (clk * curr_cycle)
    cpu_power           = cpu_power + (self.num_L1D_coh_accs + self.num_L1D_ev_cap + \
                                       self.num_L1D_wr_misses + self.num_L1I_coh_accs + \
                                       self.num_L1I_misses) * intra_dir_dyn / (clk * curr_cycle)
    cpu_power           = cpu_power + (self.num_L2_rd_accs + self.num_L1D_wr_accs) * (l1d_wr_dyn +l1d_wr_dyn_tag) / (clk * curr_cycle)
    cpu_power           = cpu_power + (self.num_L1D_coh_accs - self.num_L1D_ev_coh - self.num_L1D_ev_cap) * l1d_rd_dyn_tag / (clk * curr_cycle)
    cpu_power           = cpu_power + (self.num_L2_rd_accs + self.num_L2_ev_coh + self.num_L2_ev_cap) * (missb + fillb + prefetchb + l2_rd_dyn + l2_rd_dyn_tag) / (clk * curr_cycle)
    cpu_power           = cpu_power + (self.num_L2_coh_accs - self.num_L2_ev_coh - self.num_L2_ev_cap) * l2_rd_dyn_tag / (clk * curr_cycle)
    cpu_power           = cpu_power + (self.num_MC_rds + self.num_L2_wr_accs) * (l2_wr_dyn + l2_wr_dyn_tag) / (clk * curr_cycle)
    cpu_power           = cpu_power + (L2_mfbuffer_dyn*2*self.num_L2_wr_misses +\
                           L2_WBB_dyn*2*(self.num_L2_ev_cap + self.num_L2_ev_coh) +\
                           L2_prefetchbuffer_dyn*2*self.num_L2_wr_misses)/(clk * curr_cycle)        

    traffic_through_intra_crossbar = (self.num_L1D_rd_misses+self.num_L1D_wr_misses)*(0.25+1) + self.num_L1I_misses*(0.25+1) + \
                                     self.num_L1I_coh_accs*(1+0.25) + self.num_L1D_coh_accs*(1+0.25) + \
                                     self.num_L1D_ev_cap*(1+0.25)
    cpu_power = cpu_power + Local_xbar_dyn * traffic_through_intra_crossbar / (clk * curr_cycle)
    
    self.num_Dir_accs = self.num_Dir_i_to_tr + self.num_Dir_e_to_tr + self.num_Dir_s_to_tr + self.num_Dir_m_to_tr + \
                   self.num_Dir_m_to_i + self.num_Dir_tr_to_i + self.num_Dir_tr_to_e + self.num_Dir_tr_to_s + \
                   self.num_Dir_tr_to_m + self.num_Dir_nacks + self.num_Dir_bypass + \
                   self.num_Dir_evict + self.num_Dir_invalidate + self.num_Dir_from_mc
    cpu_power           = cpu_power + self.num_Dir_accs*dir_dyn / (clk * curr_cycle)
    cpu_power           = cpu_power + (self.xbar_accs) * l2_main_xbar_wr_dyn / (clk * curr_cycle)
    cpu_power           = cpu_power + l1i_leak + l1d_leak + l2_leak + dir_leak + l2_main_xbar_leak
    cpu_power           = cpu_power + iprefetchb_leak + itlb_leak + dtlb_leak + miss_leak + fillb_leak
    cpu_power           = cpu_power + dprefetchb_leak + dwbb_leak + EXU_leak + FPU_leak + Local_xbar_leak
    cpu_power           = cpu_power + MC_logic_leak
    cpu_power           = cpu_power + Top_wire + Core_wire + L2_wire + Xbar_wire + MC_wire + Router_wire
    cpu_power           = cpu_power + IFU_wire + LSU_wire + EXU_wire
    pd_perc             = 1.0*self.active_pd_time/(self.num_MCs*self.num_ticks)
    mem_standby_power   = main_standby * self.num_MCs * self.num_ranks_per_MC * ( (1 - pd_perc) + pd_perc*pd_power_scale )
    mem_refresh_power   = main_refresh * self.num_MCs * self.num_ranks_per_MC
#    mem_dynamic_power   = (self.num_MC_acts*main_act_dyn/self.num_vmds_per_rank + self.num_MC_rds*main_rd_dyn + self.num_MC_wrs*main_wr_dyn) / (clk * curr_cycle)
    mem_dynamic_power   = (self.num_MC_acts*(main_act_dyn + MC_logic_dyn)/self.num_vmds_per_rank + self.num_MC_rds*(main_rd_dyn + MC_logic_dyn) + self.num_MC_wrs*(main_wr_dyn + MC_logic_dyn)) / (clk * curr_cycle)
    mem_io_power        = (self.num_MC_acts*bus_act + self.num_MC_rds*bus_rd + self.num_MC_wrs*bus_wr) / (clk*curr_cycle) / 2  # todo -- /2 is a hack currently
    energy_delay        = (cpu_power + mem_standby_power + mem_refresh_power + mem_dynamic_power + mem_io_power) * curr_cycle * curr_cycle

    return (cpu_power, mem_standby_power, mem_refresh_power, mem_dynamic_power, mem_io_power, energy_delay, pd_perc)


  def show_simple(self, args):
    #print fpformat.fix(1.0*self.num_instrs*self.ticks_per_cycle/self.num_ticks, 2), fpformat.fix(1.0*self.xbar_accs*self.ticks_per_cycle/self.num_ticks, 2), fpformat.fix(1.0*(self.num_MC_rds+self.num_MC_wrs)*self.ticks_per_cycle/self.num_ticks, 2),fpformat.fix(100.0*self.num_MC_acts/(self.num_MC_rds+self.num_MC_wrs), 2) + '%'
    #print fpformat.fix(1.0*self.num_instrs*self.ticks_per_cycle/self.num_ticks, 2), fpformat.fix(100.0*self.num_MC_acts/(self.num_MC_rds+self.num_MC_wrs), 2), args
    # the last one in the below line has a hack at the end
    print self.md.mdparams['pts.mc.scheduling_policy'], self.md.mdparams['pts.mc.vmd_page_sz'], self.md.mdparams['pts.mc.num_cached_pages_per_bank'], self.num_instrs, self.num_MC_rds + self.num_MC_wrs, self.num_MC_acts, fpformat.fix(1.0*self.num_instrs*self.ticks_per_cycle/self.num_ticks, 2), fpformat.fix(100.0*self.num_MC_acts/(self.num_MC_rds+self.num_MC_wrs), 2), fpformat.fix(100*(self.num_MC_acts-self.num_MC_pres+self.num_RBoL_hits+self.num_RBoL_misses)/(self.num_MC_rds+self.num_MC_wrs+1), 2), self.num_DRAM_pages
    sys.exit()
 

  def show(self):
    # show summary
    print 'L1I'
    print ' - # of requests = '+str(self.num_L1I_accs)
    print ' - # of coherency accesses = '+str(self.num_L1I_coh_accs)
    print ' - miss rate = ' + fpformat.fix(100.0*self.num_L1I_misses/self.num_L1I_accs,2) + '%'
    
    print 'L1D'
    print ' - # of RD requests = '+str(self.num_L1D_rd_accs)
    print ' - # of WR requests = '+str(self.num_L1D_wr_accs)
    print ' - # of coherency (evictions, accesses) = ('+str(self.num_L1D_ev_coh)+', '+str(self.num_L1D_coh_accs)+')'
    print ' - # of capacity evictions = '+str(self.num_L1D_ev_cap)
    print ' - RD miss rate = ' + fpformat.fix(100.0*self.num_L1D_rd_misses/self.num_L1D_rd_accs,2) + '%'
    print ' - WR miss rate = ' + fpformat.fix(100.0*self.num_L1D_wr_misses/self.num_L1D_wr_accs,2) + '%'
    print ' - coherency access ratio = ' + fpformat.fix(100.0*self.num_L1D_coh_accs/(self.num_L1D_coh_accs+self.num_L1D_rd_accs+self.num_L1D_wr_accs), 2) + '%'
    
    print 'L2'
    print ' - # of RD requests = '+str(self.num_L2_rd_accs)
    print ' - # of WR requests = '+str(self.num_L2_wr_accs)
    print ' - # of coherency (evictions, accesses) = ('+str(self.num_L2_ev_coh)+', '+str(self.num_L2_coh_accs)+')'
    print ' - # of capacity evictions = '+str(self.num_L2_ev_cap)
    print ' - RD miss rate = ' + fpformat.fix(100.0*self.num_L2_rd_misses/self.num_L2_rd_accs, 2) + '%'
    print ' - WR miss rate = ' + fpformat.fix(100.0*self.num_L2_wr_misses/self.num_L2_wr_accs, 2) + '%'
    print ' - coherency access ratio = ' + fpformat.fix(100.0*self.num_L2_coh_accs/(self.num_L2_coh_accs+self.num_L2_rd_accs+self.num_L2_wr_accs), 2) + '%'
    
    print 'Xbar'
    print ' - # of accesses = '+str(self.xbar_accs)
    
    self.num_Dir_accs = self.num_Dir_i_to_tr + self.num_Dir_e_to_tr + self.num_Dir_s_to_tr + self.num_Dir_m_to_tr + \
                   self.num_Dir_m_to_i + self.num_Dir_tr_to_i + self.num_Dir_tr_to_e + self.num_Dir_tr_to_s + \
                   self.num_Dir_tr_to_m + self.num_Dir_nacks + self.num_Dir_bypass + \
                   self.num_Dir_evict + self.num_Dir_invalidate + self.num_Dir_from_mc
    if self.num_Dir_accs > 0:
      print 'Dir'
      print ' - # of accesses = '+str(self.num_Dir_accs)+', # of directory cache accesses = '+str(self.num_Dir_cache_acc)
      print ' - ratio (i->tr, e->tr, s->tr, m->tr, m->i, tr->i, tr->e, tr->s, tr->m) = (' \
            + fpformat.fix(100.0*self.num_Dir_i_to_tr/self.num_Dir_accs, 3) + ', '\
            + fpformat.fix(100.0*self.num_Dir_e_to_tr/self.num_Dir_accs, 3) + ', '\
            + fpformat.fix(100.0*self.num_Dir_s_to_tr/self.num_Dir_accs, 3) + ', '\
            + fpformat.fix(100.0*self.num_Dir_m_to_tr/self.num_Dir_accs, 3) + ', '\
            + fpformat.fix(100.0*self.num_Dir_m_to_i/self.num_Dir_accs, 3) + ', '\
            + fpformat.fix(100.0*self.num_Dir_tr_to_i/self.num_Dir_accs, 3) + ', '\
            + fpformat.fix(100.0*self.num_Dir_tr_to_e/self.num_Dir_accs, 3) + ', '\
            + fpformat.fix(100.0*self.num_Dir_tr_to_s/self.num_Dir_accs, 3) + ', '\
            + fpformat.fix(100.0*self.num_Dir_tr_to_m/self.num_Dir_accs, 3) + ') %'
      print ' - ratio (nacks, bypass, evict, invalidate, from_mc) = (' \
            + fpformat.fix(100.0*self.num_Dir_nacks/self.num_Dir_accs, 3) + ', '\
            + fpformat.fix(100.0*self.num_Dir_bypass/self.num_Dir_accs, 3) + ', '\
            + fpformat.fix(100.0*self.num_Dir_evict/self.num_Dir_accs, 3) + ', '\
            + fpformat.fix(100.0*self.num_Dir_invalidate/self.num_Dir_accs, 3) + ', '\
            + fpformat.fix(100.0*self.num_Dir_from_mc/self.num_Dir_accs, 3) + ') %'
      print ' - directory cache miss rate = '+ fpformat.fix(100.0*self.num_Dir_cache_miss/(1+self.num_Dir_cache_acc),3)+' %'
    
    if self.num_MC_rds > 0:
      print 'MC'
      print ' - # of RD requests = ' + str(self.num_MC_rds)
      print ' - # of WR requests = ' + str(self.num_MC_wrs)
      print ' - ACT / (RD + WR)  = ' + fpformat.fix(100.0*self.num_MC_acts/(self.num_MC_rds+self.num_MC_wrs), 2) + '%'
    else:
      self.num_MC_rds = 1
      self.num_MCs    = 1
    
    print ''
    print 'access ratio [ L1 : L2 : Xbar : Dir : MC ] = [ ' \
          + fpformat.fix((1.0*self.num_L1I_accs+self.num_L1D_rd_accs+self.num_L1D_wr_accs)/(self.num_MC_rds+self.num_MC_wrs), 2) + ' : ' \
          + fpformat.fix((1.0*self.num_L2_rd_accs+self.num_L2_wr_accs)/(self.num_MC_rds+self.num_MC_wrs), 2) + ' : ' \
          + fpformat.fix((1.0*self.xbar_accs)/(self.num_MC_rds+self.num_MC_wrs), 2) + ' : ' \
          + fpformat.fix((1.0*self.num_Dir_accs)/(self.num_MC_rds+self.num_MC_wrs), 2) + ' : 1 ]'
    print '# of cond (broadcast, signal, wait)        = (' + str(self.num_cond_broadcast) + ', ' \
          + str(self.num_cond_signal) + ', ' + str(self.num_cond_wait) + ')'
    print '# of (lock, trylock, barrier)              = (' + str(self.num_lock) + ', ' \
          + str(self.num_trylock) + ', ' + str(self.num_barrier/self.num_hthreads) + ')'
    
    print ''
    print '# of instrs = ' + str(self.num_instrs) + ' = ' + fpformat.fix(1.0*self.num_instrs/10**9, 3) + 'G,  # of x87 instrs = ' + fpformat.fix(1.0*self.num_x87_ops/10**9, 3) + 'G,  # of instrs with spin loops = ' + fpformat.fix(1.0*self.num_instrs_spin/10**9, 3) + 'G'
    print 'IPC         = ' + fpformat.fix(1.0*self.num_instrs*self.ticks_per_cycle/self.num_ticks, 2)
    print 'Xbar BW     = ' + fpformat.fix(1.0*self.xbar_accs*self.ticks_per_cycle/self.num_ticks, 2) + ' accs/cycle'
    print 'MC  BW      = ' + fpformat.fix(1.0*(self.num_MC_rds+self.num_MC_wrs)*self.ticks_per_cycle/self.num_ticks, 3) + ' accs/cycle,  active PD time = ' + fpformat.fix(100.0*self.active_pd_time/(self.num_MCs*self.num_ticks), 2) + ' %'
    print 'avg mem WR latency          = ' + fpformat.fix(1.0*self.total_mem_wr_time/self.num_L1D_wr_accs/self.ticks_per_cycle, 3) + ' cycles'
    print 'avg mem RD latency          = ' + fpformat.fix(1.0*self.total_mem_rd_time/self.num_L1D_rd_accs/self.ticks_per_cycle, 3) + ' cycles'
    print '# of mem ops per instr       = ' + fpformat.fix(1.0*(self.num_L1D_rd_accs+self.num_L1D_wr_accs)/self.num_instrs, 3)
    print '# of branch misses per instr = ' + fpformat.fix(1.0*self.num_br_misses/self.num_instrs, 5)
    print '# of TLBD misses per instr   = ' + fpformat.fix(1.0*self.num_TLBD_misses/self.num_instrs, 5)
    print '# of TLBI misses per instr   = ' + fpformat.fix(1.0*self.num_TLBI_misses/self.num_instrs, 5)
    
    print '(# of L2 misses) / (# of instructions) = ' + fpformat.fix(1.0*(self.num_L2_rd_misses + self.num_L2_wr_misses)/self.num_instrs,4)
    print '(# MC accesses) / (# of instructions)  = ' + fpformat.fix(1.0*(self.num_MC_rds + self.num_MC_wrs)/self.num_instrs,4)
    
