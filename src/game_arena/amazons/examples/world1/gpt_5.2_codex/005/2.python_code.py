
import numpy as np

# Directions for queen-like movement
DIRS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

def reachable(board, r, c):
    """Yield all empty squares reachable from (r,c) with queen moves."""
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
            yield (nr, nc)
            nr += dr
            nc += dc

def mobility(board, player):
    """Count total reachable empty squares for all amazons of player."""
    total = 0
    positions = np.argwhere(board == player)
    for r, c in positions:
        total += sum(1 for _ in reachable(board, r, c))
    return total

def generate_moves(board, player):
    """Generate all legal (from,to,arrow) moves for player."""
    moves = []
    positions = np.argwhere(board == player)
    for r, c in positions:
        for tr, tc in reachable(board, r, c):
            # Move amazon
            temp = board.copy()
            temp[r, c] = 0
            temp[tr, tc] = player
            # Shoot arrow
            for ar, ac in reachable(temp, tr, tc):
                moves.append((r, c, tr, tc, ar, ac))
    return moves

def policy(board) -> str:
    board = np.array(board, dtype=int)
    moves = generate_moves(board, 1)
    if not moves:
        # Should not happen in valid gameplay
        return "0,0:0,0:0,0"
    best_move = moves[0]
    best_score = -1e9

    for move in moves:
        r, c, tr, tc, ar, ac = move
        temp = board.copy()
        temp[r, c] = 0
        temp[tr, tc] = 1
        temp[ar, ac] = -1

        my_mob = mobility(temp, 1)
        opp_mob = mobility(temp, 2)
        score = my_mob - opp_mob

        if score > best_score:
            best_score = score
            best_move = move

    r, c, tr, tc, ar, ac = best_move
    return f"{r},{c}:{tr},{tc}:{ar},{ac}"
