
from __future__ import annotations

from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Returns (i,j,k) for a 3x3x3 Tic Tac Toe board.
    board[i][j][k] in {0 empty, 1 self, -1 opponent}
    """
    SIZE = 3

    # Generate all winning lines (49 total) as lists of (i,j,k)
    lines = []

    # Helper to add a line from endpoints with step (di,dj,dk)
    def add_line(si, sj, sk, di, dj, dk):
        line = []
        for t in range(SIZE):
            i, j, k = si + di*t, sj + dj*t, sk + dk*t
            line.append((i, j, k))
        lines.append(line)

    # 3 axis-aligned lines in each direction
    # We can systematically generate:
    # - all i fixed: (i, j, k) along j
    for i in range(SIZE):
        for k in range(SIZE):
            add_line(i, 0, k, 0, 1, 0)  # varying j
    for i in range(SIZE):
        for j in range(SIZE):
            add_line(i, j, 0, 0, 0, 1)  # varying k
    for j in range(SIZE):
        for k in range(SIZE):
            add_line(0, j, k, 1, 0, 0)  # varying i

    # Planes: for each plane, include 2 diagonals
    # xy planes (k fixed): i,j vary
    for k in range(SIZE):
        add_line(0, 0, k, 1, 1, 0)
        add_line(0, 2, k, 1, -1, 0)

    # xz planes (j fixed): i,k vary
    for j in range(SIZE):
        add_line(0, j, 0, 1, 0, 1)
        add_line(0, j, 2, 1, 0, -1)

    # yz planes (i fixed): j,k vary
    for i in range(SIZE):
        add_line(i, 0, 0, 0, 1, 1)
        add_line(i, 0, 2, 0, 1, -1)

    # Space diagonals: 4 long diagonals through cube
    add_line(0, 0, 0, 1, 1, 1)
    add_line(0, 0, 2, 1, 1, -1)
    add_line(0, 2, 0, 1, -1, 1)
    add_line(0, 2, 2, 1, -1, -1)

    # Sanity: should be 49
    # (Not strictly required, but helps ensure correctness.)
    # If duplicates occur due to generation, we can unique them by set signature.
    uniq = {}
    for ln in lines:
        sig = tuple(sorted(ln))
        uniq[sig] = ln
    lines = list(uniq.values())

    def available_cells():
        for i in range(SIZE):
            for j in range(SIZE):
                for k in range(SIZE):
                    if board[i][j][k] == 0:
                        yield (i, j, k)

    def line_counts_at_move(cell):
        """Count how many self/opponent pieces on each line that passes through cell."""
        i0, j0, k0 = cell
        affected = []
        for ln in lines:
            if (i0, j0, k0) in ln:
                s = 0
                o = 0
                z = 0
                for (i, j, k) in ln:
                    v = board[i][j][k]
                    if v == 1:
                        s += 1
                    elif v == -1:
                        o += 1
                    else:
                        z += 1
                affected.append((ln, s, o, z))
        return affected

    def find_winning_move(for_player: int):
        """If player can win in one move, return that move; else None."""
        target = for_player
        for (i, j, k) in available_cells():
            # place hypothetically
            for ln in lines:
                if (i, j, k) not in ln:
                    continue
                s = 0
                o = 0
                empties = 0
                for (ii, jj, kk) in ln:
                    v = board[ii][jj][kk]
                    if v == 0:
                        empties += 1
                        if (ii, jj, kk) == (i, j, k):
                            v = target
                    if v == 1:
                        s += 1
                    elif v == -1:
                        o += 1
                # For player target, check if all 3 are target
                # Compute counts accordingly:
                if target == 1 and s == 3 and o == 0:
                    return (i, j, k)
                if target == -1 and o == 3 and s == 0:
                    return (i, j, k)
        return None

    # 1) Win now
    move = find_winning_move(1)
    if move is not None:
        return move

    # 2) Block opponent win
    move = find_winning_move(-1)
    if move is not None:
        return move

    # 3) Heuristic scoring
    # For each available move, score based on:
    # - lines where opponent has 0 pieces (so our progress is possible)
    # - among those, prefer lines with more of our pieces (e.g., 2-in-a-row threats)
    # Also incorporate blocking value by looking at lines where we have 0 pieces.
    best_move = None
    best_score = -10**18

    # Bias ordering for tie-breaking: center, then edges/corners
    def preference(i, j, k):
        # center
        if (i, j, k) == (1, 1, 1):
            return 100
        # corners
        if all(x in (0, 2) for x in (i, j, k)):
            return 10
        # face centers
        if sum(x == 1 for x in (i, j, k)) == 2:
            return 5
        return 0

    for cell in available_cells():
        i0, j0, k0 = cell
        score = 0
        # evaluate lines passing through cell
        for ln in lines:
            if cell not in ln:
                continue
            s = 0
            o = 0
            z = 0
            for (i, j, k) in ln:
                v = board[i][j][k]
                if v == 1:
                    s += 1
                elif v == -1:
                    o += 1
                else:
                    z += 1
            # if we play here, it becomes our piece
            # so replace one empty with our token
            if z > 0:
                z -= 1
                s += 1

            # If opponent already has a piece on this line, we still might block,
            # but we don't get productive completion value from it.
            if o == 0:
                # our line is still "clean" (opponent not present)
                if s == 3:
                    score += 10**9  # would have been caught by winning move
                elif s == 2 and z == 0:
                    score += 10**6  # immediate threat (should be possible)
                elif s == 2:
                    score += 2000
                elif s == 1:
                    score += 200
                else:
                    score += 0

            # Blocking: if our token is not present on that line (i.e., s before move would be 0),
            # playing here can reduce opponent threats only if opponent has pieces.
            # We'll compute line potential for opponent if they were to play elsewhere,
            # using a symmetric clean-line idea:
            # Recompute what opponent sees if we place here: opponent's pieces unchanged.
            if s == 0:
                # our move doesn't help completion if line is currently ours-only? Actually s==0 means line had no 1.
                # But we just placed our token, so afterwards s!=0. So we interpret blocking differently:
                pass

            # Instead, use direct opponent-threat measure on the line considering current board and the move:
            # If after our move, the line has no opponent pieces and has 2 opponent empties -> not relevant.
            # We'll more simply approximate:
            # score increases if opponent currently has 2-in-line with one empty at/including this cell.
            # We can detect by looking at current counts before placement, where:
            # opponent has 2 and we place in the only empty -> blocking threat.
            # So compute current counts before placement:
            cur_s = 0
            cur_o = 0
            cur_z = 0
            for (i, j, k) in ln:
                v = board[i][j][k]
                if v == 1:
                    cur_s += 1
                elif v == -1:
                    cur_o += 1
                else:
                    cur_z += 1
            if cur_o == 2 and cur_z == 1:
                # opponent would win next by playing the remaining empty; we are choosing one such empty because cell in ln and it's empty
                score += 800000
            elif cur_o == 1 and cur_z == 2 and cur_s == 0:
                # contesting a partially filled line
                score += 120
            elif cur_o == 1 and cur_z == 2 and cur_s > 0:
                # mixed lines are less important
                score += 20

        score += preference(i0, j0, k0)

        # If we can create multiple threats, this heuristic still tends to win often,
        # but we can slightly boost multiplicative effect.
        # Count how many "two-in-a-row" opportunities we'd create (clean lines with s==2 and remaining empty count).
        threat_count = 0
        for ln in lines:
            if cell not in ln:
                continue
            cur_s = cur_o = cur_z = 0
            for (i, j, k) in ln:
                v = board[i][j][k]
                if v == 1:
                    cur_s += 1
                elif v == -1:
                    cur_o += 1
                else:
                    cur_z += 1
            if cur_o == 0:
                # after placing, s increases by 1 and z decreases by 1
                new_s = cur_s + 1
                new_z = cur_z - 1
                if new_s == 2 and new_z == 1:
                    threat_count += 1
        score += threat_count * 3000

        if score > best_score:
            best_score = score
            best_move = cell

    # As a last resort, pick any legal move
    if best_move is None:
        for cell in available_cells():
            best_move = cell
            break

    return best_move
