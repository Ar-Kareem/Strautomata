
from functools import lru_cache

LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)

# Center > corners > edges
CELL_PREF = {
    0: 2, 1: 1, 2: 2,
    3: 1, 4: 3, 5: 1,
    6: 2, 7: 1, 8: 2,
}


def _terminal_value(state):
    """Return:
    100 if we have won,
    -100 if opponent has won,
    0 if draw / invalid double-win state,
    None otherwise.
    """
    our_win = False
    opp_win = False

    for a, b, c in LINES:
        s = state[a] + state[b] + state[c]
        if s == 3:
            our_win = True
        elif s == -3:
            opp_win = True

    if our_win and opp_win:
        # Invalid position, but treat safely as terminal.
        return 0
    if our_win:
        return 100
    if opp_win:
        return -100
    if 0 not in state:
        return 0
    return None


@lru_cache(maxsize=None)
def _solve(state, player):
    """Minimax value of state from our perspective.
    player = 1 if it's our turn, -1 if it's opponent's turn.

    Depth sensitivity:
    - earlier wins are better
    - later losses are better
    """
    term = _terminal_value(state)
    if term is not None:
        return term

    empties = [i for i, v in enumerate(state) if v == 0]

    if player == 1:
        best = -10**9
        for i in empties:
            nxt = list(state)
            nxt[i] = 1
            score = _solve(tuple(nxt), -1)

            # Prefer quicker wins and slower losses.
            if score > 0:
                score -= 1
            elif score < 0:
                score += 1

            if score > best:
                best = score
            if best == 99:  # immediate winning continuation
                break
        return best

    best = 10**9
    for i in empties:
        nxt = list(state)
        nxt[i] = -1
        score = _solve(tuple(nxt), 1)

        # Prefer quicker wins and slower losses.
        if score > 0:
            score -= 1
        elif score < 0:
            score += 1

        if score < best:
            best = score
        if best == -99:  # opponent immediate winning continuation
            break
    return best


def _count_threats(state, player):
    """Count lines with exactly two of player's marks and one empty."""
    total = 0
    for a, b, c in LINES:
        vals = (state[a], state[b], state[c])
        if vals.count(player) == 2 and vals.count(0) == 1:
            total += 1
    return total


def _positional_score(state):
    """Heuristic used only to break minimax ties."""
    score = 0
    for a, b, c in LINES:
        vals = (state[a], state[b], state[c])

        # Reward lines still open for us, especially with our marks already in them.
        if -1 not in vals:
            score += 1 + vals.count(1)

        # Penalize lines still open for the opponent.
        if 1 not in vals:
            score -= vals.count(-1)

    return score


def _tie_break(state, move_idx):
    return (
        _count_threats(state, 1),
        -_count_threats(state, -1),
        _positional_score(state),
        CELL_PREF[move_idx],
        -move_idx,  # deterministic final tie-break
    )


def policy(board: list[list[int]]) -> tuple[int, int]:
    legal = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    if not legal:
        # No legal move exists; return a safe tuple.
        return (0, 0)

    flat = tuple(board[r][c] for r in range(3) for c in range(3))

    # If given a terminal/invalid board with empties, still return a legal move.
    if _terminal_value(flat) is not None:
        return legal[0]

    best_move = legal[0]
    best_key = None

    for r, c in legal:
        idx = 3 * r + c
        nxt = list(flat)
        nxt[idx] = 1
        nxt = tuple(nxt)

        score = _solve(nxt, -1)
        key = (score,) + _tie_break(nxt, idx)

        if best_key is None or key > best_key:
            best_key = key
            best_move = (r, c)

    return best_move
