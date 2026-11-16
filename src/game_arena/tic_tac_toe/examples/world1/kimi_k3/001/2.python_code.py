
from functools import lru_cache

# Winning lines over a flattened 9-cell board.
_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),      # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),      # columns
    (0, 4, 8), (2, 4, 6),                 # diagonals
)

# Move preference: center, then corners, then edges.
_PREF = (4, 0, 2, 6, 8, 1, 3, 5, 7)


def _winner(state):
    """Return 1 if we won, -1 if opponent won, 0 otherwise."""
    for a, b, c in _LINES:
        s = state[a] + state[b] + state[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


@lru_cache(maxsize=None)
def _value(state, turn):
    """
    Exact minimax value of `state` (tuple of 9 cells) with `turn` to move.
    Positive  => we (player 1) win; sooner wins score higher.
    Negative  => opponent wins; later losses score higher (more chances
                 for the opponent to blunder).
    Zero      => draw with perfect play.
    """
    w = _winner(state)
    played = 9 - state.count(0)
    if w == 1:
        return 10 - played
    if w == -1:
        return played - 10
    if played == 9:
        return 0

    vals = []
    for i in _PREF:
        if state[i] == 0:
            nxt = list(state)
            nxt[i] = turn
            vals.append(_value(tuple(nxt), -turn))
    return max(vals) if turn == 1 else min(vals)


def _avg_reply_value(state):
    """
    Average minimax value over all possible opponent replies, assuming a
    uniformly random (fallible) opponent. Used only to break ties between
    moves that are equally good under perfect play: we pick the move that
    gives the opponent the most ways to lose.
    """
    replies = [j for j in _PREF if state[j] == 0]
    if not replies:
        return float("inf")  # game already decided by our move
    total = 0
    for j in replies:
        nxt = list(state)
        nxt[j] = -1
        total += _value(tuple(nxt), 1)
    return total / len(replies)


def policy(board: list[list[int]]) -> tuple[int, int]:
    flat = tuple(board[r][c] for r in range(3) for c in range(3))
    empties = [i for i in _PREF if flat[i] == 0]

    if not empties:
        # No legal move exists (terminal board); should never be called here.
        return (0, 0)

    # Evaluate every candidate move exactly.
    best_val = None
    candidates = []
    for i in empties:
        nxt = list(flat)
        nxt[i] = 1
        nxt = tuple(nxt)
        v = _value(nxt, -1)
        if best_val is None or v > best_val:
            best_val = v
            candidates = [(i, nxt)]
        elif v == best_val:
            candidates.append((i, nxt))

    if len(candidates) == 1:
        return divmod(candidates[0][0], 3)

    # Tie-break: maximize trap potential against imperfect opponents,
    # then positional preference (center > corner > edge).
    pref_rank = {cell: r for r, cell in enumerate(_PREF)}
    best_cell, _ = max(
        candidates,
        key=lambda t: (_avg_reply_value(t[1]), -pref_rank[t[0]]),
    )
    return divmod(best_cell, 3)
