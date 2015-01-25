#include <iostream>
#include <iomanip>
#include <fstream>
#include <string>
#include <sstream>
#include "PTS.h"
#include "McSim.h"
#include <unistd.h>
#include <stdint.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <signal.h>

using namespace std;
using namespace PinPthread;

struct Programs
{
  int32_t num_threads;
  int32_t agile_bank_th_perc;
  string num_skip_first_instrs;
  uint32_t tid_to_htid;  // id offset
  string trace_name;
  string path;
  string directory;
  string agile_page_list_file_name;
  vector<string> prog_n_argv;
  int sockfd;
  struct sockaddr_in my_addr;
  char * buffer;
  int port_num;
  int pid;
};


int main(int argc, char * argv[])
{
  string line, temp;
  istringstream sline;
  string mdfile;
  string runfile;
  bool   run_manually = false;
  uint64_t remap_interval = 0;
  string remapfile;
  for (int i = 0; i < argc; i++)
  {
    if (argv[i] == string("-mdfile"))
    {
      i++;
      mdfile = argv[i];
    }
    else if (argv[i] == string("-runfile"))
    {
      i++;
      runfile = argv[i];
    }
    else if (argv[i] == string("-h"))
    {
      cout << argv[0] << " -mdfile mdfile -runfile runfile -run_manually -remapfile remapfile -remap_interval instrs" << endl;
      exit(1);
    }
    else if (argv[i] == string("-run_manually"))
    {
      run_manually = true;
    }
    else if (argv[i] == string("-remap_interval"))
    {
      i++;
      sline.clear();
      sline.str(string(argv[i]));
      sline >> remap_interval;
    }
    else if (argv[i] == string("-remapfile"))
    {
      i++;
      remapfile = argv[i];
    }
  }

  PthreadTimingSimulator * pts = new PthreadTimingSimulator(mdfile);
  string pin_name;
  string pintool_name;
  string ld_library_path_full;
  vector<Programs> programs;
  vector<uint32_t> htid_to_tid;
  vector<uint32_t> htid_to_pid;
  int32_t          addr_offset_lsb = pts->get_param_uint64("addr_offset_lsb", 48);
  uint64_t        max_total_instrs = pts->get_param_uint64("max_total_instrs", 1000000000);
  uint64_t       num_instrs_per_th = pts->get_param_uint64("num_instrs_per_th", 0);
  int32_t      interleave_base_bit = pts->get_param_uint64("pts.mc.interleave_base_bit", 14);


  ifstream fin(runfile.c_str());
  if (fin.good() == false)
  {
    cout << "failed to open the runfile " << runfile << endl;
    exit(1);
  }

  // it is assumed that pin and pintool names are listed in the first two lines
  char * pin_ptr     = getenv("PIN");
  char * pintool_ptr = getenv("PINTOOL");
  char * ld_library_path = getenv("LD_LIBRARY_PATH");
  pin_name           = (pin_ptr == NULL) ? "pinbin" : pin_ptr;
  pintool_name       = (pintool_ptr == NULL) ? "mypthreadtool" : pintool_ptr;
  
//  ld_library_path_full = string("LD_LIBRARY_PATH=")+ld_library_path;

  struct sockaddr_in their_addr;
  socklen_t addr_len = sizeof(their_addr);
  memset(&their_addr, 0, sizeof(their_addr));
  uint32_t idx    = 0;
  uint32_t offset = 0;
  uint32_t num_th_passed_instr_count = 0;
  //uint32_t num_hthreads = pts->get_num_hthreads();

  while (getline(fin, line))
  {
    // #_threads #_skip_1st_instrs dir prog_n_argv
    // if #_threads is 0, trace file is specified at the location of #_skip_1st_instrs
    if (line.empty() == true || line[0] == '#') continue;
    programs.push_back(Programs());
    sline.clear();
    if (line[0] == 'A')
    {
      sline.str(line);
      sline >> temp >> programs[idx].num_threads >> programs[idx].agile_bank_th_perc
            >> programs[idx].agile_page_list_file_name
            >> programs[idx].num_skip_first_instrs
            >> programs[idx].directory;
    }
    else
    {
      sline.str(line);
      sline >> programs[idx].num_threads;
      if (programs[idx].num_threads < -100)
      {
        programs[idx].agile_bank_th_perc = 100;
        programs[idx].num_threads = programs[idx].num_threads/(-100);
        programs[idx].trace_name = string();
        sline >> programs[idx].num_skip_first_instrs >> programs[idx].directory;
      }
      else if (programs[idx].num_threads <= 0)
      {
        programs[idx].agile_bank_th_perc = 0 - programs[idx].num_threads;
        programs[idx].num_threads = 1;
        sline >> programs[idx].trace_name >> programs[idx].directory;
      }
      else
      {
        programs[idx].trace_name = string();
        sline >> programs[idx].num_skip_first_instrs >> programs[idx].directory;
      }
    }
    
    //programs[idx].directory = string("PATH=")+programs[idx].directory+":"+string(getenv("PATH"));
    programs[idx].tid_to_htid = offset;
    for (int32_t j = 0; j < programs[idx].num_threads; j++)
    {
      htid_to_tid.push_back(j);
      htid_to_pid.push_back(idx);
    }
    while (sline.eof() == false)
    {
      sline >> temp;
      programs[idx].prog_n_argv.push_back(temp);
    }

    memset(&programs[idx].my_addr, 0, sizeof(&programs[idx].my_addr));
    programs[idx].sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    programs[idx].my_addr.sin_family = AF_INET;
    programs[idx].my_addr.sin_port = htons(0);
    programs[idx].my_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    //bzero(&(programs[idx].my_addr.sin_zero), 8);
    programs[idx].buffer = new char[sizeof(PTSMessage)];

    if (programs[idx].sockfd < 0 || bind(programs[idx].sockfd, (struct sockaddr *)&(programs[idx].my_addr), sizeof(struct sockaddr)))
    {
      cout << "network error" << endl;
      exit(1);
    }

    getsockname(programs[idx].sockfd, (struct sockaddr *)&their_addr, &addr_len);
    programs[idx].port_num = ntohs(their_addr.sin_port);
    //cout << ntohs(programs[idx].my_addr.sin_port) << "   " << inet_ntoa(programs[idx].my_addr.sin_addr) << endl;
    //cout << ntohs(their_addr.sin_port) << "   " << inet_ntoa(their_addr.sin_addr) << endl;

    if (idx > 0)
    {
      pts->add_instruction(offset, 0, 0, 0, 0, 0, 0, 0, 0,
          false, false, false, false, false,
          0, 0, 0, 0, 0, 0, 0, 0);
      pts->set_active(offset, true);
    }

    offset += programs[idx].num_threads;
    idx++;
  }
  fin.close();

  // error checkings
  if (offset > pts->get_num_hthreads())
  {
    cout << "more threads (" << offset << ") than the number of threads (" << pts->get_num_hthreads() << ") specified in " << mdfile << endl;
    exit(1);
  }

  if (programs.size() <= 0)
  {
    cout << "we need at least one program to run" << endl;
    exit(1);
  }

  if (run_manually == false)
  {
    cout << "in case when the program exits with an error, please run the following command" << endl;
    cout << "kill -9 ";
  }
  // fork n execute
  for (uint32_t i = 0; i < programs.size(); i++)
  {
    pid_t pID = fork();
    if (pID < 0)
    {
      cout << "failed to fork" << endl;
      exit(1);
    }
    else if (pID == 0)
    {
      // child process
      chdir(programs[i].directory.c_str());
      char * envp[3];
      envp [0] = NULL;
      envp [1] = NULL;
      envp [2] = NULL;

      ld_library_path_full = string("LD_LIBRARY_PATH=")+ld_library_path;

      //envp[0] = (char *)programs[i].directory.c_str();
      //envp[0] = (char *)"PATH=::$PATH:";
      programs[i].path = string("PATH=")+programs[i].directory+string(":")+string(getenv("PATH"));
      envp[0] = (char *)programs[i].path.c_str();

      if (ld_library_path == NULL)
      {

        envp[1] = (char *)"LD_LIBRARY_PATH=";

      }
      else
      {
          envp[1] = (char *)(ld_library_path_full.c_str());
//    	  envp[1] = (char *)(string("LD_LIBRARY_PATH=")+string(ld_library_path)).c_str();

      }
      //string ld_path = string("LD_LIBRARY_PATH=")+ld_library_path;
      //envp[1] = (char *)(ld_path.c_str());
      //envp[2] = NULL;

      char ** argp = new char * [programs[i].prog_n_argv.size() + 17];
      int  curr_argc = 0;
      char port_num_str[10];
      char perc_str[10];
      sprintf(port_num_str, "%d", programs[i].port_num);
      argp[curr_argc++] = (char *)pin_name.c_str();
      //argp[curr_argc++] = (char *)"-separate_memory";
      argp[curr_argc++] = (char *)"-t";
      argp[curr_argc++] = (char *)pintool_name.c_str();
      argp[curr_argc++] = (char *)"-port";
      argp[curr_argc++] = port_num_str;
      if (programs[i].trace_name.size() > 0)
      {
        argp[curr_argc++] = (char *)"-trace_name";
        argp[curr_argc++] = (char *)programs[i].trace_name.c_str();

        if (programs[i].prog_n_argv.size() > 1)
        {
          argp[curr_argc++] = (char *)"-trace_skip_first";
          argp[curr_argc++] = (char *)programs[i].prog_n_argv[programs[i].prog_n_argv.size() - 1].c_str();
        }
      }
      else
      {
        argp[curr_argc++] = (char *)"-skip_first";
        argp[curr_argc++] = (char *)programs[i].num_skip_first_instrs.c_str();
      }
      if (programs[i].agile_bank_th_perc > 0)
      {
        sprintf(perc_str, "%d", programs[i].agile_bank_th_perc);
        argp[curr_argc++] = (char *)"-agile_bank_th_perc";
        argp[curr_argc++] = perc_str;
      }
      if (programs[i].agile_page_list_file_name.empty() == false)
      {
        argp[curr_argc++] = (char *)"-agile_page_list_file_name";
        argp[curr_argc++] = (char *)programs[i].agile_page_list_file_name.c_str();
      }
      argp[curr_argc++] = (char *)"--";
      for (uint32_t j = 0; j < programs[i].prog_n_argv.size(); j++)
      {
        argp[curr_argc++] = (char *)programs[i].prog_n_argv[j].c_str();
      }
      argp[curr_argc++] = NULL;

      if (run_manually == true)
      {
        int jdx = 0;
        while (argp[jdx] != NULL)
        {
          cout << argp[jdx] << " ";
          jdx++;
        }
        cout << endl;
        exit(1);
      }
      else
      {
        execve(pin_name.c_str(), argp, envp);
      }
    }
    else 
    {
      if (run_manually == false)
      {
        cout << pID << " ";
      }
      programs[i].pid = pID;
    }
  }
  if (run_manually == false)
  {
    cout << endl << flush;
  }

  if (remap_interval != 0)
  {
    fin.open(remapfile.c_str());
    if (fin.good() == false)
    {
      cout << "failed to open the remapfile " << remapfile << endl;
      exit(1);
    }
  }

  uint64_t * num_fetched_instrs = new uint64_t[htid_to_pid.size()];
  for (uint32_t i = 0; i < htid_to_pid.size(); i++)
  {
    num_fetched_instrs[i] = 0;
  }
  int32_t * old_mapping = new int32_t [htid_to_pid.size()];
  int32_t * old_mapping_inv = new int32_t [htid_to_pid.size()];
  int32_t * new_mapping = new int32_t [htid_to_pid.size()];

  for (uint32_t i = 0; i < htid_to_pid.size(); i++)
  {
    old_mapping[i] = i;
    old_mapping_inv[i] = i;
  }

  uint64_t old_total_instrs = 0;

  // get a packet from the first program
  recvfrom(programs[0].sockfd, programs[0].buffer, sizeof(PTSMessage), 0, (struct sockaddr *)&(programs[0].my_addr), &addr_len);
  sendto  (programs[0].sockfd, programs[0].buffer, sizeof(PTSMessage), 0, (struct sockaddr *)&(programs[0].my_addr), addr_len);

  int  curr_pid   = 0;
  bool any_thread = true;

  while (any_thread)
  {
    Programs * curr_p = &(programs[curr_pid]);
    recvfrom(curr_p->sockfd, curr_p->buffer, sizeof(PTSMessage), 0, (struct sockaddr *)&(curr_p->my_addr), &addr_len);
    PTSMessage * pts_m = (PTSMessage *)curr_p->buffer;

    if (pts->mcsim->num_fetched_instrs >= max_total_instrs ||
        num_th_passed_instr_count >= offset)
    {
      for (uint32_t i = 0; i < programs.size(); i++)
      {
        kill(programs[i].pid, SIGKILL/*SIGTERM*/);
      }
      break;
    }

    if (remap_interval > 0 && 
        pts_m->type == pts_resume_simulation &&
        pts->mcsim->num_fetched_instrs/remap_interval > old_total_instrs/remap_interval)
    {
      old_total_instrs = pts->mcsim->num_fetched_instrs;

      if (!getline(fin, line))
      {
        for (uint32_t i = 0; i < programs.size(); i++)
        {
          kill(programs[i].pid, SIGKILL/*SIGTERM*/);
        }
        break;
      }
      else
      {
        sline.clear();
        sline.str(line);
        for (uint32_t i = 0; i < htid_to_pid.size(); i++)
        {
          sline >> new_mapping[i];

          if (curr_pid == old_mapping[i])
          {
            curr_pid = new_mapping[i];
          }
        }
      }

      for (uint32_t i = 0; i < htid_to_pid.size(); i++)
      {
        if (old_mapping[i] == new_mapping[i]) continue;
        pts->mcsim->add_instruction(old_mapping[i], pts->get_curr_time(), 0, 0, 0, 0, 0, 0, 0,
                                    false, false, true, true, false, 
                                    0, 0, 0, 0, new_mapping[i], 0, 0, 0);
      }
      for (uint32_t i = 0; i < htid_to_pid.size(); i++)
      {
        if (old_mapping[i] == new_mapping[i]) continue;
        pts->mcsim->add_instruction(new_mapping[i], pts->get_curr_time(), 0, 0, 0, 0, 0, 0, 0,
                                    false, false, true, true, true, 
                                    0, 0, 0, 0, old_mapping[i], 0, 0, 0);
      }
      //cout << " NEW mapping ";
      for (uint32_t i = 0; i < htid_to_pid.size(); i++)
      {
        //cout << new_mapping[i] << "  ";
        old_mapping[i] = new_mapping[i];
        old_mapping_inv[new_mapping[i]] = i;
      }
      //cout << endl;
    }

    //if (pts->get_curr_time() >= 12100000) cout << " ** " << pts_m->type << endl;
    switch (pts_m->type)
    {
      case pts_resume_simulation:
      {
        pair<uint32_t, uint64_t> ret = pts->mcsim->resume_simulation(pts_m->bool_val);  // <thread_id, time>
        curr_pid = old_mapping[htid_to_pid[ret.first]];
        curr_p = &(programs[curr_pid]);
        pts_m  = (PTSMessage *)curr_p->buffer;
        pts_m->type         = pts_resume_simulation;
        pts_m->uint32_t_val = htid_to_tid[ret.first];
        pts_m->uint64_t_val = ret.second;
      //if (ret.second >= 12100000)
      //  cout << "resume  tid = " << ret.first << ", pid = " << curr_pid << ", curr_time = " << ret.second << endl;
        break;
      }
      case pts_add_instruction:
      {
        uint32_t num_instrs = pts_m->uint32_t_val;
        uint32_t num_available_slot = 0;
        assert(num_instrs > 0);
        for (uint32_t i = 0; i < num_instrs; i++)
        {
          PTSInstr * ptsinstr = &(pts_m->val.instr[i]);
          num_available_slot = pts->mcsim->add_instruction(
            old_mapping_inv[curr_p->tid_to_htid + ptsinstr->hthreadid_],
            ptsinstr->curr_time_,
            ptsinstr->waddr + (ptsinstr->waddr  == 0 ? 0 : ((((uint64_t)curr_pid) << addr_offset_lsb) + (((uint64_t)curr_pid) << interleave_base_bit))),
            ptsinstr->wlen,
            ptsinstr->raddr + (ptsinstr->raddr  == 0 ? 0 : ((((uint64_t)curr_pid) << addr_offset_lsb) + (((uint64_t)curr_pid) << interleave_base_bit))),
            ptsinstr->raddr2+ (ptsinstr->raddr2 == 0 ? 0 : ((((uint64_t)curr_pid) << addr_offset_lsb) + (((uint64_t)curr_pid) << interleave_base_bit))),
            ptsinstr->rlen,
            ptsinstr->ip    + ((((uint64_t)curr_pid) << addr_offset_lsb) + (((uint64_t)curr_pid) << interleave_base_bit)),
            ptsinstr->category,
            ptsinstr->isbranch,
            ptsinstr->isbranchtaken,
            ptsinstr->islock,
            ptsinstr->isunlock,
            ptsinstr->isbarrier,
            ptsinstr->rr0,
            ptsinstr->rr1,
            ptsinstr->rr2,
            ptsinstr->rr3,
            ptsinstr->rw0,
            ptsinstr->rw1,
            ptsinstr->rw2,
            ptsinstr->rw3);
        }
        if (num_instrs_per_th > 0)
        {
          if (num_fetched_instrs[curr_p->tid_to_htid + pts_m->val.instr[0].hthreadid_] < num_instrs_per_th &&
              num_fetched_instrs[curr_p->tid_to_htid + pts_m->val.instr[0].hthreadid_] + num_instrs >= num_instrs_per_th)
          {
            num_th_passed_instr_count++;
            cout << "  -- hthread " << curr_p->tid_to_htid + pts_m->val.instr[0].hthreadid_ << " executed " << num_instrs_per_th
                 << " instrs at cycle " << pts_m->val.instr[0].curr_time_ << endl;
          }
        }
        num_fetched_instrs[curr_p->tid_to_htid + pts_m->val.instr[0].hthreadid_] += num_instrs;
        //PTSInstr * ptsinstr = &(pts_m->val.instr[0]);
        //if (ptsinstr->curr_time_ >= 12100000)
        //  cout << "add  tid = " << curr_p->tid_to_htid + ptsinstr->hthreadid_ << ", pid = " << curr_pid
        //       << ", curr_time = " << ptsinstr->curr_time_ << ", num_instr = " << num_instrs
        //       << ", num_avilable_slot = " << num_available_slot << endl;
        pts_m->uint32_t_val = num_available_slot;
        break;
      }
      case pts_get_num_hthreads:
        pts_m->uint32_t_val = pts->get_num_hthreads();
        break;
      case pts_get_param_uint64:
        pts_m->uint64_t_val = pts->get_param_uint64(pts_m->val.str, pts_m->uint64_t_val);
        break;
      case pts_get_param_bool:
        pts_m->bool_val = pts->get_param_bool(pts_m->val.str, pts_m->bool_val);
        break;
      case pts_get_curr_time:
        pts_m->uint64_t_val = pts->get_curr_time();
        break;
      case pts_set_active:
        pts->set_active(old_mapping_inv[curr_p->tid_to_htid + pts_m->uint32_t_val], pts_m->bool_val);
        break;
      case pts_set_stack_n_size:
        pts->set_stack_n_size(
            old_mapping_inv[curr_p->tid_to_htid + pts_m->uint32_t_val],
            pts_m->stack_val       + ((((uint64_t)curr_pid) << addr_offset_lsb) + (((uint64_t)curr_pid) << interleave_base_bit)),
            pts_m->stacksize_val);
        break;
      case pts_constructor:
        break;
      case pts_destructor:
      {
        //sendto(curr_p->sockfd, curr_p->buffer, sizeof(PTSMessage), 0, (struct sockaddr *)&(curr_p->my_addr), addr_len);
        pair<uint32_t, uint64_t> ret = pts->resume_simulation(true);  // <thread_id, time>
        if (ret.first == pts->get_num_hthreads())
        {
          any_thread = false;
          break;
        }
        pts_m->uint32_t_val = pts->get_num_hthreads();
        curr_pid = old_mapping[htid_to_pid[ret.first]];
        curr_p = &(programs[curr_pid]);
        pts_m  = (PTSMessage *)curr_p->buffer;
        pts_m->type         = pts_resume_simulation;
        pts_m->uint32_t_val = htid_to_tid[ret.first];
        pts_m->uint64_t_val = ret.second;
        //cout << curr_pid << "   " << pts_m->uint32_t_val << "   " << pts_m->uint64_t_val << endl;
        break;
      }
      default:
        cout << "type " << pts_m->type << " is not supported" << endl;
        assert(0);
        break;
    }
    sendto(curr_p->sockfd, curr_p->buffer, sizeof(PTSMessage)-sizeof(instr_n_str), 0, (struct sockaddr *)&(curr_p->my_addr), addr_len);
  }

  for (uint32_t i = 0; i < htid_to_pid.size(); i++)
  {
    cout << "  -- th[" << setw(3) << i << "] fetched " << num_fetched_instrs[i] << " instrs" << endl;
  }
  delete pts;
  /*recvfrom(programs[0].sockfd, programs[0].buffer, sizeof(PTSMessage), 0, (struct sockaddr *)&(programs[0].my_addr), &addr_len);
  cout << (((PTSMessage *)programs[0].buffer)->type) << endl;
  cout << (((PTSMessage *)programs[0].buffer)->val.str) << endl;
  strcpy(((PTSMessage *)programs[0].buffer)->val.str, "nono");
  cout << "^^" << sendto(programs[0].sockfd, programs[0].buffer, sizeof(PTSMessage), 0, (struct sockaddr *)&(programs[0].my_addr), addr_len) << endl;*/
  return 0;
}

