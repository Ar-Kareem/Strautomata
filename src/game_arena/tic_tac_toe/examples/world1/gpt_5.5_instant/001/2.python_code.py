
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Perfect-play Tic Tac Toe policy for player 1.
    board: 3x3 list of lists with 0 empty, 1 self, -1 opponent.
    returns: (row, col) legal empty cell.
    """

    def legal_moves(b):
        return [(r, c) for r in range(3) for c in range(3) if b[r][c] == 0]

    def winner_tuple(t):
        lines = (
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        )
        for a, b, c in lines:
            s = t[a] + t[b] + t[c]
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0

    def fallback_move():
        preferred = [
            (1, 1),
            (0, 0), (0, 2), (2, 0), (2, 2),
            (0, 1), (1, 0), (1, 2), (2, 1)
        ]
        for r, c in preferred:
            if 0 <= r < 3 and 0 <= c < 3 and board[r][c] == 0:
                return (r, c)
        return (0, 0)

    try:
        state = tuple(board[r][c] for r in range(3) for c in range(3))
        moves = [i for i, v in enumerate(state) if v == 0]
        if not moves:
            return fallback_move()

        @lru_cache(None)
        def minimax(state, turn):
            w = winner_tuple(state)
            empty_count = state.count(0)

            if w == 1:
                return 100 + empty_count
            if w == -1:
                return -100 - empty_count
            if empty_count == 0:
                return 0

            if turn == 1:
                best = -10**9
                for i, v in enumerate(state):
                    if v == 0:
                        ns = list(state)
                        ns[i] = 1
                        score = minimax(tuple(ns), -1)
                        if score > best:
                            best = score
                return best
            else:
                best = 10**9
                for i, v in enumerate(state):
                    if v == 0:
                        ns = list(state)
                        ns[i] = -1
                        score = minimax(tuple(ns), 1)
                        if score < best:
                            best = score
                return best

        # Move ordering improves tie-breaking: center, corners, edges.
        ordered_indices = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        best_score = -10**9
        best_idx = None

        for i in ordered_indices:
            if state[i] == 0:
                ns = list(state)
                ns[i] = 1
                score = minimax(tuple(ns), -1)
                if score > best_score:
                    best_score = score
                    best_idx = i

        if best_idx is not None:
            return (best_idx // 3, best_idx % 3)

        return fallback_move()

    except Exception:
        return fallback_move()
