
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Perfect-play Tic Tac Toe policy for player 1.
    board: 3x3 list of lists, with 0 empty, 1 us, -1 opponent.
    returns: (row, col), guaranteed legal if any legal move exists.
    """

    # Convert defensively to immutable tuple form.
    try:
        b = tuple(tuple(int(board[r][c]) for c in range(3)) for r in range(3))
    except Exception:
        # Extremely defensive fallback; should never occur in arena.
        return (0, 0)

    legal = [(r, c) for r in range(3) for c in range(3) if b[r][c] == 0]
    if not legal:
        # No legal move exists. This should not be requested, but return valid-shaped tuple.
        return (0, 0)

    def winner(pos):
        lines = (
            # rows
            pos[0], pos[1], pos[2],
            # columns
            (pos[0][0], pos[1][0], pos[2][0]),
            (pos[0][1], pos[1][1], pos[2][1]),
            (pos[0][2], pos[1][2], pos[2][2]),
            # diagonals
            (pos[0][0], pos[1][1], pos[2][2]),
            (pos[0][2], pos[1][1], pos[2][0]),
        )
        for line in lines:
            s = line[0] + line[1] + line[2]
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0

    def board_full(pos):
        return all(pos[r][c] != 0 for r in range(3) for c in range(3))

    def make_move(pos, r, c, player):
        rows = [list(row) for row in pos]
        rows[r][c] = player
        return tuple(tuple(row) for row in rows)

    def move_order(pos):
        # Center, corners, edges. This improves pruning and tie quality.
        preferred = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
        return [(r, c) for (r, c) in preferred if pos[r][c] == 0]

    @lru_cache(None)
    def minimax(pos, turn, alpha, beta):
        """
        Returns score from player 1 perspective.
        Positive is good for us, negative is bad.
        Magnitude prefers quicker wins and slower losses.
        """
        w = winner(pos)
        if w == 1:
            empties = sum(1 for r in range(3) for c in range(3) if pos[r][c] == 0)
            return 10 + empties
        if w == -1:
            empties = sum(1 for r in range(3) for c in range(3) if pos[r][c] == 0)
            return -10 - empties
        if board_full(pos):
            return 0

        if turn == 1:
            best = -100
            for r, c in move_order(pos):
                val = minimax(make_move(pos, r, c, 1), -1, alpha, beta)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if beta <= alpha:
                    break
            return best
        else:
            best = 100
            for r, c in move_order(pos):
                val = minimax(make_move(pos, r, c, -1), 1, alpha, beta)
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if beta <= alpha:
                    break
            return best

    # Immediate tactical checks are redundant with minimax but cheap and robust.

    # 1. Win immediately if possible.
    for r, c in legal:
        if winner(make_move(b, r, c, 1)) == 1:
            return (r, c)

    # 2. Block opponent's immediate win.
    for r, c in legal:
        if winner(make_move(b, r, c, -1)) == -1:
            return (r, c)

    # 3. Choose the minimax-best legal move.
    best_move = legal[0]
    best_score = -100

    # Use strong static preference for deterministic tie-breaking.
    preferred = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
    ordered_legal = [(r, c) for (r, c) in preferred if b[r][c] == 0]

    for r, c in ordered_legal:
        nxt = make_move(b, r, c, 1)
        score = minimax(nxt, -1, -100, 100)
        if score > best_score:
            best_score = score
            best_move = (r, c)

    # Final safety check.
    if b[best_move[0]][best_move[1]] == 0:
        return best_move

    return legal[0]
