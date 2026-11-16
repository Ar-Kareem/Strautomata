
import time
from typing import List, Tuple

# Precompute all winning lines for 4x4 board
LINES = []
for r in range(4):
    LINES.append(tuple(r*4 + c for c in range(4)))
for c in range(4):
    LINES.append(tuple(r*4 + c for r in range(4)))
LINES.append((0, 5, 10, 15))
LINES.append((3, 6, 9, 12))

CENTER_INDICES = {5, 6, 9, 10}

def check_winner(state: Tuple[int, ...]):
    for line in LINES:
        s = state[line[0]] + state[line[1]] + state[line[2]] + state[line[3]]
        if s == 4:
            return 1
        if s == -4:
            return -1
    if 0 not in state:
        return 0  # draw
    return None

def evaluate(state: Tuple[int, ...]) -> int:
    # Heuristic evaluation from perspective of player 1
    weights = [0, 1, 10, 50, 1000]
    score = 0
    for line in LINES:
        vals = [state[i] for i in line]
        if 1 in vals and -1 in vals:
            continue
        c1 = vals.count(1)
        cm = vals.count(-1)
        if cm == 0:
            score += weights[c1]
        elif c1 == 0:
            score -= weights[cm]
    return score

def policy(board: List[List[int]]) -> Tuple[int, int]:
    start_time = time.time()
    time_limit = 0.95  # seconds
    
    state = tuple(board[r][c] for r in range(4) for c in range(4))
    empties = [i for i, v in enumerate(state) if v == 0]
    
    if not empties:
        return (0, 0)  # should not happen in valid games

    # Immediate win
    for idx in empties:
        new_state = list(state)
        new_state[idx] = 1
        if check_winner(tuple(new_state)) == 1:
            return (idx // 4, idx % 4)

    # Immediate block
    for idx in empties:
        new_state = list(state)
        new_state[idx] = -1
        if check_winner(tuple(new_state)) == -1:
            return (idx // 4, idx % 4)

    # Order moves: center first, then others
    def move_priority(i):
        return (0 if i in CENTER_INDICES else 1)
    empties.sort(key=move_priority)

    memo = {}

    def negamax(st: Tuple[int, ...], player: int, depth: int, alpha: int, beta: int) -> int:
        if time.time() - start_time > time_limit:
            return evaluate(st) * player

        winner = check_winner(st)
        if winner is not None:
            if winner == 0:
                return 0
            return 100000 if winner == player else -100000
        if depth == 0:
            return evaluate(st) * player

        key = (st, player, depth)
        if key in memo:
            return memo[key]

        best = -10**9
        for i in range(16):
            if st[i] == 0:
                lst = list(st)
                lst[i] = player
                score = -negamax(tuple(lst), -player, depth - 1, -beta, -alpha)
                if score > best:
                    best = score
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    break
        memo[key] = best
        return best

    best_move = empties[0]
    best_score = -10**9
    max_depth = min(len(empties), 7)

    for depth in range(1, max_depth + 1):
        if time.time() - start_time > time_limit:
            break
        current_best = best_move
        current_score = -10**9
        for idx in empties:
            if time.time() - start_time > time_limit:
                break
            new_state = list(state)
            new_state[idx] = 1
            score = -negamax(tuple(new_state), -1, depth - 1, -10**9, 10**9)
            if score > current_score:
                current_score = score
                current_best = idx
        if time.time() - start_time <= time_limit:
            best_move = current_best
            best_score = current_score

    return (best_move // 4, best_move % 4)
