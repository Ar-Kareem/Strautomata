
import numpy as np

# Directions for queen-like movement
DIRS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

def in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6

def gen_reachable(board, start):
    sr, sc = start
    for dr, dc in DIRS:
        r, c = sr + dr, sc + dc
        while in_bounds(r, c) and board[r, c] == 0:
            yield (r, c)
            r += dr
            c += dc

def count_moves(board, player):
    count = 0
    positions = np.argwhere(board == player)
    for fr in positions:
        fr = (int(fr[0]), int(fr[1]))
        for to in gen_reachable(board, fr):
            # move amazon temporarily
            board[fr] = 0
            board[to] = player
            for _ in gen_reachable(board, to):
                count += 1
            # revert
            board[to] = 0
            board[fr] = player
    return count

def policy(board) -> str:
    player = 1
    opponent = 2
    best_move = None
    best_score = -1e18

    positions = np.argwhere(board == player)
    for fr in positions:
        fr = (int(fr[0]), int(fr[1]))
        for to in gen_reachable(board, fr):
            # move amazon temporarily
            board[fr] = 0
            board[to] = player
            for ar in gen_reachable(board, to):
                # apply arrow
                board[ar] = -1

                # evaluate
                opp_moves = count_moves(board, opponent)
                if opp_moves == 0:
                    # winning move
                    board[ar] = 0
                    board[to] = 0
                    board[fr] = player
                    return f"{fr[0]},{fr[1]}:{to[0]},{to[1]}:{ar[0]},{ar[1]}"
                my_moves = count_moves(board, player)
                score = my_moves - opp_moves

                if score > best_score:
                    best_score = score
                    best_move = (fr, to, ar)

                # revert arrow
                board[ar] = 0

            # revert move
            board[to] = 0
            board[fr] = player

    # fallback: return first legal move if no evaluation succeeded
    if best_move is None:
        for fr in positions:
            fr = (int(fr[0]), int(fr[1]))
            for to in gen_reachable(board, fr):
                board[fr] = 0
                board[to] = player
                for ar in gen_reachable(board, to):
                    board[to] = 0
                    board[fr] = player
                    return f"{fr[0]},{fr[1]}:{to[0]},{to[1]}:{ar[0]},{ar[1]}"
                board[to] = 0
                board[fr] = player
        # Should not happen
        return "0,0:0,0:0,0"

    fr, to, ar = best_move
    return f"{fr[0]},{fr[1]}:{to[0]},{to[1]}:{ar[0]},{ar[1]}"
