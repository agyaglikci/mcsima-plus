//
//  main.cpp
//  GraphTraversal
//
//  Created by Abdullah Giray Yaglikci on 2/2/15.
//  2015, University of Notre Dame.
//

#include "definitions.h"
#include "Graph.h"
#include "Node.h"

using namespace std;

extern "C" {
extern void mcsim_skip_instrs_begin();
extern void mcsim_skip_instrs_end();
extern void mcsim_spinning_begin();
extern void mcsim_spinning_end();
int32_t log_2(uint64_t);
}

pthread_mutex_t mut;

class thread_args
{
public:
    uint32_t proc_num;
    uint32_t num_processors;
    Graph * myGraph;
    double * value;
    pthread_barrier_t * barrier;

};

void *gotoNext(void *arg)
{
    thread_args *p=(thread_args *)arg;
    int startIndex = p->proc_num;
    *(p->value) = 1.0;
    pthread_barrier_wait(p->barrier);

    Node myNode = *p->myGraph->nodeArray[startIndex];
    for (int i = 0 ; i < NUM_OF_PROC * NUM_OF_LINKS ; i++) {
        myNode = *myNode.getHitPointer();
    }
    return (NULL);
}

int main(int argc, char* argv[]) {
    mcsim_skip_instrs_begin();
    pthread_barrier_t * barrier = new pthread_barrier_t;
    pthread_barrier_init(barrier, NULL, NUM_OF_PROC);
    pthread_t *threads = new pthread_t[NUM_OF_PROC];;
    thread_args * th_args = new thread_args[NUM_OF_PROC];

    Graph * myGraph = new Graph();
    
    /* Start up thread */
    
    for (uint32_t i = 0; i < NUM_OF_PROC; i++)
    {
        th_args[i].proc_num=i;
        th_args[i].myGraph = myGraph;
        th_args[i].num_processors = NUM_OF_PROC;
        th_args[i].value          = new double;
        *(th_args[i].value)       = 0.0;
        th_args[i].barrier        = barrier;
    }

    mcsim_skip_instrs_end();
    double sum = 0.0;

    for (uint32_t i = 1; i < NUM_OF_PROC; i++)
    {
        pthread_create(&(threads[i]), NULL, gotoNext, (void *)(&(th_args[i])));
    }
    
    gotoNext((void *)(&(th_args[0])));
    sum += *(th_args[0].value);

    /* Synchronize the completion of each thread. */
    
    for (uint32_t i = 1; i < NUM_OF_PROC; i++)
    {
        pthread_join(threads[i], NULL);
        sum += *(th_args[i].value);
    }

    cout << sum << endl;
    return 0;   
}

int32_t log_2(uint64_t number)
{
    int cumulative = 1;
    int32_t out = 0;
    int done = 0;
    
    while ((cumulative < number) && (!done) && (out < 50)) {
        if (cumulative == number) {
            done = 1;
        } else {
            cumulative = cumulative * 2;
            out ++;
        }
    }
    
    if (cumulative == number) {
        return(out);
    } else {
        return(-1);
    }
}

