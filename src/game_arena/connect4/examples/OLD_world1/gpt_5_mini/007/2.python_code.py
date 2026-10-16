
from typing import List

ROWS = 6
COLS = 7

def policy(board: List[List[int]]) -> int:
    """
    Choose a column to drop a disc for the current player (1).
    Strategy:
    1. If a move wins immediately, play it.
    2. If opponent has an immediate winning move, block it.
    3. Otherwise score moves by a heuristic:
       - Prefer center columns.
       - Prefer moves that create 2/3-in-a-row for us and avoid creating them for opponent.
       - Heavily avoid moves that allow opponent an immediate win next turn.
    Returns column index 0..6 (must be a non-full column).
    """
    # Helpers
    def next_row(col: int):
        for r in range(ROWS - 1, -1, -1):
            if board[r][col] == 0:
                return r
        return None

    def is_win_at(r: int, c: int, player: int) -> bool:
        # Check four directions
        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in dirs:
            count = 1
            # forward
            rr, cc = r + dr, c + dc
            while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
                count += 1
                rr += dr
                cc += dc
            # backward
            rr, cc = r - dr, c - dc
            while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
                count += 1
                rr -= dr
                cc -= dc
            if count >= 4:
                return True
        return False

    def is_win_after(col: int, player: int) -> bool:
        r = next_row(col)
        if r is None:
            return False
        board[r][col] = player
        w = is_win_at(r, col, player)
        board[r][col] = 0
        return w

    # Valid moves: columns with at least one empty
    valid_cols = [c for c in range(COLS) if next_row(c) is not None]
    if not valid_cols:
        # Should not happen in regular play, but pick 0 as fallback
        return 0

    # 1) Immediate win
    for c in valid_cols:
        if is_win_after(c, 1):
            return c

    # 2) Immediate block of opponent
    opp_winning_cols = [c for c in valid_cols if is_win_after(c, -1)]
    if len(opp_winning_cols) == 1:
        return opp_winning_cols[0]
    elif len(opp_winning_cols) > 1:
        # Multiple threats: cannot block both; pick one of them (try center-most)
        # Prefer blocking the one closer to center
        center = COLS // 2
        return min(opp_winning_cols, key=lambda x: abs(x - center))

    # 3) Heuristic scoring
    # We will simulate each move, avoid moves that allow opponent immediate win.
    # Score windows of length 4 across the board.
    window_weights = {0: 0, 1: 1, 2: 50, 3: 500, 4: 100000}
    center_col = COLS // 2

    def score_board_for_player(player: int) -> int:
        score = 0
        # horizontal windows
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [board[r][c + i] for i in range(4)]
                my = window.count(player)
                opp = window.count(-player)
                if opp == 0 and my > 0:
                    score += window_weights[my]
                elif my == 0 and opp > 0:
                    score -= window_weights[opp]
        # vertical windows
        for c in range(COLS):
            for r in range(ROWS - 3):
                window = [board[r + i][c] for i in range(4)]
                my = window.count(player)
                opp = window.count(-player)
                if opp == 0 and my > 0:
                    score += window_weights[my]
                elif my == 0 and opp > 0:
                    score -= window_weights[opp]
        # diagonal down-right
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board[r + i][c + i] for i in range(4)]
                my = window.count(player)
                opp = window.count(-player)
                if opp == 0 and my > 0:
                    score += window_weights[my]
                elif my == 0 and opp > 0:
                    score -= window_weights[opp]
        # diagonal up-right
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [board[r - i][c + i] for i in range(4)]
                my = window.count(player)
                opp = window.count(-player)
                if opp == 0 and my > 0:
                    score += window_weights[my]
                elif my == 0 and opp > 0:
                    score -= window_weights[opp]
        return score

    best_col = valid_cols[0]
    best_score = -10**9

    for c in valid_cols:
        r = next_row(c)
        # simulate drop
        board[r][c] = 1

        # Check if this move allows opponent immediate win next turn
        opponent_can_win = False
        for c2 in range(COLS):
            r2 = None
            for rr in range(ROWS - 1, -1, -1):
                if board[rr][c2] == 0:
                    r2 = rr
                    break
            if r2 is not None:
                # simulate opponent drop
                board[r2][c2] = -1
                if is_win_at(r2, c2, -1):
                    opponent_can_win = True
                board[r2][c2] = 0
            if opponent_can_win:
                break

        if opponent_can_win:
            score = -1000000  # heavily penalize
        else:
            # Score board for us (positive is good)
            score = score_board_for_player(1)
            # small bonus for being near center and for lower rows (stability)
            score += max(0, 3 - abs(c - center_col)) * 5
            score += (ROWS - r)  # prefer lower (more supported) placements slightly

        # revert
        board[r][c] = 0

        # tie-breaker: prefer center column if equal score (closer to center)
        if score > best_score or (score == best_score and abs(c - center_col) < abs(best_col - center_col)):
            best_score = score
            best_col = c

    return best_col
