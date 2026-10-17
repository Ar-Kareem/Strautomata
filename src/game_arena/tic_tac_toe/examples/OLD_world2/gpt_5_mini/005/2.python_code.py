
from functools import lru_cache
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose next move for 4x4 tic-tac-toe.
    board: 4x4 list of lists with 0 (empty), 1 (us), -1 (opponent)
    returns (row, col) in 0..3
    """
    # Flatten board to tuple for hashing/caching
    flat = tuple(board[r][c] for r in range(4) for c in range(4))

    # Precompute winning index sets
    ROWS = [[4*r + c for c in range(4)] for r in range(4)]
    COLS = [[r*4 + c for r in range(4)] for c in range(4)]
    DIAGS = [[0,5,10,15], [3,6,9,12]]
    LINES = ROWS + COLS + DIAGS

    def terminal_state(b_flat):
        # return 1 if we (1) win, -1 if opponent (-1) wins, 0 if draw, None if non-terminal
        for line in LINES:
            s = sum(b_flat[i] for i in line)
            if s == 4:
                return 1
            if s == -4:
                return -1
        if 0 not in b_flat:
            return 0  # draw
        return None

    @lru_cache(maxsize=None)
    def minimax(b_flat: Tuple[int, ...], player: int) -> int:
        """
        Return game value from perspective of player 1:
        1 => win for us, 0 => draw, -1 => loss for us.
        'player' is the side to move (1 or -1).
        """
        term = terminal_state(b_flat)
        if term is not None:
            return term

        if player == 1:
            best = -2
            # maximize
            for i, v in enumerate(b_flat):
                if v == 0:
                    nb = list(b_flat)
                    nb[i] = 1
                    val = minimax(tuple(nb), -1)
                    if val > best:
                        best = val
                        if best == 1:
                            break  # best possible
            return best
        else:
            best = 2
            # minimize
            for i, v in enumerate(b_flat):
                if v == 0:
                    nb = list(b_flat)
                    nb[i] = -1
                    val = minimax(tuple(nb), 1)
                    if val < best:
                        best = val
                        if best == -1:
                            break  # worst possible for us
            return best

    # If immediate winning move available, pick it; else pick minimax-optimal move.
    best_score = -2
    best_moves = []

    # Move ordering: prefer central-ish squares for tie-breaking
    priority_indices = [5,6,9,10, 1,2,4,7,8,11, 0,3,12,15,13,14]
    # If some indices not present (they are), fallback to natural order
    seen = set()
    ordered_indices = [i for i in priority_indices if 0 <= i < 16]
    ordered_indices += [i for i in range(16) if i not in ordered_indices]

    for i in ordered_indices:
        if flat[i] == 0:
            nb = list(flat)
            nb[i] = 1
            val = minimax(tuple(nb), -1)
            if val > best_score:
                best_score = val
                best_moves = [i]
                if best_score == 1:
                    break  # immediate winning move found
            elif val == best_score:
                best_moves.append(i)

    if not best_moves:
        # no empty found? return (0,0) as fallback
        return (0, 0)

    # choose first best move (already ordered by priority)
    chosen = best_moves[0]
    return divmod(chosen, 4)
