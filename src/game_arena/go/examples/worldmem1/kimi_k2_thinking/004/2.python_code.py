
import numpy as np
from typing import List, Tuple, Set, Dict
import random

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    """
    Strategic Go policy for 19x19 board.
    Prioritizes: 1) Captures, 2) Atari defense, 3) Strategic points, 4) Extensions, 5) Random
    """
    BOARD_SIZE = 19
    
    # Initialize board (0=empty, 1=my, 2=opponent)
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int8)
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = 2
    
    # Get ko position from memory
    ko_position = memory.get('ko_position', None)
    
    # Get all legal moves (checking for ko and suicide)
    legal_moves = _get_legal_moves(board, ko_position)
    
    if not legal_moves:
        return (0, 0), {'ko_position': None}
    
    # Try to find best move in order of priority
    move = _find_best_move(board, legal_moves)
    
    # Update memory for next turn
    new_memory = _update_ko_memory(board, move, memory)
    
    return move, new_memory

def _get_legal_moves(board: np.ndarray, ko_position: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Generate all legal moves (no suicide, no ko)"""
    BOARD_SIZE = board.shape[0]
    legal = []
    
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] != 0:
                continue
            
            move = (r+1, c+1)
            
            # Ko rule
            if ko_position and move == ko_position:
                continue
            
            # Suicide rule check
            if _is_suicide_move(board, r, c):
                continue
            
            legal.append(move)
    
    return legal

def _is_suicide_move(board: np.ndarray, r: int, c: int) -> bool:
    """Check if move at (r,c) is suicide"""
    BOARD_SIZE = board.shape[0]
    
    # If any adjacent point is empty, not suicide
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            if board[nr, nc] == 0:
                return False
    
    # Check if captures opponent stones
    if _would_capture(board, r, c):
        return False
    
    # Check if connects to my stones with liberties
    if _connects_to_liberty(board, r, c):
        return False
    
    return True

def _would_capture(board: np.ndarray, r: int, c: int) -> bool:
    """Check if move would capture opponent stones"""
    BOARD_SIZE = board.shape[0]
    
    # Temporarily place stone
    original = board[r, c]
    board[r, c] = 1  # My stone
    
    captures = False
    
    # Check each adjacent opponent stone
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            if board[nr, nc] == 2:  # Opponent
                if _get_group_liberties(board, nr, nc) == 0:
                    captures = True
                    break
    
    # Restore board
    board[r, c] = original
    
    return captures

def _connects_to_liberty(board: np.ndarray, r: int, c: int) -> bool:
    """Check if move connects to my stones that have liberties"""
    BOARD_SIZE = board.shape[0]
    
    # Temporarily place stone
    original = board[r, c]
    board[r, c] = 1  # My stone
    
    # Check if new group has liberties
    libs = _get_group_liberties(board, r, c)
    
    # Restore board
    board[r, c] = original
    
    return libs > 0

def _get_group_liberties(board: np.ndarray, r: int, c: int) -> int:
    """Get number of liberties for stone/group at (r,c)"""
    BOARD_SIZE = board.shape[0]
    stone_color = board[r, c]
    if stone_color == 0:
        return 0
    
    visited = {(r, c)}
    queue = [(r, c)]
    liberties = set()
    
    while queue:
        cr, cc = queue.pop(0)
        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if board[nr, nc] == 0:
                    liberties.add((nr, nc))
                elif board[nr, nc] == stone_color and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
    
    return len(liberties)

def _find_best_move(board: np.ndarray, legal_moves: List[Tuple[int, int]]) -> Tuple[int, int]:
    """Find best move based on heuristics"""
    
    # 1. Capture moves
    capture_moves = _find_captures(board, legal_moves)
    if capture_moves:
        return random.choice(capture_moves)
    
    # 2. Defense moves (save stones in atari)
    defense_moves = _find_defenses(board, legal_moves)
    if defense_moves:
        return random.choice(defense_moves)
    
    # 3. Strategic moves (3-3 corners, star points)
    strategic_moves = _find_strategic_points(legal_moves)
    if strategic_moves:
        return random.choice(strategic_moves)
    
    # 4. Extension moves (play near my stones)
    extension_moves = _find_extensions(board, legal_moves)
    if extension_moves:
        return random.choice(extension_moves)
    
    # 5. Random move
    return random.choice(legal_moves)

def _find_captures(board: np.ndarray, legal_moves: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Find moves that capture opponent stones"""
    capture_moves = []
    BOARD_SIZE = board.shape[0]
    
    for move in legal_moves:
        r, c = move[0]-1, move[1]-1
        
        # Check adjacent opponent stones
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if board[nr, nc] == 2:  # Opponent
                    if _get_group_liberties(board, nr, nc) == 1:
                        capture_moves.append(move)
                        break
    
    return capture_moves

def _find_defenses(board: np.ndarray, legal_moves: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Find moves that defend my stones in atari"""
    defense_moves = []
    BOARD_SIZE = board.shape[0]
    
    # Find my stones with 1 liberty
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] == 1 and _get_group_liberties(board, r, c) == 1:
                # Find the liberty
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                        if board[nr, nc] == 0:
                            move = (nr+1, nc+1)
                            if move in legal_moves and move not in defense_moves:
                                defense_moves.append(move)
    
    return defense_moves

def _find_strategic_points(legal_moves: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Return strategic points that are legal moves"""
    # 3-3 corners, star points, and center
    strategic = [
        (3, 3), (3, 17), (17, 3), (17, 17),  # 3-3 corners
        (9, 9),  # Center
        (9, 3), (3, 9), (9, 17), (17, 9),  # Mid-side star points
        (5, 5), (5, 15), (15, 5), (15, 15),  # 5-5 points
    ]
    
    return [p for p in strategic if p in legal_moves]

def _find_extensions(board: np.ndarray, legal_moves: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Find moves adjacent to my stones"""
    BOARD_SIZE = board.shape[0]
    extensions = set()
    
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] == 1:  # My stone
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                        if board[nr, nc] == 0:
                            move = (nr+1, nc+1)
                            if move in legal_moves:
                                extensions.add(move)
    
    return list(extensions)

def _update_ko_memory(board: np.ndarray, move: Tuple[int, int], old_memory: Dict) -> Dict:
    """Simple ko memory: if we capture exactly one stone, remember its position"""
    if move == (0, 0):
        return {'ko_position': None}
    
    BOARD_SIZE = board.shape[0]
    r, c = move[0]-1, move[1]-1
    
    # Check if this move captures exactly one stone
    captured_positions = []
    
    # Temporarily place stone
    original = board[r, c]
    board[r, c] = 1
    
    # Check adjacent opponent stones
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            if board[nr, nc] == 2 and _get_group_liberties(board, nr, nc) == 0:
                # Capture this group
                group = _get_stone_group(board, nr, nc)
                captured_positions.extend(group)
    
    # Restore board
    board[r, c] = original
    
    # If exactly one stone captured, that's a ko position
    if len(captured_positions) == 1:
        ko_pos = captured_positions[0]
        return {'ko_position': (ko_pos[0]+1, ko_pos[1]+1)}
    
    return {'ko_position': None}

def _get_stone_group(board: np.ndarray, r: int, c: int) -> List[Tuple[int, int]]:
    """Get all stones in the group at (r,c)"""
    BOARD_SIZE = board.shape[0]
    stone_color = board[r, c]
    if stone_color == 0:
        return []
    
    visited = {(r, c)}
    queue = [(r, c)]
    group = [(r, c)]
    
    while queue:
        cr, cc = queue.pop(0)
        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if board[nr, nc] == stone_color and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
                    group.append((nr, nc))
    
    return group
