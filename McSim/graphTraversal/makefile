TARGET = GRAPHTRAVERSAL
OBJS = main.o Graph.o Node.o
VPATH = SRC INCLUDE
#CFLAGS = -O0 -g -ggdb -w  -Wall
CFLAGS = -O3 -w -g -DNDEBUG -fno-builtin
#LDFLAGS = -lpthread 
LDFLAGS = ../../Pthread/libmypthread.a
WRAPPER_OBJ = ../../Apps/mcsim_wrapper.o
CC = g++ 

$(TARGET): $(OBJS) $(WRAPPER_OBJ)
	$(CC) -static $(OBJS) $(WRAPPER_OBJ) $(CFLAGS) -o $(TARGET) $(LDFLAGS)

.SUFFIXES:
.SUFFIXES:	.o .c .C .h .H

$(WRAPPER_OBJ): %.o: %.c
	gcc -O0 -g -c $< -o $@

$(OBJS): %.o: %.cc
	$(CC) -c $(CFLAGS) -c $< -o $@

clean:
	rm -f *.o $(OBJS) $(TARGET) pin*.log
