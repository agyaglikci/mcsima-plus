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

/* --------------------------------------------------------------------------- */
/* PthreadBarrier:                                                             */
/* manipulates pthread barrier objects                                         */
/* manages the synchronization of threads using barriers                       */
/* --------------------------------------------------------------------------- */

#ifndef PTHREAD_BARRIER_H
#define PTHREAD_BARRIER_H

#include "PthreadAttr.h"

namespace PinPthread 
{

    class PthreadBarrier
    {
      public:
        static int pthread_barrier_init(pthread_barrier_t*, const pthread_barrierattr_t *, unsigned int num);
        static int pthread_barrier_destroy(pthread_barrier_t*);
    };

    typedef std::vector<pthread_t> pthread_barrierwaiterfifo_t;

    class PthreadBarrierWaiters
    {
      public:
        PthreadBarrierWaiters(unsigned int num);
        ~PthreadBarrierWaiters();
        void PushWaiter(pthread_t);
        void PopWaiter(pthread_t*);
        bool IsEmpty();
      public:
        unsigned int num_participants;
        pthread_barrierwaiterfifo_t waiters; // fifo of waiting threads for one barrier
    };

    typedef std::map<pthread_barrier_t*, PthreadBarrierWaiters *> pthreadbarrier_queue_t;

    class PthreadBarrierManager 
    {
      public:
        bool HasMoreWaiters(pthread_barrier_t *);
        bool AddWaiter(pthread_barrier_t *, pthread_t);  // true if ready to remove
        void RemoveWaiter(pthread_barrier_t *, pthread_t *);
        void InitWaiters(pthread_barrier_t *, unsigned int num);
        void DestroyWaiters(pthread_barrier_t *);
      private:
        pthreadbarrier_queue_t barriers; // list of waiting threads indexed by barrier
    };
    
} // namespace PinPthread
    
#endif  // #ifndef PTHREAD_BARRIER_H
