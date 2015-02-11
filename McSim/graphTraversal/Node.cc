//
//  Node.cpp
//  GraphTraversal
//
//  Created by Abdullah Giray Yaglikci on 2/2/15.
//  Copyright (c) 2015 Pikseladam. All rights reserved.
//

#include "Node.h"

Node::Node(int index){
    nodeIndex = index;
    nodeHint = new hint();
}

void Node::setHintPointer(Node *neighbor){
    nodeHint->nodePointer = neighbor;
    //cout << "Strongest neighbor for node #" << this->nodeIndex << " is node #" << neighbor->nodeIndex << endl;
}

Node * Node::getHitPointer(){
    return nodeHint->nodePointer;
}