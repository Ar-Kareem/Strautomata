
import numpy as np
import random

# Constants
BOARD_SIZE = 19
PASS_MOVE = (0, 0)
EMPTY = 0
BLACK = 1
WHITE = -1

# Directions (up, down, left, right)
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def policy(me, opponent, memory):
    """
    Main policy function for Go AI.
    Priorities: 1) Captures, 2) Defenses, 3) Opening, 4) Random legal move
    """
    # Create 0-indexed board
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int8)
    for r, c in me:
        board[r-1, c-1] = BLACK
    for r, c in opponent:
        board[r-1, c-1] = WHITE
    
    # Get ko point from memory (or None if not set)
    ko_point = memory.get('ko', None)
    
    # Generate all legal moves (excluding ko and suicide)
    legal_moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] == EMPTY and (r, c) != ko_point:
                if not is_suicide(board, r, c, BLACK, WHITE):
                    legal_moves.append((r, c))
    
    # If no legal moves, pass
    if not legal_moves:
        return PASS_MOVE, {'ko': None}
    
    # Priority 1: Capture moves
    capture_moves = find_capture_moves(board, legal_moves, BLACK, WHITE)
    if capture_moves:
        # Choose the capture that captures the most stones
        best_capture = max(capture_moves, key=lambda x: x[1])
        move = (best_capture[0][0] + 1, best_capture[0][1] + 1)
        # Update ko point if this is a single-stone capture
        new_ko = update_ko(board, best_capture[0], BLACK, WHITE)
        return move, {'ko': new_ko}
    
    # Priority 2: Defense moves (save our groups in atari)
    defense_moves = find_defense_moves(board, legal_moves, BLACK, WHITE)
    if defense_moves:
        move = (defense_moves[0][0] + 1, defense_moves[0][1] + 1)
        return move, {'ko': None}
    
    # Priority 3: Opening strategy (first 30 moves)
    total_stones = len(me) + len(opponent)
    if total_stones < 30:
        opening_move = get_opening_move(board)
        if opening_move:
            return opening_move, {'ko': None}
    
    # Priority 4: Play a random legal move
    move = random.choice(legal_moves)
    move = (move[0] + 1, move[1] + 1)
    return move, {'ko': None}


def is_suicide(board, r, c, player, opponent):
    """
    Check if a move is suicide (no liberties and doesn't capture).
    Fast check by temporarily placing the stone.
    """
    temp_board = board.copy()
    temp_board[r, c] = player
    
    # If we capture opponent stones, it's not suicide
    if get_captured_stones(temp_board, opponent):
        return False
    
    # Check if the new group has liberties
    return get_liberty_count(temp_board, r, c) == 0


def get_captured_stones(board, player):
    """
    Get all stones of 'player' that have no liberties.
    Returns list of (r, c) tuples.
    """
    captured = []
    visited = set()
    
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] == player and (r, c) not in visited:
                group, liberties = get_group_and_liberties(board, r, c)
                visited.update(group)
                if liberties == 0:
                    captured.extend(group)
    
    return captured


def get_group_and_liberties(board, r, c):
    """
    Get the group of stones at (r, c) and its liberty count.
    Returns (group_list, liberty_count)
    """
    player = board[r, c]
    if player == EMPTY:
        return [], 0
    
    group = [(r, c)]
    liberties = set()
    visited = {(r, c)}
    stack = [(r, c)]
    
    while stack:
        cr, cc = stack.pop()
        for dr, dc in DIRS:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if board[nr, nc] == EMPTY:
                    liberties.add((nr, nc))
                elif board[nr, nc] == player and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    group.append((nr, nc))
                    stack.append((nr, nc))
    
    return group, len(liberties)


def get_liberty_count(board, r, c):
    """
    Get the number of liberties for the group at (r, c).
    Faster version when we only need the count.
    """
    player = board[r, c]
    if player == EMPTY:
        return 0
    
    liberties = set()
    visited = {(r, c)}
    stack = [(r, c)]
    
    while stack:
        cr, cc = stack.pop()
        for dr, dc in DIRS:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if board[nr, nc] == EMPTY:
                    liberties.add((nr, nc))
                elif board[nr, nc] == player and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    stack.append((nr, nc))
    
    return len(liberties)


def find_capture_moves(board, legal_moves, player, opponent):
    """
    Find all capture moves among legal_moves.
    Returns list of ((r, c), capture_count) tuples.
    """
    capture_moves = []
    
    for r, c in legal_moves:
        # Simulate the move
        temp_board = board.copy()
        temp_board[r, c] = player
        
        # Check for captures
        captured = get_captured_stones(temp_board, opponent)
        if captured:
            capture_moves.append(((r, c), len(captured)))
    
    return capture_moves


def update_ko(board, move, player, opponent):
    """
    Check if a move creates a ko situation.
    Returns the ko point (r, c) if it's a single-stone capture, else None.
    """
    r, c = move
    temp_board = board.copy()
    temp_board[r, c] = player
    
    captured = get_captured_stones(temp_board, opponent)
    if len(captured) == 1:
        return captured[0]  # This is the ko point
    
    return None


def find_defense_moves(board, legal_moves, player, opponent):
    """
    Find moves that defend our groups with only 1 liberty.
    Returns list of (r, c) defense moves.
    """
    defense_moves = []
    checked_groups = set()
    
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] != player:
                continue
            
            # Get group and liberties
            group, liberties = get_group_and_liberties(board, r, c)
            
            # Skip if we've already checked this group
            group_key = tuple(sorted(group))
            if group_key in checked_groups:
                continue
            checked_groups.add(group_key)
            
            # If group is in atari (1 liberty), find the liberty
            if liberties == 1:
                # Find the single liberty
                for gr, gc in group:
                    for dr, dc in DIRS:
                        nr, nc = gr + dr, gc + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            if board[nr, nc] == EMPTY and (nr, nc) in legal_moves:
                                defense_moves.append((nr, nc))
                # Break to avoid duplicate defense moves for the same group
                break
    
    return defense_moves


def get_opening_move(board):
    """
    Get a good opening move (fuseki).
    Prioritizes star points, then corner approaches.
    """
    # Star points (4-4 points)
    star_points = [
        (3, 3), (3, 9), (3, 15),
        (9, 3), (9, 9), (9, 15),
        (15, 3), (15, 9), (15, 15)
    ]
    
    for r, c in star_points:
        if board[r-1, c-1] == EMPTY:
            return (r, c)
    
    # If all star points taken, try corner approaches
    corner_approaches = [
        (3, 5), (5, 3), (3, 13), (13, 3),
        (15, 5), (5, 15), (15, 13), (13, 15)
    ]
    
    for r, c in corner_approaches:
        if board[r-1, c-1] == EMPTY:
            return (r, c)
    
    # Fallback: pass (shouldn't happen early game)
    return None
