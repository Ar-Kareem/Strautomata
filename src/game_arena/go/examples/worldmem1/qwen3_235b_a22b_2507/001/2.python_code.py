
import numpy as np
from collections import deque

def is_on_board(r, c):
    return 1 <= r <= 19 and 1 <= c <= 19

def get_neighbors(r, c):
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if is_on_board(nr, nc):
            neighbors.append((nr, nc))
    return neighbors

def find_group(board, r, c, color):
    """Returns the group (set of connected stones) and its liberties."""
    color_val = 1 if color == 'me' else -1
    visited = set()
    group = set()
    queue = deque([(r, c)])
    liberties = set()
    while queue:
        pos = queue.popleft()
        if pos in visited:
            continue
        visited.add(pos)
        pr, pc = pos
        if board[pr-1, pc-1] == color_val:
            group.add((pr, pc))
            for nr, nc in get_neighbors(pr, nc):
                if board[nr-1, nc-1] == 0:
                    liberties.add((nr, nc))
                elif board[nr-1, nc-1] == color_val and (nr, nc) not in visited:
                    queue.append((nr, nc))
    return group, liberties

def count_liberties(board, r, c, color):
    """Count liberties of the group at (r,c)."""
    if board[r-1, c-1] == (1 if color == 'me' else -1):
        _, liberties = find_group(board, r, c, color)
        return len(liberties)
    return 0

def would_have_liberties_after_play(board, r, c, color):
    """Simulate placing a stone and check if the group has liberties."""
    board = board.copy()
    color_val = 1 if color == 'me' else -1
    board[r-1, c-1] = color_val
    # Check if any captured opponent groups give new liberties
    opponent_color_val = -color_val
    for nr, nc in get_neighbors(r, c):
        if board[nr-1, nc-1] == opponent_color_val:
            opp_group, _ = find_group(board, nr, nc, 'opponent' if color == 'me' else 'me')
            opp_liberties_count = 0
            for orow, ocol in opp_group:
                for lr, lc in get_neighbors(orow, ocol):
                    if board[lr-1, lc-1] == 0:
                        opp_liberties_count += 1
                        break
                if opp_liberties_count:
                    break
            if opp_liberties_count == 0:  # captured
                for orow, ocol in opp_group:
                    board[orow-1, ocol-1] = 0  # remove captured stones

    # Now check if own group has liberties
    my_group, my_liberties = find_group(board, r, c, color)
    return len(my_liberties) > 0

def get_legal_actions(board, me_stones, opp_stones):
    legal_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if board[r-1, c-1] != 0:
                continue
            if would_have_liberties_after_play(board, r, c, 'me'):
                legal_moves.append((r, c))
    return legal_moves

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    board = np.zeros((19, 19), dtype=np.int8)
    
    # Fill board: 1 for me, -1 for opponent
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = -1
    
    # Update move count in memory
    if 'move_count' not in memory:
        memory['move_count'] = 0
    memory['move_count'] += 1
    move_count = memory['move_count']
    
    # Get legal actions
    legal_actions = get_legal_actions(board, me, opponent)
    if not legal_actions:
        return (0, 0), memory  # pass
    
    # 1. Prioritize moves that capture opponent stones
    capture_moves = []
    for r, c in legal_actions:
        board_next = board.copy()
        board_next[r-1, c-1] = 1
        captured_any = False
        for nr, nc in get_neighbors(r, c):
            if board_next[nr-1, nc-1] == -1:
                opp_group, _ = find_group(board_next, nr, nc, 'opponent')
                opp_liberties_count = 0
                for orow, ocol in opp_group:
                    for lr, lc in get_neighbors(orow, ocol):
                        if board_next[lr-1, lc-1] == 0:
                            opp_liberties_count += 1
                            break
                    if opp_liberties_count:
                        break
                if opp_liberties_count == 0:
                    captured_any = True
                    break
        if captured_any:
            capture_moves.append((r, c))
    
    if capture_moves:
        best_move = capture_moves[0]  # Prefer first capture (could be improved)
        return best_move, memory
    
    # 2. Prevent own capture: if any of my groups has 1 liberty, save it
    critical_defense = []
    for r, c in me:
        liberties = count_liberties(board, r, c, 'me')
        if liberties == 1:
            # Find the liberty point
            _, lib_set = find_group(board, r, c, 'me')
            for lr, lc in lib_set:
                if (lr, lc) in legal_actions:
                    critical_defense.append((lr, lc))
    if critical_defense:
        return critical_defense[0], memory  # defend first critical group
    
    # 3. Opening moves: play corner 4-4, then sides, then center
    opening_prefs = [
        (4, 4), (4, 16), (16, 4), (16, 16),  # corners
        (4, 10), (10, 4), (16, 10), (10, 16), (10, 10),  # sides and center
        (3, 3), (3, 17), (17, 3), (17, 17),  # alternative corner
    ]
    for move in opening_prefs:
        if move in legal_actions:
            return move, memory

    # 4. Play center if early
    if move_count < 30:
        center = (10, 10)
        if center in legal_actions:
            return center, memory

    # 5. Avoid edge and prefer more central moves
    legal_actions_sorted = sorted(legal_actions, key=lambda x: -(abs(x[0]-10)**2 + abs(x[1]-10)**2))
    
    # 6. Avoid immediate suicide or low-value edge moves unless necessary
    for move in legal_actions_sorted:
        if would_have_liberties_after_play(board, move[0], move[1], 'me'):
            return move, memory

    # Last resort: return first legal action
    return legal_actions[0], memory
