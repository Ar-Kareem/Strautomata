
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to a hashable state (tuple of tuples)
    state = tuple(tuple(row) for row in board)

    @lru_cache(maxsize=None)
    def winner_and_terminal(s):
        # returns: 1 if our win, -1 if opponent win, 0 if draw, None if game ongoing
        lines = []
        # rows
        for r in range(3):
            lines.append((s[r][0], s[r][1], s[r][2]))
        # cols
        for c in range(3):
            lines.append((s[0][c], s[1][c], s[2][c]))
        # diagonals
        lines.append((s[0][0], s[1][1], s[2][2]))
        lines.append((s[0][2], s[1][1], s[2][0]))

        for a, b, c in lines:
            if a == b == c != 0:
                return a  # 1 or -1
        # check draw
        if all(s[r][c] != 0 for r in range(3) for c in range(3)):
            return 0
        return None

    def get_turn(s):
        # Our marks are 1, opponent marks are -1.
        # Determine whose turn it is based on counts.
        cnt1 = sum(1 for r in range(3) for c in range(3) if s[r][c] == 1)
        cntm1 = sum(1 for r in range(3) for c in range(3) if s[r][c] == -1)
        # If equal, it's our turn (assumes we are "player 1" who starts)
        return 1 if cnt1 == cntm1 else -1

    @lru_cache(maxsize=None)
    def minimax(s):
        terminal = winner_and_terminal(s)
        if terminal is not None:
            # terminal can be 1, -1, or 0(draw)
            if terminal == 1:
                return 1  # win for us
            elif terminal == -1:
                return -1  # loss for us
            else:
                return 0  # draw

        turn = get_turn(s)  # 1 for our turn, -1 for opponent turn
        best = -2 if turn == 1 else 2

        for r in range(3):
            for c in range(3):
                if s[r][c] == 0:
                    # apply move for current player
                    new_rows = [list(row) for row in s]
                    new_rows[r][c] = turn
                    ns = tuple(tuple(row) for row in new_rows)
                    val = minimax(ns)
                    if turn == 1:
                        if val > best:
                            best = val
                            if best == 1:
                                return 1
                    else:
                        if val < best:
                            best = val
                            if best == -1:
                                return -1
        return best

    # Choose move that achieves best minimax value for us
    turn = get_turn(state)
    if turn != 1:
        # If somehow called when it's opponent's turn, still return a legal move.
        # We'll pick the move that maximizes the opponent, i.e., minimizes our outcome.
        # (Arena likely always calls when it's our turn, but this keeps it robust.)
        target_val = -1
        best_val = 2
        best_move = None
        for r in range(3):
            for c in range(3):
                if state[r][c] == 0:
                    new_rows = [list(row) for row in state]
                    new_rows[r][c] = -1
                    ns = tuple(tuple(row) for row in new_rows)
                    val = minimax(ns)  # value from our perspective
                    if val < best_val:
                        best_val = val
                        best_move = (r, c)
                        if best_val == -1:
                            return best_move
        # Fallback (should not happen)
        return best_move if best_move is not None else (0, 0)

    best_val = -2
    best_moves = []

    for r in range(3):
        for c in range(3):
            if state[r][c] == 0:
                new_rows = [list(row) for row in state]
                new_rows[r][c] = 1
                ns = tuple(tuple(row) for row in new_rows)
                val = minimax(ns)  # value from our perspective
                if val > best_val:
                    best_val = val
                    best_moves = [(r, c)]
                elif val == best_val:
                    best_moves.append((r, c))

    # Tie-breaker: prefer center, then corners, then edges for stability.
    priority = [
        (1, 1),
        (0, 0), (0, 2), (2, 0), (2, 2),
        (0, 1), (1, 0), (1, 2), (2, 1),
    ]
    best_set = set(best_moves)
    for m in priority:
        if m in best_set:
            return m
    # Otherwise return any legal move from the best set
    return best_moves[0]
