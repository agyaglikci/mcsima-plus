/*BEGIN_LEGAL 
Intel Open Source License 

Copyright (c) 2002-2014 Intel Corporation. All rights reserved.
 
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.  Redistributions
in binary form must reproduce the above copyright notice, this list of
conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.  Neither the name of
the Intel Corporation nor the names of its contributors may be used to
endorse or promote products derived from this software without
specific prior written permission.
 
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE INTEL OR
ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
END_LEGAL */


#include "init_alarm.H"
#include "control_manager.H"


using namespace CONTROLLER;

VOID INIT_ALARM::Activate(CONTROL_MANAGER* manager){

    // If start event already called then just exit
    if (_start_called)
        return;

    _manager = manager;
    _first = TRUE;

    TRACE_AddInstrumentFunction(OnTrace, this);
#ifdef TARGET_LINUX
    PIN_AddForkFunction(FPOINT_AFTER_IN_CHILD, AfterForkInChildCallback, 
                        (VOID *)this);
#endif
}

VOID INIT_ALARM::OnTrace(TRACE trace, VOID *vthis){
    INIT_ALARM *me = static_cast<INIT_ALARM*>(vthis);

    // Add an instrumentation point to the very first instruction.
    if (me->_first)
    {
        INS firstIns = BBL_InsHead(TRACE_BblHead(trace));
        if (me->_manager->PassContext())
        {
            INS_InsertCall(
                firstIns, IPOINT_BEFORE, AFUNPTR(Start),
                IARG_CALL_ORDER, me->_manager->GetInsOrder(),
                IARG_CONTEXT, 
                IARG_INST_PTR,
                IARG_THREAD_ID, 
                IARG_ADDRINT, me, 
                IARG_END);
        }
        else
        {
            INS_InsertCall(
                firstIns, IPOINT_BEFORE, AFUNPTR(Start),
                IARG_CALL_ORDER, me->_manager->GetInsOrder(),
                IARG_ADDRINT, static_cast<ADDRINT>(0),
                IARG_INST_PTR,
                IARG_THREAD_ID, 
                IARG_ADDRINT, me,
                IARG_END);
        }
        me->_first = false;
    }
}

#ifdef TARGET_LINUX
// After fork() the child inherits all the data structures from the parent
// so we need to reset the "_first" flag.
VOID INIT_ALARM::AfterForkInChildCallback(THREADID tid, const CONTEXT* ctxt,
                                          VOID * arg)
{
    INIT_ALARM *me = static_cast<INIT_ALARM*>(arg);
    me->_first = TRUE;
}
#endif

VOID INIT_ALARM::Start(CONTEXT *ctxt, ADDRINT ip, THREADID tid, VOID *vthis){
    INIT_ALARM *me = static_cast<INIT_ALARM*>(vthis);
    me->_manager->Fire(EVENT_START,ctxt,Addrint2VoidStar(ip),tid,TRUE);

    // Flag to indicate that start event was already called
    me->_start_called = TRUE;

    // We want to call the handler exactly once.  Invalidate the trace to 
    // prevent it from being called again even if the program's first 
    // instruction is re-executed.
    CODECACHE_InvalidateTraceAtProgramAddress(ip);
}

