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
 *  This tool was created to test, if Pin loads all the required
 *  images when it is attached to application and also after 
 *  the application is loading additional libraries dynamically.
 *  attach_dlib_load_app used as a test application.
 */
// @ORIGINAL_AUTHOR: Evgeny Volodarsky

#include "pin.H"
#include <iostream>
#include <fstream>

#define LOADED_IMAGES 5 // Number of libraries that should be loaded when test app starts running

// Global variables

// A knob for defining the file with list of loaded images
KNOB<string> KnobImagesLog(KNOB_MODE_WRITEONCE, "pintool",
    "imageslog", "images.log", "specify images file name");

// A knob for defining the shared log file name
KNOB<string> KnobReadyLog(KNOB_MODE_WRITEONCE, "pintool",
    "readylog", "ready.log", "specify ready log file name (shared with test app)");
	
fstream images;				// File with list of loaded images
int counter = 0;

// Pin calls this function every time a new img is loaded.
// Here we replace the original routine.
VOID ImageLoad( IMG img, VOID *v )
{
	images << IMG_Name(img) << endl;
	counter++;
	if( counter >= LOADED_IMAGES ) {
		fstream ready_file;
		ready_file.open(KnobReadyLog.Value().c_str(), ios::out | ios::trunc);
		if(!ready_file)
		{
			std::cerr << "Error opening ready.log for writing" << endl;
			return;
		}
		ready_file << "Pin attached";
		ready_file.close();
	}
}

// This function is called when the application exits
VOID Fini(INT32 code, VOID *v)
{
    images.close();
}

// Initialize and start Pin in Jit mode.
int main( INT32 argc, CHAR *argv[] )
{
	// Initialize symbol processing
	PIN_InitSymbols();

	// Initialize pin
	PIN_Init(argc, argv);

	// Open file to create the list of loaded images
	images.open(KnobImagesLog.Value().c_str(), ios::out | ios::trunc);
	if(!images)
	{
		std::cerr << "Error opening images.log for writing" << endl;
		return 1;
	}

	// Register ImageLoad to be called when an image is loaded
	IMG_AddInstrumentFunction( ImageLoad, 0 );

	// Register Fini to be called when the application exits
	PIN_AddFiniFunction(Fini, 0);

	// Start the program in jit mode, never returns
	PIN_StartProgram();

    return 0;
}
