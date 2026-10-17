
import time
from typing import List, Tuple, Dict, Optional

# Board from current player's perspective:
# state = (y0,y1,y2,y3,y4,y5, ys,  o0,o1,o2,o3,o4,o5, os)
State = Tuple[int, ...]  # length 14

# Transposition table entry: (depth, value, flag, best_move)
# flag: 0 EXACT, 1 LOWERBOUND, 2 UPPERBOUND
TTEntry = Tuple[int, int, int, int]


EXACT, LOWER, UPPER = 0, 1, 2

# Heuristic weights (tuned to value stores heavily; others break ties and guide tactics)
W_STORE = 40
W_SEEDS = 2
W_MAXGAIN = 6
W_EXTRA = 3
W_MOBILITY = 1

# Terminal scaling so the search strongly prefers winning final outcomes
TERMINAL_SCALE = 10000

# Time management (policy is expected to be called repeatedly in an arena)
TIME_LIMIT_SEC = 0.95
TIME_SAFETY_SEC = 0.02


def policy(you: List[int], opponent: List[int]) -> int:
    """
    Returns a legal move index 0..5 such that you[i] > 0.
    """
    # Always ensure legality fallback
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        # Problem statement says this won't happen, but keep safe.
        return 0

    start = time.perf_counter()
    deadline = start + TIME_LIMIT_SEC

    root: State = (
        you[0], you[1], you[2], you[3], you[4], you[5], you[6],
        opponent[0], opponent[1], opponent[2], opponent[3], opponent[4], opponent[5], opponent[6],
    )

    tt: Dict[State, TTEntry] = {}

    # Move ordering at root: use TT best move if available; otherwise heuristic order.
    best_move = legal[0]
    best_score = -10**18

    # Iterative deepening
    # Depth here counts moves (plies). Extra turns still consume depth (keeps time predictable).
    max_depth = 20
    for depth in range(1, max_depth + 1):
        if time.perf_counter() > deadline - TIME_SAFETY_SEC:
            break
        try:
            move, score = _search_root(root, depth, tt, deadline)
        except _TimeUp:
            break
        if move is not None:
            best_move, best_score = move, score

        # If we found a forced win/loss at terminal scale, no need to go deeper.
        if abs(best_score) >= TERMINAL_SCALE // 2:
            break

    # Ensure the move is legal even if something unexpected happens
    if best_move not in legal:
        return legal[0]
    return best_move


class _TimeUp(Exception):
    pass


def _time_check(deadline: float) -> None:
    if time.perf_counter() > deadline - TIME_SAFETY_SEC:
        raise _TimeUp


def _search_root(state: State, depth: int, tt: Dict[State, TTEntry], deadline: float) -> Tuple[Optional[int], int]:
    _time_check(deadline)

    moves = _legal_moves(state)
    if not moves:
        # No legal move: should not happen by problem statement
        return None, _eval(state)

    # TT best move first if present
    tt_ent = tt.get(state)
    if tt_ent is not None:
        _, _, _, tt_best = tt_ent
        if tt_best in moves:
            moves.remove(tt_best)
            moves.insert(0, tt_best)

    # Then heuristic ordering
    moves.sort(key=lambda m: _move_order_key(state, m), reverse=True)

    alpha = -10**18
    beta = 10**18
    best_move = moves[0]
    best_val = -10**18

    for m in moves:
        _time_check(deadline)
        child, extra, terminal = _apply_move_next_state(state, m)
        if extra:
            val = _negamax(child, depth - 1, alpha, beta, tt, deadline)
        else:
            val = -_negamax(child, depth - 1, -beta, -alpha, tt, deadline)

        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    return best_move, best_val


def _negamax(state: State, depth: int, alpha: int, beta: int, tt: Dict[State, TTEntry], deadline: float) -> int:
    _time_check(deadline)

    # Terminal check: if either side houses are empty, game is effectively over (stores already swept by our move gen)
    if _is_terminal(state):
        ys = state[6]
        os = state[13]
        return (ys - os) * TERMINAL_SCALE

    if depth <= 0:
        return _eval(state)

    alpha0 = alpha

    # TT lookup
    ent = tt.get(state)
    if ent is not None:
        ent_depth, ent_val, ent_flag, ent_best = ent
        if ent_depth >= depth:
            if ent_flag == EXACT:
                return ent_val
            if ent_flag == LOWER:
                alpha = max(alpha, ent_val)
            elif ent_flag == UPPER:
                beta = min(beta, ent_val)
            if alpha >= beta:
                return ent_val

    moves = _legal_moves(state)
    if not moves:
        # No legal moves (shouldn't happen in non-terminal), just evaluate
        return _eval(state)

    # Move ordering: TT best move first
    if ent is not None:
        ent_best = ent[3]
        if ent_best in moves:
            moves.remove(ent_best)
            moves.insert(0, ent_best)

    moves.sort(key=lambda m: _move_order_key(state, m), reverse=True)

    best_val = -10**18
    best_move = moves[0]

    for m in moves:
        _time_check(deadline)
        child, extra, terminal = _apply_move_next_state(state, m)
        if extra:
            val = _negamax(child, depth - 1, alpha, beta, tt, deadline)
        else:
            val = -_negamax(child, depth - 1, -beta, -alpha, tt, deadline)

        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    # Store TT entry
    flag = EXACT
    if best_val <= alpha0:
        flag = UPPER
    elif best_val >= beta:
        flag = LOWER
    tt[state] = (depth, best_val, flag, best_move)

    return best_val


def _legal_moves(state: State) -> List[int]:
    return [i for i in range(6) if state[i] > 0]


def _is_terminal(state: State) -> bool:
    # After we apply move, we sweep to stores if terminal, so terminal means all houses empty.
    # But to be robust: game ends if either side has empty houses.
    y_empty = (state[0] | state[1] | state[2] | state[3] | state[4] | state[5]) == 0
    o_empty = (state[7] | state[8] | state[9] | state[10] | state[11] | state[12]) == 0
    return y_empty or o_empty


def _move_order_key(state: State, move: int) -> int:
    """
    Higher is better for ordering: prioritize extra turns and big immediate store gains/captures.
    """
    # Quick simulation to get immediate store delta and extra turn.
    ystore_before = state[6]
    child_raw, extra, terminal, ystore_after, ostore_after = _apply_move_raw(state, move)
    gain = ystore_after - ystore_before

    # Extra-turn bonus, capture/gain bonus, endgame bonus
    key = gain * 100
    if extra:
        key += 500
    if terminal:
        # Prefer moves that end the game favorably
        key += (ystore_after - ostore_after) * 10
    return key


def _apply_move_next_state(state: State, move: int) -> Tuple[State, bool, bool]:
    """
    Apply a move from current player's perspective and return:
      next_state: from the perspective of the next player to move
      extra: whether current player moves again (then next_state is same perspective)
      terminal: whether game ended after the move (with sweeping done)
    """
    raw_state, extra, terminal, ystore_after, ostore_after = _apply_move_raw(state, move)

    if extra:
        return raw_state, True, terminal

    # Swap perspective: opponent becomes "you"
    # raw_state = (y0..y5, ys, o0..o5, os) after mover's move.
    y0, y1, y2, y3, y4, y5, ys, o0, o1, o2, o3, o4, o5, os = raw_state
    swapped: State = (o0, o1, o2, o3, o4, o5, os, y0, y1, y2, y3, y4, y5, ys)
    return swapped, False, terminal


def _apply_move_raw(state: State, move: int) -> Tuple[State, bool, bool, int, int]:
    """
    Apply a move from current player's perspective and return:
      new_state (same perspective),
      extra (last seed in your store),
      terminal (after sweep),
      your_store_after,
      opp_store_after.

    Uses an efficient sowing method (full-cycle distribution) while preserving correct capture behavior.
    """
    y0, y1, y2, y3, y4, y5, ys, o0, o1, o2, o3, o4, o5, os = state
    you_h = [y0, y1, y2, y3, y4, y5]
    opp_h = [o0, o1, o2, o3, o4, o5]

    s = you_h[move]
    # Move guaranteed legal by caller
    you_h[move] = 0

    # Build sowing ring pits[0..12] excluding opponent store:
    # 0..5: your houses, 6: your store, 7..12: opponent houses
    pits = [0] * 13
    pits[0:6] = you_h
    pits[6] = ys
    pits[7:13] = opp_h

    q, r = divmod(s, 13)

    if q:
        # each full cycle adds 1 to every pit (excluding opponent store)
        # (13 fixed operations)
        for i in range(13):
            pits[i] += q

    # remainder distribution: next r pits after 'move'
    # If r==0, last position is the starting pit (move index) after full cycles.
    for t in range(1, r + 1):
        pits[(move + t) % 13] += 1

    last_pos = (move + s) % 13
    extra = (last_pos == 6)

    # Capture if last seed lands in your empty house and opposite has seeds
    if 0 <= last_pos <= 5:
        # If it ends with exactly 1 seed, it was empty before the last drop.
        if pits[last_pos] == 1:
            opp_pos = 12 - last_pos  # maps your i to opponent (7..12) index: 7+(5-i) = 12-i
            if pits[opp_pos] > 0:
                pits[6] += pits[opp_pos] + 1
                pits[opp_pos] = 0
                pits[last_pos] = 0

    # Unpack back
    you_h = pits[0:6]
    ys = pits[6]
    opp_h = pits[7:13]

    # Terminal sweeping (if either side empty)
    sum_you = you_h[0] + you_h[1] + you_h[2] + you_h[3] + you_h[4] + you_h[5]
    sum_opp = opp_h[0] + opp_h[1] + opp_h[2] + opp_h[3] + opp_h[4] + opp_h[5]
    terminal = False
    if sum_you == 0 or sum_opp == 0:
        terminal = True
        if sum_you:
            ys += sum_you
            you_h = [0, 0, 0, 0, 0, 0]
        if sum_opp:
            os += sum_opp
            opp_h = [0, 0, 0, 0, 0, 0]

    new_state: State = (
        you_h[0], you_h[1], you_h[2], you_h[3], you_h[4], you_h[5], ys,
        opp_h[0], opp_h[1], opp_h[2], opp_h[3], opp_h[4], opp_h[5], os
    )
    return new_state, extra, terminal, ys, os


def _eval(state: State) -> int:
    """
    Heuristic evaluation from the perspective of the player to move.
    Larger is better.
    """
    y0, y1, y2, y3, y4, y5, ys, o0, o1, o2, o3, o4, o5, os = state

    store_diff = ys - os
    you_sum = y0 + y1 + y2 + y3 + y4 + y5
    opp_sum = o0 + o1 + o2 + o3 + o4 + o5
    seed_diff = you_sum - opp_sum

    # Mobility and "initiative"
    you_moves = int(y0 > 0) + int(y1 > 0) + int(y2 > 0) + int(y3 > 0) + int(y4 > 0) + int(y5 > 0)

    # Extra-turn potential: count moves that end in store (rough but helpful)
    extra_pot = 0
    houses = (y0, y1, y2, y3, y4, y5)
    for i in range(6):
        s = houses[i]
        if s <= 0:
            continue
        if (i + s) % 13 == 6:
            extra_pot += 1

    # Tactical max immediate store gain for you and for opponent (one-move lookahead feature)
    max_gain_you = _max_immediate_gain(state)

    # Opponent max gain: evaluate from opponent-to-move perspective by swapping
    swapped = (o0, o1, o2, o3, o4, o5, os, y0, y1, y2, y3, y4, y5, ys)
    max_gain_opp = _max_immediate_gain(swapped)

    val = 0
    val += W_STORE * store_diff
    val += W_SEEDS * seed_diff
    val += W_MAXGAIN * (max_gain_you - max_gain_opp)
    val += W_EXTRA * extra_pot
    val += W_MOBILITY * you_moves

    return val


def _max_immediate_gain(state: State) -> int:
    """
    Maximum immediate increase in the current player's store achievable in one move.
    Used only in eval; keep it relatively cheap.
    """
    ys_before = state[6]
    best = 0
    for m in range(6):
        if state[m] <= 0:
            continue
        raw, extra, terminal, ys_after, os_after = _apply_move_raw(state, m)
        gain = ys_after - ys_before
        if gain > best:
            best = gain
    return best
