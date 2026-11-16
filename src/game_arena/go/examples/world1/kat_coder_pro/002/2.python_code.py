
import random
import numpy as np
from typing import List, Tuple, Set

# Go board size
BOARD_SIZE = 19

# Directions for neighbors (up, down, left, right)
DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

def is_valid_position(pos: Tuple[int, int]) -> bool:
    """Check if a position is within the board boundaries."""
    return 1 <= pos[0] <= BOARD_SIZE and 1 <= pos[1] <= BOARD_SIZE

def get_neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Get all valid neighboring positions."""
    row, col = pos
    neighbors = []
    for dr, dc in DIRECTIONS:
        new_pos = (row + dr, col + dc)
        if is_valid_position(new_pos):
            neighbors.append(new_pos)
    return neighbors

def has_liberty(pos: Tuple[int, int], board: np.ndarray) -> bool:
    """Check if a group containing pos has at least one liberty."""
    if board[pos[0], pos[1]] == 0:  # Empty position has liberties
        return True
    
    color = board[pos[0], pos[1]]
    visited = set()
    stack = [pos]
    
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        
        for neighbor in get_neighbors(current):
            if board[neighbor[0], neighbor[1]] == 0:  # Found a liberty
                return True
            elif board[neighbor[0], neighbor[1]] == color and neighbor not in visited:
                stack.append(neighbor)
    
    return False

def get_group(pos: Tuple[int, int], board: np.ndarray) -> Set[Tuple[int, int]]:
    """Get all stones in the group containing pos."""
    if board[pos[0], pos[1]] == 0:
        return set()
    
    color = board[pos[0], pos[1]]
    group = set()
    stack = [pos]
    
    while stack:
        current = stack.pop()
        if current in group:
            continue
        group.add(current)
        
        for neighbor in get_neighbors(current):
            if board[neighbor[0], neighbor[1]] == color and neighbor not in group:
                stack.append(neighbor)
    
    return group

def is_legal_move(pos: Tuple[int, int], board: np.ndarray) -> bool:
    """Check if a move is legal according to Go rules."""
    if not is_valid_position(pos):
        return False
    
    if board[pos[0], pos[1]] != 0:  # Position is occupied
        return False
    
    # Temporarily place the stone
    board[pos[0], pos[1]] = 1  # Assume we are player 1
    
    # Check if the move captures any opponent stones
    captured = False
    for neighbor in get_neighbors(pos):
        if board[neighbor[0], neighbor[1]] == 2 and not has_liberty(neighbor, board):
            captured = True
            break
    
    # Check if our stone is self-captured
    self_captured = not has_liberty(pos, board)
    
    # Remove the temporarily placed stone
    board[pos[0], pos[1]] = 0
    
    # A move is legal if it doesn't self-capture (unless it captures opponent stones)
    return not self_captured or captured

def evaluate_position(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> float:
    """Simple heuristic to evaluate the position."""
    # Count liberties for our stones
    board = np.zeros((BOARD_SIZE + 2, BOARD_SIZE + 2), dtype=int)
    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = 2
    
    # Count liberties for our stones
    my_liberties = 0
    for r, c in me:
        for neighbor in get_neighbors((r, c)):
            if board[neighbor[0], neighbor[1]] == 0:
                my_liberties += 1
    
    # Count liberties for opponent stones
    opp_liberties = 0
    for r, c in opponent:
        for neighbor in get_neighbors((r, c)):
            if board[neighbor[0], neighbor[1]] == 0:
                opp_liberties += 1
    
    # Heuristic: More liberties is better, fewer opponent liberties is better
    return my_liberties - opp_liberties

def simulate_move(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], move: Tuple[int, int]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """Simulate making a move and return the new board state."""
    board = np.zeros((BOARD_SIZE + 2, BOARD_SIZE + 2), dtype=int)
    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = 2
    
    # Make the move
    board[move[0], move[1]] = 1
    
    # Capture opponent stones
    new_opponent = []
    for r, c in opponent:
        if has_liberty((r, c), board):
            new_opponent.append((r, c))
    
    # Remove captured stones
    new_me = me + [move]
    return new_me, new_opponent

def get_legal_moves(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Get all legal moves."""
    # Create board representation
    board = np.zeros((BOARD_SIZE + 2, BOARD_SIZE + 2), dtype=int)
    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = 2
    
    # Check all positions
    legal_moves = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if is_legal_move((r, c), board):
                legal_moves.append((r, c))
    
    return legal_moves

def mcts(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], iterations: int = 1000) -> Tuple[int, int]:
    """Monte Carlo Tree Search to find the best move."""
    legal_moves = get_legal_moves(me, opponent)
    
    if not legal_moves:
        return (0, 0)  # Pass
    
    # Initialize scores
    scores = {move: 0.0 for move in legal_moves}
    visits = {move: 0 for move in legal_moves}
    
    for _ in range(iterations):
        # Selection - choose a move using UCT
        total_visits = sum(visits.values())
        best_score = -float('inf')
        best_move = legal_moves[0]
        
        for move in legal_moves:
            if visits[move] == 0:
                # Always explore unvisited moves
                best_move = move
                break
            
            # UCT formula
            exploitation = scores[move] / visits[move]
            exploration = np.sqrt(np.log(total_visits) / visits[move])
            uct_score = exploitation + exploration
            
            if uct_score > best_score:
                best_score = uct_score
                best_move = move
        
        # Simulation - play random moves until game end
        current_me, current_opponent = simulate_move(me, opponent, best_move)
        visits[best_move] += 1
        
        # Simulate random playout
        score = 0
        for _ in range(50):  # Limited depth simulation
            # Switch roles (simulate opponent's move)
            temp_me = current_opponent
            temp_opponent = current_me
            
            # Get legal moves for the "opponent"
            temp_legal_moves = get_legal_moves(temp_me, temp_opponent)
            
            if not temp_legal_moves:
                break  # Game over
            
            # Random move
            random_move = random.choice(temp_legal_moves)
            current_me, current_opponent = simulate_move(temp_me, temp_opponent, random_move)
            
            # Evaluate position
            score += evaluate_position(current_me, current_opponent)
        
        scores[best_move] += score
    
    # Choose the move with the highest score
    best_move = max(scores, key=lambda k: scores[k])
    return best_move

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """Main policy function."""
    # Check for immediate tactical opportunities
    board = np.zeros((BOARD_SIZE + 2, BOARD_SIZE + 2), dtype=int)
    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = 2
    
    # Look for captures
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r, c] == 0:  # Empty position
                # Check if this move captures opponent stones
                board[r, c] = 1
                captures = 0
                for neighbor in get_neighbors((r, c)):
                    if board[neighbor[0], neighbor[1]] == 2 and not has_liberty(neighbor, board):
                        captures += 1
                board[r, c] = 0
                
                if captures > 0:
                    return (r, c)
    
    # Use MCTS to find the best move
    return mcts(me, opponent)

# Standard Python entry point
if __name__ == "__main__":
    # Example usage (for testing)
    me = [(10, 10)]
    opponent = [(9, 10), (11, 10)]
    print(policy(me, opponent))
