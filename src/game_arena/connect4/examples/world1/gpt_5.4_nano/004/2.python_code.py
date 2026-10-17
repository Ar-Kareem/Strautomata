
from typing import List, Tuple

def policy(board: list[list[int]]) -> int:
    ROWS, COLS = 6, 7
    me = 1
    opp = -1

    def legal_cols(b: List[List[int]]) -> List[int]:
        return [c for c in range(COLS) if b[0][c] == 0]

    def drop_row(b: List[List[int]], c: int) -> int:
        # lowest empty cell in column c
        for r in range(ROWS - 1, -1, -1):
            if b[r][c] == 0:
                return r
        return -1  # should not happen for legal c

    def check_win_from(b: List[List[int]], r: int, c: int, player: int) -> bool:
        # Check 4 directions: horiz, vert, diag \, diag /
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            # forward
            rr, cc = r + dr, c + dc
            while 0 <= rr < ROWS and 0 <= cc < COLS and b[rr][cc] == player:
                count += 1
                rr += dr
                cc += dc
            # backward
            rr, cc = r - dr, c - dc
            while 0 <= rr < ROWS and 0 <= cc < COLS and b[rr][cc] == player:
                count += 1
                rr -= dr
                cc -= dc
            if count >= 4:
                return True
        return False

    def immediate_win_cols(b: List[List[int]], player: int) -> List[int]:
        wins = []
        for c in legal_cols(b):
            r = drop_row(b, c)
            # simulate
            b[r][c] = player
            if check_win_from(b, r, c, player):
                wins.append(c)
            b[r][c] = 0
        return wins

    def evaluate_window(window: List[int], player: int) -> int:
        # window length 4
        oppp = -player
        cnt_player = window.count(player)
        cnt_opp = window.count(oppp)
        cnt_empty = window.count(0)

        # If blocked by opponent, score is small/zero for our player
        if cnt_opp > 0 and cnt_player > 0:
            return 0

        score = 0
        if cnt_player == 4:
            score += 100000
        elif cnt_player == 3 and cnt_empty == 1:
            score += 200
        elif cnt_player == 2 and cnt_empty == 2:
            score += 30
        elif cnt_player == 1 and cnt_empty == 3:
            score += 3

        # Penalize giving opponent strong threats (from our perspective)
        if cnt_opp == 3 and cnt_empty == 1:
            score -= 240
        elif cnt_opp == 2 and cnt_empty == 2:
            score -= 15

        return score

    def score_move(b: List[List[int]], c: int, player: int) -> int:
        # Place temporarily
        r = drop_row(b, c)
        b[r][c] = player

        total = 0

        # Center preference
        center = COLS // 2
        total += 6 - abs(center - c)

        # Evaluate all windows that include (r,c)
        # Horizontal
        for start_c in range(max(0, c - 3), min(COLS - 3, c) + 1):
            window = [b[r][start_c + i] for i in range(4)]
            total += evaluate_window(window, player)

        # Vertical
        for start_r in range(max(0, r - 3), min(ROWS - 3, r) + 1):
            window = [b[start_r + i][c] for i in range(4)]
            total += evaluate_window(window, player)

        # Diagonal \ (down-right)
        for k in range(-3, 1):
            start_r = r - k
            start_c = c - k
            if 0 <= start_r <= ROWS - 4 and 0 <= start_c <= COLS - 4:
                window = [b[start_r + i][start_c + i] for i in range(4)]
                total += evaluate_window(window, player)

        # Diagonal / (down-left)
        for k in range(-3, 1):
            start_r = r - k
            start_c = c + k
            if 0 <= start_r <= ROWS - 4 and 0 <= start_c <= COLS - 4:
                window = [b[start_r + i][start_c - i] for i in range(4)]
                total += evaluate_window(window, player)

        b[r][c] = 0
        return total

    # Work on a copy? We'll temporarily modify and restore; safe but ensure board isn't shared unexpectedly.
    b = [row[:] for row in board]

    legal = legal_cols(b)
    if not legal:
        return 0  # should not occur in valid game states

    # 1) Immediate win
    my_wins = immediate_win_cols(b, me)
    if my_wins:
        # If multiple wins (rare), choose the most central
        return sorted(my_wins, key=lambda x: abs((COLS//2) - x))[0]

    # 2) Immediate block (opponent's next win)
    opp_wins = immediate_win_cols(b, opp)
    if opp_wins:
        return sorted(opp_wins, key=lambda x: abs((COLS//2) - x))[0]

    # 3) Otherwise, evaluate scored moves
    # Tie-break by center bias
    scored: List[Tuple[int, int]] = []
    for c in legal:
        s = score_move(b, c, me)
        # add small center bias to break ties consistently
        s += (10 - abs((COLS // 2) - c))
        scored.append((s, c))

    scored.sort(reverse=True)  # highest score first
    best_score, best_col = scored[0]

    # Ensure legality
    if b[0][best_col] != 0:
        # fallback: choose first legal near center
        return sorted(legal, key=lambda x: abs((COLS//2) - x))[0]

    return best_col
