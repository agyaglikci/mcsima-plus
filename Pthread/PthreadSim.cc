#include "PthreadSim.h"

using namespace PinPthread;

/* --------------------------------------------------------------------------- */
/* PthreadSim Constructor and Destructor:                                      */
/* --------------------------------------------------------------------------- */

//PthreadSim::PthreadSim(uint32_t argc, char** argv) :
PthreadSim::PthreadSim(uint32_t port_num) :
  new_thread_id(0)
{
  mallocmanager = new PthreadMalloc();
  scheduler = new PthreadScheduler();
  joinmanager = new PthreadJoinManager();
  cancelmanager = new PthreadCancelManager();
  cleanupmanager = new PthreadCleanupManager();
  condmanager = new PthreadCondManager();
  mutexmanager = new PthreadMutexManager();
  tlsmanager = new PthreadTLSManager();
  barriermanager = new PthreadBarrierManager();
  pthread_create(NULL, NULL, NULL, 0, 0);
}

void PthreadSim::initiate(CONTEXT * ctxt)
{
}

PthreadSim::~PthreadSim() 
{
  delete scheduler;
  delete joinmanager;
  delete cancelmanager;
  delete cleanupmanager;
  delete condmanager;
  delete mutexmanager;
  delete tlsmanager;
  delete barriermanager;
}

/* --------------------------------------------------------------------------- */
/* pthread_cancel:                                                             */
/* send a cancellation request to the given thread                             */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_cancel(pthread_t thread) 
{
  if (scheduler->current->second->executed == false)
  {
    return 0;
  }
  if (!scheduler->IsThreadValid(thread))
  {
    std::cout << "[ERROR] Canceling a Nonexistent Thread: "
      << dec << thread << "!\n" << flush;
    return ESRCH;
  }
  if (cancelmanager->Cancel(thread)) 
  {
    ASSERTX(thread != scheduler->GetCurrentThread());
#if VERBOSE
    std::cout << "Cancel Thread " << thread << " Immediately\n" << flush;
#endif
    pthread_t joining_thread;
    if (joinmanager->KillThread(thread, PTHREAD_CANCELED, &joining_thread)) 
    {
      scheduler->UnblockThread(joining_thread);
    }
    cancelmanager->KillThread(thread);
    tlsmanager->KillThread(thread);
    scheduler->KillThread(thread);
  }
  return 0;
}

/* --------------------------------------------------------------------------- */
/* pthread_cleanup_pop:                                                        */
/* remove the most recently installed cleanup handler                          */
/* also execute the handler if execute is not 0                                */
/* --------------------------------------------------------------------------- */

void PthreadSim::pthread_cleanup_pop_(int execute, CONTEXT* ctxt) 
{
  cleanupmanager->PopHandler(scheduler->GetCurrentThread(), execute, ctxt);
}

/* --------------------------------------------------------------------------- */
/* pthread_cleanup_push:                                                       */
/* install the routine function with argument arg as a cleanup handler for     */
/* the current thread                                                          */
/* --------------------------------------------------------------------------- */

void PthreadSim::pthread_cleanup_push_(ADDRINT routine, ADDRINT arg) 
{
  cleanupmanager->PushHandler(scheduler->GetCurrentThread(), routine, arg);
}

/* --------------------------------------------------------------------------- */
/* pthread_cond_broadcast:                                                     */
/* restart all the threads that are waiting on the given condition variable    */
/* nothing happens if no threads are waiting on cond                           */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_cond_broadcast(pthread_cond_t* cond) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
#if VERBOSE
  std::cout << "Thread " << dec << scheduler->GetCurrentThread() 
    << " Broadcasts on Condition " << hex << cond << "\n" << flush;
#endif
  pthread_t waiting_thread;
  pthread_mutex_t* mutex;
  while (condmanager->HasMoreWaiters(cond)) 
  {
    condmanager->RemoveWaiter(cond, &waiting_thread, &mutex);
#if VERBOSE
    std::cout << "Release Waiter " << dec << waiting_thread << "\n" << flush;
    std::cout << "Thread " << dec << waiting_thread << " Locks Mutex "
      << hex << mutex << "\n" << flush;
#endif
    bool blocked = mutexmanager->Lock(waiting_thread, mutex, false);
    if (!blocked) 
    {
      scheduler->UnblockThread(waiting_thread);
    }
  }
  return 0;
}

/* --------------------------------------------------------------------------- */
/* pthread_cond_destroy:                                                       */
/* destroy a condition variable, freeing the resources it might hold           */
/* as in the linuxthreads implementation, only check that there are no waiters */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_cond_destroy(pthread_cond_t* cond) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
  if (condmanager->HasMoreWaiters(cond)) 
  {
    std::cout << "[ERROR] Destroying Condition " << hex << cond
      << " Even Though There Are Still Waiting Threads!\n" << flush;
    return EBUSY;
  }
  return 0;
}

/* --------------------------------------------------------------------------- */
/* pthread_cond_signal:                                                        */
/* restart one of the threads that are waiting on the given condition variable */
/* if several threads are waiting on cond, an arbitrary one is restarted,      */
/* nothing happens if no threads are waiting on cond                           */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_cond_signal(pthread_cond_t* cond) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
#if VERBOSE
  std::cout << "Thread " << dec << scheduler->GetCurrentThread() 
    << " Signals on Condition " << hex << cond << "\n" << flush;
#endif
  if (condmanager->HasMoreWaiters(cond)) 
  {
    pthread_t waiting_thread;
    pthread_mutex_t* mutex;
    condmanager->RemoveWaiter(cond, &waiting_thread, &mutex);
#if VERBOSE
    std::cout << "Release Waiter " << dec << waiting_thread << "\n" << flush;
    std::cout << "Thread " << dec << waiting_thread << " Locks Mutex "
      << hex << mutex << "\n" << flush;
#endif
    bool blocked = mutexmanager->Lock(waiting_thread, mutex, false);
    if (!blocked) 
    {
      scheduler->UnblockThread(waiting_thread);
    }
  }
  return 0;
}

/* --------------------------------------------------------------------------- */
/* pthread_cond_timedwait:                                                     */
/* same as pthread_cond_wait, but bounds the duration of the wait              */
/* --------------------------------------------------------------------------- */

void PthreadSim::pthread_cond_timedwait(pthread_cond_t* cond, pthread_mutex_t* mutex,
    const struct timespec* abstime, CONTEXT * context) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return;
  }
  ASSERTX(abstime->tv_sec > 3600*10);
  pthread_cond_wait(cond, mutex, context);
}

/* --------------------------------------------------------------------------- */
/* pthread_cond_wait:                                                          */
/* atomically unlocks the mutex and waits for the condition variable to be     */
/* signaled (the mutex must be locked on entrace to pthread_cond_wait)         */
/* re-acquires the mutex before returning                                      */
/* --------------------------------------------------------------------------- */

void PthreadSim::pthread_cond_wait(pthread_cond_t* cond, pthread_mutex_t* mutex,
    CONTEXT * context) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return;
  }
  pthread_t current = scheduler->GetCurrentThread();
#if VERBOSE
  std::cout << "Thread " << dec << current << " Waits on Condition "
    << hex << cond << "\n" << flush;
#endif
  pthread_mutex_unlock(mutex);
  condmanager->AddWaiter(cond, current, mutex);
  scheduler->BlockThread(current);
  scheduler->SwitchThreads(context, true);
}

/* --------------------------------------------------------------------------- */
/* pthread_create:                                                             */
/* create a new thread with the given attribute                                */
/* start the thread running func(arag) at the given starting point             */
/* --------------------------------------------------------------------------- */

void PthreadSim::pthread_create(pthread_t* thread, pthread_attr_t* _attr,
    CONTEXT* startctxt,
    ADDRINT func, ADDRINT arg) 
{
#if VERBOSE
  std::cout << "Create Thread " << dec << new_thread_id << "\n" << flush;
#endif
  pthread_attr_t attr;
  if (_attr != NULL) 
  {
    attr = *_attr;
  }
  else 
  {
    attr = PthreadAttr::PTHREAD_ATTR_DEFAULT();
  }
  scheduler->AddThread(new_thread_id, &attr, startctxt, func, arg);
  joinmanager->AddThread(new_thread_id, &attr);
  cancelmanager->AddThread(new_thread_id);
  tlsmanager->AddThread(new_thread_id);
  if (thread != NULL) 
  {
    *thread = new_thread_id;
  }
  new_thread_id++;
  //docontextswitch(startctxt);
}

/* --------------------------------------------------------------------------- */
/* pthread_detach:                                                             */
/* put a running thread in the detached state, so that resources are           */
/* freed upon termination; do not detach if other threads are joining          */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_detach(pthread_t thread) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
  /* cannot detach a nonexistent thread */
  if (!scheduler->IsThreadValid(thread))
  {
    std::cout << "[ERROR] Detaching a nonexistent thread: "
      << dec << thread << "!\n" << flush;
    return ESRCH;
  }
  return joinmanager->DetachThread(thread);
}

/* --------------------------------------------------------------------------- */
/* pthread_equal:                                                              */
/* determine if two thread identifiers refer to the same thread                */
/* return non-zero if they are the same thread, 0 otherwise                    */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_equal(pthread_t thread1, pthread_t thread2) 
{
  if (thread1 == thread2) 
  {
    return 1;
  }
  else 
  {
    return 0;
  }
}

/* --------------------------------------------------------------------------- */
/* pthread_exit:                                                               */
/* the current thread terminates with the return value retval                  */
/* destroy the current thread and run the next scheduled thread                */
/* --------------------------------------------------------------------------- */

void PthreadSim::pthread_exit(void* retval, CONTEXT* ctxt) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return;
  }
  pthread_t current = scheduler->GetCurrentThread();
  pthread_cleanup_pop_(1, ctxt);
#if VERBOSE
  std::cout << "Thread " << dec << current << " Exits\n" << flush;
#endif
  pthread_t joining_thread;
  if (joinmanager->KillThread(current, retval, &joining_thread)) 
  {
    scheduler->UnblockThread(joining_thread);
  }
  cancelmanager->KillThread(current);
  tlsmanager->KillThread(current);
  scheduler->KillThread(current);
  scheduler->SwitchThreads(NULL, true);
}

/* --------------------------------------------------------------------------- */
/* pthread_getattr:                                                            */
/* return the attributes associated with the thread                            */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_getattr(pthread_t th, pthread_attr_t* _attr) 
{
  /* NYI: detachstate, schedpolicy, inheritsched, scope */
  pthread_attr_t attr = PthreadAttr::PTHREAD_ATTR_DEFAULT();
  scheduler->GetAttr(th, &attr);
  joinmanager->GetAttr(th, &attr);
  _attr = &attr;
  return 0;
}

/* --------------------------------------------------------------------------- */
/* pthread_getspecific:                                                        */
/* return the data for the current thread associated with the given key        */
/* --------------------------------------------------------------------------- */

void* PthreadSim::pthread_getspecific(pthread_key_t key) 
{
  pthread_t current = scheduler->GetCurrentThread();
  return tlsmanager->GetData(current, key);
}

/* --------------------------------------------------------------------------- */
/* pthread_join:                                                               */
/* suspend the current thread until th terminates                              */
/* thread_return gets the return value of th                                   */
/* --------------------------------------------------------------------------- */

void PthreadSim::pthread_join(pthread_t th, void** thread_return, CONTEXT* ctxt) 
{
  if (scheduler->current->second->executed == false)
  {
    return;
  }
  pthread_t current = scheduler->GetCurrentThread();
  pthread_testcancel(ctxt);
#if VERBOSE
  std::cout << "Thread " << dec << current << " Joins Thread " << th << "\n" << flush;
#endif
  bool blocked = joinmanager->JoinThreads(current, th, thread_return);
  if (blocked) 
  {
    scheduler->BlockThread(current);
    scheduler->SwitchThreads(ctxt, true);
  }
}

/* --------------------------------------------------------------------------- */
/* pthread_key_create:                                                         */
/* allocate a key for all currently executing threads                          */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_key_create(pthread_key_t* key, void(*func)(void*)) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
  ASSERTX(key != NULL);
  int error = tlsmanager->AddKey(key, func);
#if VERBOSE
  std::cout << "Thread " << dec << scheduler->GetCurrentThread()
    << " Creates Key " << hex << *key << "\n" << flush;
#endif
  return error;
}

/* --------------------------------------------------------------------------- */
/* pthread_key_delete:                                                         */
/* deallocate a key for all currently executing threads                        */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_key_delete(pthread_key_t key) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
#if VERBOSE
  std::cout << "Delete Key " << hex << key << "\n" << flush;
#endif
  return tlsmanager->RemoveKey(key);
}

/* --------------------------------------------------------------------------- */
/* pthread_kill:                                                               */
/* kill the given thread (ignore the signal parameter)                         */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_kill(pthread_t thread, int signo) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
#if VERBOSE
  std::cout << "Kill Thread " << dec << thread << "\n" << flush;
#endif
  if (scheduler->IsThreadValid(thread) && (signo != 0))
  {
    cancelmanager->SetState(thread, PTHREAD_CANCEL_ENABLE, NULL);
    cancelmanager->SetType(thread, PTHREAD_CANCEL_ASYNCHRONOUS, NULL);
    pthread_cancel(thread);
    return 0;
  }
  else 
  {
    return ESRCH;
  }
}

/* --------------------------------------------------------------------------- */
/* pthread_mutex_lock:                                                         */
/* the current thread either blocks on or locks the given mutex                */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_mutex_lock(pthread_mutex_t* mutex, CONTEXT * context)
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
  pthread_t current = scheduler->GetCurrentThread();
  bool blocked = mutexmanager->Lock(current, mutex, false);
#if VERBOSE
  std::cout << "Thread " << dec << current << " Locks Mutex " << hex << mutex << "\n" << flush;
#endif
  if (blocked)
  {
    scheduler->BlockThread(current);
    scheduler->SwitchThreads(context, true);
  }

  return 0;
}

/* --------------------------------------------------------------------------- */
/* pthread_mutex_trylock:                                                      */
/* the current thread tries to lock the given mutex                            */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_mutex_trylock(pthread_mutex_t* mutex) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
  pthread_t current = scheduler->GetCurrentThread();
#if VERBOSE
  std::cout << "Thread " << dec << current << " Trylocks Mutex " << hex << mutex << "\n" << flush;
#endif
  return mutexmanager->Lock(current, mutex, true);
}

/* --------------------------------------------------------------------------- */
/* pthread_mutex_unlock:                                                       */
/* the current thread releases the given mutex                                 */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_mutex_unlock(pthread_mutex_t* mutex) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
  pthread_t current = scheduler->GetCurrentThread();
  pthread_t spinning_thread;
  int error;
  bool blocked = mutexmanager->Unlock(current, mutex, &spinning_thread, &error);
#if VERBOSE
  std::cout << "Thread " << dec << current << " Unlocks Mutex " << hex << mutex << "\n" << flush;
#endif
  if (blocked)
  {
    scheduler->UnblockThread(spinning_thread);
  }
  return error;
}

/* --------------------------------------------------------------------------- */
/* pthread_self:                                                               */
/* return the current thread's ID                                              */
/* --------------------------------------------------------------------------- */

pthread_t PthreadSim::pthread_self() 
{
  return scheduler->GetCurrentThread();
}

/* --------------------------------------------------------------------------- */
/* pthread_setcancelstate:                                                     */
/* change the cancellation state for the current thread                        */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_setcancelstate(int newstate, int* oldstate) 
{
  return cancelmanager->SetState(scheduler->GetCurrentThread(), newstate, oldstate);
}

/* --------------------------------------------------------------------------- */
/* pthread_setcanceltype:                                                      */
/* change the cancellation type for the current thread                         */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_setcanceltype(int newtype, int* oldtype) 
{
  return cancelmanager->SetType(scheduler->GetCurrentThread(), newtype, oldtype);
}

/* --------------------------------------------------------------------------- */
/* pthread_setspecific:                                                        */
/* associate the given data with the given key for the current thread          */
/* --------------------------------------------------------------------------- */

int PthreadSim::pthread_setspecific(pthread_key_t key, void* data) 
{
  pthread_t current = scheduler->GetCurrentThread();
  return tlsmanager->SetData(current, key, data);
}

/* --------------------------------------------------------------------------- */
/* pthread_testcancel:                                                         */
/* test for pending cancellation and execute it                                */
/* --------------------------------------------------------------------------- */

void PthreadSim::pthread_testcancel(CONTEXT* ctxt) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return;
  }
  pthread_t current = scheduler->GetCurrentThread();
  if (cancelmanager->IsCanceled(current) )
  {
#if VERBOSE
    std::cout << "Thread " << dec << current << " is Canceled\n" << flush;
#endif
    pthread_exit(PTHREAD_CANCELED, ctxt);
  }
}

/* --------------------------------------------------------------------------- */
/* inmtmode:                                                                   */
/* determine whether there is more than 1 active thread running                */
/* --------------------------------------------------------------------------- */

bool PthreadSim::inmtmode() 
{
  return (scheduler->GetNumActiveThreads() > 1);
}

/* --------------------------------------------------------------------------- */
/* docontextswitch:                                                            */
/* request the scheduler to schedule a new thread                              */
/* --------------------------------------------------------------------------- */

void PthreadSim::docontextswitch(const CONTEXT * context) 
{
  if (mallocmanager->CanSwitchThreads()) 
  {
    scheduler->SwitchThreads(context, false);
  }
#if VERYVERYVERBOSE
  else 
  {
    std::cout << "In the Middle of Memory (De)Allocation -> "
      << "Disable Context Switching\n" << flush;
  }
#endif    
}

void PthreadSim::process_ins(
    const CONTEXT * context, ADDRINT ip,
    ADDRINT raddr, ADDRINT raddr2, UINT32 rlen,
    ADDRINT waddr, UINT32 wlen,
    bool isbranch, bool isbranchtaken, uint32_t category,
    uint32_t rr0, uint32_t rr1, uint32_t rr2, uint32_t rr3,
    uint32_t rw0, uint32_t rw1, uint32_t rw2, uint32_t rw3)
{
  if (scheduler->nactive > 1)
  cout << hex << context << "  " << ip << "  " << PIN_GetContextReg(context, REG_STACK_PTR) << "  " << PIN_GetContextReg(context, REG_GBP) << "  " << PIN_GetContextReg(context, REG_GDI) << "  " << PIN_GetContextReg(context, REG_GAX) <<  endl;
  if (rlen || wlen)
  {
    docontextswitch(context);
  }
}


void PthreadSim::mcsim_skip_instrs_begin()
{
}


void PthreadSim::mcsim_skip_instrs_end()
{
}


void PthreadSim::mcsim_spinning_begin()
{
}


void PthreadSim::mcsim_spinning_end()
{
}


void PthreadSim::set_stack(CONTEXT * ctxt)
{
}


/* --------------------------------------------------------------------------- */
/* threadsafemalloc:                                                           */
/* pass the call/return information to mallocmanager to turn context switching */
/* off and on appropriately for thread safety                                  */
/* --------------------------------------------------------------------------- */

void PthreadSim::threadsafemalloc(bool iscall, bool istailcall,
    const string* rtn_name)
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return;
  }
  mallocmanager->Analyze(scheduler->GetCurrentThread(),
      iscall, istailcall, rtn_name);
}


int PthreadSim::pthread_barrier_init(
    pthread_barrier_t * barrier,
    pthread_barrierattr_t * barrierattr,
    unsigned int num)
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
  barriermanager->InitWaiters(barrier, num);
  return 0;
}


int PthreadSim::pthread_barrier_destroy(pthread_barrier_t * barrier)
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
  barriermanager->DestroyWaiters(barrier);
  return 0;
}


int PthreadSim::pthread_barrier_wait(
    pthread_barrier_t * barrier,
    CONTEXT * context) 
{
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
  pthread_t current = scheduler->GetCurrentThread();
  if (scheduler->nactive > 1 && scheduler->current->second->executed == false)
  {
    return 0;
  }
#if VERBOSE
  std::cout << "Thread " << dec << current << " Waits on Barrier " << hex << barrier << "\n" << flush;
#endif
  if (barriermanager->AddWaiter(barrier, current))
  {
    pthread_t waiting_thread;
    while (barriermanager->HasMoreWaiters(barrier)) 
    {
      barriermanager->RemoveWaiter(barrier, &waiting_thread);
      if (current != waiting_thread) 
      {
        scheduler->UnblockThread(waiting_thread);
        //scheduler->UnblockThread(waiting_thread, ins_barrier);
      }
      //else
      //{
      //  scheduler->add_synch_instruction(current, ins_barrier);
      //}
    }
  }
  else
  {
    scheduler->BlockThread(current);
    scheduler->SwitchThreads(context, true);
  }

  return 0;
}

