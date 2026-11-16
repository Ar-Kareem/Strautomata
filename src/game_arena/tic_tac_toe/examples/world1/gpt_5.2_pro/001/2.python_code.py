
from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple, Optional

# Preferred move order: center, corners, edges
PREFERRED_IDXS = (4, 0, 2, 6, 8, 1, 3, 5, 7)

# Winning lines (indices into a flattened 0..8 board)
WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
    (0, 4, 8), (2, 4, 6),             # diags
)


def _flatten(board: List[List[int]]) -> Tuple[int, ...]:
    # Defensive flattening; if shape is wrong, coerce best-effort to length 9
    flat = []
    for r in range(3):
        row = board[r] if r < len(board) else []
        for c in range(3):
            v = row[c] if c < len(row) else 0
            if v not in (-1, 0, 1):
                v = 0
            flat.append(v)
    return tuple(flat[:9])


def _winner(flat: Tuple[int, ...]) -> int:
    # Returns 1 if we won, -1 if opponent won, 0 otherwise
    for a, b, c in WIN_LINES:
        s = flat[a] + flat[b] + flat[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _legal_moves(flat: Tuple[int, ...]) -> Tuple[int, ...]:
    return tuple(i for i, v in enumerate(flat) if v == 0)


def _apply(flat: Tuple[int, ...], idx: int, player: int) -> Tuple[int, ...]:
    lst = list(flat)
    lst[idx] = player
    return tuple(lst)


def _better_for_us(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    """
    Compare two results (outcome, dist) from our perspective.
    outcome: 1 win, 0 draw, -1 loss
    dist: plies to terminal under optimal play from that state
    """
    ao, ad = a
    bo, bd = b
    if ao != bo:
        return ao > bo
    if ao == 1:
        return ad < bd   # win faster
    if ao == -1:
        return ad > bd   # lose slower
    return ad < bd       # draw sooner (arbitrary but consistent)


def _better_for_opp(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    """
    Opponent chooses moves to minimize our outcome.
    For equal outcome, they choose tie-breaks that are worst for us:
    - if we will win anyway: delay our win
    - if we will lose anyway: hasten our loss
    - if draw: hasten terminal (arbitrary)
    """
    ao, ad = a
    bo, bd = b
    if ao != bo:
        return ao < bo
    if ao == 1:
        return ad > bd   # delay our win
    if ao == -1:
        return ad < bd   # hasten our loss
    return ad < bd       # end draw sooner (arbitrary)


@lru_cache(maxsize=None)
def _solve(flat: Tuple[int, ...], turn: int) -> Tuple[int, int]:
    """
    Returns (outcome, dist) under optimal play from this position,
    where outcome is from our perspective (player +1).
    turn: +1 if it's our move, -1 if it's opponent's move.
    """
    w = _winner(flat)
    if w != 0:
        return (w, 0)

    moves = _legal_moves(flat)
    if not moves:
        return (0, 0)  # draw

    best: Optional[Tuple[int, int]] = None
    if turn == 1:
        for idx in moves:
            child = _apply(flat, idx, 1)
            co, cd = _solve(child, -1)
            cand = (co, cd + 1)
            if best is None or _better_for_us(cand, best):
                best = cand
    else:
        for idx in moves:
            child = _apply(flat, idx, -1)
            co, cd = _solve(child, 1)
            cand = (co, cd + 1)
            if best is None or _better_for_opp(cand, best):
                best = cand

    # best can't be None because moves is non-empty
    return best  # type: ignore[return-value]


def policy(board: list[list[int]]) -> tuple[int, int]:
    flat = _flatten(board)
    moves = _legal_moves(flat)
    if not moves:
        # No legal move exists; this should not happen in a valid arena call.
        return (0, 0)

    # Decide whose turn it "should" be by counts; if ambiguous, assume it's our turn.
    c1 = sum(1 for v in flat if v == 1)
    c2 = sum(1 for v in flat if v == -1)
    turn = 1 if c1 <= c2 else 1  # arena typically calls us on our turn; keep robust

    # 1) If we can win immediately, do it.
    for idx in moves:
        if _winner(_apply(flat, idx, 1)) == 1:
            return (idx // 3, idx % 3)

    # 2) If opponent can win immediately next, block it.
    #    (i.e., if placing -1 on some empty cell would win for them, play there now)
    for idx in moves:
        if _winner(_apply(flat, idx, -1)) == -1:
            return (idx // 3, idx % 3)

    # 3) Otherwise, full perfect-play search.
    best_move = None
    best_res: Optional[Tuple[int, int]] = None

    # Use preferred ordering for stability and stronger practical play.
    ordered_moves = [i for i in PREFERRED_IDXS if i in moves]
    if len(ordered_moves) != len(moves):
        # If something odd happened, append any remaining legal moves.
        remaining = [i for i in moves if i not in set(ordered_moves)]
        ordered_moves.extend(remaining)

    for idx in ordered_moves:
        child = _apply(flat, idx, 1)
        res = _solve(child, -1)
        # Add one ply for this move (for consistent tie-breaking at root)
        cand = (res[0], res[1] + 1)
        if best_res is None or _better_for_us(cand, best_res):
            best_res = cand
            best_move = idx

    if best_move is None:
        # Fallback: first legal move (should never happen)
        best_move = moves[0]

    return (best_move // 3, best_move % 3)
