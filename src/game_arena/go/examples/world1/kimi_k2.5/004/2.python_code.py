
import numpy as np
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Convert to 0-indexed board (0-18)
    board = np.zeros((19, 19), dtype=np.int8)
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = 2
    
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def count_liberties(r: int, c: int, player: int):
        """Count liberties of group at (r,c). Returns (liberty_count, group_size)."""
        if board[r, c] != player:
            return 0, 0
        visited = set()
        libs = set()
        stack = [(r, c)]
        size = 0
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            size += 1
            for dr, dc in dirs:
                nr, nc = cr + dr, cc + dc
                if 0 <= nr < 19 and 0 <= nc < 19:
                    if board[nr, nc] == 0:
                        libs.add((nr, nc))
                    elif board[nr, nc] == player and (nr, nc) not in visited:
                        stack.append((nr, nc))
        return len(libs), size
    
    # Empty board: play star point
    if len(me) == 0 and len(opponent) == 0:
        return (4, 4)
    
    # Generate candidates (empty points adjacent to stones)
    candidates = set()
    for r in range(19):
        for c in range(19):
            if board[r, c] == 0:
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] != 0:
                        candidates.add((r, c))
                        break
    
    if not candidates:
        # Board full or isolated - find any legal move
        for r in range(19):
            for c in range(19):
                if board[r, c] == 0:
                    board[r, c] = 1
                    libs, _ = count_liberties(r, c, 1)
                    board[r, c] = 0
                    if libs > 0:
                        return (r+1, c+1)
        return (0, 0)
    
    capture_moves = []  # (r, c, capture_size)
    save_moves = []     # (r, c, resulting_libs)
    
    for r, c in candidates:
        board[r, c] = 1
        
        # Check for captures
        capture_size = 0
        is_capture = False
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 2:
                libs, size = count_liberties(nr, nc, 2)
                if libs == 0:
                    is_capture = True
                    capture_size += size
        
        # Check suicide (illegal if no capture)
        self_libs, _ = count_liberties(r, c, 1)
        if self_libs == 0 and not is_capture:
            board[r, c] = 0
            continue
        
        # Check if saves own stone in atari
        is_save = False
        saved_libs = 0
        if not is_capture:
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 1:
                    # Check if this neighbor was in atari (would have 0 libs after we play)
                    # Actually check if the combined group has good liberties
                    libs, _ = count_liberties(nr, nc, 1)
                    if libs > 0:  # Valid save
                        is_save = True
                        saved_libs = libs
                        break
        
        board[r, c] = 0
        
        if is_capture:
            capture_moves.append((r, c, capture_size))
        elif is_save:
            save_moves.append((r, c, saved_libs))
    
    # Priority 1: Capture largest group
    if capture_moves:
        capture_moves.sort(key=lambda x: -x[2])
        r, c, _ = capture_moves[0]
        return (r+1, c+1)
    
    # Priority 2: Save own group (prefer most resulting liberties)
    if save_moves:
        save_moves.sort(key=lambda x: -x[2])
        r, c, _ = save_moves[0]
        return (r+1, c+1)
    
    # Priority 3: Heuristic evaluation
    all_r = [s[0]-1 for s in me] + [s[0]-1 for s in opponent]
    all_c = [s[1]-1 for s in me] + [s[1]-1 for s in opponent]
    center_r = sum(all_r) / len(all_r) if all_r else 9
    center_c = sum(all_c) / len(all_c) if all_c else 9
    
    best_move = None
    best_score = -float('inf')
    
    for r, c in candidates:
        # Skip illegal (suicide)
        board[r, c] = 1
        libs, _ = count_liberties(r, c, 1)
        if libs == 0:
            board[r, c] = 0
            continue
        
        # Check how many opponent groups this puts in atari
        atari_bonus = 0
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 2:
                opp_libs, _ = count_liberties(nr, nc, 2)
                if opp_libs == 1:
                    atari_bonus += 10
        board[r, c] = 0
        
        score = 0
        
        # Positional preferences
        dist_to_center = abs(r - center_r) + abs(c - center_c)
        score -= dist_to_center * 2
        
        # Prefer corners and sides (early game)
        is_corner_area = (r <= 4 or r >= 14) and (c <= 4 or c >= 14)
        is_side = (r <= 4 or r >= 14 or c <= 4 or c >= 14)
        if is_corner_area:
            score += 20
        elif is_side:
            score += 5
        
        # Avoid self-atari
        if libs == 1:
            score -= 30
        elif libs == 2:
            score -= 5
        
        # Atari bonus
        score += atari_bonus
        
        # Connection heuristic
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr, nc] == 1:
                    score += 3
                elif board[nr, nc] == 2:
                    score += 1
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    if best_move:
        return (best_move[0]+1, best_move[1]+1)
    
    return (0, 0)
