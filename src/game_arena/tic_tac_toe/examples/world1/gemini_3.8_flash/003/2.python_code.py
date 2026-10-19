
import functools

# All 8 winning lines in a 3x3 grid (represented as flat indices 0-8)
WINNING_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def _check_winner(state: tuple[int, ...]) -> int:
    """Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
    for a, b, c in WINNING_LINES:
        if state[a] != 0 and state[a] == state[b] == state[c]:
            return state[a]
    return 0


@functools.lru_cache(maxsize=None)
def _minimax(state: tuple[int, ...], is_my_turn: bool) -> int:
    """Minimax search returning optimal outcome score."""
    winner = _check_winner(state)
    empty_indices = [i for i, val in enumerate(state) if val == 0]
    depth = 9 - len(empty_indices)

    if winner == 1:
        return 100 - depth
    if winner == -1:
        return depth - 100
    if not empty_indices:
        return 0

    if is_my_turn:
        best_score = -999
        for idx in empty_indices:
            next_state = list(state)
            next_state[idx] = 1
            score = _minimax(tuple(next_state), False)
            if score > best_score:
                best_score = score
        return best_score
    else:
        best_score = 999
        for idx in empty_indices:
            next_state = list(state)
            next_state[idx] = -1
            score = _minimax(tuple(next_state), True)
            if score < best_score:
                best_score = score
        return best_score


@functools.lru_cache(maxsize=None)
def _expectimax(state: tuple[int, ...], is_my_turn: bool) -> float:
    """Expectimax search assuming opponent plays uniformly among available moves."""
    winner = _check_winner(state)
    if winner == 1:
        return 1.0
    if winner == -1:
        return -1.0

    empty_indices = [i for i, val in enumerate(state) if val == 0]
    if not empty_indices:
        return 0.0

    if is_my_turn:
        best_val = -1.0
        for idx in empty_indices:
            next_state = list(state)
            next_state[idx] = 1
            val = _expectimax(tuple(next_state), False)
            if val > best_val:
                best_val = val
        return best_val
    else:
        total_val = 0.0
        for idx in empty_indices:
            next_state = list(state)
            next_state[idx] = -1
            total_val += _expectimax(tuple(next_state), True)
        return total_val / len(empty_indices)


def policy(board: list[list[int]]) -> tuple[int, int]:
    """Computes the optimal next move for player 1 on the given 3x3 board."""
    flat_state = tuple(board[r][c] for r in range(3) for c in range(3))
    empty_indices = [i for i, val in enumerate(flat_state) if val == 0]

    if not empty_indices:
        return (0, 0)

    best_move = empty_indices[0]
    best_key = (-float("inf"), -float("inf"))

    for idx in empty_indices:
        next_state = list(flat_state)
        next_state[idx] = 1
        next_tuple = tuple(next_state)

        # Minimax value guarantees non-loss; Expectimax breaks ties to punish blunders
        m_val = _minimax(next_tuple, False)
        e_val = _expectimax(next_tuple, False)

        candidate_key = (m_val, e_val)
        if candidate_key > best_key:
            best_key = candidate_key
            best_move = idx

    return (best_move // 3, best_move % 3)
