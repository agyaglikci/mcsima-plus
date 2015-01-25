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

#include "interactive_listener.H"

#if !defined(TARGET_WINDOWS)
#include <sys/select.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <errno.h>
#endif

using namespace CONTROLLER;

VOID INTERACTIVE_LISTENER::Active(){
    //create new thread that will listen to the FIFO 
    PIN_SpawnInternalThread(WaitForUserSiganl, this, 0 ,NULL);
    PIN_AddFiniFunction(Fini,this);
}

VOID INTERACTIVE_LISTENER::Fini(INT32, VOID* v){
#if !defined(TARGET_WINDOWS)
    INTERACTIVE_LISTENER* l = static_cast<INTERACTIVE_LISTENER*>(v);
    unlink(l->_fifo_name.c_str());
#endif
}
 

VOID INTERACTIVE_LISTENER::WaitForUserSiganl(VOID* v){
    /* this function creates the FIFO file and opens it.
     * then it checks if there is info ready to be read from the FIFO.
     * once in 0.5 sec we are checking if PIN is exiting in order to 
     * close the file descriptor and exit the loop.
     */
#if !defined(TARGET_WINDOWS)
    INTERACTIVE_LISTENER* listener = static_cast<INTERACTIVE_LISTENER*>(v);
    const char *fifo = listener->_fifo_name.c_str();
    mkfifo(fifo, S_IRWXU); //Read, write, execute by owner
    
    //opening for RW since I do not want to be blocked here
    int fd = open(fifo, O_RDWR);
    if(fd == 0){
        ASSERT(FALSE,"failed to open fifo file, errno: " + decstr(errno));
    }

    char buf[1];
    fd_set rfds;
    struct timeval tv;
    int retval;

    /* Wait up to 0.5 seconds. */
    tv.tv_sec = 0;
    tv.tv_usec = 500000; //time in microsec.

    while (1){
        if (PIN_IsProcessExiting()){
            close(fd);
            return;
        }
        FD_ZERO(&rfds);
        FD_SET(fd, &rfds);
        memset(buf,0,1);
        retval = select(fd+1, &rfds, NULL, NULL, &tv);
        if(retval == -1){
            ASSERT(FALSE,"error in select function, errno: " + decstr(errno));
        }
        else if (retval){
            int res = read(fd,buf,1);
            if (res > 0){
                if(buf[0] == '1'){
                    listener->_signaled = 1;
                }    
            }
        }
    }
#endif
}

