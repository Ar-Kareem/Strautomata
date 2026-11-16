
import numpy as np
from collections import deque
from typing import Set, Tuple

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Convert to 0-indexed numpy array for faster processing
    board = np.zeros((19, 19), dtype=np.int8)
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = 2
    
    player = 1
    opp = 2
    
    def neighbors(r: int, c: int):
        """Generate valid neighbor coordinates"""
        if r > 0: yield r-1, c
        if r < 18: yield r+1, c
        if c > 0: yield r, c-1
        if c < 18: yield r, c+1
    
    def get_group_libs(board: np.ndarray, r: int, c: int, color: int) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        """Return (group_stones, liberties) for a stone at (r,c)"""
        if board[r, c] != color:
            return set(), set()
        group = set()
        libs = set()
        stack = [(r, c)]
        group.add((r, c))
        
        while stack:
            cr, cc = stack.pop()
            for nr, nc in neighbors(cr, cc):
                val = board[nr, nc]
                if val == 0:
                    libs.add((nr, nc))
                elif val == color and (nr, nc) not in group:
                    group.add((nr, nc))
                    stack.append((nr, nc))
        return group, libs
    
    def is_legal(board: np.ndarray, r: int, c: int, color: int) -> bool:
        """Check if move is legal (not occupied, not suicide)"""
        if board[r, c] != 0:
            return False
        
        # Check for immediate empty neighbor
        for nr, nc in neighbors(r, c):
            if board[nr, nc] == 0:
                return True
        
        # Check for captures
        for nr, nc in neighbors(r, c):
            if board[nr, nc] == 3 - color:
                _, libs = get_group_libs(board, nr, nc, 3 - color)
                if len(libs) == 1 and (r, c) in libs:
                    return True
        
        # Check connection to own group with liberties
        for nr, nc in neighbors(r, c):
            if board[nr, nc] == color:
                _, libs = get_group_libs(board, nr, nc, color)
                if len(libs) > 1:
                    return True
        
        return False
    
    # 1. Find urgent moves (captures and saves)
    captures = []  # (move, size)
    saves = []
    visited_opp = set()
    visited_me = set()
    
    for r in range(19):
        for c in range(19):
            if board[r, c] == opp and (r, c) not in visited_opp:
                group, libs = get_group_libs(board, r, c, opp)
                visited_opp.update(group)
                if len(libs) == 1:
                    cap_move = libs.pop()
                    if is_legal(board, cap_move[0], cap_move[1], player):
                        captures.append((cap_move, len(group)))
            
            elif board[r, c] == player and (r, c) not in visited_me:
                group, libs = get_group_libs(board, r, c, player)
                visited_me.update(group)
                if len(libs) == 1:
                    save_move = libs.pop()
                    if is_legal(board, save_move[0], save_move[1], player):
                        saves.append(save_move)
    
    # Play biggest capture
    if captures:
        captures.sort(key=lambda x: -x[1])
        m = captures[0][0]
        return (m[0] + 1, m[1] + 1), memory
    
    # Save own stones
    if saves:
        m = saves[0]
        return (m[0] + 1, m[1] + 1), memory
    
    # 2. Opening: if board is empty or sparse, play 4-4 or center
    if len(me) == 0:
        openings = [(3, 3), (3, 15), (15, 3), (15, 15), (9, 9)]
        for r, c in openings:
            if is_legal(board, r, c, player):
                return (r + 1, c + 1), memory
    
    # 3. Generate candidates near existing stones
    candidates = set()
    stones = list(me) + list(opponent)
    
    for r, c in stones:
        r0, c0 = r-1, c-1  # convert to 0-indexed
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r0 + dr, c0 + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                    candidates.add((nr, nc))
    
    if not candidates:
        return (0, 0), memory
    
    # 4. Evaluate candidates
    best_move = None
    best_score = -9999
    
    for r, c in candidates:
        if not is_legal(board, r, c, player):
            continue
        
        score = 0
        
        # Center control (Manhattan distance from center)
        dist_center = abs(r - 9) + abs(c - 9)
        score += (18 - dist_center) * 2
        
        # Local features
        for nr, nc in neighbors(r, c):
            val = board[nr, nc]
            if val == player:
                score += 8
                # Favor extending from groups with few liberties
                _, libs = get_group_libs(board, nr, nc, player)
                if len(libs) <= 2:
                    score += 10
            elif val == opp:
                score += 3
                # Favor putting opponent in atari
                _, libs = get_group_libs(board, nr, nc, opp)
                if len(libs) == 2:
                    score += 12
        
        # Avoid edges early game
        if len(me) < 30:
            if r == 0 or r == 18 or c == 0 or c == 18:
                score -= 5
            if r == 1 or r == 17 or c == 1 or c == 17:
                score -= 2
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    if best_move:
        return (best_move[0] + 1, best_move[1] + 1), memory
    
    return (0, 0), memory
