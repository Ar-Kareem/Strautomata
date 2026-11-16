
import random
import math
import numpy as np
from collections import defaultdict

def get_neighbors(row, col):
    """Get all 6 neighboring hex cells"""
    neighbors = []
    # Hexagonal neighbors (including diagonals)
    directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 11 and 0 <= new_col < 11:
            neighbors.append((new_row, new_col))
    return neighbors

def get_opponent(color):
    return 'w' if color == 'b' else 'b'

def get_target_sides(color):
    """Get the two target sides for each color"""
    if color == 'b':
        return (0, 10)  # top and bottom
    else:
        return (0, 10)  # left and right

def get_win_condition(color):
    """Get win condition for each color"""
    if color == 'b':
        return lambda r, c: r == 0 or r == 10
    else:
        return lambda r, c: c == 0 or c == 10

def is_game_over(me, opp, color):
    """Check if the game is over (player won)"""
    # Check if any of our stones can reach both target sides
    visited = set()
    queue = []
    
    # Add all stones on the correct starting side to the queue
    if color == 'b':
        for r, c in me:
            if r == 0:
                queue.append((r, c))
                visited.add((r, c))
    else:
        for r, c in me:
            if c == 0:
                queue.append((r, c))
                visited.add((r, c))
    
    if not queue:
        return False
    
    # BFS to see if we can reach the opposite side
    win_condition = get_win_condition(color)
    
    while queue:
        r, c = queue.pop(0)
        if win_condition(r, c):
            return True
            
        # Check neighbors
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in me and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))
    
    return False

def evaluate_position(me, opp, color):
    """Simple heuristic evaluation for position"""
    # Simple evaluation: prioritize center control
    score = 0
    
    # Center positions are generally more valuable
    center_positions = [(5, 5), (4, 5), (5, 4), (6, 5), (5, 6)]
    for pos in center_positions:
        if pos in me:
            score += 2
        elif pos in opp:
            score -= 1
    
    # Empty center positions are also valuable
    for pos in center_positions:
        if pos not in me and pos not in opp:
            score += 1
    
    return score

def simulate_game(me, opp, color):
    """Simple simulation for MCTS"""
    current_me = me[:]
    current_opp = opp[:]
    current_color = color
    
    # Make a few random moves until game ends or we hit a depth limit
    max_moves = 20
    for _ in range(max_moves):
        # Get all possible moves
        empty_cells = []
        for r in range(11):
            for c in range(11):
                if (r, c) not in current_me and (r, c) not in current_opp:
                    empty_cells.append((r, c))
        
        if not empty_cells:
            break
            
        # Pick a random move
        move = random.choice(empty_cells)
        
        if current_color == color:
            current_me.append(move)
        else:
            current_opp.append(move)
            
        # Check if this wins the game
        if is_game_over(current_me, current_opp, current_color):
            return 1 if current_color == color else -1
            
        # Switch players
        current_color = get_opponent(current_color)
    
    # If we can't determine winner, evaluate based on simple heuristics
    return evaluate_position(current_me, current_opp, color) / 10.0

class MCTSNode:
    def __init__(self, move, parent=None, color=None):
        self.move = move
        self.parent = parent
        self.color = color
        self.children = []
        self.visits = 0
        self.wins = 0
        self.untried_moves = []
        
    def ucb1(self, exploration=1.41):
        if self.visits == 0:
            return float('inf')
        return self.wins / self.visits + exploration * math.sqrt(math.log(self.parent.visits) / self.visits)
    
    def is_fully_expanded(self):
        return len(self.untried_moves) == 0
    
    def is_terminal(self):
        # This is an approximation
        return self.visits > 100 or self.visits > 1000

def mcts_policy(me, opp, color, iterations=2000):
    """MCTS-based policy for Hex"""
    
    # Create root node
    root = MCTSNode(None)
    
    # Get all possible moves
    empty_cells = []
    for r in range(11):
        for c in range(11):
            if (r, c) not in me and (r, c) not in opp:
                empty_cells.append((r, c))
    
    if not empty_cells:
        return (0, 0)
        
    root.untried_moves = empty_cells[:]
    
    # Run MCTS iterations
    for _ in range(iterations):
        # Selection
        node = root
        while node.is_fully_expanded() and not node.is_terminal():
            # Select child with best UCB1
            best_child = max(node.children, key=lambda child: child.ucb1())
            node = best_child
            
        # Expansion
        if not node.is_terminal():
            # Pick a random untried move
            move = random.choice(node.untried_moves)
            node.untried_moves.remove(move)
            
            # Create child node
            child = MCTSNode(move, parent=node, color=get_opponent(color) if node.color is None else get_opponent(node.color))
            node.children.append(child)
            
            # Simulation
            result = simulate_game(me + ([move] if color == get_opponent(node.color) else []), 
                                 opp + ([move] if color != get_opponent(node.color) else []), 
                                 color)
            
            # Backpropagation
            current_node = child
            while current_node is not None:
                current_node.visits += 1
                if result > 0:
                    current_node.wins += 1
                current_node = current_node.parent
    
    # Choose best move based on most visits
    if not root.children:
        return random.choice(empty_cells)
        
    best_child = max(root.children, key=lambda child: child.visits)
    return best_child.move

def policy(me, opp, color):
    """Main policy function"""
    # If it's the first move, play in center for symmetry
    if len(me) == 0 and len(opp) == 0:
        return (5, 5)
    
    # Try to win if possible
    empty_cells = []
    for r in range(11):
        for c in range(11):
            if (r, c) not in me and (r, c) not in opp:
                empty_cells.append((r, c))
    
    # Try to find a winning move
    for move in empty_cells:
        new_me = me + [move]
        if is_game_over(new_me, opp, color):
            return move
    
    # Try to block opponent winning move
    opponent_color = get_opponent(color)
    for move in empty_cells:
        new_opp = opp + [move]
        if is_game_over(new_opp, me, opponent_color):
            return move
            
    # Use MCTS for move selection
    return mcts_policy(me, opp, color, 2000)
