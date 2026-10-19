
import time
from typing import Optional

# =========================
# Constants and precompute
# =========================

BOARD_SIZE = 8
NUM_SQUARES = 64

BIT = [1 << i for i in range(NUM_SQUARES)]
IDX_TO_RC = [(i // 8, i % 8) for i in range(NUM_SQUARES)]
ROW_MASKS = [sum(1 << (r * 8 + c) for c in range(8)) for r in range(8)]

WIN_SCORE = 10**8
INF = 10**9

EXACT = 0
LOWER = 1
UPPER = 2

TT = {}
DEADLINE = 0.0
NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


# =========================
# Utility
# =========================

def opp_color(color: str) -> str:
    return 'b' if color == 'w' else 'w'


def goal_row(color: str) -> int:
    return 7 if color == 'w' else 0


def home_row(color: str) -> int:
    return 0 if color == 'w' else 7


def direction(color: str) -> int:
    return 1 if color == 'w' else -1


def progress_row(r: int, color: str) -> int:
    return r if color == 'w' else 7 - r


def bits_from_list(pieces: list[tuple[int, int]]) -> int:
    bb = 0
    for r, c in pieces:
        bb |= 1 << (r * 8 + c)
    return bb


def iter_bits(bb: int):
    while bb:
        lsb = bb & -bb
        yield lsb.bit_length() - 1
        bb ^= lsb


def apply_move(me: int, opp: int, frm: int, to: int) -> tuple[int, int]:
    me2 = (me ^ BIT[frm]) | BIT[to]
    if opp & BIT[to]:
        opp2 = opp ^ BIT[to]
    else:
        opp2 = opp
    return me2, opp2


# =========================
# Move generation
# =========================

def gen_moves(me: int, opp: int, color: str) -> list[tuple[int, int]]:
    occ = me | opp
    dr = direction(color)
    moves = []

    for frm in iter_bits(me):
        r, c = IDX_TO_RC[frm]
        nr = r + dr
        if nr < 0 or nr > 7:
            continue

        # Forward: only if empty
        to = nr * 8 + c
        if not (occ & BIT[to]):
            moves.append((frm, to))

        # Diagonal left: legal if not occupied by own piece
        if c > 0:
            to = nr * 8 + (c - 1)
            if not (me & BIT[to]):
                moves.append((frm, to))

        # Diagonal right: legal if not occupied by own piece
        if c < 7:
            to = nr * 8 + (c + 1)
            if not (me & BIT[to]):
                moves.append((frm, to))

    return moves


# =========================
# Tactical helpers
# =========================

def threatened(idx: int, opp: int, color: str) -> bool:
    # Is a piece of side "color" on idx capturable by opponent next move?
    r, c = IDX_TO_RC[idx]
    dr = direction(color)
    rr = r + dr  # squares from which opponent can capture onto idx
    if 0 <= rr <= 7:
        if c > 0 and (opp & BIT[rr * 8 + (c - 1)]):
            return True
        if c < 7 and (opp & BIT[rr * 8 + (c + 1)]):
            return True
    return False


def supported(idx: int, me: int, color: str) -> bool:
    # Does side "color" have a piece that could capture onto idx?
    r, c = IDX_TO_RC[idx]
    dr = direction(color)
    rr = r - dr
    if 0 <= rr <= 7:
        if c > 0 and (me & BIT[rr * 8 + (c - 1)]):
            return True
        if c < 7 and (me & BIT[rr * 8 + (c + 1)]):
            return True
    return False


def is_passed(idx: int, opp: int, color: str) -> bool:
    r, c = IDX_TO_RC[idx]
    dr = direction(color)
    rr = r + dr
    while 0 <= rr <= 7:
        for cc in (c - 1, c, c + 1):
            if 0 <= cc <= 7 and (opp & BIT[rr * 8 + cc]):
                return False
        rr += dr
    return True


def count_goal_threats(me: int, opp: int, color: str) -> int:
    # Number of pieces with an immediate winning move to the goal row.
    dr = direction(color)
    g = goal_row(color)
    pregoal = g - dr
    occ = me | opp
    count = 0

    candidates = me & ROW_MASKS[pregoal]
    for frm in iter_bits(candidates):
        _, c = IDX_TO_RC[frm]
        nr = g

        # Forward
        to = nr * 8 + c
        if not (occ & BIT[to]):
            count += 1
            continue

        # Diagonals
        can_win = False
        if c > 0:
            to = nr * 8 + (c - 1)
            if not (me & BIT[to]):
                can_win = True
        if not can_win and c < 7:
            to = nr * 8 + (c + 1)
            if not (me & BIT[to]):
                can_win = True

        if can_win:
            count += 1

    return count


def has_immediate_win(me: int, opp: int, color: str) -> bool:
    # Win by reaching goal row OR by capturing the opponent's last piece.
    dr = direction(color)
    g = goal_row(color)
    occ = me | opp
    last_opp = opp if opp and (opp & (opp - 1)) == 0 else 0

    for frm in iter_bits(me):
        r, c = IDX_TO_RC[frm]
        nr = r + dr
        if nr < 0 or nr > 7:
            continue

        # Forward to goal
        to = nr * 8 + c
        if nr == g and not (occ & BIT[to]):
            return True

        # Diagonals
        if c > 0:
            to = nr * 8 + (c - 1)
            if not (me & BIT[to]):
                if nr == g or (last_opp and (last_opp & BIT[to])):
                    return True
        if c < 7:
            to = nr * 8 + (c + 1)
            if not (me & BIT[to]):
                if nr == g or (last_opp and (last_opp & BIT[to])):
                    return True

    return False


def is_immediate_win_move(me: int, opp: int, color: str, frm: int, to: int) -> bool:
    r2, _ = IDX_TO_RC[to]
    if r2 == goal_row(color):
        return True
    if (opp & BIT[to]) and ((opp ^ BIT[to]) == 0):
        return True
    return False


# =========================
# Evaluation
# =========================

def piece_value(idx: int, me: int, opp: int, color: str) -> int:
    r, c = IDX_TO_RC[idx]
    p = progress_row(r, color)
    dist_to_goal = 7 - p

    # Base + strong advancement incentive
    v = 100 + 13 * p * p

    # Central columns tend to be more flexible
    v += 7 - abs(2 * c - 7)

    # Safety / support
    th = threatened(idx, opp, color)
    sup = supported(idx, me, color)
    if th:
        if sup:
            v -= 8
        else:
            v -= 35 + 6 * p
    elif sup:
        v += 14

    # Passed pawn bonus
    if is_passed(idx, opp, color):
        v += 10 + 18 * p

    # Near-promotion urgency
    if dist_to_goal == 1:
        v += 190
    elif dist_to_goal == 2:
        v += 60

    # Immediate attacking chances
    dr = direction(color)
    nr = r + dr
    if 0 <= nr <= 7:
        if c > 0 and (opp & BIT[nr * 8 + (c - 1)]):
            v += 16
        if c < 7 and (opp & BIT[nr * 8 + (c + 1)]):
            v += 16

    return v


def evaluate(me: int, opp: int, color: str) -> int:
    my_score = 0
    op_score = 0
    my_best = -1
    op_best = -1
    my_count = 0
    op_count = 0

    for idx in iter_bits(me):
        r, _ = IDX_TO_RC[idx]
        my_best = max(my_best, progress_row(r, color))
        my_score += piece_value(idx, me, opp, color)
        my_count += 1

    oc = opp_color(color)
    for idx in iter_bits(opp):
        r, _ = IDX_TO_RC[idx]
        op_best = max(op_best, progress_row(r, oc))
        op_score += piece_value(idx, opp, me, oc)
        op_count += 1

    score = my_score - op_score

    # Race / piece-count adjustments
    score += 55 * (my_best - op_best)
    score += 18 * (my_count - op_count)

    # Immediate promotion threats matter a lot
    score += 110 * count_goal_threats(me, opp, color)
    score -= 130 * count_goal_threats(opp, me, oc)

    return score


# =========================
# Terminal detection
# =========================

def terminal_score(me: int, opp: int, color: str, ply: int) -> Optional[int]:
    if me == 0:
        return -WIN_SCORE + ply
    if opp == 0:
        return WIN_SCORE - ply

    if me & ROW_MASKS[goal_row(color)]:
        return WIN_SCORE - ply
    if opp & ROW_MASKS[home_row(color)]:
        return -WIN_SCORE + ply

    return None


# =========================
# Move ordering
# =========================

def move_order_score(me: int, opp: int, color: str, frm: int, to: int, tt_move: Optional[tuple[int, int]] = None) -> int:
    if tt_move is not None and (frm, to) == tt_move:
        return 10**7

    cap = 1 if (opp & BIT[to]) else 0
    me2, opp2 = apply_move(me, opp, frm, to)
    r2, c2 = IDX_TO_RC[to]
    p2 = progress_row(r2, color)

    score = 0

    # Absolute priorities
    if r2 == goal_row(color):
        score += 2_000_000
    if cap and opp2 == 0:
        score += 1_500_000

    # Captures are strong
    if cap:
        score += 20_000
        score += 100 * progress_row(r2, opp_color(color))

    # Prefer safe/supported advanced moves
    th = threatened(to, opp2, color)
    sup = supported(to, me2, color)

    if th:
        if sup:
            score -= 20
        else:
            score -= 600
    else:
        score += 120

    if sup:
        score += 80

    score += 40 * p2 * p2
    score += 10 - abs(2 * c2 - 7)

    return score


def order_moves(me: int, opp: int, color: str, moves: list[tuple[int, int]], tt_move: Optional[tuple[int, int]] = None) -> list[tuple[int, int]]:
    scored = []
    for frm, to in moves:
        scored.append((move_order_score(me, opp, color, frm, to, tt_move), (frm, to)))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


# =========================
# Search
# =========================

def negamax(me: int, opp: int, color: str, depth: int, alpha: int, beta: int, ply: int) -> tuple[int, Optional[tuple[int, int]]]:
    global NODE_COUNTER, DEADLINE, TT

    NODE_COUNTER += 1
    if (NODE_COUNTER & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout

    t = terminal_score(me, opp, color, ply)
    if t is not None:
        return t, None

    if depth == 0:
        return evaluate(me, opp, color), None

    key = (me, opp, 1 if color == 'w' else 0)
    alpha0, beta0 = alpha, beta
    tt_move = None

    entry = TT.get(key)
    if entry is not None:
        entry_depth, flag, val, saved_move = entry
        tt_move = saved_move
        if entry_depth >= depth:
            if flag == EXACT:
                return val, saved_move
            elif flag == LOWER:
                alpha = max(alpha, val)
            else:
                beta = min(beta, val)
            if alpha >= beta:
                return val, saved_move

    moves = gen_moves(me, opp, color)
    if not moves:
        return -WIN_SCORE + ply, None

    moves = order_moves(me, opp, color, moves, tt_move)

    best_score = -INF
    best_move = moves[0]
    next_color = opp_color(color)

    for frm, to in moves:
        me2, opp2 = apply_move(me, opp, frm, to)
        child_score, _ = negamax(opp2, me2, next_color, depth - 1, -beta, -alpha, ply + 1)
        score = -child_score

        if score > best_score:
            best_score = score
            best_move = (frm, to)

        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    # Store TT entry with bound type
    if best_score <= alpha0:
        flag = UPPER
    elif best_score >= beta0:
        flag = LOWER
    else:
        flag = EXACT
    TT[key] = (depth, flag, best_score, best_move)

    return best_score, best_move


# =========================
# Public policy
# =========================

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global DEADLINE, NODE_COUNTER, TT

    me_bits = bits_from_list(me)
    opp_bits = bits_from_list(opp)

    legal_moves = gen_moves(me_bits, opp_bits, color)

    # If terminal/no-move state is somehow passed in, return something deterministic.
    # Arena states should normally always be nonterminal.
    if not legal_moves:
        if me:
            return (me[0], me[0])
        return ((0, 0), (0, 0))

    # Immediate winning move? Take it.
    winning_moves = [m for m in legal_moves if is_immediate_win_move(me_bits, opp_bits, color, m[0], m[1])]
    if winning_moves:
        best = order_moves(me_bits, opp_bits, color, winning_moves)[0]
        return (IDX_TO_RC[best[0]], IDX_TO_RC[best[1]])

    # Prefer moves that do not allow an immediate opponent win, if any exist.
    oc = opp_color(color)
    safe_moves = []
    for frm, to in legal_moves:
        me2, opp2 = apply_move(me_bits, opp_bits, frm, to)
        if not has_immediate_win(opp2, me2, oc):
            safe_moves.append((frm, to))

    candidate_moves = safe_moves if safe_moves else legal_moves
    best = order_moves(me_bits, opp_bits, color, candidate_moves)[0]

    # Search setup
    if len(TT) > 300000:
        TT.clear()

    DEADLINE = time.perf_counter() + 0.95
    NODE_COUNTER = 0

    # Iterative deepening
    depth = 1
    try:
        while depth <= 12:
            score, move = negamax(me_bits, opp_bits, color, depth, -INF, INF, 0)
            if move is not None:
                best = move

            # Stop early on clearly forced positions
            if abs(score) >= WIN_SCORE // 2:
                break

            depth += 1
    except SearchTimeout:
        pass

    # Final legality check
    legal_set = set(legal_moves)
    if best not in legal_set:
        best = legal_moves[0]

    return (IDX_TO_RC[best[0]], IDX_TO_RC[best[1]])
