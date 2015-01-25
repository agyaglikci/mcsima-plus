#!/usr/bin/env python
# -*- python -*-

import os
import sys

if len(sys.argv) != 2:
    print 'Error Usage: python cntrl_client.py <file_name>'
    exit(1)
    
fifo_name = sys.argv[1]
if not os.path.exists(fifo_name):
    print 'fifo file: ' + fifo_name + ' does not exists'
    print 'Have you run SDE with interactive controller?' 
    exit(1)

try:
    f = open(fifo_name, 'w')
    f.write("1")
    f.close()
except:
    print 'ERROR: failed sending signal to SDE'
    
    
