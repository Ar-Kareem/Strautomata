
import numpy as np
from typing import List, Tuple, Optional

# Othello policy implementing negamax with alpha-beta and positional heuristics.

# Positional weights (classic Othello heuristic table)
WEIGHTS = np.array([
    [120, -20, 20, 5, 5, 20, -20, 120],
    [-20, -40, -5, -5, -5, -5, -40, -20],
    [20, -5, 15, 3, 3, 15, -5, 20],
    [5, -5, 3, 3, 3, 3, -5, 5],
    [5, -5, 3, 3, 3, 3, -5, 5],
    [20, -5, 15, 3, 3, 15, -5, 20],
    [-20, -40, -5, -5, -5, -5, -40, -20],
    [120, -20, 20, 5, 5, 20, -20, 120]
], dtype=int)

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),          (0, 1),
              (1, -1),  (1, 0), (1, 1)]

# Convert row,col to move string like 'd3'
def rc_to_move(r: int, c: int) -> str:
    return chr(ord('a') + c) + str(r + 1)

# Get legal moves for 'player' given opponent 'opp'
def legal_moves(player: np.ndarray, opp: np.ndarray) -> List[Tuple[int, int]]:
    moves = []
    occupied = player | opp
    for r in range(8):
        for c in range(8):
            if occupied[r, c]:
                continue
            # check 8 directions
            ok = False
            for dr, dc in DIRECTIONS:
                rr, cc = r + dr, c + dc
                found_opp = False
                while 0 <= rr < 8 and 0 <= cc < 8:
                    if opp[rr, cc]:
                        found_opp = True
                        rr += dr; cc += dc
                        continue
                    if player[rr, cc]:
                        if found_opp:
                            ok = True
                        break
                    # empty
                    break
                if ok:
                    moves.append((r, c))
                    break
    return moves

# Apply a move for 'player' at (r,c); return new (player, opp)
def apply_move(player: np.ndarray, opp: np.ndarray, move: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    r0, c0 = move
    new_player = player.copy()
    new_opp = opp.copy()
    # Place the disc
    new_player[r0, c0] = 1
    # Flip in each direction
    for dr, dc in DIRECTIONS:
        rr, cc = r0 + dr, c0 + dc
        flips = []
        while 0 <= rr < 8 and 0 <= cc < 8:
            if new_opp[rr, cc]:
                flips.append((rr, cc))
                rr += dr; cc += dc
                continue
            if new_player[rr, cc]:
                # flip all flips
                for fr, fc in flips:
                    new_player[fr, fc] = 1
                    new_opp[fr, fc] = 0
                break
            # empty or off-board
            break
    return new_player, new_opp

# Evaluate from the perspective of 'player' given opponent 'opp'
def evaluate(player: np.ndarray, opp: np.ndarray) -> int:
    # Weighted positional difference
    wdiff = int((WEIGHTS * (player - opp)).sum())
    # Mobility: difference in number of legal moves
    player_moves = len(legal_moves(player, opp))
    opp_moves = len(legal_moves(opp, player))
    mobility = player_moves - opp_moves
    # Corner occupancy
    corners = [(0,0),(0,7),(7,0),(7,7)]
    corner_score = 0
    for r,c in corners:
        if player[r,c]:
            corner_score += 1
        elif opp[r,c]:
            corner_score -= 1
    # Disc difference (small weight)
    disc_diff = int(player.sum() - opp.sum())
    # Combine with tuned weights
    score = wdiff + 100 * corner_score + 10 * mobility + 2 * disc_diff
    return score

# Negamax with alpha-beta. player/opp are arrays with current player to move.
def negamax(player: np.ndarray, opp: np.ndarray, depth: int, alpha: int, beta: int) -> Tuple[int, Optional[Tuple[int,int]]]:
    moves = legal_moves(player, opp)
    if depth == 0 or (not moves and not legal_moves(opp, player)):
        # Terminal or depth limit: evaluate
        return evaluate(player, opp), None

    if not moves:
        # Pass: opponent moves
        val, _ = negamax(opp, player, depth - 1, -beta, -alpha)
        return -val, None

    best_move = None
    # Move ordering: try corners first, then by immediate heuristic (capture count)
    def move_score_est(m):
        r,c = m
        base = WEIGHTS[r,c]
        # Estimate flips count quickly
        flips = 0
        for dr,dc in DIRECTIONS:
            rr,cc = r+dr, c+dc
            cnt = 0
            while 0<=rr<8 and 0<=cc<8:
                if opp[rr,cc]:
                    cnt += 1
                    rr += dr; cc += dc
                    continue
                if player[rr,cc]:
                    flips += cnt
                break
        return base + flips*5

    moves_sorted = sorted(moves, key=move_score_est, reverse=True)

    for m in moves_sorted:
        new_player, new_opp = apply_move(player, opp, m)
        val, _ = negamax(new_opp, new_player, depth - 1, -beta, -alpha)
        val = -val
        if val > alpha:
            alpha = val
            best_move = m
        if alpha >= beta:
            break
    return alpha, best_move

# Main policy function required by the arena
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Ensure booleans/ints
    player = (you.astype(np.int8))
    opp = (opponent.astype(np.int8))

    moves = legal_moves(player, opp)
    if not moves:
        return "pass"

    empties = 64 - int(player.sum() + opp.sum())

    # Adaptive depth
    # Fallback depth 4; increase late game or when few legal moves
    max_depth = 4
    if empties <= 20:
        max_depth = 6
    if empties <= 10:
        max_depth = 8
    # If branching is small (few moves), increase deeper but keep cap
    if len(moves) <= 4 and max_depth < 8:
        max_depth = min(8, max_depth + 2)

    # If any corner move available, play it immediately (strong rule)
    corner_moves = [(r,c) for r,c in moves if (r,c) in [(0,0),(0,7),(7,0),(7,7)]]
    if corner_moves:
        r,c = corner_moves[0]
        return rc_to_move(r,c)

    # Run negamax search
    score, best = negamax(player, opp, max_depth, -10**9, 10**9)
    if best is None:
        # As fallback, pick the move with highest immediate heuristic
        best = max(moves, key=lambda m: (WEIGHTS[m[0], m[1]]))
    return rc_to_move(best[0], best[1])

# If running as a module, you can test policy with a basic starting position
if __name__ == "__main__":
    # Set up standard Othello start
    you = np.zeros((8,8), dtype=int)
    opp = np.zeros((8,8), dtype=int)
    # standard starting position (white at d4,e5; black at e4,d5). Here we just set one side
    # Suppose we're black with discs at d4 (r3,c3) and e5 (r4,c4)
    you[3,3] = 1
    you[4,4] = 1
    opp[3,4] = 1
    opp[4,3] = 1
    print(policy(you, opp))
