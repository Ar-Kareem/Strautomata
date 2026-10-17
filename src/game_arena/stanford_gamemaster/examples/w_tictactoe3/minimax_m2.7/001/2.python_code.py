
import sys
sys.setrecursionlimit(10000)

def policy(state, role):
    """
    Tic‑Tac‑Toe policy using full‑depth minimax with α‑β pruning.
    Returns a legal move in Stanford syntax, e.g. mark(2,1).
    """
    # ---------- 1. Build the board ----------
    # board[r][c] = 'x', 'o', or 'b' (blank)
    board = [['b'] * 3 for _ in range(3)]
    for prop in state:
        if prop[0] == 'cell':
            r = int(prop[1]) - 1   # convert to 0‑based index
            c = int(prop[2]) - 1
            owner = prop[3]
            board[r][c] = owner

    # ---------- 2. Helper functions ----------
    def empty_cells(b):
        """Return list of (row, col) tuples for blank cells."""
        return [(i, j) for i in range(3) for j in range(3) if b[i][j] == 'b']

    def winner(b):
        """Return 'x', 'o' if that player has three in a line, else None."""
        lines = [
            # rows
            [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],
            # columns
            [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],
            # diagonals
            [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)]
        ]
        for line in lines:
            vals = [b[r][c] for r, c in line]
            if vals[0] != 'b' and vals[0] == vals[1] == vals[2]:
                return vals[0]
        return None

    def is_full(b):
        return all(b[i][j] != 'b' for i in range(3) for j in range(3))

    # ---------- 3. Minimax with α‑β ----------
    opponent = 'o' if role == 'x' else 'x'

    def minimax(b, depth, is_maximising, alpha, beta):
        """
        Returns +1 if the position is winning for `role`,
        -1 if losing, 0 if a draw (or unknown).
        """
        w = winner(b)
        if w == role:
            return 1
        if w == opponent:
            return -1
        if is_full(b):
            return 0

        empties = empty_cells(b)

        if is_maximising:
            max_eval = -2  # lower than any possible score
            for r, c in empties:
                b[r][c] = role
                eval_score = minimax(b, depth + 1, False, alpha, beta)
                b[r][c] = 'b'
                if eval_score > max_eval:
                    max_eval = eval_score
                if max_eval > alpha:
                    alpha = max_eval
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 2
            for r, c in empties:
                b[r][c] = opponent
                eval_score = minimax(b, depth + 1, True, alpha, beta)
                b[r][c] = 'b'
                if eval_score < min_eval:
                    min_eval = eval_score
                if min_eval < beta:
                    beta = min_eval
                if beta <= alpha:
                    break
            return min_eval

    # ---------- 4. Choose the best move ----------
    best_move = None
    best_score = -2

    for r, c in empty_cells(board):
        board[r][c] = role
        score = minimax(board, 0, False, -2, 2)
        board[r][c] = 'b'
        if score > best_score:
            best_score = score
            best_move = (r, c)

    # There must always be at least one empty cell when the function is called
    row, col = best_move
    return f"mark({row + 1},{col + 1})"
