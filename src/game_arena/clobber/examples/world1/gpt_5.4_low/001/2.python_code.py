
import time
from typing import List, Tuple, Dict

ROWS = 5
COLS = 6
N = ROWS * COLS

# Directions: (dr, dc, char)
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

# Precompute adjacency and move masks
ADJ = [[] for _ in range(N)]  # list of (to_idx, dir_char)
NEI_MASK = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        mask = 0
        for dr, dc, ch in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                ADJ[i].append((j, ch))
                mask |= 1 << j
        NEI_MASK[i] = mask

# Transposition table: (you_bits, opp_bits) -> exact result in {-1, +1}
TT_EXACT: Dict[Tuple[int, int], int] = {}
# Optional shallow evaluation cache
TT_MOVES: Dict[Tuple[int, int], List[Tuple[int, int, str]]] = {}

# Time control
TIME_LIMIT = 0.93
START_TIME = 0.0


def _time_up() -> bool:
    return (time.perf_counter() - START_TIME) >= TIME_LIMIT


def _to_bits(board) -> int:
    # Accept nested lists or numpy arrays
    bits = 0
    for r in range(ROWS):
        row = board[r]
        for c in range(COLS):
            if int(row[c]) == 1:
                bits |= 1 << (r * COLS + c)
    return bits


def _iter_bits(bits: int):
    while bits:
        lsb = bits & -bits
        idx = lsb.bit_length() - 1
        yield idx
        bits ^= lsb


def _move_to_str(fr: int, dch: str) -> str:
    return f"{fr // COLS},{fr % COLS},{dch}"


def _generate_moves(you: int, opp: int) -> List[Tuple[int, int, str]]:
    key = (you, opp)
    cached = TT_MOVES.get(key)
    if cached is not None:
        return cached

    moves = []
    y = you
    while y:
        lsb = y & -y
        fr = lsb.bit_length() - 1
        # Only adjacent opponent cells are legal destinations
        targets = opp & NEI_MASK[fr]
        if targets:
            for to, ch in ADJ[fr]:
                if (targets >> to) & 1:
                    moves.append((fr, to, ch))
        y ^= lsb

    TT_MOVES[key] = moves
    return moves


def _apply_move(you: int, opp: int, mv: Tuple[int, int, str]) -> Tuple[int, int]:
    fr, to, _ = mv
    # Current player piece moves from fr to to, capturing opp at to
    new_opp = (you ^ (1 << fr)) | (1 << to)
    new_you = opp ^ (1 << to)
    # Swap roles: opponent becomes player to move
    return new_you, new_opp


def _mobility(you: int, opp: int) -> int:
    count = 0
    y = you
    while y:
        lsb = y & -y
        fr = lsb.bit_length() - 1
        if opp & NEI_MASK[fr]:
            # Count exact number of legal captures from this piece
            count += (opp & NEI_MASK[fr]).bit_count()
        y ^= lsb
    return count


def _heuristic(you: int, opp: int) -> int:
    my_moves = _mobility(you, opp)
    if my_moves == 0:
        return -100000
    opp_moves = _mobility(opp, you)
    piece_diff = you.bit_count() - opp.bit_count()
    # Mobility dominates; piece count is weak tie-breaker
    return 100 * (my_moves - opp_moves) + 3 * piece_diff


def _ordered_moves(you: int, opp: int, moves: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
    scored = []
    for mv in moves:
        ny, no = _apply_move(you, opp, mv)
        opp_reply_count = len(_generate_moves(ny, no))
        # After the swap, "ny" is opponent-to-move from our original perspective.
        # Fewer replies for them is better.
        score = -opp_reply_count

        # Mild preference for central destinations
        _, to, _ = mv
        r, c = divmod(to, COLS)
        score -= abs(r - 2) + abs(c - 2.5)

        scored.append((score, mv))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [mv for _, mv in scored]


def _negamax(you: int, opp: int, depth: int, alpha: int, beta: int) -> int:
    if _time_up():
        raise TimeoutError

    key = (you, opp)
    if key in TT_EXACT:
        return TT_EXACT[key]

    moves = _generate_moves(you, opp)
    if not moves:
        TT_EXACT[key] = -1
        return -1

    if depth == 0:
        return _heuristic(you, opp)

    best = -10**9
    for mv in _ordered_moves(you, opp, moves):
        ny, no = _apply_move(you, opp, mv)
        val = -_negamax(ny, no, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    # Store exact only for solved win/loss values when fully searched enough
    if best in (-1, 1):
        TT_EXACT[key] = best
    return best


def _choose_move(you: int, opp: int) -> Tuple[int, int, str]:
    moves = _generate_moves(you, opp)
    if not moves:
        return None  # Should not happen in valid nonterminal calls

    # Immediate fallback: legal move with best local ordering
    ordered = _ordered_moves(you, opp, moves)
    best_move = ordered[0]

    # Fast exact check for immediate winning move
    for mv in ordered:
        ny, no = _apply_move(you, opp, mv)
        if not _generate_moves(ny, no):
            return mv

    # Iterative deepening
    depth = 1
    while True:
        if _time_up():
            break
        current_best = best_move
        current_best_val = -10**9
        alpha = -10**9
        beta = 10**9
        try:
            for mv in ordered:
                ny, no = _apply_move(you, opp, mv)
                val = -_negamax(ny, no, depth - 1, -beta, -alpha)
                if val > current_best_val:
                    current_best_val = val
                    current_best = mv
                if val > alpha:
                    alpha = val
            best_move = current_best

            # Reorder around PV for next iteration
            ordered = [best_move] + [m for m in ordered if m != best_move]

            # If solved as a forced win, no need to search deeper
            if current_best_val == 1:
                break

            depth += 1
        except TimeoutError:
            break

    return best_move


def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    global START_TIME
    START_TIME = time.perf_counter()

    yb = _to_bits(you)
    ob = _to_bits(opponent)

    mv = _choose_move(yb, ob)

    # Absolute safety fallback: return the first legal move if anything went wrong
    if mv is None:
        moves = _generate_moves(yb, ob)
        if moves:
            mv = moves[0]
        else:
            # No legal move exists. Arena should not call policy on terminal states.
            # Return a syntactically valid string as last resort.
            return "0,0,U"

    return _move_to_str(mv[0], mv[2])
