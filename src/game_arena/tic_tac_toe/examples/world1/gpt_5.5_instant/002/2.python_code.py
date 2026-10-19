
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Perfect-play Tic Tac Toe policy for player 1.
    board: 3x3 list where 0=empty, 1=self, -1=opponent.
    returns: (row, col) legal empty cell.
    """

    # Defensive normalization to tuple-of-tuples for hashing and safety.
    b = tuple(tuple(int(board[r][c]) for c in range(3)) for r in range(3))

    def legal_moves(state):
        return [(r, c) for r in range(3) for c in range(3) if state[r][c] == 0]

    def winner(state):
        lines = []
        lines.extend(state)
        lines.extend(tuple(state[r][c] for r in range(3)) for c in range(3))
        lines.append((state[0][0], state[1][1], state[2][2]))
        lines.append((state[0][2], state[1][1], state[2][0]))
        for line in lines:
            s = sum(line)
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0

    def make_move(state, move, player):
        r, c = move
        rows = [list(row) for row in state]
        rows[r][c] = player
        return tuple(tuple(row) for row in rows)

    def side_to_move(state):
        # In normal arena calls, we are player 1 and should move when counts are equal
        # or opponent has one extra. This also handles unusual states sensibly.
        ones = sum(1 for r in range(3) for c in range(3) if state[r][c] == 1)
        negs = sum(1 for r in range(3) for c in range(3) if state[r][c] == -1)
        return 1 if ones <= negs else -1

    # Good deterministic ordering improves alpha-beta pruning and tie-breaking.
    preferred_order = [
        (1, 1),
        (0, 0), (0, 2), (2, 0), (2, 2),
        (0, 1), (1, 0), (1, 2), (2, 1)
    ]

    @lru_cache(None)
    def minimax(state, turn, alpha, beta):
        w = winner(state)
        if w != 0:
            # Large terminal score. Depth component handled by remaining empties:
            # quicker own wins are better, slower losses are better.
            empties = len(legal_moves(state))
            return w * (100 + empties)

        moves = legal_moves(state)
        if not moves:
            return 0

        ordered = [m for m in preferred_order if m in moves]

        if turn == 1:
            best = -10**9
            for m in ordered:
                score = minimax(make_move(state, m, 1), -1, alpha, beta)
                if score > best:
                    best = score
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best
        else:
            best = 10**9
            for m in ordered:
                score = minimax(make_move(state, m, -1), 1, alpha, beta)
                if score < best:
                    best = score
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return best

    moves = legal_moves(b)
    if not moves:
        # No legal move exists; this should not be called on a full board.
        # Return a valid-shaped tuple as last-resort API compliance.
        return (0, 0)

    # Immediate tactical checks, useful and robust.
    # 1. Win now if possible.
    for m in preferred_order:
        if m in moves and winner(make_move(b, m, 1)) == 1:
            return m

    # 2. Block opponent's immediate win.
    for m in preferred_order:
        if m in moves and winner(make_move(b, m, -1)) == -1:
            return m

    turn = side_to_move(b)

    # If somehow called when opponent would be to move, still choose the move
    # that maximizes our outcome after placing our own mark.
    best_move = moves[0]
    best_score = -10**9

    ordered_moves = [m for m in preferred_order if m in moves]
    for m in ordered_moves:
        next_state = make_move(b, m, 1)
        score = minimax(next_state, -1, -10**9, 10**9)

        # Small strategic tie-breakers for stable arena performance.
        if m == (1, 1):
            score += 0.3
        elif m in [(0, 0), (0, 2), (2, 0), (2, 2)]:
            score += 0.2
        else:
            score += 0.1

        if score > best_score:
            best_score = score
            best_move = m

    # Absolute legal fallback.
    r, c = best_move
    if 0 <= r < 3 and 0 <= c < 3 and b[r][c] == 0:
        return best_move
    return moves[0]
