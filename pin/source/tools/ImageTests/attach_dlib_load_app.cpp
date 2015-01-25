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
/*
 *  This application used by attach_dlib_load_jit_tool pintool.
 *	It performs some mathematical calculations, waits until pin attached
 *	and then loads additional libraries.
 */
// @ORIGINAL_AUTHOR: Evgeny Volodarsky

#include <iostream>
#include <fstream>
#include <string>
#include <cstdlib>		/* srand, rand */
#include <ctime>		/* time */
#include <cmath>		/* sin */
#include <dlfcn.h>		/* dlopen */
#include <unistd.h>		/* sleep */

#define TIME_LIMIT 300 // Set the time limit to 5 minutes

using namespace std;

int main( int argc, char *argv[] )
{
	// Check the number of parameters
    if (argc < 4) {
        cerr << "Usage: " << argv[0] << " otput_file ready_file dll_file" << endl;
        return 1;
    }
	// Output file definition
	ofstream out(argv[1], ios::trunc);
	
	double x;
	fstream ready_file;

	// Initialize random seed
	srand(time(NULL));
	
	// Calculate and print sin() of 10 random values
	for(int i=0 ; i<10 ; ++i)
	{
		x = 100.0 * rand() / RAND_MAX;
		out << "x = " << x << "\t-->\t" << "sin(x) = " << sin(x) << endl;
	}

	ready_file.open(argv[2], ios::out | ios::trunc);
	if(!ready_file.is_open() || ready_file.fail())
	{
		cerr << "Testapp: Error opening ready.log for writing" << endl;
		return 1;
	}
	ready_file << "Testapp: ready.log created";
	ready_file.close();
	ready_file.clear();

	string line(""), ready("Pin attached");
	int counter = 0;
	// Wait until Pin will be attached to test application process
	while( line != ready )
	{
		out << "Testapp: Waiting for pintool. Start sleeping for 1 second..." << endl;
		sleep(1);
		out << "Testapp: End sleeping..." << endl;
		counter++; 
		if( counter >= TIME_LIMIT ){
			cerr << "Testapp: Something wrong. Waiting too much time..." << endl;
			return 1;
		}
		
		ready_file.open(argv[2], ios::in);
		if(!ready_file.is_open() || ready_file.fail())
		{
			cerr << "Testapp: Error opening ready.log for reading" << endl;
			continue;
		}
		getline(ready_file,line);
		ready_file.close();
		ready_file.clear();
	}

	void *dl1 = dlopen("libutil.so.1", RTLD_LAZY);
	if( dl1 == NULL ) out << "Testapp: libutil.so.1 NOT LOADED!!!" << endl;
	void *dl2 = dlopen(argv[3], RTLD_LAZY);
	if( dl2 == NULL ) out << "Testapp: " << argv[3] << " NOT LOADED!!!" << endl;

	ready_file.open(argv[2], ios::out | ios::trunc);
	if(!ready_file.is_open() || ready_file.fail())
	{
		cerr << "Testapp: Error opening ready.log for writing" << endl;
		return 1;
	}
	ready_file << "Testapp loaded additional libraries";
	ready_file.close();
	ready_file.clear();

	out << "Testapp: Done!" << endl;
	out.close();
	
	return 0;
}
