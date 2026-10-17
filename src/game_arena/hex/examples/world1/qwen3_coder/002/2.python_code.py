
import time
import random
from typing import List, Tuple, Set, Dict
import sys

class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}
    
    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
            return x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1

def get_neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    i, j = pos
    # All 8 neighbors minus (i-1,j-1) and (i+1,j+1)
    neighbors = [
        (i-1, j), (i-1, j+1),
        (i, j-1), (i, j+1),
        (i+1, j-1), (i+1, j)
    ]
    return [(r, c) for r, c in neighbors if 0 <= r <= 10 and 0 <= c <= 10]

def has_won_black(placed: Set[Tuple[int, int]]) -> bool:
    uf = UnionFind()
    top_nodes = []
    bottom_nodes = []
    
    for pos in placed:
        uf.find(pos)
        if pos[0] == 0:
            top_nodes.append(pos)
        if pos[0] == 10:
            bottom_nodes.append(pos)
            
    # Connect all top nodes to a virtual top node
    virtual_top = (-1, -1)
    for node in top_nodes:
        uf.union(virtual_top, node)
        
    # Connect all bottom nodes to a virtual bottom node
    virtual_bottom = (11, 11)
    for node in bottom_nodes:
        uf.union(virtual_bottom, node)
        
    # Union adjacent black stones
    for pos in placed:
        for neighbor in get_neighbors(pos):
            if neighbor in placed:
                uf.union(pos, neighbor)
                
    # Check if top is connected to bottom
    if virtual_top in uf.parent and virtual_bottom in uf.parent:
        return uf.find(virtual_top) == uf.find(virtual_bottom)
    return False

def has_won_white(placed: Set[Tuple[int, int]]) -> bool:
    uf = UnionFind()
    left_nodes = []
    right_nodes = []
    
    for pos in placed:
        uf.find(pos)
        if pos[1] == 0:
            left_nodes.append(pos)
        if pos[1] == 10:
            right_nodes.append(pos)
            
    # Connect all left nodes to a virtual left node
    virtual_left = (-1, -1)
    for node in left_nodes:
        uf.union(virtual_left, node)
        
    # Connect all right nodes to a virtual right node
    virtual_right = (11, 11)
    for node in right_nodes:
        uf.union(virtual_right, node)
        
    # Union adjacent white stones
    for pos in placed:
        for neighbor in get_neighbors(pos):
            if neighbor in placed:
                uf.union(pos, neighbor)
                
    # Check if left is connected to right
    if virtual_left in uf.parent and virtual_right in uf.parent:
        return uf.find(virtual_left) == uf.find(virtual_right)
    return False

class Node:
    def __init__(self, me: Set[Tuple[int, int]], opp: Set[Tuple[int, int]], color: str, parent_move: Tuple[int, int] = None, parent = None):
        self.me = me
        self.opp = opp
        self.color = color
        self.parent_move = parent_move
        self.parent = parent
        self.children: List[Node] = []
        self.visits = 0
        self.wins = 0
        self.untried_moves: List[Tuple[int, int]] = []
        self.is_terminal = False
        self.terminal_result = None
        self._init_untried_moves()
        self._check_terminal()
    
    def _init_untried_moves(self):
        all_cells = {(i, j) for i in range(11) for j in range(11)}
        used = self.me | self.opp
        self.untried_moves = list(all_cells - used)
        random.shuffle(self.untried_moves)
    
    def _check_terminal(self):
        if self.color == 'b':
            if has_won_black(self.me):
                self.is_terminal = True
                self.terminal_result = 1
                return
            elif has_won_white(self.opp):
                self.is_terminal = True
                self.terminal_result = 0
                return
        else:
            if has_won_white(self.me):
                self.is_terminal = True
                self.terminal_result = 1
                return
            elif has_won_black(self.opp):
                self.is_terminal = True
                self.terminal_result = 0
                return
        
        if not self.untried_moves and not self.children:
            self.is_terminal = True
            self.terminal_result = 0.5 # Draw (shouldn't happen in Hex)
    
    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0
    
    def best_child(self, c_param=1.414):
        choices_weights = [
            (child.wins / child.visits) + c_param * ((2 * (child.visits + 1e-9)) ** 0.5) / (self.visits + 1e-9)
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]
    
    def expand(self):
        if not self.untried_moves:
            return self
        move = self.untried_moves.pop()
        new_me = self.opp.copy()
        new_opp = self.me.copy()
        new_opp.add(move)
        new_color = 'b' if self.color == 'w' else 'w'
        child_node = Node(new_me, new_opp, new_color, move, self)
        self.children.append(child_node)
        return child_node
    
    def rollout(self) -> float:
        current_me = self.me.copy()
        current_opp = self.opp.copy()
        current_color = self.color
        moves = list({(i, j) for i in range(11) for j in range(11)} - current_me - current_opp)
        random.shuffle(moves)
        
        for move in moves:
            if current_color == 'b':
                current_me.add(move)
                if has_won_black(current_me):
                    return 1.0 if self.color == 'b' else 0.0
            else:
                current_me.add(move)
                if has_won_white(current_me):
                    return 1.0 if self.color == 'w' else 0.0
            current_me, current_opp = current_opp, current_me
            current_color = 'b' if current_color == 'w' else 'w'
        return 0.5 # Should not happen
    
    def backpropagate(self, result: float):
        self.visits += 1
        self.wins += result
        if self.parent:
            self.parent.backpropagate(1 - result)

def mcts(root: Node, time_limit: float) -> Tuple[int, int]:
    start_time = time.time()
    iterations = 0
    while time.time() - start_time < time_limit:
        node = root
        # Selection
        while not node.is_terminal and node.is_fully_expanded():
            node = node.best_child()
        
        # Expansion
        if not node.is_terminal:
            if node.untried_moves:
                node = node.expand()
            # Simulation
            result = node.rollout()
            # Backpropagation
            node.backpropagate(result)
        else:
            # Terminal node reached, just backpropagate the result
            if node.terminal_result is not None:
                node.backpropagate(node.terminal_result)
            else:
                result = node.rollout()
                node.backpropagate(result)
        iterations += 1
    
    # Select best move
    if not root.children:
        # Should not happen, but just in case pick a random unoccupied cell
        all_cells = {(i, j) for i in range(11) for j in range(11)}
        used = root.me | root.opp
        available = list(all_cells - used)
        return random.choice(available) if available else (0, 0)
    
    best_child = max(root.children, key=lambda c: c.wins / (c.visits + 1e-9))
    return best_child.parent_move

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    
    root = Node(me_set, opp_set, color)
    
    # Run MCTS with 0.95 seconds to allow some buffer
    move = mcts(root, 0.95)
    
    # Validate move is legal
    all_cells = {(i, j) for i in range(11) for j in range(11)}
    used = me_set | opp_set
    if move in used or move not in all_cells:
        # Fallback to first available move
        available = list(all_cells - used)
        if available:
            return available[0]
        else:
            # Board full, shouldn't happen but return (0,0)
            return (0, 0)
            
    return move
