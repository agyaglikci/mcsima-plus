#include "PthreadScheduler.h"
#include <stdlib.h>

using namespace PinPthread;

/* --------------------------------------------------------------------------- */
/* PthreadScheduler Constructor and Destructor                                 */
/* --------------------------------------------------------------------------- */

PthreadScheduler::PthreadScheduler() :
    nactive(0)                        {}

PthreadScheduler::~PthreadScheduler() {}

/* --------------------------------------------------------------------------- */
/* AddThread:                                                                  */
/* add an active thread to the queue                                           */
/* --------------------------------------------------------------------------- */

void PthreadScheduler::AddThread(pthread_t thread, pthread_attr_t* attr,
                                 CONTEXT* startctxt,
                                 ADDRINT func, ADDRINT arg)
{
    ASSERTX(pthreads.find(thread) == pthreads.end());
    pthreads[thread] = new Pthread(attr, startctxt, func, arg);
    if (pthreads.size() == 1) 
    {
        current = pthreads.begin();
    }
    nactive++;
}

/* --------------------------------------------------------------------------- */
/* KillThread:                                                                 */
/* destroy the given thread                                                    */
/* --------------------------------------------------------------------------- */

void PthreadScheduler::KillThread(pthread_t thread) 
{
    if (thread == GetCurrentThread()) 
    {
        ASSERTX(IsActive(thread));
        FixupCurrentPtr();
    }
    pthreads.erase(thread);
    nactive--;
}

/* --------------------------------------------------------------------------- */
/* SwitchThreads:                                                              */
/* schedule a new thread, or run a new thread upon the current                 */
/* thread's termination                                                        */
/* --------------------------------------------------------------------------- */

void PthreadScheduler::SwitchThreads(const CONTEXT* context, bool mustswitch) 
{
    if (pthreads.empty()) 
    {
#if VERBOSE
        std::cout << "No more threads to run - exit program!\n" << flush;
#endif
        exit(0);
    }
    else if ((nactive > 1)  || mustswitch)
    {
      /*if (context != NULL)
      {
        cout << hex << GetCurrentThread() << " " << PIN_GetContextReg(context, REG_INST_PTR) << endl;
      }*/
      if (current->second->executed == false && context != NULL)
      {
        current->second->executed = true;
        return;
      }
      else
      {
        current->second->executed = false;
      }

        if (context != NULL) 
        {
#if VERYVERYVERBOSE
            std::cout << "Save Thread " << dec << GetCurrentThread() << "\n" << flush;
#endif
            /*for (int i = REG_PHYSICAL_CONTEXT_BEGIN; i <= REG_PHYSICAL_CONTEXT_END; i++)
            {
              current->second->registers[i] = PIN_GetContextReg(context, (REG)i);
            }
            PIN_GetContextFPState(context, current->second->fpstate);*/
            PIN_SaveContext(context, GetCurrentContext());
        }
        AdvanceCurrentPtr();
        if (HasStarted(current))
        {
#if VERYVERYVERBOSE
            std::cout << "Run Thread " << dec << GetCurrentThread() << "\n" << flush;
#endif
            /*for (int i = REG_PHYSICAL_CONTEXT_BEGIN; i <= REG_PHYSICAL_CONTEXT_END; i++)
            {
              PIN_SetContextReg(GetCurrentStartCtxt(), (REG)i, current->second->registers[i]);
            }
            PIN_SetContextFPState(GetCurrentStartCtxt(), current->second->fpstate);*/
            PIN_ExecuteAt(GetCurrentStartCtxt());
        }
        else 
        {
#if VERBOSE
            std::cout << "Start Thread " << dec << GetCurrentThread() << "\n" << flush;
#endif
            StartThread(current);
            /*for (int i = REG_PHYSICAL_CONTEXT_BEGIN; i <= REG_PHYSICAL_CONTEXT_END; i++)
            {
              PIN_SetContextReg(GetCurrentStartCtxt(), (REG)i, current->second->registers[i]);
            }
            PIN_SetContextFPState(GetCurrentStartCtxt(), current->second->fpstate);*/
            PIN_ExecuteAt(GetCurrentStartCtxt());
        }
    }
}

/* --------------------------------------------------------------------------- */
/* BlockThread:                                                                */
/* deschedule the given thread                                                 */
/* --------------------------------------------------------------------------- */

void PthreadScheduler::BlockThread(pthread_t thread) 
{
    ASSERTX(IsActive(thread));
    SetActiveState(thread, false);
    nactive--;
    ASSERT(nactive > 0, "[ERROR] Deadlocked!\n");
}

/* --------------------------------------------------------------------------- */
/* UnblockThread:                                                              */
/* enable the given thread to be scheduled again                               */
/* --------------------------------------------------------------------------- */

void PthreadScheduler::UnblockThread(pthread_t thread) 
{
    ASSERTX(!IsActive(thread));
    SetActiveState(thread, true);
    nactive++;
}

/* --------------------------------------------------------------------------- */
/* GetCurrentThread:                                                           */
/* return the id of the current thread running                                 */
/* --------------------------------------------------------------------------- */

pthread_t PthreadScheduler::GetCurrentThread() 
{
    return current->first;
}

/* --------------------------------------------------------------------------- */
/* IsThreadValid:                                                              */
/* determine whether the given thread is valid (active or inactive)            */
/* --------------------------------------------------------------------------- */

bool PthreadScheduler::IsThreadValid(pthread_t thread) 
{
    return (pthreads.find(thread) != pthreads.end());
}

/* --------------------------------------------------------------------------- */
/* GetAttr:                                                                    */
/* return the given thread's attribute fields relevant to the scheduler        */
/* --------------------------------------------------------------------------- */

void PthreadScheduler::GetAttr(pthread_t thread, pthread_attr_t* attr) 
{
    pthread_queue_t::iterator threadptr = pthreads.find(thread);
    ADDRINT stacksize = (threadptr->second)->stacksize;
    ADDRINT* stack = (threadptr->second)->stack;
    if (stack == NULL) 
    {
        PthreadAttr::_pthread_attr_setstack(attr, (void*)0xbfff0000, 0x10000);
    }
    else 
    {
        PthreadAttr::_pthread_attr_setstack(attr, (void*)stack, stacksize);
    }
}

/* --------------------------------------------------------------------------- */
/* GetNumActiveThreads:                                                        */
/* return the number of currently active threads                               */
/* --------------------------------------------------------------------------- */

UINT32 PthreadScheduler::GetNumActiveThreads() 
{
    return nactive;
}

/* --------------------------------------------------------------------------- */
/* Scheduling Functions:                                                       */
/* --------------------------------------------------------------------------- */

void PthreadScheduler::SetCurrentPtr(pthread_t thread) 
{
    current = GetThreadPtr(thread);
}

void PthreadScheduler::AdvanceCurrentPtr() 
{
    do 
    {
        current++;
        if (current == pthreads.end()) 
        {
            current = pthreads.begin();
        }
    } while (!IsActive(current));
}

void PthreadScheduler::FixupCurrentPtr() 
{
    if (current == pthreads.begin()) 
    {
        current = --(pthreads.end());
    }
    else 
    {
        current--;
    }
}

/* --------------------------------------------------------------------------- */
/* Pthread Constructor and Destructor:                                         */
/* --------------------------------------------------------------------------- */

Pthread::Pthread(pthread_attr_t* attr, CONTEXT* _startctxt,
                 ADDRINT func, ADDRINT arg) :
    active(true), executed(false)
{
    if (_startctxt != NULL)   // new threads
    {
        started = false;
        stacksize = 0x100000;
        if (((stacksize / sizeof(ADDRINT)) % 2) == 0)       // align stack
        {
            stacksize += sizeof(ADDRINT);
        }
        stack = (ADDRINT*)mmap(0, stacksize,
                               PROT_READ | PROT_WRITE | PROT_EXEC,
                               MAP_PRIVATE | MAP_ANON,
                               -1, 0);
        ASSERTX(stack != MAP_FAILED);
        mprotect(stack, sizeof(ADDRINT), PROT_NONE);        // delineate top of stack
        ADDRINT* sp = &(stack[stacksize/sizeof(ADDRINT) - 1]);
        ASSERTX(((ADDRINT)sp & 0x7) == 0);
        //*(sp--) = arg;
        //*(sp--) = func;
        *(sp) = (ADDRINT)StartThreadFunc;
        PIN_SaveContext(_startctxt, &startctxt);
        cout << hex << func << "  " << arg << "  " << stack << "  " << _startctxt << "  " << &startctxt << endl;
        //*(sp)   = PIN_GetContextReg(&startctxt, REG_GBP);
        PIN_SetContextReg(&startctxt, REG_STACK_PTR, (ADDRINT)sp);
        PIN_SetContextReg(&startctxt, REG_GDI, (ADDRINT)arg);
        //PIN_SetContextReg(&startctxt, REG_GBP, (ADDRINT)sp);
        PIN_SetContextReg(&startctxt, REG_INST_PTR, (ADDRINT)func);
        /*registers = new ADDRINT[REG_PHYSICAL_CONTEXT_END + 1];
        fpstate   = new FPSTATE;
        for (int i = REG_PHYSICAL_CONTEXT_BEGIN; i <= REG_PHYSICAL_CONTEXT_END; i++)
        {
          registers[i] = PIN_GetContextReg(&startctxt, (REG)i);
        }
        PIN_GetContextFPState(&startctxt, fpstate);*/
    }
    else                      // initial thread
    {
        stack = NULL;
        stacksize = 0;
        started = true;

        /*registers = new ADDRINT[REG_PHYSICAL_CONTEXT_END + 1];
        fpstate   = new FPSTATE;*/
    }
}

Pthread::~Pthread() 
{
    //delete [] registers;
    //delete fpstate;
    //CHAR * fpstate_char = reinterpret_cast<CHAR *>(fpstate);
    munmap(stack, stacksize);
}

/* --------------------------------------------------------------------------- */
/* Functions for Manipulating STL Structure(s):                                */
/* --------------------------------------------------------------------------- */

pthread_queue_t::iterator PthreadScheduler::GetThreadPtr(pthread_t thread) 
{
    pthread_queue_t::iterator threadptr = pthreads.find(thread);
    ASSERTX(threadptr != pthreads.end());
    return threadptr;
}

bool PthreadScheduler::IsActive(pthread_t thread) 
{
    return IsActive(GetThreadPtr(thread));
}

bool PthreadScheduler::IsActive(pthread_queue_t::iterator threadptr) 
{
    return ((threadptr->second)->active);
}

void PthreadScheduler::SetActiveState(pthread_t thread, bool active) 
{
    pthread_queue_t::iterator threadptr = GetThreadPtr(thread);
    (threadptr->second)->active = active;
}

bool PthreadScheduler::HasStarted(pthread_queue_t::iterator threadptr) 
{
    return ((threadptr->second)->started);
}

void PthreadScheduler::StartThread(pthread_queue_t::iterator threadptr) 
{
    (threadptr->second)->started = true;
}

CONTEXT* PthreadScheduler::GetCurrentContext() 
{
    return (&((current->second)->startctxt));
}

CONTEXT* PthreadScheduler::GetCurrentStartCtxt() 
{
    return (&((current->second)->startctxt));
}


