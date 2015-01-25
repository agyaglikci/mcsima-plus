SHELL = /bin/sh
.PHONY: all depend clean
.SUFFIXES: .cc .o

default: all

TOOLS_DIR = ..
EXTENGINELIB = true
#include ./makefile.gnu.config

PIN_HOME ?= $(TOOLS_DIR)

# Select static or dynamic linking for tool
# only applies to unix
#PIN_DYNAMIC = -static
PIN_DYNAMIC = -ldl

PIN_CXXFLAGS   = -DBIGARRAY_MULTIPLIER=1 -DUSING_XED $(DBG)
PIN_CXXFLAGS  += -fno-strict-aliasing -I$(PIN_HOME)/Include -I$(PIN_HOME)/InstLib
PIN_LPATHS     = -L$(PIN_HOME)/Lib/ -L$(PIN_HOME)/ExtLib/
PIN_LDFLAGS    = $(DBG)

TARGET_LONG=intel64
PIN_KIT ?= ../../..

XEDKIT        = $(PIN_KIT)/extras/xed2-$(TARGET_LONG)
PIN_LPATHS   += -L$(XEDKIT)/lib -L$(PIN_KIT)/$(TARGET_LONG)/lib -L$(PIN_KIT)/$(TARGET_LONG)/lib-ext
PIN_CXXFLAGS += -I$(XEDKIT)/include -I$(PIN_KIT)/extras/components/include \
                -I$(PIN_KIT)/source/include/pin -I$(PIN_KIT)/source/include/pin/gen
VSCRIPT_DIR = $(PIN_KIT)/source/include/pin

PIN_BASE_LIBS := 
PIN_BASE_LIBS += -lxed
PIN_BASE_LIBS += -ldwarf -lelf ${PIN_DYNAMIC}

PIN_CXXFLAGS += -DTARGET_IA32E -DHOST_IA32E
PIN_CXXFLAGS += -fPIC
PIN_CXXFLAGS += -DTARGET_LINUX
PIN_CXXFLAGS += $(OPT)

PIN_SOFLAGS = -shared -Wl,-Bsymbolic -Wl,--version-script=$(VSCRIPT_DIR)/pintool.ver
PIN_LDFLAGS += $(PIN_SOFLAGS)

PIN_LIBS = -lpin $(PIN_BASE_LIBS) $(PIN_BASE_LIBS_MAC)
PIN_LDFLAGS +=  ${PIN_LPATHS}

LIBS += -L/usr/local/lib -lsnappy
INCS += -I/usr/local/include

ifeq ($(TAG),dbg)
  DBG = -Wall
  OPT = -ggdb -g -O0
else
  DBG = -DNDEBUG
  OPT = -O3 -g
endif

CXXFLAGS_COMMON = -Wno-unknown-pragmas $(DBG) $(OPT) 
#CXX = g++ -m32
#CC  = gcc -m32
CXX = g++
CC  = gcc
PINFLAGS = 

SRCS_COMMON  = PthreadUtil.cc \
	PthreadAttr.cc \
	PthreadOnce.cc \
	PthreadKey.cc \
	PthreadMutexAttr.cc \
	PthreadMutex.cc \
	PthreadBarrier.cc \
	PthreadCondAttr.cc \
	PthreadCond.cc \
	PthreadCleanup.cc \
	PthreadCancel.cc \
	PthreadJoin.cc \
	PthreadMalloc.cc

ifneq ($(EXTENGINELIB),)
  SRCS = $(SRCS_COMMON) EEPthreadSim.cc EEPthreadScheduler.cc PTS.cc
  CXXFLAGS = $(CXXFLAGS_COMMON) -DEXTENGINE
else
  SRCS = $(SRCS_COMMON) PthreadSim.cc PthreadScheduler.cc
  CXXFLAGS = $(CXXFLAGS_COMMON)
endif

OBJS = $(patsubst %.cc,obj_$(TAG)/%.o,$(SRCS))
MYPIN_CXXFLAGS = $(subst -I../,-I$(TOOLS_DIR)/,$(PIN_CXXFLAGS))
MYPIN_LDFLAGS  = $(subst -L../,-L$(TOOLS_DIR)/,$(PIN_LDFLAGS))

all: obj_$(TAG)/mypthreadtool obj_$(TAG)/libmypthread.a
	cp -f obj_$(TAG)/mypthreadtool mypthreadtool
	cp -f obj_$(TAG)/libmypthread.a libmypthread.a

obj_$(TAG)/mypthreadtool : $(OBJS) obj_$(TAG)/mypthreadtool.o 
	$(CXX) $(OBJS) $@.o $(MYPIN_LDFLAGS) -o $@ $(PIN_LIBS) $(LIBS) -pthread
#	$(CXX) $(OBJS) $@.o $(MYPIN_LDFLAGS) -o $@ $(PIN_LIBS) $(LIBS) $(EXTENGINELIB) -pthread

obj_$(TAG)/%.o : %.cc
	$(CXX) -c $(CXXFLAGS) $(MYPIN_CXXFLAGS) $(INCS) -o $@ $<

obj_$(TAG)/libmypthread.a : mypthread.cc
	$(CC) -c -o obj_$(TAG)/mypthread.o mypthread.cc
	ar ru obj_$(TAG)/libmypthread.a obj_$(TAG)/mypthread.o
	ranlib obj_$(TAG)/libmypthread.a

clean:
	-rm -f *.o mypthreadtool pin.log libmypthread.a

