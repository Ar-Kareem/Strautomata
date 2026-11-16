
from functools import lru_cache

WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

# Prefer center, then corners, then edges.
MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)
MOVE_PREF = {
    4: 30,
    0: 20, 2: 20, 6: 20, 8: 20,
    1: 10, 3: 10, 5: 10, 7: 10,
}


def _to_state(board):
    """Convert the board into a flat immutable tuple."""
    state = []
    for r in range(3):
        for c in range(3):
            try:
                v = board[r][c]
            except Exception:
                v = 0

            if v == 1:
                state.append(1)
            elif v == -1:
                state.append(-1)
            else:
                state.append(0)

    return tuple(state)


def _winner(state):
    """Return 1 if we won, -1 if opponent won, otherwise 0."""
    for a, b, c in WIN_LINES:
        s = state[a] + state[b] + state[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _set_cell(state, idx, value):
    return state[:idx] + (value,) + state[idx + 1:]


@lru_cache(maxsize=None)
def _minimax(state, turn):
    """
    Perfect-play minimax score from our perspective.
    Positive is good for us, negative is good for opponent.
    """
    w = _winner(state)
    empty_count = state.count(0)

    if w == 1:
        return 100 + empty_count       # prefer faster wins
    if w == -1:
        return -100 - empty_count      # prefer slower losses
    if empty_count == 0:
        return 0

    if turn == 1:
        best = -10_000
        for idx in MOVE_ORDER:
            if state[idx] == 0:
                score = _minimax(_set_cell(state, idx, 1), -1)
                if score > best:
                    best = score
        return best
    else:
        best = 10_000
        for idx in MOVE_ORDER:
            if state[idx] == 0:
                score = _minimax(_set_cell(state, idx, -1), 1)
                if score < best:
                    best = score
        return best


def _strategic_value(state, move_idx):
    """
    Tie-breaker among equally optimal minimax moves.
    Rewards center/corners, open lines, and fork pressure.
    """
    value = MOVE_PREF.get(move_idx, 0)

    if state[4] == 1:
        value += 8
    elif state[4] == -1:
        value -= 8

    our_threats = 0
    opp_threats = 0

    for line in WIN_LINES:
        ours = 0
        opps = 0
        for idx in line:
            if state[idx] == 1:
                ours += 1
            elif state[idx] == -1:
                opps += 1

        if opps == 0:
            if ours == 1:
                value += 2
            elif ours == 2:
                value += 14
            elif ours == 3:
                value += 80

        if ours == 0:
            if opps == 1:
                value -= 1
            elif opps == 2:
                value -= 16
            elif opps == 3:
                value -= 80

        if ours == 2 and opps == 0:
            our_threats += 1
        if opps == 2 and ours == 0:
            opp_threats += 1

    # Forks are especially powerful in Tic Tac Toe.
    if our_threats >= 2:
        value += 35 * our_threats
    if opp_threats >= 2:
        value -= 40 * opp_threats

    return value


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = _to_state(board)

    legal = [idx for idx in MOVE_ORDER if state[idx] == 0]

    # A full board should not be passed to the policy, but return safely anyway.
    if not legal:
        return (0, 0)

    # 1. Take an immediate win.
    for idx in legal:
        next_state = _set_cell(state, idx, 1)
        if _winner(next_state) == 1:
            return (idx // 3, idx % 3)

    # 2. Block an immediate opponent win.
    for idx in legal:
        opp_state = _set_cell(state, idx, -1)
        if _winner(opp_state) == -1:
            return (idx // 3, idx % 3)

    # 3. Otherwise use perfect minimax search.
    best_idx = legal[0]
    best_score = -10_000
    best_tiebreak = -10_000

    for idx in legal:
        next_state = _set_cell(state, idx, 1)
        score = _minimax(next_state, -1)
        tiebreak = _strategic_value(next_state, idx)

        if score > best_score or (score == best_score and tiebreak > best_tiebreak):
            best_score = score
            best_tiebreak = tiebreak
            best_idx = idx

    return (best_idx // 3, best_idx % 3)
