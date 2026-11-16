
def policy(board: list[list[int]]) -> tuple[int, int]:
    # 4x4 Tic Tac Toe (4 in a row wins). Board values: 0 empty, 1 us, -1 opponent.

    n = 4

    def lines():
        L = []

        # Rows
        for r in range(n):
            L.append([(r, c) for c in range(n)])
        # Cols
        for c in range(n):
            L.append([(r, c) for r in range(n)])
        # Diagonals (main and anti)
        L.append([(i, i) for i in range(n)])
        L.append([(i, n - 1 - i) for i in range(n)])
        return L

    ALL_LINES = lines()

    def winner_in_line(cells):
        s = sum(board[r][c] for r, c in cells)
        if s == n:      # 1*4
            return 1
        if s == -n:     # -1*4
            return -1
        return 0

    def available_moves():
        moves = []
        for r in range(n):
            for c in range(n):
                if board[r][c] == 0:
                    moves.append((r, c))
        return moves

    moves = available_moves()

    # If board is empty at all (early game), prefer center-ish squares.
    def center_score(r, c):
        # Manhattan distance from center (1.5, 1.5); smaller is better
        return abs(r - 1.5) + abs(c - 1.5)

    # Step 1: Immediate win
    for r, c in moves:
        board[r][c] = 1
        # Check if we created a win in any line containing (r,c)
        win = False
        for L in ALL_LINES:
            if (r, c) in L:
                if winner_in_line(L) == 1:
                    win = True
                    break
        board[r][c] = 0
        if win:
            return (r, c)

    # Step 2: Block opponent immediate win
    for r, c in moves:
        board[r][c] = -1
        block = False
        for L in ALL_LINES:
            if (r, c) in L:
                if winner_in_line(L) == -1:
                    block = True
                    break
        board[r][c] = 0
        if block:
            return (r, c)

    # Step 3: Heuristic evaluation: maximize "open" lines for us,
    # with tie-breaking by center preference.
    #
    # An open line for a player means: it contains no opponent marks.
    # For our evaluation score, we count lines that would remain possible for us.
    def line_open_for(player, cells):
        opp = -player
        for r, c in cells:
            if board[r][c] == opp:
                return False
        return True

    # If we place our mark at (r,c), count how many open lines we create/strengthen.
    best_move = None
    best_score = None

    for r, c in moves:
        board[r][c] = 1

        us_lines = 0
        # Optional: prefer lines where we also increase immediate threat count
        for L in ALL_LINES:
            if (r, c) in L and line_open_for(1, L):
                us_lines += 1

        # Also consider how much this move blocks opponent from being able to open lines.
        # (Not required for correctness but helps.)
        opp_block = 0
        for L in ALL_LINES:
            if (r, c) in L and line_open_for(-1, L):
                # If our move is in a line that opponent could also have kept open, it reduces symmetry.
                # We approximate "blocking" by counting how many lines are still open for opponent
                # after we play. Lower is better.
                pass

        # Convert to a sortable tuple:
        # Primary: maximize us_lines.
        # Secondary: minimize center distance.
        # Tertiary: prefer moves that also reduce opponent's open lines.
        opp_open_after = 0
        for L in ALL_LINES:
            if any((rr, cc) == (r, c) for rr, cc in L):
                if line_open_for(-1, L):
                    opp_open_after += 1
            else:
                # For lines not containing (r,c), open status unchanged
                if line_open_for(-1, L):
                    opp_open_after += 1

        board[r][c] = 0

        # We don't want to overfit to opp_open_after; use it only as tie-breaker.
        score_tuple = (us_lines, -opp_open_after, -center_score(r, c), -abs(r - c))
        if best_score is None or score_tuple > best_score:
            best_score = score_tuple
            best_move = (r, c)

    # Fallback (should never happen since moves is non-empty unless board full)
    if best_move is None:
        return moves[0]

    return best_move
