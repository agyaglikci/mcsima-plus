//
//  Graph.cpp
//  GraphTraversal
//
//  Created by Abdullah Giray Yaglikci on 2/3/15.
//  Copyright (c) 2015 Pikseladam. All rights reserved.
//

#include "Graph.h"

Graph::Graph(){
    
    for (int i = 0; i < GRAPH_SIZE; i++) {
        for (int j = 0; j < GRAPH_SIZE ; j++ ) {
            this->adjacencyMatrix[i][j] = -1;
        }
    }
    
    // Adjacency matrix weight values are calculated as Gaussian Distribution by using the following coefficients:
    // Variance = NUM_OF_LINKS
    // Scale = GRAPH_SIZE
    // Expected Value is some offset of some scaled index (scale factor is 61 since it is a prime number; offset is 3 for no reason)
    double_t alpha = 100*GRAPH_SIZE / sqrt(2 * M_PI * NUM_OF_LINKS);
    for (int32_t i = 0 ; i < GRAPH_SIZE ; i++) {
        int32_t expectedValue = (i*61+3)%GRAPH_SIZE;
        for (int32_t j = 0 ; j < GRAPH_SIZE ; j++) {
            this->adjacencyMatrix[i][j] = (int) (alpha * exp(-pow(j-expectedValue,2)/(GRAPH_SIZE)));
        }
    }
    
    for (int i = 0 ; i < GRAPH_SIZE; i++) {
        nodeArray[i] = new Node(i);
    }
    
    for (int i = 0; i < GRAPH_SIZE; i++) {
        nodeArray[i]->setHintPointer(this->getStrongestNeighbor(i));
    }
    //logAdjMatrix();

}

void Graph::logAdjMatrix(){
    for (int i = 0; i < GRAPH_SIZE; i++) {
        for (int j = 0; j < GRAPH_SIZE; j++) {
            cout << this->adjacencyMatrix[i][j] << "\t";
        }
        cout << endl;
    }
    
}

Node * Graph::getStrongestNeighbor(int nodeIndex){
    int strongestIndex = (int) (nodeIndex / 2);
    int strongestValue = this->adjacencyMatrix[nodeIndex][strongestIndex];
    
    for (int j = 0; j < GRAPH_SIZE; j++) {
        if (strongestValue < this->adjacencyMatrix[nodeIndex][j]) {
            strongestIndex = j;
            strongestValue = this->adjacencyMatrix[nodeIndex][j];
        }
    }
    //cout << "Strongest of #" << nodeIndex << " is #" << strongestIndex << " with value " << strongestValue << endl;
    return this->nodeArray[strongestIndex];
}


