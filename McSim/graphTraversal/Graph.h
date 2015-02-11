//
//  Graph.h
//  GraphTraversal
//
//  Created by Abdullah Giray Yaglikci on 2/3/15.
//  Copyright (c) 2015 Pikseladam. All rights reserved.
//

#ifndef __GraphTraversal__Graph__
#define __GraphTraversal__Graph__

#include "definitions.h"
#include "Node.h"

class Graph{
public:
    Node * nodeArray [GRAPH_SIZE];
    int32_t adjacencyMatrix [GRAPH_SIZE][GRAPH_SIZE];
    
    Graph();
    void logAdjMatrix();
    Node * getStrongestNeighbor(int nodeIndex);

};


#endif /* defined(__GraphTraversal__Graph__) */
