
"""
Pentago policy – greedy heuristic search.
Pre‑computes all possible 5‑in‑a‑row lines, then for every legal move:
  * checks instant win/loss,
  * evaluates the resulting board with a simple linear‑line heuristic,
  * selects the highest‑scoring non‑losing move (or the least‑bad losing move).
"""

# ----------------------------------------------------------------------
# 1.  Pre‑compute all 5‑cell lines (horizontal, vertical, both diagonals)
# ----------------------------------------------------------------------
def _generate_lines():
    """Return a list of lines, each line is a list of (r,c) cells (0‑based)."""
    lines = []

    # horizontal
    for r in range(6):
        for c0 in range(0, 2):          # start columns 0 and 1 give a length‑5 window
            line = [(r, c0 + i) for i in range(5)]
            lines.append(line)

    # vertical
    for c in range(6):
        for r0 in range(0, 2):
            line = [(r0 + i, c) for i in range(5)]
            lines.append(line)

    # diagonal down‑right (dr = +1, dc = +1)
    for r0 in range(0, 2):
        for c0 in range(0, 2):
            line = [(r0 + i, c0 + i) for i in range(5)]
            lines.append(line)

    # diagonal down‑left (dr = +1, dc = -1)
    for r0 in range(0, 2):
        for c0 in range(4, 6):
            line = [(r0 + i, c0 - i) for i in range(5)]
            lines.append(line)

    return lines


_LINES = _generate_lines()          # all 5‑cell lines, used for evaluation


# ----------------------------------------------------------------------
# 2.  Rotate a single 3×3 quadrant
# ----------------------------------------------------------------------
def _rotate(you, opp, quadrant, direction):
    """
    Rotate the given quadrant (0..3) of both boards.
    direction is 'L' (90° anticlockwise) or 'R' (90° clockwise).
    Returns (new_you, new_opp) – deep copies.
    """
    # deep copy the whole boards
    new_you = [row[:] for row in you]
    new_opp = [row[:] for row in opp]

    # top‑left corner of the quadrant
    r0 = (quadrant // 2) * 3
    c0 = (quadrant % 2) * 3

    # extract the 3×3 blocks
    block_y = [[new_you[r0 + i][c0 + j] for j in range(3)] for i in range(3)]
    block_o = [[new_opp[r0 + i][c0 + j] for j in range(3)] for i in range(3)]

    # rotated blocks (the two formulae come from the 90° rotation of a 3×3 matrix)
    if direction == 'L':                # anticlockwise
        rot_y = [[block_y[j][2 - i] for j in range(3)] for i in range(3)]
        rot_o = [[block_o[j][2 - i] for j in range(3)] for i in range(3)]
    else:                               # clockwise
        rot_y = [[block_y[2 - j][i] for j in range(3)] for i in range(3)]
        rot_o = [[block_o[2 - j][i] for j in range(3)] for i in range(3)]

    # write the rotated blocks back
    for i in range(3):
        for j in range(3):
            new_you[r0 + i][c0 + j] = rot_y[i][j]
            new_opp[r0 + i][c0 + j] = rot_o[i][j]

    return new_you, new_opp


# ----------------------------------------------------------------------
# 3.  Evaluate a board position
# ----------------------------------------------------------------------
def _evaluate(you, opp):
    """
    Heuristic evaluation of a board.
    Returns:
        score          – higher is better for the player to move
        you_win        – bool, do we have ≥5 in a row?
        opp_win        – bool, does the opponent have ≥5 in a row?
        my_four        – number of open lines with exactly four of our marbles
        opp_four       – number of open lines with exactly four opponent marbles
    """
    score = 0
    you_win = False
    opp_win = False
    my_four = 0
    opp_four = 0

    for line in _LINES:
        my_cnt = 0
        opp_cnt = 0
        for r, c in line:
            if you[r][c]:
                my_cnt += 1
            if opp[r][c]:
                opp_cnt += 1

        # win detection (≥5 in this 5‑cell window)
        if my_cnt >= 5:
            you_win = True
        if opp_cnt >= 5:
            opp_win = True

        # blocked line – ignore for the open‑line heuristics
        if my_cnt > 0 and opp_cnt > 0:
            continue

        # simple quadratic weighting for open lines
        score += my_cnt * my_cnt * 10
        score -= opp_cnt * opp_cnt * 10

        # extra bonus / penalty for an open line of exactly four
        if my_cnt == 4:
            my_four += 1
            score += 1000
        if opp_cnt == 4:
            opp_four += 1
            score -= 1000

    # a draw (both win) is far better than a loss – give it a big bonus
    if you_win and opp_win:
        score += 5000

    return score, you_win, opp_win, my_four, opp_four


# ----------------------------------------------------------------------
# 4.  The policy that the arena calls
# ----------------------------------------------------------------------
def policy(you, opponent):
    """
    Return a legal move for the current player.
    The move is a string: "row,col,quadrant,direction"
      row, col      : 1‑based coordinates of the empty cell where we place
      quadrant      : 0..3 (top‑left, top‑right, bottom‑left, bottom‑right)
      direction     : 'L' (anticlockwise) or 'R' (clockwise)
    """
    # make sure we work with mutable list‑of‑lists
    you = [list(row) for row in you]
    opponent = [list(row) for row in opponent]

    # collect empty cells
    empties = [(r, c) for r in range(6) for c in range(6)
               if you[r][c] == 0 and opponent[r][c] == 0]

    best_move = None                 # fallback (may be a losing move)
    best_score = -float('inf')
    best_nonlosing_move = None
    best_nonlosing_score = -float('inf')

    # iterate over every legal (place, rotate) combination
    for r, c in empties:
        for quad in range(4):
            for direction in ('L', 'R'):
                # copy boards and place a marble
                new_you = [row[:] for row in you]
                new_opp = [row[:] for row in opponent]
                new_you[r][c] = 1

                # apply the quadrant rotation
                new_you, new_opp = _rotate(new_you, new_opp, quad, direction)

                # evaluate the resulting position
                score, you_win, opp_win, _, _ = _evaluate(new_you, new_opp)

                # ---- immediate pure win ? ----
                if you_win and not opp_win:
                    # winning move – play it instantly
                    return f"{r+1},{c+1},{quad},{direction}"

                # ---- immediate loss (opponent already has ≥5) ----
                if opp_win and not you_win:
                    # treat as a very bad move, but keep it as a last‑resort fallback
                    score = -1e9

                # update best non‑losing move (draws are included here)
                if not (opp_win and not you_win):          # i.e. not a plain loss
                    if score > best_nonlosing_score:
                        best_nonlosing_score = score
                        best_nonlosing_move = (r, c, quad, direction)

                # update absolute best (used if every move loses)
                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, direction)

    # if we have a move that does not lose, prefer it
    if best_nonlosing_move is not None:
        r, c, quad, direction = best_nonlosing_move
        return f"{r+1},{c+1},{quad},{direction}"

    # all moves lose – just return the least‑bad one
    r, c, quad, direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"
