
import numpy as np
from typing import List, Tuple, Set, Dict
import random

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    A strategic Go policy that evaluates the board state and makes intelligent moves.
    
    Strategy:
    1. Evaluate potential threats and opportunities
    2. Prioritize moves that increase our liberties while reducing opponent's liberties
    3. Focus on territory expansion and group safety
    4. Implement basic life-and-death evaluation
    """
    
    # Convert lists to sets for faster lookups
    my_stones = set(me)
    opponent_stones = set(opponent)
    
    # Initialize board (19x19)
    board = np.zeros((19, 19), dtype=int)
    
    # Fill board: 1 for my stones, -1 for opponent stones, 0 for empty
    for r, c in my_stones:
        board[r-1, c-1] = 1
    for r, c in opponent_stones:
        board[r-1, c-1] = -1
    
    # Get all empty positions
    empty_positions = []
    for r in range(19):
        for c in range(19):
            if board[r, c] == 0:
                empty_positions.append((r+1, c+1))
    
    if not empty_positions:
        return (0, 0)  # Pass if no moves available
    
    # Evaluate each empty position
    best_score = float('-inf')
    best_move = empty_positions[0]
    
    for move in empty_positions:
        score = evaluate_move(board, move, my_stones, opponent_stones)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def evaluate_move(board: np.ndarray, move: Tuple[int, int], 
                 my_stones: Set[Tuple[int, int]], opponent_stones: Set[Tuple[int, int]]) -> float:
    """
    Evaluate the quality of a move based on multiple factors.
    """
    r, c = move
    row, col = r - 1, c - 1
    
    score = 0.0
    
    # 1. Basic safety - avoid suicide moves
    if is_suicide_move(board, row, col, 1):
        return float('-inf')
    
    # 2. Liberty analysis
    my_liberties_gain = count_liberties_after_move(board, row, col, 1)
    opponent_liberties_loss = evaluate_opponent_liberties_loss(board, row, col, -1)
    
    score += my_liberties_gain * 2.0
    score -= opponent_liberties_loss * 1.5
    
    # 3. Connectivity - prefer moves that connect to existing groups
    connectivity_bonus = evaluate_connectivity(board, row, col, 1)
    score += connectivity_bonus * 3.0
    
    # 4. Territory control - prefer moves on edges and corners
    territory_bonus = evaluate_territory_value(r, c)
    score += territory_bonus
    
    # 5. Threat evaluation - block opponent's potential captures
    threat_bonus = evaluate_threats(board, row, col, opponent_stones)
    score += threat_bonus * 2.5
    
    # 6. Expansion potential - prefer moves that open up future options
    expansion_bonus = evaluate_expansion_potential(board, row, col)
    score += expansion_bonus
    
    return score

def is_suicide_move(board: np.ndarray, row: int, col: int, color: int) -> bool:
    """
    Check if placing a stone at (row, col) would be a suicide move.
    """
    # Create a copy of the board
    test_board = board.copy()
    test_board[row, col] = color
    
    # Check if the new stone has any liberties
    if has_liberties(test_board, row, col, color):
        return False
    
    # Check if any opponent stones would be captured
    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and test_board[nr, nc] == -color:
            if not has_liberties(test_board, nr, nc, -color):
                return False  # Would capture opponent, so not suicide
    
    return True

def has_liberties(board: np.ndarray, row: int, col: int, color: int) -> bool:
    """
    Check if the group containing the stone at (row, col) has any liberties.
    """
    visited = set()
    stack = [(row, col)]
    visited.add((row, col))
    
    while stack:
        r, c = stack.pop()
        
        # Check for liberties
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr, nc] == 0:
                    return True
                elif board[nr, nc] == color and (nr, nc) not in visited:
                    stack.append((nr, nc))
                    visited.add((nr, nc))
    
    return False

def count_liberties_after_move(board: np.ndarray, row: int, col: int, color: int) -> int:
    """
    Count the liberties of the group after placing a stone.
    """
    test_board = board.copy()
    test_board[row, col] = color
    
    # Find all stones in the group
    group_stones = []
    stack = [(row, col)]
    visited = set()
    visited.add((row, col))
    
    while stack:
        r, c = stack.pop()
        group_stones.append((r, c))
        
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and test_board[nr, nc] == color and (nr, nc) not in visited:
                stack.append((nr, nc))
                visited.add((nr, nc))
    
    # Count unique liberties
    liberties = set()
    for r, c in group_stones:
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and test_board[nr, nc] == 0:
                liberties.add((nr, nc))
    
    return len(liberties)

def evaluate_opponent_liberties_loss(board: np.ndarray, row: int, col: int, opponent_color: int) -> int:
    """
    Evaluate how many liberties this move would remove from opponent groups.
    """
    loss = 0
    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == opponent_color:
            # Count liberties before and after
            liberties_before = count_liberties_of_group(board, nr, nc, opponent_color)
            test_board = board.copy()
            test_board[row, col] = -opponent_color  # Place our stone
            liberties_after = count_liberties_of_group(test_board, nr, nc, opponent_color)
            loss += max(0, liberties_before - liberties_after)
    return loss

def count_liberties_of_group(board: np.ndarray, row: int, col: int, color: int) -> int:
    """
    Count liberties of a specific group.
    """
    group_stones = []
    stack = [(row, col)]
    visited = set()
    visited.add((row, col))
    
    while stack:
        r, c = stack.pop()
        group_stones.append((r, c))
        
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == color and (nr, nc) not in visited:
                stack.append((nr, nc))
                visited.add((nr, nc))
    
    liberties = set()
    for r, c in group_stones:
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                liberties.add((nr, nc))
    
    return len(liberties)

def evaluate_connectivity(board: np.ndarray, row: int, col: int, color: int) -> float:
    """
    Evaluate how well this move connects to existing stones.
    """
    bonus = 0.0
    
    # Check adjacent positions for friendly stones
    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == color:
            bonus += 1.0
    
    # Check diagonal positions for potential connections
    for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == color:
            bonus += 0.5
    
    return bonus

def evaluate_territory_value(row: int, col: int) -> float:
    """
    Evaluate the territorial value of a position.
    Corners and edges are generally more valuable.
    """
    # Distance to edges
    dist_top = row - 1
    dist_bottom = 19 - row
    dist_left = col - 1
    dist_right = 19 - col
    
    min_dist_edge = min(dist_top, dist_bottom, dist_left, dist_right)
    
    # Higher value for corners and edges
    if min_dist_edge == 0:  # On edge
        return 1.5
    elif min_dist_edge == 1:  # One away from edge
        return 1.0
    elif min_dist_edge <= 3:  # Within 3 of edge
        return 0.5
    else:
        return 0.0

def evaluate_threats(board: np.ndarray, row: int, col: int, opponent_stones: Set[Tuple[int, int]]) -> float:
    """
    Evaluate if this move blocks opponent threats or creates threats of our own.
    """
    bonus = 0.0
    
    # Check if we're blocking an opponent's potential capture
    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == -1:
            # Check if this opponent stone has only 1 liberty (would be captured next)
            liberties = count_liberties_of_group(board, nr, nc, -1)
            if liberties == 1:
                bonus += 2.0
            elif liberties == 2:
                bonus += 1.0
    
    return bonus

def evaluate_expansion_potential(board: np.ndarray, row: int, col: int) -> float:
    """
    Evaluate the potential for future expansion from this position.
    """
    bonus = 0.0
    
    # Count empty spaces in the vicinity
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            nr, nc = row + dr, col + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                bonus += 0.1
    
    return bonus
