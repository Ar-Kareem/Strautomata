
import numpy as np
from collections import defaultdict
from typing import List, Tuple, Dict

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    """
    Competitive Go policy using multi-layered priority evaluation.
    
    Args:
        me: List of (row, col) tuples for player's stones
        opponent: List of (row, col) tuples for opponent's stones
        memory: Dictionary for state persistence
        
    Returns:
        Tuple of (action, memory) where action is (row, col) or (0,0) for pass
    """
    
    # Initialize or update memory
    if 'board' not in memory:
        memory['board'] = {}
        memory['move_count'] = 0
    
    board = memory['board']
    board.clear()
    
    # Build board state
    for r, c in me:
        board[(r, c)] = 1
    for r, c in opponent:
        board[(r, c)] = -1
    
    memory['move_count'] += 1
    move_number = memory['move_count']
    
    # Get all empty points
    empty_points = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in board:
                empty_points.append((r, c))
    
    if not empty_points:
        return (0, 0), memory
    
    # Evaluate all legal moves
    legal_moves = []
    for point in empty_points:
        is_suicide = check_suicide(point, me, opponent, board)
        if not is_suicide:
            score = evaluate_move(point, me, opponent, board, move_number)
            legal_moves.append((score, point))
    
    if not legal_moves:
        return (0, 0), memory
    
    # Sort by score and return best move
    legal_moves.sort(reverse=True)
    best_move = legal_moves[0][1]
    
    return best_move, memory


def check_suicide(move: Tuple[int, int], me: List[Tuple[int, int]], 
                  opponent: List[Tuple[int, int]], board: Dict) -> bool:
    """
    Check if a move is a suicide move (not capturing anything).
    """
    r, c = move
    temp_board = board.copy()
    temp_board[move] = 1  # Place our stone
    
    # Check if this move captures opponent stones
    captured = get_captured_stones(-1, temp_board, move)
    if captured:
        return False  # Not suicide if it captures
    
    # Check if our stone has any liberties after placement
    return not has_liberties(move, 1, temp_board)


def get_captured_stones(player: int, board: Dict, last_move: Tuple[int, int]) -> List[Tuple[int, int]]:
    """
    Get list of opponent stones captured by a move.
    """
    captured = []
    r, c = last_move
    opponent = -player
    
    # Check all adjacent opponent groups
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if (nr, nc) in board and board[(nr, nc)] == opponent:
            group = get_group((nr, nc), board)
            if not group_has_liberties(group, board):
                captured.extend(group)
    
    return captured


def get_group(start: Tuple[int, int], board: Dict) -> List[Tuple[int, int]]:
    """
    Get all stones in a connected group.
    """
    player = board[start]
    group = [start]
    visited = {start}
    queue = [start]
    
    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in board and board[(nr, nc)] == player and (nr, nc) not in visited:
                visited.add((nr, nc))
                group.append((nr, nc))
                queue.append((nr, nc))
    
    return group


def has_liberties(stone: Tuple[int, int], player: int, board: Dict) -> bool:
    """
    Check if a stone has at least one liberty.
    """
    r, c = stone
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if (nr, nc) not in board:
            return True
    return False


def group_has_liberties(group: List[Tuple[int, int]], board: Dict) -> bool:
    """
    Check if a group has any liberties.
    """
    liberties = set()
    for r, c in group:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) not in board:
                liberties.add((nr, nc))
    return len(liberties) > 0


def evaluate_move(move: Tuple[int, int], me: List[Tuple[int, int]], 
                  opponent: List[Tuple[int, int]], board: Dict, move_number: int) -> float:
    """
    Evaluate a move with multi-layered priority system.
    Returns a score - higher is better.
    """
    r, c = move
    score = 0.0
    
    # Priority 1: Capture opponent stones (highest priority)
    score += evaluate_capture(move, board) * 1000
    
    # Priority 2: Escape from atari (self-defense)
    score += evaluate_self_escape(move, me, board) * 500
    
    # Priority 3: Create eyes
    score += evaluate_eye_creation(move, me, board) * 200
    
    # Priority 4: Strategic position value
    score += evaluate_strategic_value(r, c, move_number) * 50
    
    # Priority 5: Connection and shape
    score += evaluate_connection(move, me, board) * 30
    
    # Priority 6: Extension and influence
    score += evaluate_extension(move, opponent, board) * 20
    
    # Add small random factor to break ties
    score += hash(move) % 100 / 10000.0
    
    return score


def evaluate_capture(move: Tuple[int, int], board: Dict) -> int:
    """
    Evaluate capture potential - prioritize moves that capture stones.
    """
    r, c = move
    captures = 0
    
    # Temporarily place stone
    temp_board = board.copy()
    temp_board[move] = 1
    
    # Check adjacent opponent groups
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if (nr, nc) in temp_board and temp_board[(nr, nc)] == -1:
            group = get_group((nr, nc), temp_board)
            if not group_has_liberties(group, temp_board):
                captures += len(group)
    
    return captures


def evaluate_self_escape(move: Tuple[int, int], me: List[Tuple[int, int]], 
                         board: Dict) -> int:
    """
    Evaluate escape from atari potential.
    """
    r, c = move
    temp_board = board.copy()
    temp_board[move] = 1
    
    # Check if this move saves a group from capture
    escape_score = 0
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if (nr, nc) in temp_board and temp_board[(nr, nc)] == 1:
            group = get_group((nr, nc), temp_board)
            liberties = count_liberties(group, temp_board)
            if liberties <= 2:  # Group was in atari or close
                escape_score += (3 - liberties) * 10
    
    return escape_score


def count_liberties(group: List[Tuple[int, int]], board: Dict) -> int:
    """
    Count liberties of a group.
    """
    liberties = set()
    for r, c in group:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) not in board:
                liberties.add((nr, nc))
    return len(liberties)


def evaluate_eye_creation(move: Tuple[int, int], me: List[Tuple[int, int]], 
                          board: Dict) -> int:
    """
    Evaluate potential for creating eyes.
    """
    r, c = move
    eye_score = 0
    
    temp_board = board.copy()
    temp_board[move] = 1
    
    # Check adjacent empty points for potential eyes
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if (nr, nc) not in temp_board:
            # Check if this empty point could become an eye
            if is_potential_eye((nr, nc), temp_board):
                eye_score += 1
    
    return eye_score


def is_potential_eye(point: Tuple[int, int], board: Dict) -> bool:
    """
    Check if a point could potentially become an eye.
    """
    r, c = point
    # Count adjacent friendly stones
    friendly_adjacent = 0
    empty_adjacent = 0
    
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if (nr, nc) in board:
            if board[(nr, nc)] == 1:
                friendly_adjacent += 1
        else:
            empty_adjacent += 1
    
    # A point is more likely to be an eye if surrounded by friendly stones
    return friendly_adjacent >= 2


def evaluate_strategic_value(r: int, c: int, move_number: int) -> float:
    """
    Evaluate strategic position value based on board location.
    """
    # Corner positions are most valuable in opening
    corners = [(3, 3), (3, 4), (4, 3), (4, 4), 
               (3, 16), (3, 15), (4, 16), (4, 15),
               (16, 3), (16, 4), (15, 3), (15, 4),
               (16, 16), (16, 15), (15, 16), (15, 15)]
    
    if (r, c) in corners:
        # Prefer 3-3 and 4-4 in early opening
        if move_number <= 20:
            return 1.0 if (r % 5 in [3, 4] and c % 5 in [3, 4]) else 0.8
        else:
            return 0.6
    
    # Side positions
    sides = []
    for i in range(4, 16):
        sides.extend([(i, 3), (i, 4), (i, 16), (i, 15),
                      (3, i), (4, i), (16, i), (15, i)])
    
    if (r, c) in sides:
        return 0.4
    
    # Center value increases as game progresses
    center_distance = abs(r - 10) + abs(c - 10)
    center_value = max(0, 0.3 - center_distance * 0.01) * (1 + move_number / 100)
    
    return center_value


def evaluate_connection(move: Tuple[int, int], me: List[Tuple[int, int]], 
                        board: Dict) -> int:
    """
    Evaluate connection potential - connecting groups or strengthening shape.
    """
    r, c = move
    connection_score = 0
    
    # Check adjacent friendly stones
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if (nr, nc) in board and board[(nr, nc)] == 1:
            connection_score += 5
    
    # Bonus for connecting separate groups
    groups_connected = len(set(id(get_group(neighbor, board)) 
                              for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                              if (nr := r + dr, nc := c + dc) in board 
                              and board[(nr, nc)] == 1))
    
    if groups_connected > 1:
        connection_score += 10 * groups_connected
    
    return connection_score


def evaluate_extension(move: Tuple[int, int], opponent: List[Tuple[int, int]], 
                      board: Dict) -> int:
    """
    Evaluate extension potential - extending from existing stones and building influence.
    """
    r, c = move
    extension_score = 0
    
    # Count opponent stones in vicinity
    opponent_nearby = 0
    for dr in range(-4, 5):
        for dc in range(-4, 5):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if (nr, nc) in board and board[(nr, nc)] == -1:
                distance = abs(dr) + abs(dc)
                opponent_nearby += max(0, 5 - distance)
    
    # Extension is better when there's opponent influence to counter
    if opponent_nearby > 0:
        extension_score = min(opponent_nearby, 20)
    
    # Bonus for moves that reduce opponent influence
    extension_score += count_adjacent_empty(r, c, board) * 2
    
    return extension_score


def count_adjacent_empty(r: int, c: int, board: Dict, radius: int = 3) -> int:
    """
    Count empty points near a location.
    """
    empty_count = 0
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) not in board:
                empty_count += 1
    return empty_count
