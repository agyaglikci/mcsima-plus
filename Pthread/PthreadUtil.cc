#include "PthreadUtil.h"

namespace PinPthread
{

/* --------------------------------------------------------------------------- */
/* StartThreadFunc:                                                            */
/* wrapper function for the thread func to catch the end of the thread         */
/* --------------------------------------------------------------------------- */

void StartThreadFunc(void*(*func)(void*), void* arg)
{
#ifdef TARGET_IA32E
    void * retval = NULL;
#else
    void* retval = func(arg);
#endif
    pthread_exit(retval);
}

} // namespace PinPthread
