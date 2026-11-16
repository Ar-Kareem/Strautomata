
from __future__ import annotations

def policy(state: list[list[object]], role: str) -> str:
    # --- Helpers to parse state ---
    board = [["b" for _ in range(3)] for _ in range(3)]
    for fact in state:
        if len(fact) >= 4 and fact[0] == "cell":
            r = int(fact[1]) - 1
            c = int(fact[2]) - 1
            board[r][c] = str(fact[3])

    me = role  # role should be "x" or "o"
    opp = "o" if me == "x" else "x"

    lines = [
        [(0,0),(0,1),(0,2)],
        [(1,0),(1,1),(1,2)],
        [(2,0),(2,1),(2,2)],
        [(0,0),(1,0),(2,0)],
        [(0,1),(1,1),(2,1)],
        [(0,2),(1,2),(2,2)],
        [(0,0),(1,1),(2,2)],
        [(0,2),(1,1),(2,0)],
    ]

    def winner(bd):
        for line in lines:
            a,b,c = line
            v = bd[a[0]][a[1]]
            if v != "b" and v == bd[b[0]][b[1]] and v == bd[c[0]][c[1]]:
                return v
        return None

    def terminal_score(bd, maximizing_player):
        w = winner(bd)
        if w == maximizing_player:
            return 1
        if w is None:
            # check draw
            for i in range(3):
                for j in range(3):
                    if bd[i][j] == "b":
                        return None
            return 0  # draw
        else:
            return -1  # maximizing_player lost

    def legal_moves(bd):
        moves = []
        for i in range(3):
            for j in range(3):
                if bd[i][j] == "b":
                    moves.append((i,j))
        return moves

    # Minimax with alpha-beta; exhaustive search is tiny for tic-tac-toe.
    def minimax(bd, current_player, maximizing_player, alpha, beta):
        sc = terminal_score(bd, maximizing_player)
        if sc is not None:
            return sc, None

        best_move = None
        moves = legal_moves(bd)

        if current_player == maximizing_player:
            value = -2
            for (i,j) in moves:
                bd[i][j] = current_player
                v, _ = minimax(bd, opp if current_player == me else (me), maximizing_player, alpha, beta)
                # Above line is wrong if current_player is not necessarily me/opp; fix:
                bd[i][j] = "b"

            # We'll implement properly below without the confusing line
        # Proper implementation:
        if current_player == maximizing_player:
            value = -2
            for (i,j) in moves:
                bd[i][j] = current_player
                next_player = opp if current_player == me else me
                # Since maximizing_player is either me or opp, derive opponent each time:
                # if current_player is 'x' opponent is 'o', else vice versa.
                next_player = "o" if current_player == "x" else "x"
                v, _ = minimax(bd, next_player, maximizing_player, alpha, beta)
                bd[i][j] = "b"
                if v > value:
                    value = v
                    best_move = (i,j)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, best_move
        else:
            value = 2
            for (i,j) in moves:
                bd[i][j] = current_player
                next_player = "o" if current_player == "x" else "x"
                v, _ = minimax(bd, next_player, maximizing_player, alpha, beta)
                bd[i][j] = "b"
                if v < value:
                    value = v
                    best_move = (i,j)
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value, best_move

    # Current player is role; we assume state is consistent with it.
    maximizing_player = me
    current_player = me

    # First, quick check for immediate win/block to avoid any edge-case mismatch.
    # (Still use minimax afterwards.)
    empties = legal_moves(board)
    for (i,j) in empties:
        board[i][j] = me
        if winner(board) == me:
            return f"mark({i+1},{j+1})"
        board[i][j] = "b"
    for (i,j) in empties:
        board[i][j] = opp
        if winner(board) == opp:
            return f"mark({i+1},{j+1})"
        board[i][j] = "b"

    # Full minimax
    _, move = minimax(board, current_player, maximizing_player, alpha=-2, beta=2)
    if move is None:
        # Fallback: choose any empty cell (shouldn't happen)
        (i,j) = empties[0]
        return f"mark({i+1},{j+1})"
    i,j = move
    return f"mark({i+1},{j+1})"
