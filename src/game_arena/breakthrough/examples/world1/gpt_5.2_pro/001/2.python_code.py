
import time
from typing import List, Tuple, Optional, Dict, Any

Move = Tuple[Tuple[int, int], Tuple[int, int]]

# --- Bitboard helpers (bit index = row*8 + col, row 0 is bottom) ---

ROW0_MASK = (1 << 8) - 1
ROW7_MASK = ROW0_MASK << 56

MATE = 1_000_000
INF = 10**18

# Transposition table reused across calls
# key -> (depth, flag, value, best_move_idx)
# flag: 0 exact, 1 lowerbound, 2 upperbound
_TT: Dict[Tuple[int, int, str], Tuple[int, int, int, Optional[Tuple[int, int]]]] = {}


def _rc_to_idx(r: int, c: int) -> int:
    return (r << 3) | c


def _idx_to_rc(i: int) -> Tuple[int, int]:
    return (i >> 3, i & 7)


def _list_to_bb(lst: List[Tuple[int, int]]) -> int:
    bb = 0
    for r, c in lst:
        bb |= 1 << _rc_to_idx(r, c)
    return bb


def _popcount(x: int) -> int:
    return x.bit_count()


def _iter_bits(bb: int):
    while bb:
        lsb = bb & -bb
        i = lsb.bit_length() - 1
        yield i
        bb ^= lsb


def _goal_mask(turn: str) -> int:
    # Player to move wants to reach opponent home row:
    # white -> row 7, black -> row 0
    return ROW7_MASK if turn == "w" else ROW0_MASK


def _opponent(turn: str) -> str:
    return "b" if turn == "w" else "w"


def _generate_moves_idx(p_bb: int, o_bb: int, turn: str) -> List[Tuple[int, int, bool]]:
    """
    Returns list of (from_idx, to_idx, is_capture).
    Legal moves only.
    """
    occ = p_bb | o_bb
    moves: List[Tuple[int, int, bool]] = []

    if turn == "w":
        for fr in _iter_bits(p_bb):
            r, c = _idx_to_rc(fr)

            # forward
            if r < 7:
                to = fr + 8
                if ((occ >> to) & 1) == 0:
                    moves.append((fr, to, False))

            # diag left
            if r < 7 and c > 0:
                to = fr + 7
                if ((p_bb >> to) & 1) == 0:
                    is_cap = ((o_bb >> to) & 1) == 1
                    # diagonal move allowed whether empty or capture
                    moves.append((fr, to, is_cap))

            # diag right
            if r < 7 and c < 7:
                to = fr + 9
                if ((p_bb >> to) & 1) == 0:
                    is_cap = ((o_bb >> to) & 1) == 1
                    moves.append((fr, to, is_cap))

    else:  # turn == "b"
        for fr in _iter_bits(p_bb):
            r, c = _idx_to_rc(fr)

            # forward
            if r > 0:
                to = fr - 8
                if ((occ >> to) & 1) == 0:
                    moves.append((fr, to, False))

            # diag left (to r-1, c-1)
            if r > 0 and c > 0:
                to = fr - 9
                if ((p_bb >> to) & 1) == 0:
                    is_cap = ((o_bb >> to) & 1) == 1
                    moves.append((fr, to, is_cap))

            # diag right (to r-1, c+1)
            if r > 0 and c < 7:
                to = fr - 7
                if ((p_bb >> to) & 1) == 0:
                    is_cap = ((o_bb >> to) & 1) == 1
                    moves.append((fr, to, is_cap))

    return moves


def _attacks_bb(p_bb: int, turn: str) -> int:
    """
    Squares that side 'turn' could capture into next move.
    (i.e., diagonal forward destinations from its pieces)
    """
    atk = 0
    if turn == "w":
        for fr in _iter_bits(p_bb):
            r, c = _idx_to_rc(fr)
            if r < 7 and c > 0:
                atk |= 1 << (fr + 7)
            if r < 7 and c < 7:
                atk |= 1 << (fr + 9)
    else:
        for fr in _iter_bits(p_bb):
            r, c = _idx_to_rc(fr)
            if r > 0 and c > 0:
                atk |= 1 << (fr - 9)
            if r > 0 and c < 7:
                atk |= 1 << (fr - 7)
    return atk


def _apply_move(p_bb: int, o_bb: int, turn: str, mv: Tuple[int, int, bool]):
    """
    Apply move for current player (p_bb). Returns:
    (next_p_bb, next_o_bb, next_turn, win_now)
    State convention: next_p_bb belongs to player to move next.
    """
    fr, to, is_cap = mv
    fr_bit = 1 << fr
    to_bit = 1 << to

    new_p = (p_bb ^ fr_bit) | to_bit
    new_o = o_bb
    if is_cap:
        new_o = o_bb & ~to_bit

    # Check immediate win by reaching goal row or capturing all opponent pieces
    win_now = False
    if (new_p & _goal_mask(turn)) != 0:
        win_now = True
    elif new_o == 0:
        win_now = True

    # Swap perspective for next ply: next player pieces first
    return new_o, new_p, _opponent(turn), win_now


def _progress_sum(bb: int, turn: str) -> int:
    s = 0
    if turn == "w":
        for i in _iter_bits(bb):
            r, _ = _idx_to_rc(i)
            s += r
    else:
        for i in _iter_bits(bb):
            r, _ = _idx_to_rc(i)
            s += (7 - r)
    return s


def _max_progress(bb: int, turn: str) -> int:
    mx = 0
    if turn == "w":
        for i in _iter_bits(bb):
            r, _ = _idx_to_rc(i)
            if r > mx:
                mx = r
    else:
        for i in _iter_bits(bb):
            r, _ = _idx_to_rc(i)
            pr = 7 - r
            if pr > mx:
                mx = pr
    return mx


def _passed_pawn_bonus(p_bb: int, o_bb: int, turn: str) -> int:
    """
    Approx passed pawn: no opponent pawn exists ahead on same/adjacent files.
    Bonus increases as pawn advances.
    """
    opp_positions = [(_idx_to_rc(i)) for i in _iter_bits(o_bb)]
    bonus = 0
    if turn == "w":
        for i in _iter_bits(p_bb):
            r, c = _idx_to_rc(i)
            blocked = False
            for ro, co in opp_positions:
                if ro > r and abs(co - c) <= 1:
                    blocked = True
                    break
            if not blocked:
                bonus += (r + 1) * 6
    else:
        for i in _iter_bits(p_bb):
            r, c = _idx_to_rc(i)
            blocked = False
            for ro, co in opp_positions:
                if ro < r and abs(co - c) <= 1:
                    blocked = True
                    break
            if not blocked:
                bonus += (8 - r) * 6
    return bonus


def _center_bonus(bb: int) -> int:
    # Encourage central files (2..5)
    b = 0
    for i in _iter_bits(bb):
        _, c = _idx_to_rc(i)
        if 2 <= c <= 5:
            b += 2
    return b


def _evaluate(p_bb: int, o_bb: int, turn: str) -> int:
    """
    Static eval from viewpoint of side to move (p_bb).
    Positive means good for side to move.
    """
    # Terminal-like checks (should normally be caught on move application)
    if (o_bb & _goal_mask(_opponent(turn))) != 0:
        return -MATE + 1
    if (p_bb & _goal_mask(turn)) != 0:
        return MATE - 1
    if o_bb == 0:
        return MATE - 1
    if p_bb == 0:
        return -MATE + 1

    my_n = _popcount(p_bb)
    op_n = _popcount(o_bb)

    material = (my_n - op_n) * 120

    adv = (_progress_sum(p_bb, turn) - _progress_sum(o_bb, _opponent(turn))) * 8
    spear = (_max_progress(p_bb, turn) - _max_progress(o_bb, _opponent(turn))) * 25

    passed = _passed_pawn_bonus(p_bb, o_bb, turn) - _passed_pawn_bonus(o_bb, p_bb, _opponent(turn))

    mob = (len(_generate_moves_idx(p_bb, o_bb, turn)) - len(_generate_moves_idx(o_bb, p_bb, _opponent(turn)))) * 3

    # Safety: pieces currently en prise (opponent can capture them)
    opp_atk = _attacks_bb(o_bb, _opponent(turn))
    my_en_prise = _popcount(opp_atk & p_bb)
    my_safety = -my_en_prise * 18

    center = (_center_bonus(p_bb) - _center_bonus(o_bb)) * 4

    return material + adv + spear + passed + mob + my_safety + center


def _move_order_score(p_bb: int, o_bb: int, turn: str, mv: Tuple[int, int, bool]) -> int:
    fr, to, is_cap = mv
    score = 0

    # Captures first
    if is_cap:
        score += 500

    # Advance / promotion proximity
    r_to, c_to = _idx_to_rc(to)
    if turn == "w":
        score += r_to * 12
        if r_to == 7:
            score += 20000
    else:
        score += (7 - r_to) * 12
        if r_to == 0:
            score += 20000

    # Center preference
    if 2 <= c_to <= 5:
        score += 25

    # Slight penalty if moving into an attacked square (basic blunder avoidance in ordering)
    # Compute opponent attacks in resulting position approximately:
    # (we won't simulate captures exactly here; just use current opponent attack map)
    opp_atk = _attacks_bb(o_bb, _opponent(turn))
    if (opp_atk >> to) & 1:
        score -= 60

    # Prefer diagonal over straight a little (often creates threats)
    if abs((_idx_to_rc(fr)[1]) - c_to) == 1:
        score += 10

    return score


def _negamax(
    p_bb: int,
    o_bb: int,
    turn: str,
    depth: int,
    alpha: int,
    beta: int,
    t0: float,
    t_limit: float,
) -> Tuple[int, Optional[Tuple[int, int, bool]]]:
    if time.perf_counter() - t0 > t_limit:
        raise TimeoutError

    # No pieces / reached goal: handle as terminal
    if o_bb == 0:
        return (MATE - (10 - depth), None)
    if p_bb == 0:
        return (-MATE + (10 - depth), None)
    if (p_bb & _goal_mask(turn)) != 0:
        return (MATE - (10 - depth), None)
    if (o_bb & _goal_mask(_opponent(turn))) != 0:
        return (-MATE + (10 - depth), None)

    if depth == 0:
        return (_evaluate(p_bb, o_bb, turn), None)

    key = (p_bb, o_bb, turn)
    tt_entry = _TT.get(key)
    if tt_entry is not None:
        tt_depth, flag, val, best_mv_idx = tt_entry
        if tt_depth >= depth:
            if flag == 0:
                return val, (best_mv_idx[0], best_mv_idx[1], ((o_bb >> best_mv_idx[1]) & 1) == 1) if best_mv_idx else None
            elif flag == 1:
                alpha = max(alpha, val)
            elif flag == 2:
                beta = min(beta, val)
            if alpha >= beta:
                return val, (best_mv_idx[0], best_mv_idx[1], ((o_bb >> best_mv_idx[1]) & 1) == 1) if best_mv_idx else None

    moves = _generate_moves_idx(p_bb, o_bb, turn)
    if not moves:
        # No legal moves -> lose
        return (-MATE + (10 - depth), None)

    # Order moves: TT best first if exists, then heuristic ordering
    if tt_entry is not None and tt_entry[3] is not None:
        fr_best, to_best = tt_entry[3]
        # rebuild capture flag in current position
        is_cap_best = ((o_bb >> to_best) & 1) == 1
        best_mv = (fr_best, to_best, is_cap_best)
        # stable: move it to front if present
        try:
            idx = moves.index(best_mv)
            moves[0], moves[idx] = moves[idx], moves[0]
        except ValueError:
            pass

    moves.sort(key=lambda mv: _move_order_score(p_bb, o_bb, turn, mv), reverse=True)

    best_move: Optional[Tuple[int, int, bool]] = None
    orig_alpha = alpha

    best_val = -INF
    for mv in moves:
        next_p, next_o, next_turn, win_now = _apply_move(p_bb, o_bb, turn, mv)
        if win_now:
            val = MATE - (10 - depth)
        else:
            child_val, _ = _negamax(next_p, next_o, next_turn, depth - 1, -beta, -alpha, t0, t_limit)
            val = -child_val

        if val > best_val:
            best_val = val
            best_move = mv

        alpha = max(alpha, val)
        if alpha >= beta:
            break

    # Store in TT
    flag = 0
    if best_val <= orig_alpha:
        flag = 2  # upper
    elif best_val >= beta:
        flag = 1  # lower

    best_mv_idx_store = (best_move[0], best_move[1]) if best_move is not None else None
    _TT[key] = (depth, flag, int(best_val), best_mv_idx_store)

    return int(best_val), best_move


def _fallback_move(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Move:
    p_bb = _list_to_bb(me)
    o_bb = _list_to_bb(opp)
    moves = _generate_moves_idx(p_bb, o_bb, color)
    if not moves:
        # If truly no legal move, there is no legal return; this should not happen in normal arena calls.
        # Return a deterministic placeholder within bounds (still may be illegal).
        return ((0, 0), (0, 0))
    moves.sort(key=lambda mv: _move_order_score(p_bb, o_bb, color, mv), reverse=True)
    fr, to, _ = moves[0]
    return (_idx_to_rc(fr), _idx_to_rc(to))


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Move:
    """
    Returns a legal Breakthrough move for the current player.
    """
    p_bb = _list_to_bb(me)
    o_bb = _list_to_bb(opp)
    turn = color

    # Always ensure we can return something legal
    legal_moves = _generate_moves_idx(p_bb, o_bb, turn)
    if not legal_moves:
        return _fallback_move(me, opp, color)

    # Quick win check: if any move reaches goal row or captures last piece, play it immediately
    gmask = _goal_mask(turn)
    for mv in legal_moves:
        fr, to, is_cap = mv
        to_bit = 1 << to
        if (to_bit & gmask) != 0:
            return (_idx_to_rc(fr), _idx_to_rc(to))
        if is_cap and (o_bb & ~to_bit) == 0:
            return (_idx_to_rc(fr), _idx_to_rc(to))

    t0 = time.perf_counter()
    # Keep under 1s with margin
    t_limit = 0.92

    best_move: Optional[Tuple[int, int, bool]] = None

    # Iterative deepening
    # Depth choice: start at 2 to be stable, then increase
    for depth in (2, 3, 4, 5, 6, 7):
        try:
            val, mv = _negamax(p_bb, o_bb, turn, depth, -MATE, MATE, t0, t_limit)
            if mv is not None:
                best_move = mv
            # If we found a forced mate-like value, stop early
            if best_move is not None and abs(val) > MATE // 2:
                break
        except TimeoutError:
            break

    if best_move is None:
        return _fallback_move(me, opp, color)

    fr, to, _ = best_move
    return (_idx_to_rc(fr), _idx_to_rc(to))
