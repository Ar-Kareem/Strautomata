
import random
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    4x4 Tic Tac Toe (connect-4 on a 4x4):
    - 1  = our player
    - -1 = opponent
    - 0  = empty
    """
    N = 4
    L = 4  # need 4 in a line on 4x4

    # Collect all winning lines (rows, cols, diags)
    lines = []
    # rows
    for r in range(N):
        lines.append([(r, c) for c in range(N)])
    # cols
    for c in range(N):
        lines.append([(r, c) for r in range(N)])
    # main diag
    lines.append([(i, i) for i in range(N)])
    # anti diag
    lines.append([(i, N - 1 - i) for i in range(N)])

    def winner(b):
        # returns 1 if we win, -1 if opponent wins, else 0
        for line in lines:
            vals = [b[r][c] for (r, c) in line]
            s = sum(vals)
            # for 4 cells, sum==4 means all 1; sum==-4 means all -1
            if s == L:
                return 1
            if s == -L:
                return -1
        return 0

    def available_moves(b):
        moves = []
        for r in range(N):
            for c in range(N):
                if b[r][c] == 0:
                    moves.append((r, c))
        return moves

    # If already terminal (shouldn't happen), return any legal move
    legal = available_moves(board)
    if not legal:
        return (0, 0)

    # Immediate win/block checks
    w = winner(board)
    if w != 0:
        # game already ended; just return a legal move
        return legal[0]

    def would_win(b, move, player):
        r, c = move
        b[r][c] = player
        res = winner(b)
        b[r][c] = 0
        return res == player

    # 1) Take winning move if exists
    for m in legal:
        if would_win(board, m, 1):
            return m

    # 2) Block opponent immediate win if exists
    for m in legal:
        if would_win(board, m, -1):
            return m

    # Heuristic scoring:
    # For each line, consider counts of our marks and opponent marks.
    # If a line has opponent marks, it is only valuable if it's not immediate threat;
    # scoring uses powers to strongly prefer lines closer to completion.
    #
    # Additionally, avoid moves that would allow opponent to win immediately.
    def line_score(our_count, opp_count):
        # line length is 4
        if opp_count > 0 and our_count > 0:
            return 0
        if our_count == 0 and opp_count == 0:
            return 1  # small preference for freedom
        if our_count > 0:
            # reward completion potential
            # 1 -> 10, 2 -> 100, 3 -> 1000 (4 would already be caught as immediate win)
            return (10 ** our_count)
        if opp_count > 0:
            # penalize opponent potential
            return -(10 ** opp_count)
        return 0

    def evaluate_move(move):
        r, c = move
        # Avoid giving opponent an immediate win (extra safety)
        board[r][c] = 1
        opp_legal = available_moves(board)
        opp_immediate = False
        for om in opp_legal:
            if would_win(board, om, -1):
                opp_immediate = True
                break
        board[r][c] = 0
        if opp_immediate:
            return -10**18

        # Compute heuristic score for placing at (r,c)
        score = 0
        for line in lines:
            # Only lines that include (r,c) are affected, but full evaluation is fine for 4x4.
            vals = [board[rr][cc] for (rr, cc) in line]
            # If (r,c) is empty, treat it as our mark in this evaluation
            vals2 = []
            for (rr, cc), v in zip(line, vals):
                if rr == r and cc == c:
                    vals2.append(1)
                else:
                    vals2.append(v)
            our_count = sum(1 for v in vals2 if v == 1)
            opp_count = sum(1 for v in vals2 if v == -1)
            score += line_score(our_count, opp_count)

        # Small positional tie-breakers (center-ish gets slight bonus)
        center_bonus = 0
        if (r, c) in [(1, 1), (1, 2), (2, 1), (2, 2)]:
            center_bonus = 3
        elif (r, c) in [(0, 0), (0, 3), (3, 0), (3, 3)]:
            center_bonus = 1
        score += center_bonus
        return score

    # Choose the best heuristic move
    best_score = -10**18
    best_moves = []
    # Randomize among equal scores to avoid predictability
    random.shuffle(legal)
    for m in legal:
        sc = evaluate_move(m)
        if sc > best_score:
            best_score = sc
            best_moves = [m]
        elif sc == best_score:
            best_moves.append(m)

    return best_moves[0]
