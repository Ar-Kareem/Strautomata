
from typing import List, Optional

def policy(state: list[list[object]], role: str) -> str:
    # Extract current board
    board = [["b" for _ in range(3)] for _ in range(3)]
    for fact in state:
        if isinstance(fact, list) and len(fact) >= 4 and fact[0] == "cell":
            r = int(fact[1]) - 1
            c = int(fact[2]) - 1
            board[r][c] = str(fact[3])

    me = role
    opp = "o" if me == "x" else "x"

    def empties():
        for r in range(3):
            for c in range(3):
                if board[r][c] == "b":
                    yield r, c

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

    def winner_of(bd: List[List[str]], player: str) -> bool:
        for line in lines:
            if all(bd[r][c] == player for r, c in line):
                return True
        return False

    def find_winning_move(player: str) -> Optional[tuple]:
        for r, c in empties():
            bd = [row[:] for row in board]
            bd[r][c] = player
            if winner_of(bd, player):
                return r, c
        return None

    # 1) Win now
    win_move = find_winning_move(me)
    if win_move is not None:
        r, c = win_move
        return f"mark({r+1},{c+1})"

    # 2) Block opponent win
    block_move = find_winning_move(opp)
    if block_move is not None:
        r, c = block_move
        return f"mark({r+1},{c+1})"

    # Helper to count immediate threats (two-in-a-row with one empty)
    def threat_count(player: str) -> int:
        cnt = 0
        for line in lines:
            vals = [board[r][c] for r, c in line]
            if vals.count(player) == 2 and vals.count("b") == 1:
                cnt += 1
        return cnt

    # 3) Fork detection: move that results in at least two threats for me
    # For each candidate empty cell, simulate and count threats
    fork_candidates = []
    for r, c in empties():
        bd = [row[:] for row in board]
        bd[r][c] = me
        # compute threat count on this simulated board
        # local winner_of uses closure lines, so just count patterns directly
        tcnt = 0
        for line in lines:
            vals = [bd[rr][cc] for rr, cc in line]
            if vals.count(me) == 2 and vals.count("b") == 1:
                tcnt += 1
        if tcnt >= 2:
            fork_candidates.append((r, c))
    if fork_candidates:
        # Deterministic pick: prefer center, then corners, then edges
        def pref(rc):
            r, c = rc
            if (r, c) == (1, 1):
                return 0
            if (r, c) in [(0,0),(0,2),(2,0),(2,2)]:
                return 1
            return 2
        r, c = sorted(fork_candidates, key=pref)[0]
        return f"mark({r+1},{c+1})"

    # 4) Otherwise: choose strategically best square
    # Prefer center, corners, then edges. Also avoid giving opponent immediate win (already blocked threats of 1),
    # but we can still avoid creating new immediate wins for opponent.
    priority = []
    for r, c in empties():
        if (r, c) == (1, 1):
            pr = 0
        elif (r, c) in [(0,0),(0,2),(2,0),(2,2)]:
            pr = 1
        else:
            pr = 2
        priority.append((pr, r, c))

    # Filter moves that would allow opponent to win immediately (safety)
    safe_moves = []
    for pr, r, c in priority:
        bd = [row[:] for row in board]
        bd[r][c] = me
        # If opponent can win next, mark unsafe
        can_opp_win = False
        for rr, cc in [(rr, cc) for rr, cc in empties()]:
            # empties() is from original board; need empty positions in simulated board
            pass
        # compute opponent winning in simulated bd
        for rr in range(3):
            for cc in range(3):
                if bd[rr][cc] == "b":
                    bd2 = [row[:] for row in bd]
                    bd2[rr][cc] = opp
                    if winner_of(bd2, opp):
                        can_opp_win = True
                        break
            if can_opp_win:
                break
        if not can_opp_win:
            safe_moves.append((pr, r, c))

    chosen = None
    if safe_moves:
        chosen = sorted(safe_moves, key=lambda x: (x[0], x[1], x[2]))[0]
        _, r, c = chosen
    else:
        # fallback: best priority available
        _, r, c = sorted(priority, key=lambda x: (x[0], x[1], x[2]))[0]

    return f"mark({r+1},{c+1})"
