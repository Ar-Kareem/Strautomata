
import itertools
import copy

def policy(board: list[list[int]]) -> int:
    def get_move_row(b, col):
        for row in reversed(range(6)):
            if b[row][col] == 0:
                return row
        return None

    def check_win(b, p):
        # Check horizontal
        for r in range(6):
            for c in range(4):
                if all(b[r][c+i] == p for i in range(4)):
                    return True
        # Check vertical
        for c in range(7):
            for r in range(3):
                if all(b[r+i][c] == p for i in range(4)):
                    return True
        # Check diagonal down-right
        for r in range(3):
            for c in range(3):
                if all(b[r+i][c+i] == p for i in range(4)):
                    return True
        # Check diagonal down-left
        for r in range(3):
            for c in range(3, 7):
                if all(b[r+i][c-i] == p for i in range(4)):
                    return True
        return False

    adjacent_moves = [c for c in range(7) if not all(board[i][c] != 0 for i in range(6))]

    # Step 1: Check for immediate win
    for move in adjacent_moves:
        new_board = [r.copy() for r in board]
        row = get_move_row(new_board, move)
        new_board[row][move] = 1
        if check_win(new_board, 1):
            return move

    # Step 2: Check moves that prevent opponent's immediate win
    safe_moves = []
    for move in adjacent_moves:
        new_board = [r.copy() for r in board]
        row = get_move_row(board, move)
        new_board[row][move] = 1
        opponent_win_found = False
        for opp_move in range(7):
            if all(board[i][opp_move] != 0 for i in range(6)):
                continue
            opp_new_board = [r.copy() for r in new_board]
            opp_row = get_move_row(opp_new_board, opp_move)
            opp_new_board[opp_row][opp_move] = -1
            if check_win(opp_new_board, -1):
                opponent_win_found = True
                break
        if not opponent_win_found:
            safe_moves.append(move)

    if safe_moves:
        # Step 3: Select best move using heuristic evaluation
        best_score = -float('inf')
        best_move = None
        for move in safe_moves:
            new_board = [r.copy() for r in board]
            row = get_move_row(board, move)
            new_board[row][move] = 1
            current_score = evaluate_board(new_board)
            if current_score > best_score:
                best_score = current_score
                best_move = move
        return best_move

    # Fallback: Choose any available move (least safe)
    return max(adjacent_moves, key=lambda c: (evaluate_board([r.copy() for r in board], c), c))

def evaluate_board(board):
    score = 0
    players = [1, -1]
    for player in players:
        for r in range(6):
            for c in range(3):
                window = [board[r][c+i] if c+i <7 else 0 for i in range(4)]
                if player == 1:
                    score += score_window(window, player)
                else:
                    score -= score_window(window, player)
        for c in range(7):
            for r in range(3):
                window = [board[r+i][c] for i in range(4)]
                if player == 1:
                    score += score_window(window, player)
                else:
                    score -= score_window(window, player)
        for r in range(3):
            for c in range(3):
                window = [board[r+i][c+i] for i in range(4)]
                if player == 1:
                    score += score_window(window, player)
                else:
                    score -= score_window(window, player)
        for r in range(3):
            for c in range(3, 7):
                window = [board[r+i][c-i] for i in range(4)]
                if player == 1:
                    score += score_window(window, player)
                else:
                    score -= score_window(window, player)
    return score

def score_window(window, player):
    mine = sum(1 for d in window if d == player)
    opp = sum(1 for d in window if d == -player)
    empty = window.count(0)

    if mine == 4:
        return 1000
    if opp == 4:
        return -1000
    if empty == 1:
        if mine == 3:
            return 50
        elif opp == 3:
            return -50
        return 0

    if len(window) !=4:
        for s in range(0,4):
            w = window[s:s+4]
            if len(w) == 4:
                if player == 1:
                    score += score_small_window(w, player)
                else:
                    score -= score_small_window(w, player)
    return 0

def score_small_window(w, p):
    m = sum(1 for d in w if d == p)
    o = sum(1 for d in w if d == -p)
    e = sum(1 for d in w if d == 0)
    if m ==4:
        return 1000
    if o ==4:
        return -1000
    if m ==3 and e ==1:
        return 50 if p ==1 else -50
    if o ==3:
        return -50 if p ==1 else 50
    if m >=2:
        return 10 if p ==1 else -10
    return 0

if __name__ == "__main__":
    pass
