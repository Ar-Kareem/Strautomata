
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose a move for 4x4 Tic Tac Toe.
    board: 4x4 list of lists with 0 (empty), 1 (us), -1 (opponent).
    Returns (row, col) with 0 <= row,col <= 3.
    Strategy:
    - If we can win immediately, make that move.
    - If opponent can win immediately, block it. If multiple threats, try to play a move that neutralizes all threats.
    - Otherwise, evaluate empty cells by line potentials and pick the best.
    """
    SIZE = 4

    def empty_cells(b):
        return [(r, c) for r in range(SIZE) for c in range(SIZE) if b[r][c] == 0]

    def lines_through(r, c):
        # return list of lists of coordinates for the four possible lines through (r,c)
        res = []
        # row
        res.append([(r, j) for j in range(SIZE)])
        # col
        res.append([(i, c) for i in range(SIZE)])
        # main diagonal
        if r == c:
            res.append([(i, i) for i in range(SIZE)])
        # anti-diagonal
        if r + c == SIZE - 1:
            res.append([(i, SIZE - 1 - i) for i in range(SIZE)])
        return res

    def is_win_after(b, r, c, player):
        # simulate placing player at (r,c) and check if that completes any 4-in-row
        # Only need to check lines that pass through (r,c)
        for line in lines_through(r, c):
            win = True
            for (i, j) in line:
                val = b[i][j]
                if i == r and j == c:
                    val = player
                if val != player:
                    win = False
                    break
            if win:
                return True
        return False

    def opponent_immediate_wins(b):
        threats = []
        for (r, c) in empty_cells(b):
            if is_win_after(b, r, c, -1):
                threats.append((r, c))
        return threats

    # quick terminal: if no empties, return first cell (shouldn't normally happen when asked to move)
    empties = empty_cells(board)
    if not empties:
        return (0, 0)

    # 1) Our immediate winning move
    for (r, c) in empties:
        if is_win_after(board, r, c, 1):
            return (r, c)

    # 2) Opponent immediate winning moves (threats)
    threats = opponent_immediate_wins(board)
    if threats:
        # If exactly one threat, block it.
        if len(threats) == 1:
            return threats[0]
        # If multiple threats, try to find a move that after placing our mark eliminates all threats
        for (r, c) in empties:
            # simulate our move
            board[r][c] = 1
            new_threats = opponent_immediate_wins(board)
            board[r][c] = 0
            if not new_threats:
                return (r, c)
        # otherwise, try to play a move that is one of the threatened cells that also creates our threat
        # (attempt to at least reduce opponent's winning options or create a counter)
        # Prefer a threatened cell that creates our immediate win next turn (fork-like)
        best_choice = None
        best_score = None
        for (r, c) in threats:
            # evaluate by counting how many lines this cell improves for us
            score = 0
            for line in lines_through(r, c):
                cnt_own = sum(1 for (i, j) in line if board[i][j] == 1)
                cnt_opp = sum(1 for (i, j) in line if board[i][j] == -1)
                if cnt_opp == 0:
                    score += 10 ** cnt_own
            if best_choice is None or score > best_score:
                best_choice = (r, c)
                best_score = score
        if best_choice:
            return best_choice
        # fallback: pick the first threat
        return threats[0]

    # 3) Heuristic scoring for each empty cell
    center_cells = {(1,1),(1,2),(2,1),(2,2)}
    best_move = None
    best_score = -10**9

    for (r, c) in empties:
        # simulate placing our mark
        score = 0
        for line in lines_through(r, c):
            cnt_own = sum(1 for (i, j) in line if board[i][j] == 1)
            cnt_opp = sum(1 for (i, j) in line if board[i][j] == -1)
            # after placing here, cnt_own would increase by 1 if this line contains (r,c),
            # but cnt_opp stays the same. For scoring, consider potential lines with no opponent
            if cnt_opp == 0:
                # reward lines where we have more marks; exponential preference
                score += 10 ** (cnt_own + 1)  # +1 because we considered placing here
            # penalize lines where opponent has presence (we can't use them)
            if cnt_own == 0 and cnt_opp > 0:
                # opponent potential in that line (we might want to block those)
                score -= 5 ** cnt_opp
        # small positional bonus for central control
        if (r, c) in center_cells:
            score += 50
        # favor corners a bit
        if (r, c) in {(0,0),(0,3),(3,0),(3,3)}:
            score += 10

        if score > best_score:
            best_score = score
            best_move = (r, c)

    # If for some reason none chosen, pick first empty
    if best_move is None:
        return empties[0]
    return best_move
