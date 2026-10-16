
import math
import numpy as np
import random
from typing import List, Tuple, Optional, Dict
from collections import defaultdict

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    # Board size
    BOARD_SIZE = 11
    
    # Convert lists to sets for faster lookup
    me_set = set(me)
    opp_set = set(opp)
    all_stones = me_set | opp_set
    
    # Find all empty cells
    empty_cells = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if (r, c) not in all_stones:
                empty_cells.append((r, c))
    
    # If there's only one empty cell, return it
    if len(empty_cells) == 1:
        return empty_cells[0]
    
    # MCTS parameters
    SIMULATIONS = 1000
    EXPLORATION = 1.4
    VIRTUAL_LOSS = 3
    RAVE_BIAS = 0.0
    
    # Initialize MCTS data structures
    visits = defaultdict(int)
    wins = defaultdict(float)
    rave_visits = defaultdict(int)
    rave_wins = defaultdict(float)
    children = defaultdict(list)
    
    def get_neighbors(r, c):
        """Get all neighboring cells of (r, c)"""
        neighbors = []
        # Same row
        if c > 0:
            neighbors.append((r, c-1))
        if c < BOARD_SIZE - 1:
            neighbors.append((r, c+1))
        
        # Top row
        if r > 0:
            neighbors.append((r-1, c))
            if c < BOARD_SIZE - 1:
                neighbors.append((r-1, c+1))
        
        # Bottom row
        if r < BOARD_SIZE - 1:
            neighbors.append((r+1, c))
            if c > 0:
                neighbors.append((r+1, c-1))
        
        return neighbors
    
    def is_connected_to_edge(stone, color):
        """Check if a stone is connected to the edge of the board of the appropriate color"""
        r, c = stone
        if color == 'b':  # Black connects top and bottom
            if r == 0 or r == BOARD_SIZE - 1:
                return True
        else:  # White connects left and right
            if c == 0 or c == BOARD_SIZE - 1:
                return True
        return False
    
    def evaluate_position(color):
        """Heuristic evaluation of the current position"""
        # We'll use a simple heuristic: count stones near the edges
        score = 0
        if color == 'b':
            # For black, count stones in top and bottom rows
            for r, c in me:
                if r == 0 or r == BOARD_SIZE - 1:
                    score += 1
                # Also count stones one row away from the edges
                elif r == 1 or r == BOARD_SIZE - 2:
                    score += 0.5
        else:
            # For white, count stones in left and right columns
            for r, c in me:
                if c == 0 or c == BOARD_SIZE - 1:
                    score += 1
                # Also count stones one column away from the edges
                elif c == 1 or c == BOARD_SIZE - 2:
                    score += 0.5
        return score
    
    def evaluate_move(r, c, color):
        """Heuristic evaluation of a move"""
        score = 0
        
        # Distance to edges
        if color == 'b':
            # Distance to top and bottom edges
            score += min(r, BOARD_SIZE - 1 - r)
        else:
            # Distance to left and right edges
            score += min(c, BOARD_SIZE - 1 - c)
        
        # Number of friendly stones in neighborhood
        friendly = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in me_set:
                friendly += 1
        score += friendly * 2
        
        # Number of opponent stones in neighborhood
        opponent = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in opp_set:
                opponent += 1
        score -= opponent
        
        # If move connects to edge
        if is_connected_to_edge((r, c), color):
            score += 5
        
        return score
    
    def select_move(node_state, color):
        """Select the best move using UCT with RAVE"""
        # If we haven't visited this node, return a random move
        if visits[node_state] == 0:
            return random.choice(empty_cells)
        
        # Calculate UCT values for all children
        best_move = None
        best_value = -float('inf')
        
        for move in children[node_state]:
            if visits[(node_state, move)] == 0:
                value = float('inf')
            else:
                # UCT value
                uct = (wins[(node_state, move)] / visits[(node_state, move)] +
                       EXPLORATION * math.sqrt(math.log(visits[node_state]) / visits[(node_state, move)]))
                
                # RAVE value
                if rave_visits[(node_state, move)] > 0:
                    rave = rave_wins[(node_state, move)] / rave_visits[(node_state, move)]
                    value = (1 - RAVE_BIAS) * uct + RAVE_BIAS * rave
                else:
                    value = uct
            
            if value > best_value:
                best_value = value
                best_move = move
        
        return best_move
    
    def simulate(color):
        """Simulate a game from the current position"""
        # Create copies of the sets
        me_sim = me_set.copy()
        opp_sim = opp_set.copy()
        
        # Simulate until the game is over
        while True:
            # Check if someone has won
            if has_won(me_sim, 'b' if color == 'b' else 'w'):
                return 1 if color == 'b' else 0
            if has_won(opp_sim, 'b' if color == 'w' else 'w'):
                return 0 if color == 'b' else 1
            
            # Get empty cells
            empty_cells_sim = []
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if (r, c) not in me_sim and (r, c) not in opp_sim:
                        empty_cells_sim.append((r, c))
            
            # If no empty cells, it's a draw
            if not empty_cells_sim:
                return 0.5
            
            # Choose a random move based on heuristic
            scores = []
            for r, c in empty_cells_sim:
                scores.append(evaluate_move(r, c, color))
            
            # Normalize scores to probabilities
            max_score = max(scores)
            probs = [math.exp(s - max_score) for s in scores]
            total = sum(probs)
            probs = [p / total for p in probs]
            
            # Choose a move
            move = random.choices(empty_cells_sim, weights=probs)[0]
            
            # Make the move
            if color == 'b':
                me_sim.add(move)
            else:
                opp_sim.add(move)
            
            # Switch players
            color = 'w' if color == 'b' else 'b'
    
    def has_won(stones, color):
        """Check if the given player has won"""
        # For simplicity, we'll use a BFS to check connectivity
        if color == 'b':
            # Check if any stone in the top row is connected to any stone in the bottom row
            start_stones = [(r, c) for r, c in stones if r == 0]
            target_r = BOARD_SIZE - 1
        else:
            # Check if any stone in the left column is connected to any stone in the right column
            start_stones = [(r, c) for r, c in stones if c == 0]
            target_c = BOARD_SIZE - 1
        
        if not start_stones:
            return False
        
        # BFS
        queue = start_stones[:]
        visited = set(start_stones)
        
        while queue:
            r, c = queue.pop(0)
            
            # Check if we've reached the target
            if (color == 'b' and r == target_r) or (color == 'w' and c == target_c):
                return True
            
            # Add neighbors to queue
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stones and (nr, nc) not in visited:
                    queue.append((nr, nc))
                    visited.add((nr, nc))
        
        return False
    
    # MCTS main loop
    for _ in range(SIMULATIONS):
        # Selection
        node_state = tuple(sorted(me) + sorted(opp))
        path = []
        current_color = color
        
        while True:
            # Check if the game is over
            if has_won(me_set, 'b' if color == 'b' else 'w') or has_won(opp_set, 'b' if color == 'w' else 'w'):
                break
            
            # Select a move
            move = select_move(node_state, current_color)
            path.append((node_state, move))
            
            # Make the move
            if current_color == 'b':
                me_set.add(move)
            else:
                opp_set.add(move)
            
            # Update node state
            node_state = tuple(sorted(me_set) + sorted(opp_set))
            
            # Switch players
            current_color = 'w' if current_color == 'b' else 'b'
        
        # Simulation
        result = simulate(current_color)
        
        # Backpropagation
        for node_state, move in path:
            visits[node_state] += 1
            visits[(node_state, move)] += 1
            wins[node_state] += result
            wins[(node_state, move)] += result
            
            # Update RAVE statistics
            for node_state2, move2 in path:
                if move == move2:
                    rave_visits[(node_state, move)] += 1
                    rave_wins[(node_state, move)] += result
    
    # Choose the best move
    best_move = None
    best_value = -float('inf')
    
    for move in empty_cells:
        if visits[(tuple(sorted(me) + sorted(opp)), move)] > best_value:
            best_value = visits[(tuple(sorted(me) + sorted(opp)), move)]
            best_move = move
    
    return best_move
