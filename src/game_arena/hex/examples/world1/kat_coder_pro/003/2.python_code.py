
import random
import time
import numpy as np
from collections import defaultdict
from typing import List, Tuple, Dict, Set

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    """Main policy function that returns the next move."""
    
    # Create board representation
    board = np.zeros((11, 11), dtype=int)
    
    # Mark stones on board: 1 for me, -1 for opponent, 0 for empty
    for r, c in me:
        board[r, c] = 1 if color == 'b' else -1
    
    for r, c in opp:
        board[r, c] = -1 if color == 'b' else 1
    
    # Get all empty cells
    empty_cells = []
    for r in range(11):
        for c in range(11):
            if board[r, c] == 0:
                empty_cells.append((r, c))
    
    # If it's the first move, take the center
    if len(empty_cells) == 121:
        return (5, 5)
    
    # Use MCTS to find the best move
    return mcts(board, color, empty_cells)

def get_neighbors(r: int, c: int) -> List[Tuple[int, int]]:
    """Get all neighboring cells of (r, c) on the hex board."""
    neighbors = []
    for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 11 and 0 <= nc < 11:
            neighbors.append((nr, nc))
    return neighbors

def is_path_exists(board: np.ndarray, color: str) -> bool:
    """Check if there's a path connecting the player's sides."""
    visited = set()
    
    if color == 'b':
        # Black connects top (row 0) to bottom (row 10)
        # Start from top
        queue = [(0, c) for c in range(11) if board[0, c] == 1]
        target_rows = {10}
    else:
        # White connects left (col 0) to right (col 10)
        # Start from left
        queue = [(r, 0) for r in range(11) if board[r, 0] == 1]
        target_cols = {10}
    
    while queue:
        r, c = queue.pop(0)
        if (r, c) in visited:
            continue
        visited.add((r, c))
        
        if color == 'b' and r in target_rows:
            return True
        elif color == 'w' and c in target_cols:
            return True
        
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == 1 and (nr, nc) not in visited:
                queue.append((nr, nc))
    
    return False

def evaluate_board(board: np.ndarray, color: str) -> float:
    """Evaluate the board state from the perspective of the given color."""
    # Simple heuristic: count potential connections
    score = 0
    
    # Check if we have a winning path
    if is_path_exists(board, color):
        return 1000
    
    # Check if opponent has a winning path
    if is_path_exists(board, 'w' if color == 'b' else 'b'):
        return -1000
    
    # Count stones in key positions
    for r in range(11):
        for c in range(11):
            if board[r, c] == 1:  # My stone
                # Value stones closer to the center more
                dist_to_center = abs(r - 5) + abs(c - 5)
                score += max(0, 5 - dist_to_center)
                
                # Value stones that are part of potential connections
                neighbors = get_neighbors(r, c)
                connected_stones = sum(1 for nr, nc in neighbors if board[nr, nc] == 1)
                score += connected_stones * 0.5
                
            elif board[r, c] == -1:  # Opponent's stone
                # Penalize opponent's stones in key positions
                dist_to_center = abs(r - 5) + abs(c - 5)
                score -= max(0, 5 - dist_to_center)
    
    return score

def simulate_random_game(board: np.ndarray, color: str, empty_cells: List[Tuple[int, int]]) -> float:
    """Simulate a random game from the current position."""
    # Copy the board to avoid modifying the original
    sim_board = board.copy()
    sim_empty_cells = empty_cells.copy()
    
    current_color = color
    
    while True:
        if not sim_empty_cells:
            # Draw
            return 0
        
        # Make a random move
        move = random.choice(sim_empty_cells)
        sim_empty_cells.remove(move)
        r, c = move
        
        sim_board[r, c] = 1 if current_color == color else -1
        
        # Check if current player won
        if is_path_exists(sim_board, current_color):
            return 1 if current_color == color else -1
        
        # Switch player
        current_color = 'w' if current_color == 'b' else 'b'

class Node:
    def __init__(self, board: np.ndarray, color: str, empty_cells: List[Tuple[int, int]], parent=None, move=None):
        self.board = board
        self.color = color
        self.empty_cells = empty_cells
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = empty_cells.copy()
        self.is_terminal = False
        
        # Check if this is a terminal state
        if is_path_exists(self.board, self.color):
            self.is_terminal = True
        elif is_path_exists(self.board, 'w' if self.color == 'b' else 'b'):
            self.is_terminal = True
        elif not self.untried_moves:
            self.is_terminal = True

def mcts(board: np.ndarray, color: str, empty_cells: List[Tuple[int, int]]) -> Tuple[int, int]:
    """Run Monte Carlo Tree Search to find the best move."""
    root = Node(board, color, empty_cells)
    
    start_time = time.time()
    iterations = 0
    
    while time.time() - start_time < 0.95:  # Leave some time buffer
        # Selection
        node = root
        while node.children and not node.is_terminal:
            # UCB1 selection
            best_child = None
            best_score = -float('inf')
            
            for child in node.children:
                if child.visits == 0:
                    ucb_score = float('inf')
                else:
                    ucb_score = (child.wins / child.visits + 
                                np.sqrt(2 * np.log(node.visits) / child.visits))
                
                if ucb_score > best_score:
                    best_score = ucb_score
                    best_child = child
            
            if best_child:
                node = best_child
            else:
                break
        
        # Expansion
        if not node.is_terminal and node.untried_moves:
            move = random.choice(node.untried_moves)
            node.untried_moves.remove(move)
            
            # Create new board state
            new_board = node.board.copy()
            r, c = move
            new_board[r, c] = 1 if node.color == color else -1
            
            # Create new empty cells list
            new_empty_cells = node.empty_cells.copy()
            new_empty_cells.remove(move)
            
            # Create new child node
            child = Node(new_board, 'w' if node.color == 'b' else 'b', 
                        new_empty_cells, node, move)
            node.children.append(child)
            node = child
        
        # Simulation
        if node.is_terminal:
            result = 0
            if is_path_exists(node.board, color):
                result = 1
            elif is_path_exists(node.board, 'w' if color == 'b' else 'b'):
                result = -1
        else:
            result = simulate_random_game(node.board, node.color, node.empty_cells)
        
        # Backpropagation
        while node is not None:
            node.visits += 1
            node.wins += result
            node = node.parent
        
        iterations += 1
    
    # Choose the move with the highest win rate
    best_move = None
    best_win_rate = -float('inf')
    
    for child in root.children:
        if child.visits > 0:
            win_rate = child.wins / child.visits
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                best_move = child.move
    
    # Fallback to a random move if no children were created
    if best_move is None and root.untried_moves:
        best_move = random.choice(root.untried_moves)
    
    return best_move
