
def policy(board: list[list[int]]) -> int:
    def is_winning(new_board, r, c, player):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 7 and new_board[nr][nc] == player:
                count += 1
                nr += dr
                nc += dc
            nr, nc = r - dr, c - dc
            while 0 <= nr < 6 and 0 <= nc < 7 and new_board[nr][nc] == player:
                count += 1
                nr -= dr
                nc -= dc
            if count >= 4:
                return True
        return False

    def evaluate_segment(segment, player):
        my_count = segment.count(player)
        opp_count = segment.count(-player)
        if my_count == 4:
            return 100
        elif my_count == 3 and opp_count == 0:
            return 10
        elif my_count == 2 and opp_count == 0:
            return 4
        elif my_count == 1 and opp_count == 0:
            return 2
        elif opp_count == 4:
            return -100
        elif opp_count == 3 and my_count == 0:
            return -10
        elif opp_count == 2 and my_count == 0:
            return -4
        elif opp_count == 1 and my_count == 0:
            return -1
        else:
            return 0

    def evaluate_board(b, player):
        score = 0
        # Horizontal
        for r in range(6):
            for c in range(4):
                segment = [b[r][c], b[r][c+1], b[r][c+2], b[r][c+3]]
                score += evaluate_segment(segment, player)
        # Vertical
        for c in range(7):
            for r in range(3):
                segment = [b[r][c], b[r+1][c], b[r+2][c], b[r+3][c]]
                score += evaluate_segment(segment, player)
        # Diagonal (top-left to bottom-right)
        for r in range(3):
            for c in range(4):
                segment = [b[r][c], b[r+1][c+1], b[r+2][c+2], b[r+3][c+3]]
                score += evaluate_segment(segment, player)
        # Diagonal (top-right to bottom-left)
        for r in range(3):
            for c in range(3, 7):
                segment = [b[r][c], b[r+1][c-1], b[r+2][c-2], b[r+3][c-3]]
                score += evaluate_segment(segment, player)
        return score

    valid_columns = [c for c in range(7) if board[5][c] == 0]

    # Check for immediate winning move
    for c in valid_columns:
        row = 5
        while row >= 0 and board[row][c] != 0:
            row -= 1
        new_board = [list(row) for row in board]
        new_board[row][c] = 1
        if is_winning(new_board, row, c, 1):
            return c

    # Check for opponent's potential win
    safe_columns = []
    for c in valid_columns:
        row = 5
        while row >= 0 and board[row][c] != 0:
            row -= 1
        new_board = [list(row) for row in board]
        new_board[row][c] = 1
        opponent_can_win = False
        for cd in valid_columns:
            r = 5
            while r >= 0 and new_board[r][cd] != 0:
                r -= 1
            if r == -1:
                continue
            temp_board = [list(row) for row in new_board]
            temp_board[r][cd] = -1
            if is_winning(temp_board, r, cd, -1):
                opponent_can_win = True
                break
        if not opponent_can_win:
            safe_columns.append(c)

    if safe_columns:
        scores = []
        center_weights = [1, 2, 3, 4, 3, 2, 1]
        for c in safe_columns:
            row = 5
            while row >= 0 and board[row][c] != 0:
                row -= 1
            new_board = [list(row) for row in board]
            new_board[row][c] = 1
            sc = evaluate_board(new_board, 1)
            adjusted_score = sc + center_weights[c] * 0.01
            scores.append((adjusted_score, c))
        scores.sort(reverse=True)
        return scores[0][1]
    else:
        scores = []
        center_weights = [1, 2, 3, 4, 3, 2, 1]
        for c in valid_columns:
            row = 5
            while row >= 0 and board[row][c] != 0:
                row -= 1
            new_board = [list(row) for row in board]
            new_board[row][c] = 1
            sc = evaluate_board(new_board, 1)
            adjusted_score = sc + center_weights[c] * 0.01
            scores.append((adjusted_score, c))
        scores.sort(reverse=True)
        return scores[0][1]
