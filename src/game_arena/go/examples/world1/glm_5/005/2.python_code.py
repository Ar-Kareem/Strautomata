
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    A tactical Go engine that prioritizes captures, escapes, and ataris.
    """
    size = 19
    board = np.zeros((size, size), dtype=int)
    
    # 1. Board Setup
    # 1 = Me (Current Player), 2 = Opponent
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = 2
    
    # Directions for neighbors (Up, Down, Left, Right)
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def in_bounds(r, c):
        return 0 <= r < size and 0 <= c < size

    # 2. Group Analysis
    # Identify all groups and their liberties using BFS
    # Returns list of tuples: (stones_set, liberties_set, color)
    visited = np.zeros((size, size), dtype=bool)
    groups = []
    
    for r in range(size):
        for c in range(size):
            if board[r, c] != 0 and not visited[r, c]:
                color = board[r, c]
                stones = set()
                liberties = set()
                queue = deque([(r, c)])
                visited[r, c] = True
                
                while queue:
                    qr, qc = queue.popleft()
                    stones.add((qr, qc))
                    
                    for dr, dc in dirs:
                        nr, nc = qr + dr, qc + dc
                        if in_bounds(nr, nc):
                            if board[nr, nc] == 0:
                                liberties.add((nr, nc))
                            elif board[nr, nc] == color and not visited[nr, nc]:
                                visited[nr, nc] = True
                                queue.append((nr, nc))
                
                groups.append((stones, liberties, color))

    # 3. Move Candidate Generation and Scoring
    candidate_moves = {} # map: (r, c) -> score
    
    # Analyze groups for tactical targets
    for stones, liberties, color in groups:
        # Opponent groups
        if color == 2:
            # Capture: Opponent in Atari (1 liberty)
            if len(liberties) == 1:
                move = list(liberties)[0]
                # Score based on number of stones captured
                score = 1000 + len(stones) * 100
                candidate_moves[move] = max(candidate_moves.get(move, 0), score)
            # Attack: Opponent has 2 liberties (can put in Atari)
            elif len(liberties) == 2:
                for move in liberties:
                    score = 50 + len(stones) * 5
                    candidate_moves[move] = max(candidate_moves.get(move, 0), score)
        
        # My groups
        elif color == 1:
            # Escape: My group in Atari (try to extend)
            if len(liberties) == 1:
                move = list(liberties)[0]
                # High score to save stones
                score = 900 + len(stones) * 100
                candidate_moves[move] = max(candidate_moves.get(move, 0), score)

    # 4. Strategic Moves (Fallback)
    # If no urgent tactical moves, look for proximity moves on lines 3/4
    if not candidate_moves:
        has_stones = len(me) > 0 or len(opponent) > 0
        
        for r in range(size):
            for c in range(size):
                if board[r, c] == 0:
                    # Check if near existing stones
                    if has_stones:
                        min_dist = float('inf')
                        for r2, c2 in me + opponent:
                            dist = abs(r - (r2-1)) + abs(c - (c2-1))
                            if dist < min_dist:
                                min_dist = dist
                        
                        if 1 < min_dist <= 4:
                            # Bonus for lines 3 and 4
                            line_bonus = 0
                            if r in [2, 3, 4, 14, 15, 16] or c in [2, 3, 4, 14, 15, 16]:
                                line_bonus = 10
                            
                            score = 20 - min_dist + line_bonus
                            candidate_moves[(r, c)] = candidate_moves.get((r, c), 0) + score
                    else:
                        # Opening move: star point
                        if (r, c) in [(3, 3), (3, 9), (3, 15), (9, 3), (9, 9), (9, 15), (15, 3), (15, 9), (15, 15)]:
                             candidate_moves[(r, c)] = 100

    # 5. Selection and Legality Check
    # Sort candidates by score descending
    sorted_moves = sorted(candidate_moves.items(), key=lambda item: item[1], reverse=True)

    def is_legal(move, board, player):
        r, c = move
        # Temporarily place stone
        board[r, c] = player
        
        # Check captures
        captured = False
        opp = 3 - player
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and board[nr, nc] == opp:
                # Check liberties of neighbor opponent group
                # BFS for liberties
                q = deque([(nr, nc)])
                seen = {(nr, nc)}
                has_lib = False
                while q:
                    qr, qc = q.popleft()
                    for ddr, ddc in dirs:
                        nnr, nnc = qr + ddr, qc + ddc
                        if in_bounds(nnr, nnc):
                            if board[nnr, nnc] == 0:
                                has_lib = True
                                break
                            if board[nnr, nnc] == opp and (nnr, nnc) not in seen:
                                seen.add((nnr, nnc))
                                q.append((nnr, nnc))
                    if has_lib:
                        break
                if not has_lib:
                    captured = True
        
        # If we captured, move is legal (not suicide)
        if captured:
            board[r, c] = 0 # Revert
            return True
            
        # Check if self has liberties (Suicide check)
        q = deque([(r, c)])
        seen = {(r, c)}
        has_lib = False
        while q:
            qr, qc = q.popleft()
            for ddr, ddc in dirs:
                nnr, nnc = qr + ddr, qc + ddc
                if in_bounds(nnr, nnc):
                    if board[nnr, nnc] == 0:
                        has_lib = True
                        break
                    if board[nnr, nnc] == player and (nnr, nnc) not in seen:
                        seen.add((nnr, nnc))
                        q.append((nnr, nnc))
            if has_lib:
                break
        
        board[r, c] = 0 # Revert
        return has_lib

    # Select best legal move
    for move, score in sorted_moves:
        if is_legal(move, board, 1):
            return (move[0] + 1, move[1] + 1)

    # If absolutely no moves found (shouldn't happen often), try any empty legal spot
    for r in range(size):
        for c in range(size):
            if board[r, c] == 0:
                if is_legal((r, c), board, 1):
                    return (r + 1, c + 1)

    # Pass
    return (0, 0)
