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
    for (int32_t i = 0 ; i < GRAPH_SIZE ; i++) {
        //cout << "Neighbors of node#"<<i<<" are: ";
        for (int32_t j = 0 ; j < NUM_OF_LINKS ; j++) {
            double incos = (j+1) * M_PI / GRAPH_SIZE;
            int32_t target = ((int) ((i+1) * cos(incos))) % GRAPH_SIZE;
            int32_t a = 0;
            while ((target == i || adjacencyMatrix[i][target] != -1 ) && a < GRAPH_SIZE){
                target = (target + 1) % GRAPH_SIZE;
                a++;
            }
            int32_t strength = 100 * exp(-(((i+j)%GRAPH_SIZE)-GRAPH_SIZE/2)^2/100);
            if (strength < 0) strength = 1;
            this->adjacencyMatrix[i][target] = strength;
            //cout << "("<<target<<","<<strength<<") ";
        }
        //cout << endl;
    }
    
    for (int i = 0 ; i < GRAPH_SIZE; i++) {
        nodeArray[i] = new Node(i);
    }
    
    for (int i = 0; i < GRAPH_SIZE; i++) {
        nodeArray[i]->setHintPointer(this->getStrongestNeighbor(i));
    }
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
    return this->nodeArray[strongestIndex];
}


