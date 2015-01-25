/*
 * Copyright (c) 2010 The Hewlett-Packard Development Company
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * Authors: Jung Ho Ahn
 */

#include "PTSDirectory.h"
#include "PTSRBoL.h"
#include "PTSMemoryController.h"
#include "PTSXbar.h"
#include <assert.h>
#include <iomanip>
#include <cstdlib>

using namespace PinPthread;
using namespace std;

ostream & operator<<(ostream & output, rbol_status_type rst)
{
  switch (rst)
  {
    case rst_valid:        output << "rst_valid"; break;
    case rst_dirty:        output << "rst_dirty"; break;
    case rst_coming:       output << "rst_coming"; break;
    case rst_dirty_coming: output << "rst_dirty_coming"; break;
    case rst_invalid:      output << "rst_invalid"; break;
    default: break;
  }
  return output;
}


RBoL::RBoL(
    component_type type_,
    uint32_t num_,
    McSim * mcsim_)
 :Component(type_, num_, mcsim_),
  req_l(), rep_l(),
  use_rbol   (get_param_str("use_rbol") == "true")
{
  process_interval = get_param_uint64("process_interval", 80);
}


RBoL::~RBoL()
{
}


void RBoL::show_state(uint64_t address)
{
}


void RBoL::add_req_event(
    uint64_t event_time,
    LocalQueueElement * local_event,
    Component * from)
{
  if (event_time % process_interval != 0)
  {
    event_time = event_time + process_interval - event_time%process_interval;
  }
  if (use_rbol == false)
  {
    mc->add_req_event(event_time + process_interval, local_event);
  }
  else
  {
    //if (num == 2) {cout << event_time << " Q " << hex << local_event->address << dec << " "; local_event->display();}
    geq->add_event(event_time, this);
    req_event.insert(pair<uint64_t, LocalQueueElement *>(event_time, local_event));
  }
}


void RBoL::add_rep_event(
    uint64_t event_time,
    LocalQueueElement * local_event,
    Component * from)
{
  if (event_time % process_interval != 0)
  {
    event_time = event_time + process_interval - event_time%process_interval;
  }
  if (use_rbol == false)
  {
    directory->add_rep_event(event_time + process_interval, local_event);
  }
  else
  {
    //if (num == 2) {cout << event_time << " P " << hex << local_event->address << dec << " "; local_event->display();}
    geq->add_event(event_time, this);
    rep_event.insert(pair<uint64_t, LocalQueueElement *>(event_time, local_event));
  }
}


uint32_t RBoL::process_event(uint64_t curr_time)
{
  ASSERTX(0);
  return 0;
}


