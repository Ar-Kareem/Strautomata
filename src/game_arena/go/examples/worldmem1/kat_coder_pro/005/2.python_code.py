
import random
import copy
from typing import List, Tuple, Dict

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    # If we have a move in memory, return it
    if 'move' in memory:
        return memory['move'], {}
    
    # Otherwise, simulate a game and return the first move
    board = [[0 for _ in range(19)] for _ in range(19)]
    
    # Place existing stones on the board
    for r, c in me:
        board[r-1][c-1] = 1
    for r, c in opponent:
        board[r-1][c-1] = 2
    
    # Simulate a game
    current_player = 1  # 1 for me, 2 for opponent
    while True:
        # Get all legal moves for the current player
        legal_moves = []
        for r in range(19):
            for c in range(19):
                if board[r][c] == 0:
                    # Check if this move is legal (not suicidal)
                    if is_legal_move(board, r, c, current_player):
                        legal_moves.append((r+1, c+1))
        
        # If no legal moves, pass
        if not legal_moves:
            if current_player == 1:
                return (0, 0), {}
            current_player = 3 - current_player
            continue
        
        # Choose a random legal move
        r, c = random.choice(legal_moves)
        board[r-1][c-1] = current_player
        
        # If this is the first move for player 1, remember it
        if current_player == 1:
            memory['move'] = (r, c)
            return (r, c), memory
        
        # Switch players
        current_player = 3 - current_player

def is_legal_move(board, r, c, player):
    # Simple check: a move is legal if it's not suicidal
    # This is a simplified check and doesn't handle all Go rules
    # but should be sufficient for this baseline strategy
    
    # Check if placing a stone here would capture any opponent stones
    opponent = 3 - player
    captured = False
    
    # Check adjacent positions
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == opponent:
            if has_liberties(board, nr, nc, opponent):
                captured = True
    
    # If we can capture, the move is legal
    if captured:
        return True
    
    # Otherwise, check if the move itself has liberties
    # This is a simplified check
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == 0:
            return True
    
    return False

def has_liberties(board, r, c, player):
    # Simple check if a group has liberties
    # This is a simplified implementation
    visited = set()
    stack = [(r, c)]
    while stack:
        cr, cc = stack.pop()
        if (cr, cc) in visited:
            continue
        visited.add((cr, cc))
        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr][nc] == 0:
                    return True
                elif board[nr][nc] == player and (nr, nc) not in visited:
                    stack.append((nr, nc))
    
    return False
