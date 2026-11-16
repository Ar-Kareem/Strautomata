
from __future__ import annotations
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    N = 3
    # Generate all 3-in-a-row winning lines in 3x3x3
    lines = []
    # axis-aligned: x, y, z
    for y in range(N):
        for z in range(N):
            lines.append([(x, y, z) for x in range(N)])  # varying x
    for x in range(N):
        for z in range(N):
            lines.append([(x, y, z) for y in range(N)])  # varying y
    for x in range(N):
        for y in range(N):
            lines.append([(x, y, z) for z in range(N)])  # varying z
    # face diagonals (on planes x=const, y=const, z=const)
    for z in range(N):
        # plane z fixed: (x,y) diagonals
        lines.append([(i, i, z) for i in range(N)])
        lines.append([(i, N-1-i, z) for i in range(N)])
    for y in range(N):
        # plane y fixed: (x,z) diagonals
        lines.append([(i, y, i) for i in range(N)])
        lines.append([(i, y, N-1-i) for i in range(N)])
    for x in range(N):
        # plane x fixed: (y,z) diagonals
        lines.append([(x, i, i) for i in range(N)])
        lines.append([(x, i, N-1-i) for i in range(N)])
    # space diagonals
    lines.append([(i, i, i) for i in range(N)])
    lines.append([(i, i, N-1-i) for i in range(N)])
    lines.append([(i, N-1-i, i) for i in range(N)])
    lines.append([(i, N-1-i, N-1-i) for i in range(N)])

    # Helper functions
    def get_cell(i: int, j: int, k: int) -> int:
        return board[i][j][k]

    def empty_cells():
        for i in range(N):
            for j in range(N):
                for k in range(N):
                    if get_cell(i, j, k) == 0:
                        yield (i, j, k)

    def would_win(move: Tuple[int, int, int], player: int) -> bool:
        mi, mj, mk = move
        # Check all lines that include the move
        for line in lines:
            if (mi, mj, mk) in line:
                s = 0
                for (x, y, z) in line:
                    v = player if (x, y, z) == (mi, mj, mk) else get_cell(x, y, z)
                    if v == player:
                        s += 1
                    elif v == -player:
                        s = -999  # mark impossible
                        break
                if s == N:  # would complete
                    return True
        return False

    # 1) Win immediately if possible
    my_winning_moves = []
    for m in empty_cells():
        if would_win(m, 1):
            my_winning_moves.append(m)
    if my_winning_moves:
        # If multiple (rare), pick deterministically
        return sorted(my_winning_moves)[0]

    # 2) Block opponent immediate wins
    opp_block_moves = []
    for m in empty_cells():
        if would_win(m, -1):
            opp_block_moves.append(m)
    if opp_block_moves:
        return sorted(opp_block_moves)[0]

    # 3) Heuristic scoring for best move
    # Count for each line: how many of player/opponent/empty.
    # Score lines with no opponent pieces. Favor making 2-in-a-row and preventing opponent.
    def line_score_for_player(line, player: int) -> int:
        # Return score contributed by this line assuming current board state (no hypothetical move yet).
        pc = 0
        oc = 0
        ec = 0
        for (x, y, z) in line:
            v = get_cell(x, y, z)
            if v == player:
                pc += 1
            elif v == -player:
                oc += 1
            else:
                ec += 1
        # If opponent already has a piece on this line, it's dead for player.
        if oc > 0:
            return 0
        # If line is still open:
        if pc == 0 and ec == 3:
            return 1  # slight preference for creating potential
        if pc == 1 and ec == 2:
            return 10
        if pc == 2 and ec == 1:
            return 200  # immediate threat next move
        if pc == 3:
            return 1000000
        return 0

    # For each candidate move, compute differential advantage:
    # (sum of our open-line scores after the move) - (sum of opponent open-line scores after the move)
    # with extra weight for moves that create immediate threats.
    def score_move(m: Tuple[int, int, int]) -> int:
        mi, mj, mk = m
        # temporarily evaluate without copying the board: compute per line including move
        total = 0

        # Precompute affected lines
        affected = [ln for ln in lines if (mi, mj, mk) in ln]

        # For each affected line, compute pc/oc/ec after placing
        for ln in affected:
            # Evaluate from our perspective
            pc = 0
            oc = 0
            ec = 0
            for (x, y, z) in ln:
                if (x, y, z) == (mi, mj, mk):
                    v = 1
                else:
                    v = get_cell(x, y, z)
                if v == 1:
                    pc += 1
                elif v == -1:
                    oc += 1
                else:
                    ec += 1
            if oc == 0:
                if pc == 1 and ec == 2:
                    total += 10
                elif pc == 2 and ec == 1:
                    total += 250
                elif pc == 3:
                    total += 1000000
                else:
                    total += 2  # pc==0
            # Evaluate from opponent perspective (how much we block them)
            pc2 = 0
            oc2 = 0
            ec2 = 0
            for (x, y, z) in ln:
                if (x, y, z) == (mi, mj, mk):
                    v = 1
                else:
                    v = get_cell(x, y, z)
                if v == -1:
                    pc2 += 1  # opponent pieces
                elif v == 1:
                    oc2 += 1
                else:
                    ec2 += 1
            # If our move doesn't allow opponent on that line (i.e., we put our mark and it blocks),
            # opponent contribution should be 0; otherwise, it is based on their pc2.
            if oc2 == 0:  # means no our pieces on this line after move, so opponent still could
                if pc2 == 1 and ec2 == 2:
                    total -= 10
                elif pc2 == 2 and ec2 == 1:
                    total -= 240
                elif pc2 == 3:
                    total -= 1000000
                else:
                    total -= 2
            else:
                # We placed on a line that contains our piece (including the move itself), so opponent is blocked.
                total += 5

        # Small global bias: favor central squares in each dimension for general strength
        # Centers (1,1,1) best; edge/corner less.
        center_bias = 0
        if (mi, mj, mk) == (1, 1, 1):
            center_bias = 30
        elif mi == 1 and mj == 1 or mi == 1 and mk == 1 or mj == 1 and mk == 1:
            center_bias = 12
        elif mi == 1 or mj == 1 or mk == 1:
            center_bias = 7
        total += center_bias

        return total

    # Choose best scored move; tie-break by lexicographic order for determinism
    best = None
    best_score = None
    for m in empty_cells():
        sc = score_move(m)
        if best is None or sc > best_score or (sc == best_score and m < best):
            best = m
            best_score = sc

    # Fallback (should never happen): return first empty
    if best is None:
        for m in empty_cells():
            return m
    return best
