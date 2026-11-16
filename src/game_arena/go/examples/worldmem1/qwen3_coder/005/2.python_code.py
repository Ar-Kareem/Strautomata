
import numpy as np
import random
from collections import defaultdict
import time

# Define constants
BOARD_SIZE = 19
PASS_MOVE = (0, 0)

# Helper functions for liberties and groups
def get_neighbors(pos):
    row, col = pos
    neighbors = []
    if row > 1:
        neighbors.append((row - 1, col))
    if row < BOARD_SIZE:
        neighbors.append((row + 1, col))
    if col > 1:
        neighbors.append((row, col - 1))
    if col < BOARD_SIZE:
        neighbors.append((row, col + 1))
    return neighbors

def find_group(stone, stones):
    visited = set()
    group = set()
    stack = [stone]
    
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        group.add(current)
        
        for neighbor in get_neighbors(current):
            if neighbor in stones and neighbor not in visited:
                stack.append(neighbor)
                
    return group

def get_liberties(group, me, opponent):
    liberties = set()
    for stone in group:
        for neighbor in get_neighbors(stone):
            if neighbor not in me and neighbor not in opponent:
                liberties.add(neighbor)
    return liberties

def is_capture(move, me, opponent):
    # Check if placing a stone at move captures any opponent group
    temp_me = me + [move]
    opponent_groups = []
    visited = set()
    
    for stone in opponent:
        if stone not in visited:
            group = find_group(stone, opponent)
            opponent_groups.append(group)
            visited.update(group)
    
    for group in opponent_groups:
        if not get_liberties(group, temp_me, opponent):
            return True
    return False

def get_legal_moves(me, opponent):
    # Returns all legal moves that don't violate ko or suicide rules
    my_stones = set(me)
    opp_stones = set(opponent)
    occupied = my_stones | opp_stones
    legal_moves = []
    
    for row in range(1, BOARD_SIZE + 1):
        for col in range(1, BOARD_SIZE + 1):
            move = (row, col)
            if move in occupied:
                continue
                
            # Check suicide rule
            temp_me = me + [move]
            temp_group = find_group(move, temp_me)
            if get_liberties(temp_group, me, opponent):
                legal_moves.append(move)
            elif is_capture(move, me, opponent):
                legal_moves.append(move)
                
    return legal_moves

# MCTS Node
class MCTSNode:
    def __init__(self, move, parent=None):
        self.move = move
        self.parent = parent
        self.children = []
        self.visits = 0
        self.wins = 0
        self.untried_moves = []

    def uct_select_child(self):
        # UCB1 formula for child selection
        log_parent_visits = np.log(self.visits)
        best_value = -float('inf')
        best_child = None
        
        for child in self.children:
            uct_value = (child.wins / child.visits) + np.sqrt(2 * log_parent_visits / child.visits)
            if uct_value > best_value:
                best_value = uct_value
                best_child = child
                
        return best_child

    def add_child(self, move):
        child = MCTSNode(move, parent=self)
        self.children.append(child)
        self.untried_moves.remove(move)
        return child

    def update(self, result):
        self.visits += 1
        self.wins += result

# Simulation policy
def simulate_random_game(me, opponent):
    # Simple random simulation with basic tactical awareness
    current_me = list(me)
    current_opp = list(opponent)
    turn_count = 0
    max_turns = 100
    
    while turn_count < max_turns:
        legal_moves = get_legal_moves(current_me, current_opp)
        if not legal_moves:
            break
            
        # Prefer captures when available
        capture_moves = [m for m in legal_moves if is_capture(m, current_me, current_opp)]
        if capture_moves:
            move = random.choice(capture_moves)
        else:
            move = random.choice(legal_moves)
            
        # Alternate turns
        if turn_count % 2 == 0:
            current_me.append(move)
        else:
            current_opp.append(move)
            
        turn_count += 1
    
    # Evaluate final position (simple heuristic)
    my_score = len(current_me) + len(get_legal_moves(current_me, current_opp)) // 10
    opp_score = len(current_opp) + len(get_legal_moves(current_opp, current_me)) // 10
    
    return 1 if my_score > opp_score else 0

# Main policy function
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Check for immediate captures
    legal_moves = get_legal_moves(me, opponent)
    if not legal_moves:
        return PASS_MOVE, memory
        
    capture_moves = [m for m in legal_moves if is_capture(m, me, opponent)]
    if capture_moves:
        return random.choice(capture_moves), memory
    
    # Initialize MCTS
    root = MCTSNode(None)
    root.untried_moves = legal_moves
    
    start_time = time.time()
    simulations = 0
    
    while time.time() - start_time < 0.9:  # Allow some time for other operations
        node = root
        current_me = list(me)
        current_opp = list(opponent)
        
        # Selection
        while not node.untried_moves and node.children:
            node = node.uct_select_child()
            current_me.append(node.move)
            current_me, current_opp = current_opp, current_me  # Switch sides
            
        # Expansion
        if node.untried_moves:
            move = random.choice(node.untried_moves)
            current_me.append(move)
            node = node.add_child(move)
            current_me, current_opp = current_opp, current_me  # Switch sides
            
        # Simulation
        result = simulate_random_game(current_me, current_opp)
        
        # Backpropagation
        while node:
            node.update(result)
            node = node.parent
            result = 1 - result  # Flip result for opponent's perspective
            
        simulations += 1
    
    # Select best move based on visit counts
    if not root.children:
        return random.choice(legal_moves), memory
        
    best_child = max(root.children, key=lambda c: c.visits)
    return best_child.move, memory
