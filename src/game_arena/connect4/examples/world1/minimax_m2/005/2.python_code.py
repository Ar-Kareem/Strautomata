
def score_board(board):
    score = 0
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        for i in range(6):
            for j in range(7):
                window = []
                for k in range(4):
                    r = i + dr * k
                    c = j + dc * k
                    if 0 <= r < 6 and 0 <= c < 7:
                        window.append(board[r][c])
                if len(window) == 4:
                    count_my = window.count(1)
                    count_opponent = window.count(-1)
                    count_empty = window.count(0)
                    if count_my == 4:
                        score += 100
                    elif count_my == 3 and count_empty >= 1:
                        score += 20
                    elif count_my == 2 and count_empty >= 2:
                        score += 3
                    elif count_my == 1 and count_empty >= 3:
                        score += 1
                    if count_opponent == 4:
                        score -= 100
                    elif count_opponent == 3 and count_empty >= 1:
                        score -= 20
                    elif count_opponent == 2 and count_empty >= 2:
                        score -= 3
                    elif count_opponent == 1 and count_empty >= 3:
                        score -= 1
    return score

def policy(board):
    possible_moves = [col for col in range(7) if board[0][col] == 0]
    if not possible_moves:
        return None
    best_score = -float('inf')
    best_cols = []
    for col in possible_moves:
        new_board = [row[:] for row in board]
        for row in range(5, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = 1
                break
        score = score_board(new_board)
        if score > best_score:
            best_score = score
            best_cols = [col]
        elif score == best_score:
            best_cols.append(col)
    center = 3
    best_col = min(best_cols, key=lambda col: abs(col - center))
    return best_col
