//
//  Node.h
//  GraphTraversal
//
//  Created by Abdullah Giray Yaglikci on 2/2/15.
//  Copyright (c) 2015 Pikseladam. All rights reserved.
//

#ifndef __GraphTraversal__Node__
#define __GraphTraversal__Node__

#include "definitions.h"

using namespace std;
struct hint;

class Node {
public:
    int nodeIndex;
    hint * nodeHint;
    Node(int index);
    void setHintPointer(Node * neighbor);
    Node * getHitPointer();
};

struct hint {
    uint32_t header = HINT_HEADER;
    Node * nodePointer;
    uint32_t footer = HINT_FOOTER;
};

#endif /* defined(__GraphTraversal__Node__) */
