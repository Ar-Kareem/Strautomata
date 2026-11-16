
from __future__ import annotations

def policy(state: list[list[object]], role: str) -> str:
    # Parse board
    # board[r][c] in {'x','o',None}
    board = [[None for _ in range(4)] for _ in range(4)]
    cur = None
    for fact in state:
        if not fact:
            continue
        if fact[0] == "cell":
            # ["cell", row, col, val]
            r = int(fact[1]) - 1
            c = int(fact[2]) - 1
            v = fact[3]
            if v in ("x", "o"):
                board[r][c] = v
        elif fact[0] == "control":
            cur = str(fact[1])

    me = role.strip()
    opp = "o" if me == "x" else "x"

    # Safety evaluation:
    # Terminal condition: "adjacent (non-diagonal) to its own mark" ends the game when a player marks.
    # If after we play at (r,c), on opponent's turn there exists at least one empty cell
    # adjacent to any opponent mark, then opponent can win immediately (pick that cell).
    # We score moves by the number of such immediate-winning squares available to opponent.
    #
    # Additionally, we add a mild bonus for making our own marks have more adjacent empties,
    # which tends to shorten the game in our favor.
    def empties():
        res = []
        for rr in range(4):
            for cc in range(4):
                if board[rr][cc] is None:
                    res.append((rr, cc))
        return res

    def adj4(rr, cc):
        for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
            r2, c2 = rr + dr, cc + dc
            if 0 <= r2 < 4 and 0 <= c2 < 4:
                yield r2, c2

    # Apply move temporarily
    best_move = None
    best = None

    for (r, c) in empties():
        # place
        board[r][c] = me

        # Count immediate winning options for opponent on their next move:
        # an empty cell that is adj4 to any opponent mark.
        opp_wins = 0
        for rr in range(4):
            for cc in range(4):
                if board[rr][cc] is None:
                    # check adjacency to opponent marks
                    can = False
                    for ar, ac in adj4(rr, cc):
                        if board[ar][ac] == opp:
                            can = True
                            break
                    if can:
                        opp_wins += 1

        # Our future pressure: count empty cells adjacent to our marks
        my_pressure = 0
        for rr in range(4):
            for cc in range(4):
                if board[rr][cc] is None:
                    for ar, ac in adj4(rr, cc):
                        if board[ar][ac] == me:
                            my_pressure += 1
                            break

        # Lower is better for safety; then higher pressure is better.
        # Weight safety much higher to avoid giving opponent immediate wins.
        score = (opp_wins, -my_pressure)

        # Undo
        board[r][c] = None

        if best is None or score < best:
            best = score
            best_move = (r, c)

    # Fallback (shouldn't happen)
    if best_move is None:
        # choose first empty
        for rr in range(4):
            for cc in range(4):
                if board[rr][cc] is None:
                    best_move = (rr, cc)
                    break
            if best_move is not None:
                break

    r, c = best_move
    return f"mark({r+1},{c+1})"
