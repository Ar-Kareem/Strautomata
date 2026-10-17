
from functools import lru_cache

# Preferred move order for tie-breaking and mild search ordering:
# center, corners, then edges
PREF_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)
PREF_RANK = {m: len(PREF_ORDER) - i for i, m in enumerate(PREF_ORDER)}

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


def winner(state):
    """Return 1 if we have won, -1 if opponent has won, else 0."""
    for a, b, c in LINES:
        s = state[a] + state[b] + state[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def legal_indices(state):
    """Empty cells in preferred order."""
    return [i for i in PREF_ORDER if state[i] == 0]


def count_winning_moves(player, state):
    """How many immediate winning moves does player have from this state?"""
    count = 0
    for i, v in enumerate(state):
        if v == 0:
            nxt = list(state)
            nxt[i] = player
            if winner(tuple(nxt)) == player:
                count += 1
    return count


def count_forks(player, state):
    """
    Count moves that would create at least two immediate winning threats.
    """
    count = 0
    for i, v in enumerate(state):
        if v == 0:
            nxt = list(state)
            nxt[i] = player
            if count_winning_moves(player, tuple(nxt)) >= 2:
                count += 1
    return count


def potential_score(state):
    """
    Heuristic for tie-breaking among equally optimal minimax moves.
    Rewards open lines for us and penalizes open lines for the opponent.
    """
    weights = (0, 1, 5, 100)
    score = 0
    for a, b, c in LINES:
        vals = (state[a], state[b], state[c])
        my_count = vals.count(1)
        opp_count = vals.count(-1)
        if opp_count == 0:
            score += weights[my_count]
        if my_count == 0:
            score -= weights[opp_count]
    return score


@lru_cache(maxsize=None)
def solve(state, player):
    """
    Exact minimax from our perspective.
    Returns (score, depth):
      score:  1 = forced win for us
              0 = forced draw
             -1 = forced loss for us
      depth: plies until game end under optimal play, used for tie-breaking
    """
    w = winner(state)
    if w != 0:
        return w, 0

    moves = legal_indices(state)
    if not moves:
        return 0, 0

    if player == 1:
        # Our turn: maximize score.
        best_score = -2
        best_depth = 10**9

        for m in moves:
            nxt = list(state)
            nxt[m] = 1
            score, depth = solve(tuple(nxt), -1)
            depth += 1

            if score > best_score:
                best_score, best_depth = score, depth
            elif score == best_score:
                if score == 1:
                    # Faster win is better.
                    if depth < best_depth:
                        best_depth = depth
                elif score == -1:
                    # Slower loss is better.
                    if depth > best_depth:
                        best_depth = depth
                else:
                    # For draws, earlier resolution is fine.
                    if depth < best_depth:
                        best_depth = depth

        return best_score, best_depth

    else:
        # Opponent turn: minimize our score.
        best_score = 2
        best_depth = 10**9

        for m in moves:
            nxt = list(state)
            nxt[m] = -1
            score, depth = solve(tuple(nxt), 1)
            depth += 1

            if score < best_score:
                best_score, best_depth = score, depth
            elif score == best_score:
                if score == -1:
                    # Opponent prefers faster win for themselves.
                    if depth < best_depth:
                        best_depth = depth
                elif score == 1:
                    # Opponent prefers to delay our win.
                    if depth > best_depth:
                        best_depth = depth
                else:
                    if depth < best_depth:
                        best_depth = depth

        return best_score, best_depth


def move_heuristic(next_state, move):
    """
    Tie-break heuristic among equally optimal root moves.
    Larger is better.
    """
    return (
        count_forks(1, next_state),
        count_winning_moves(1, next_state),
        -count_forks(-1, next_state),
        -count_winning_moves(-1, next_state),
        potential_score(next_state),
        PREF_RANK[move],
    )


def policy(board):
    """
    Required API:
        policy(board: list[list[int]]) -> tuple[int, int]
    """
    state = tuple(board[r][c] for r in range(3) for c in range(3))
    moves = legal_indices(state)

    # Fallback: if the board is full or malformed, return (0, 0).
    # In a normal game with at least one empty cell, the function below
    # always returns a legal move.
    if not moves:
        return (0, 0)

    best_move = moves[0]
    best_key = None

    for m in moves:
        nxt = list(state)
        nxt[m] = 1
        nxt = tuple(nxt)

        score, depth = solve(nxt, -1)
        h = move_heuristic(nxt, m)

        # Primary: win > draw > loss
        # Secondary: faster wins, slower losses
        # Tertiary: strategic tie-breaking heuristic
        if score == 1:
            key = (2, -depth) + h
        elif score == 0:
            key = (1, 0) + h
        else:
            key = (0, depth) + h

        if best_key is None or key > best_key:
            best_key = key
            best_move = m

    return (best_move // 3, best_move % 3)
