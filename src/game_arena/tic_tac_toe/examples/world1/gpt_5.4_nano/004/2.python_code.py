
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the next move for Tic Tac Toe.
    Board encoding: 0 empty, 1 us, -1 opponent.
    """
    # Convert to an immutable representation for caching
    b = tuple(tuple(row) for row in board)

    LINES = [
        (0,0,0,1,0,2), (1,0,1,1,1,2), (2,0,2,1,2,2),
        (0,0,1,0,2,0), (0,1,1,1,2,1), (0,2,1,2,2,2),
        (0,0,1,1,2,2), (0,2,1,1,2,0)
    ]

    def winner(state):
        # Returns 1 if we win, -1 if opponent wins, 0 otherwise
        for a,b1,c,d,e,f in LINES:
            v = state[a][b1]
            if v != 0 and v == state[c][d] and v == state[e][f]:
                return v
        return 0

    def full(state):
        return all(state[r][c] != 0 for r in range(3) for c in range(3))

    def moves(state):
        res = []
        for r in range(3):
            for c in range(3):
                if state[r][c] == 0:
                    res.append((r,c))
        return res

    # Minimax: maximize for us (1), minimize for opponent (-1)
    @lru_cache(maxsize=None)
    def solve(state, turn):  # turn: 1 means us to play, -1 means opponent to play
        w = winner(state)
        if w == 1:
            return 1  # win
        if w == -1:
            return -1  # loss
        if full(state):
            return 0  # draw

        # Alpha-beta pruning isn't directly helpful with tiny game,
        # but we still implement a lightweight version.
        if turn == 1:
            best = -2
            for (r,c) in moves(state):
                new_state = [list(row) for row in state]
                new_state[r][c] = 1
                val = solve(tuple(tuple(row) for row in new_state), -1)
                if val > best:
                    best = val
                if best == 1:
                    break
            return best
        else:
            best = 2
            for (r,c) in moves(state):
                new_state = [list(row) for row in state]
                new_state[r][c] = -1
                val = solve(tuple(tuple(row) for row in new_state), 1)
                if val < best:
                    best = val
                if best == -1:
                    break
            return best

    # Determine whose turn it is based on counts:
    # empty=0, us=1, opp=-1
    count_us = sum(1 for r in range(3) for c in range(3) if b[r][c] == 1)
    count_opp = sum(1 for r in range(3) for c in range(3) if b[r][c] == -1)
    turn = 1 if count_us == count_opp else -1  # if equal, we start; else opponent started and now we respond

    # If it's not our turn (shouldn't happen in normal usage), still return a legal move.
    # We'll assume we are "1" and choose best for player 'turn' accordingly.
    # But arena expects we always place 1, so 'turn' should be 1.
    if turn != 1:
        # Choose any legal move (fallback), but still legal.
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return (r, c)
        return (0, 0)

    # Choose the move that maximizes the game outcome for us.
    best_val = -2
    best_move = None
    for (r,c) in moves(b):
        new_state = [list(row) for row in b]
        new_state[r][c] = 1
        val = solve(tuple(tuple(row) for row in new_state), -1)
        if val > best_val:
            best_val = val
            best_move = (r,c)
            if best_val == 1:
                break  # cannot do better than a forced win

    # Ensure we always return a legal move
    if best_move is not None:
        return best_move
    for r in range(3):
        for c in range(3):
            if b[r][c] == 0:
                return (r, c)
    return (0, 0)
