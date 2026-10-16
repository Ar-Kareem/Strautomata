
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Board dimensions
    SIZE = 19
    
    # Initialize board with 0 = empty, 1 = me, 2 = opponent
    board = np.zeros((SIZE + 1, SIZE + 1), dtype=int)
    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = 2

    # Helper: Check if a coordinate is on the board
    def on_board(r, c):
        return 1 <= r <= SIZE and 1 <= c <= SIZE

    # Helper: Count liberties for a group starting at (r, c) for a specific player
    def get_liberties(start_r, start_c, player):
        if board[start_r, start_c] != player:
            return 0
        
        queue = deque([(start_r, start_c)])
        visited = set([(start_r, start_c)])
        liberties = 0
        visited_liberties = set()
        
        while queue:
            r, c = queue.popleft()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if on_board(nr, nc):
                    if board[nr, nc] == 0:
                        if (nr, nc) not in visited_liberties:
                            visited_liberties.add((nr, nc))
                            liberties += 1
                    elif board[nr, nc] == player and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
        return liberties

    # Helper: Check if a move is legal (basic rules: on board, empty, not suicide)
    def is_legal(r, c, player):
        if not on_board(r, c) or board[r, c] != 0:
            return False
        
        # Temporarily place stone
        board[r, c] = player
        opp = 2 if player == 1 else 1
        
        # Check suicide rule:
        # 1. If we have liberties, it's valid.
        # 2. If we don't, it's only valid if we capture opponent stones.
        my_liberties = get_liberties(r, c, player)
        
        if my_liberties > 0:
            board[r, c] = 0
            return True
            
        # Check if we captured any opponent groups
        captured = False
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if on_board(nr, nc) and board[nr, nc] == opp:
                if get_liberties(nr, nc, opp) == 0:
                    captured = True
                    break
        
        board[r, c] = 0
        return captured

    # Generate candidate moves (only near existing stones)
    candidates = set()
    all_stones = me + opponent
    if not all_stones:
        # First move: play center
        return (10, 10)
        
    for r, c in all_stones:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if on_board(nr, nc) and board[nr, nc] == 0:
                    candidates.add((nr, nc))
    
    if not candidates:
        return (0, 0) # Pass if no candidates (shouldn't happen on 19x19)

    best_move = None
    best_score = -float('inf')

    # Evaluate candidates
    for r, c in candidates:
        if not is_legal(r, c, 1):
            continue

        score = 0
        
        # 1. Liberties: Sum of liberties of the group formed by this move
        board[r, c] = 1
        score += get_liberties(r, c, 1) * 10
        
        # 2. Capture: Check if we capture opponent stones
        opp = 2
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if on_board(nr, nc) and board[nr, nc] == opp:
                if get_liberties(nr, nc, opp) == 0:
                    score += 50  # Bonus for capture
        
        # 3. Proximity to center (bias for empty board influence)
        dist = abs(r - 10) + abs(c - 10)
        score -= dist 
        
        # 4. Reduce Opponent Liberties: slightly penalize moves that give opponent more space? 
        # (Implicitly handled by capture bonuses and liberty counting)
        
        board[r, c] = 0 # Revert

        if score > best_score:
            best_score = score
            best_move = (r, c)

    if best_move is None:
        return (0, 0)

    return best_move
