
import random
from typing import List, Tuple, Set
from collections import deque

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Smart Go policy combining tactical play with strategic positioning.
    Prioritizes captures, defense, and territorial influence.
    """
    # Initialize board and stone sets
    board = set(me + opponent)
    my_stones = set(me)
    opp_stones = set(opponent)
    
    # If board is empty, play center (4,4) in 19x19 coordinates
    if not board:
        return (10, 10)
    
    # Check for immediate captures (tactical priority)
    capture_move = find_capture_move(board, my_stones, opp_stones)
    if capture_move:
        return capture_move
    
    # Check for self-atari defense
    defend_move = find_defense_move(board, my_stones, opp_stones)
    if defend_move:
        return defend_move
    
    # Check for atari threats (put opponent's groups in atari)
    atari_move = find_atari_threat(board, my_stones, opp_stones)
    if atari_move:
        return atari_move
    
    # Evaluate territory and influence opportunities
    best_move = find_territorial_move(board, my_stones, opp_stones)
    if best_move:
        return best_move
    
    # Fallback: play in empty area with best local influence
    empty_moves = get_empty_moves(board)
    if empty_moves:
        return choose_influence_move(empty_moves, my_stones, opp_stones)
    
    # Pass if no legal moves
    return (0, 0)

def find_capture_move(board: Set[Tuple[int, int]], my_stones: Set[Tuple[int, int]], 
                     opp_stones: Set[Tuple[int, int]]) -> Tuple[int, int]:
    """Find moves that capture opponent stones by reducing their liberties to 0."""
    for my_pos in my_stones:
        for neighbor in get_neighbors(my_pos):
            if neighbor not in board:  # Empty point
                temp_board = board.copy()
                temp_board.add(my_pos)
                
                # Check if this move would capture any opponent groups
                for opp_group in find_groups(temp_board, opp_stones):
                    if is_in_atari(temp_board, opp_group):
                        return neighbor
    return None

def find_defense_move(board: Set[Tuple[int, int]], my_stones: Set[Tuple[int, int]], 
                     opp_stones: Set[Tuple[int, int]]) -> Tuple[int, int]:
    """Find moves to defend my stones that are in atari."""
    for my_group in find_groups(board, my_stones):
        if len(get_liberties(board, my_group)) == 1:  # My group in atari
            liberty = get_liberties(board, my_group)[0]
            if is_legal_move(board, liberty, my_stones, opp_stones):
                return liberty
    return None

def find_atari_threat(board: Set[Tuple[int, int]], my_stones: Set[Tuple[int, int]], 
                     opp_stones: Set[Tuple[int, int]]) -> Tuple[int, int]:
    """Find moves that put opponent groups in atari."""
    for my_pos in my_stones:
        for neighbor in get_neighbors(my_pos):
            if neighbor not in board:  # Empty point
                temp_board = board.copy()
                temp_board.add(my_pos)
                
                # Check if this move puts any opponent group in atari
                for opp_group in find_groups(temp_board, opp_stones):
                    liberties = get_liberties(temp_board, opp_group)
                    if len(liberties) == 1:
                        # This move would capture next turn
                        return neighbor
    return None

def find_territorial_move(board: Set[Tuple[int, int]], my_stones: Set[Tuple[int, int]], 
                         opp_stones: Set[Tuple[int, int]]) -> Tuple[int, int]:
    """Find moves that improve territorial control."""
    empty_moves = get_empty_moves(board)
    best_move = None
    best_score = -1
    
    for move in empty_moves:
        score = evaluate_territorial_influence(board, move, my_stones, opp_stones)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def evaluate_territorial_influence(board: Set[Tuple[int, int]], move: Tuple[int, int], 
                                 my_stones: Set[Tuple[int, int]], opp_stones: Set[Tuple[int, int]]) -> int:
    """Evaluate territorial influence of a potential move."""
    score = 0
    
    # Proximity bonus (don't play too close to edges early)
    row, col = move
    distance_from_center = abs(row - 10) + abs(col - 10)
    score += max(0, 15 - distance_from_center)
    
    # Empty area expansion
    empty_count = 0
    for neighbor in get_neighbors(move):
        if neighbor not in board:
            empty_count += 1
    score += empty_count * 2
    
    # Block opponent influence
    opp_influence = 0
    for neighbor in get_neighbors(move):
        if neighbor in opp_stones:
            opp_influence += 1
    score += opp_influence * 3
    
    return score

def choose_influence_move(empty_moves: List[Tuple[int, int]], my_stones: Set[Tuple[int, int]], 
                         opp_stones: Set[Tuple[int, int]]) -> Tuple[int, int]:
    """Choose a move in empty area based on influence patterns."""
    best_move = None
    best_score = -1
    
    for move in empty_moves:
        score = evaluate_influence_pattern(move, my_stones, opp_stones)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move if best_move else random.choice(empty_moves)

def evaluate_influence_pattern(move: Tuple[int, int], my_stones: Set[Tuple[int, int]], 
                              opp_stones: Set[Tuple[int, int]]) -> int:
    """Evaluate influence pattern around a potential move."""
    score = 0
    
    # Center preference
    row, col = move
    center_dist = abs(row - 10) + abs(col - 10)
    score += max(0, 20 - center_dist)
    
    # Connect with own stones if beneficial
    my_neighbors = sum(1 for neighbor in get_neighbors(move) if neighbor in my_stones)
    score += my_neighbors * 4
    
    # Stay away from opponent stones initially
    opp_neighbors = sum(1 for neighbor in get_neighbors(move) if neighbor in opp_stones)
    score -= opp_neighbors * 2
    
    return score

def is_legal_move(board: Set[Tuple[int, int]], move: Tuple[int, int], 
                my_stones: Set[Tuple[int, int]], opp_stones: Set[Tuple[int, int]]) -> bool:
    """Check if a move is legal (no suicide, respects basic rules)."""
    temp_board = board.copy()
    temp_board.add(move)
    
    # Check if this move would create a suicidal group
    temp_my_stones = my_stones.copy()
    temp_my_stones.add(move)
    
    for group in find_groups(temp_board, temp_my_stones):
        liberties = get_liberties(temp_board, group)
        if not liberties:  # Group has no liberties (suicide)
            return False
    
    return True

def get_empty_moves(board: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Get all empty positions on the board."""
    empty_moves = []
    for row in range(1, 20):
        for col in range(1, 20):
            if (row, col) not in board:
                empty_moves.append((row, col))
    return empty_moves

def get_neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Get orthogonal neighbors of a position."""
    row, col = pos
    neighbors = []
    if row > 1:
        neighbors.append((row - 1, col))
    if row < 19:
        neighbors.append((row + 1, col))
    if col > 1:
        neighbors.append((row, col - 1))
    if col < 19:
        neighbors.append((row, col + 1))
    return neighbors

def find_groups(board: Set[Tuple[int, int]], stones: Set[Tuple[int, int]]) -> List[Set[Tuple[int, int]]]:
    """Find all connected groups of stones."""
    visited = set()
    groups = []
    
    for stone in stones:
        if stone not in visited:
            group = get_connected_group(stone, stones, visited)
            groups.append(group)
    
    return groups

def get_connected_group(start: Tuple[int, int], stones: Set[Tuple[int, int]], 
                       visited: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
    """Get all stones connected to the start stone."""
    if start in visited:
        return set()
    
    group = set()
    queue = deque([start])
    
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
            
        visited.add(current)
        group.add(current)
        
        for neighbor in get_neighbors(current):
            if neighbor in stones and neighbor not in visited:
                queue.append(neighbor)
    
    return group

def get_liberties(board: Set[Tuple[int, int]], group: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Get all liberties of a group."""
    liberties = set()
    
    for stone in group:
        for neighbor in get_neighbors(stone):
            if neighbor not in board:  # Empty point
                liberties.add(neighbor)
    
    return list(liberties)

def is_in_atari(board: Set[Tuple[int, int]], group: Set[Tuple[int, int]]) -> bool:
    """Check if a group is in atari (1 liberty)."""
    liberties = get_liberties(board, group)
    return len(liberties) == 1
