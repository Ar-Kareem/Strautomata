
import math

# Precompute all winning lines in 4x4 Tic Tac Toe
LINES = []
# Rows
for r in range(4):
    LINES.append([r*4 + c for c in range(4)])
# Columns
for c in range(4):
    LINES.append([r*4 + c for r in range(4)])
# Diagonals
LINES.append([0, 5, 10, 15])
LINES.append([3, 6, 9, 12])

WEIGHTS = {1: 1, 2: 10, 3: 100, 4: 10000}
INF = 10**7

def check_winner(flat):
    for line in LINES:
        s = flat[line[0]] + flat[line[1]] + flat[line[2]] + flat[line[3]]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0

def evaluate(flat):
    # Heuristic from player 1's perspective
    score = 0
    for line in LINES:
        vals = [flat[i] for i in line]
        if 1 in vals and -1 in vals:
            continue  # blocked line
        cnt1 = vals.count(1)
        cnt2 = vals.count(-1)
        if cnt1 > 0 and cnt2 == 0:
            score += WEIGHTS[cnt1]
        elif cnt2 > 0 and cnt1 == 0:
            score -= WEIGHTS[cnt2]
    return score

def negamax(flat, player, depth, alpha, beta, max_depth):
    winner = check_winner(flat)
    if winner != 0:
        return winner * (INF - (max_depth - depth))
    if depth == 0:
        return player * evaluate(flat)
    empties = [i for i, v in enumerate(flat) if v == 0]
    if not empties:
        return 0

    # Move ordering
    moves = []
    for idx in empties:
        flat[idx] = player
        h = player * evaluate(flat)
        flat[idx] = 0
        moves.append((h, idx))
    moves.sort(reverse=True)

    best = -INF
    for _, idx in moves:
        flat[idx] = player
        val = -negamax(flat, -player, depth - 1, -beta, -alpha, max_depth)
        flat[idx] = 0
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(board):
    # Flatten board
    flat = [cell for row in board for cell in row]

    empties = [i for i, v in enumerate(flat) if v == 0]
    if not empties:
        return (0, 0)  # fallback (shouldn't happen)

    # Immediate win
    for idx in empties:
        flat[idx] = 1
        if check_winner(flat) == 1:
            flat[idx] = 0
            return (idx // 4, idx % 4)
        flat[idx] = 0

    # Immediate block
    for idx in empties:
        flat[idx] = -1
        if check_winner(flat) == -1:
            flat[idx] = 0
            return (idx // 4, idx % 4)
        flat[idx] = 0

    # Depth selection
    empty_count = len(empties)
    if empty_count <= 6:
        depth = empty_count
    else:
        depth = 6

    best_val = -INF
    best_move = empties[0]

    # Move ordering for root
    moves = []
    for idx in empties:
        flat[idx] = 1
        h = evaluate(flat)
        flat[idx] = 0
        moves.append((h, idx))
    moves.sort(reverse=True)

    for _, idx in moves:
        flat[idx] = 1
        val = -negamax(flat, -1, depth - 1, -INF, INF, depth)
        flat[idx] = 0
        if val > best_val:
            best_val = val
            best_move = idx

    return (best_move // 4, best_move % 4)
