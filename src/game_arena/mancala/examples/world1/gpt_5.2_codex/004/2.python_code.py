
import time
from typing import List, Tuple

# Ring excludes opponent store: you[0..6], opp[0..5] -> 13 positions
RING = [('y', i) for i in range(7)] + [('o', i) for i in range(6)]
RING_LEN = 13
TIME_LIMIT = 0.9  # seconds

class Timeout(Exception):
    pass

def apply_move(you: List[int], opp: List[int], idx: int) -> Tuple[List[int], List[int], bool]:
    """Apply move idx for player 'you', return (new_you, new_opp, extra_turn)."""
    new_you = you[:]
    new_opp = opp[:]
    seeds = new_you[idx]
    new_you[idx] = 0

    start = idx + 1
    counts_you = [0] * 6  # counts of drops in each of your houses

    last_side = None
    last_pos = None

    for s in range(seeds):
        side, pos = RING[(start + s) % RING_LEN]
        if side == 'y':
            new_you[pos] += 1
            if pos < 6:
                counts_you[pos] += 1
        else:
            new_opp[pos] += 1
        last_side, last_pos = side, pos

    extra = (last_side == 'y' and last_pos == 6)

    # Capture rule
    if last_side == 'y' and last_pos is not None and last_pos < 6:
        if counts_you[last_pos] == 1 and you[last_pos] == 0 and new_opp[5 - last_pos] > 0:
            captured = new_opp[5 - last_pos]
            new_opp[5 - last_pos] = 0
            new_you[last_pos] = 0
            new_you[6] += captured + 1

    # Check for end of game and sweep remaining seeds
    sum_you = sum(new_you[0:6])
    sum_opp = sum(new_opp[0:6])
    if sum_you == 0 or sum_opp == 0:
        if sum_you > 0:
            new_you[6] += sum_you
            for i in range(6):
                new_you[i] = 0
        if sum_opp > 0:
            new_opp[6] += sum_opp
            for i in range(6):
                new_opp[i] = 0
        extra = False

    return new_you, new_opp, extra

def terminal_score(you: List[int], opp: List[int]) -> float:
    ys = you[6] + sum(you[0:6])
    os = opp[6] + sum(opp[0:6])
    return (ys - os) * 10.0

def evaluate(you: List[int], opp: List[int]) -> float:
    store_diff = you[6] - opp[6]
    house_diff = sum(you[0:6]) - sum(opp[0:6])
    extra_moves = 0
    for i in range(6):
        seeds = you[i]
        if seeds == 0:
            continue
        if (i + seeds) % RING_LEN == 6:
            extra_moves += 1
    return store_diff * 4.0 + house_diff * 1.0 + extra_moves * 0.5

def negamax(you: List[int], opp: List[int], depth: int, alpha: float, beta: float,
            start_time: float) -> float:
    if time.time() - start_time > TIME_LIMIT:
        raise Timeout

    if sum(you[0:6]) == 0 or sum(opp[0:6]) == 0:
        return terminal_score(you, opp)

    if depth == 0:
        return evaluate(you, opp)

    best = -1e18
    # Move ordering: prioritize extra moves, then larger sowing
    moves = [i for i in range(6) if you[i] > 0]
    moves.sort(key=lambda i: ((i + you[i]) % RING_LEN == 6, you[i]), reverse=True)

    for move in moves:
        ny, no, extra = apply_move(you, opp, move)
        if extra:
            score = negamax(ny, no, depth - 1, alpha, beta, start_time)
        else:
            score = -negamax(no, ny, depth - 1, -beta, -alpha, start_time)

        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(you: List[int], opponent: List[int]) -> int:
    """Return a legal move index 0..5."""
    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        return 0  # should not happen per problem statement

    start_time = time.time()
    best_move = legal_moves[0]
    depth = 1

    while True:
        if time.time() - start_time > TIME_LIMIT:
            break
        try:
            best_score = -1e18
            # Root move ordering
            moves = legal_moves[:]
            moves.sort(key=lambda i: ((i + you[i]) % RING_LEN == 6, you[i]), reverse=True)
            for move in moves:
                ny, no, extra = apply_move(you, opponent, move)
                if extra:
                    score = negamax(ny, no, depth - 1, -1e18, 1e18, start_time)
                else:
                    score = -negamax(no, ny, depth - 1, -1e18, 1e18, start_time)
                if score > best_score:
                    best_score = score
                    best_move = move
            depth += 1
        except Timeout:
            break

    return best_move
