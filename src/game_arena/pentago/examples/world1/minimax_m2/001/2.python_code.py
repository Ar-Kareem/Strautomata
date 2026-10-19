
def policy(you, opponent) -> str:
    """Select a legal Pentago move.

    you[r][c] == 1  : our marble at (r,c)
    opponent[r][c] == 1 : opponent marble at (r,c)
    Both matrices contain only 0/1 and never overlap.
    The returned string has the format "row,col,quad,dir"
    with 1‑based rows/cols, quad in {0,1,2,3}, dir in {'L','R'}.
    """

    # ----------------------------------------------------------------------
    # Helper: build a single 6x6 board where cell values are:
    #   0 – empty, 1 – our marble, 2 – opponent marble
    # ----------------------------------------------------------------------
    def build_board(you_mat, opp_mat):
        board = [[0] * 6 for _ in range(6)]
        for i in range(6):
            for j in range(6):
                if you_mat[i][j] == 1:
                    board[i][j] = 1
                elif opp_mat[i][j] == 1:
                    board[i][j] = 2
        return board

    # ----------------------------------------------------------------------
    # Helper: rotate a 3x3 quadrant of the board in‑place
    #   quad mapping:
    #       0 -> rows 0‑2, cols 0‑2   (top‑left)
    #       1 -> rows 0‑2, cols 3‑5   (top‑right)
    #       2 -> rows 3‑5, cols 0‑2   (bottom‑left)
    #       3 -> rows 3‑5, cols 3‑5   (bottom‑right)
    #   dir 'L' = 90° anticlockwise, 'R' = 90° clockwise
    # ----------------------------------------------------------------------
    def rotate_quadrant(board, quad, direction):
        if quad == 0:
            r0, c0 = 0, 0
        elif quad == 1:
            r0, c0 = 0, 3
        elif quad == 2:
            r0, c0 = 3, 0
        else:  # quad == 3
            r0, c0 = 3, 3

        # copy the 3x3 sub‑board
        tmp = [[board[r0 + di][c0 + dj] for dj in range(3)] for di in range(3)]

        if direction == 'L':  # anticlockwise: new[i][j] = old[j][2-i]
            for di in range(3):
                for dj in range(3):
                    board[r0 + di][c0 + dj] = tmp[dj][2 - di]
        else:  # 'R' clockwise: new[i][j] = old[2-j][i]
            for di in range(3):
                for dj in range(3):
                    board[r0 + di][c0 + dj] = tmp[2 - dj][di]

    # ----------------------------------------------------------------------
    # Pre‑compute the 32 possible 5‑cell line segments (horizontal,
    # vertical, diagonal).  Each segment is a list of (r,c) coordinates.
    # ----------------------------------------------------------------------
    segments = []
    # horizontal
    for r in range(6):
        for c in range(2):
            segments.append([(r, c + i) for i in range(5)])
    # vertical
    for c in range(6):
        for r in range(2):
            segments.append([(r + i, c) for i in range(5)])
    # diagonal down‑right
    for r in range(2):
        for c in range(2):
            segments.append([(r + i, c + i) for i in range(5)])
    # diagonal down‑left
    for r in range(2):
        for c in range(4, 6):
            segments.append([(r + i, c - i) for i in range(5)])

    # ----------------------------------------------------------------------
    # Build the current board and collect empty cells
    # ----------------------------------------------------------------------
    board = build_board(you, opponent)
    empty_cells = [(i, j) for i in range(6) for j in range(6) if board[i][j] == 0]

    best_move = None
    best_score = -10**9  # very low sentinel

    # ----------------------------------------------------------------------
    # Enumerate every legal move
    # ----------------------------------------------------------------------
    for i, j in empty_cells:
        # place our marble
        board_after_place = [row[:] for row in board]
        board_after_place[i][j] = 1

        # try each quadrant and direction
        for quad in range(4):
            for direction in ('L', 'R'):
                # simulate rotation on a fresh copy
                board_after_rot = [row[:] for row in board_after_place]
                rotate_quadrant(board_after_rot, quad, direction)

                # ----- evaluate the resulting board -----
                you_win = False
                opp_win = False
                my_score = 0  # heuristic for non‑terminal moves

                for seg in segments:
                    vals = [board_after_rot[r][c] for r, c in seg]

                    # win detection (all five cells equal)
                    if all(v == 1 for v in vals):
                        you_win = True
                    if all(v == 2 for v in vals):
                        opp_win = True

                    # heuristic: count our marbles in open lines (no opponent marble)
                    opp_present = any(v == 2 for v in vals)
                    my_marbles = sum(1 for v in vals if v == 1)
                    if not opp_present:
                        my_score += my_marbles

                # ----- assign a numeric score to this move -----
                if you_win and not opp_win:
                    score = 10000 + my_score                     # outright win
                elif you_win and opp_win:
                    score = 5000 + my_score                      # draw (both win)
                elif opp_win:
                    score = -1000                                 # losing move – avoid if possible
                else:
                    score = my_score                              # normal move

                # keep the best according to the scoring scheme
                if score > best_score:
                    best_score = score
                    best_move = f"{i+1},{j+1},{quad},{direction}"

    # ----------------------------------------------------------------------
    # Fallback (should never be needed, but guarantees a legal move)
    # ----------------------------------------------------------------------
    if best_move is None:
        i, j = empty_cells[0]
        best_move = f"{i+1},{j+1},0,R"

    return best_move
