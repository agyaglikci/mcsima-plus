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

#ifndef PTS_RBOL_H
#define PTS_RBOL_H

#include "McSim.h"
#include <list>
#include <stack>
#include <queue>
#include <set>

namespace PinPthread
{
  enum rbol_status_type
  {
    rst_valid,
    rst_dirty,
    rst_coming,  // from a memory controller
    rst_dirty_coming,  // similar to rst_coming but this will be rst_dirty
    rst_invalid,
  };


  class RBoL : public Component
  {
    public:
      list<LocalQueueElement *> req_l;
      list<LocalQueueElement *> rep_l;

      RBoL(component_type type_, uint32_t num_, McSim * mcsim_);
      ~RBoL();

      MemoryController * mc;  // downlink
      Directory        * directory;         // uplink

      bool use_rbol;

      void add_req_event(uint64_t, LocalQueueElement *, Component * from = NULL);
      void add_rep_event(uint64_t, LocalQueueElement *, Component * from = NULL);
      uint32_t process_event(uint64_t curr_time);
      void show_state(uint64_t);
  };
}

#endif

