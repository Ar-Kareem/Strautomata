
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    def get_board(you, opponent):
        return 2 * opponent + you  # 0: empty, 1: you, 2: opponent

    def make_move(board, player, r, c):
        opp = 3 - player
        new_board = board.copy()
        new_board[r, c] = player
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in directions:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < 8 and 0 <= cc < 8) or new_board[rr, cc] != opp:
                continue
            flips = []
            rr += dr
            cc += dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                if new_board[rr, cc] == player:
                    break
                elif new_board[rr, cc] == 0:
                    flips = []
                    break
                else:
                    flips.append((rr, cc))
                    rr += dr
                    cc += dc
            for fr, fc in flips:
                new_board[fr, fc] = player
        return new_board

    def evaluate(board):
        my_count = (board == 1).sum()
        opp_count = (board == 2).sum()
        score = my_count - opp_count
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        for r, c in corners:
            if board[r, c] == 1:
                score += 10
            elif board[r, c] == 2:
                score -= 10
        return score

    def is_legal(board, r, c, player):
        opp = 3 - player
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in directions:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < 8 and 0 <= cc < 8) or board[rr, cc] != opp:
                continue
            rr += dr
            cc += dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                if board[rr, cc] == player:
                    return True
                elif board[rr, cc] == 0:
                    break
                else:
                    rr += dr
                    cc += dc
        return False

    def get_legal_moves(board, player):
        moves = []
        for r in range(8):
            for c in range(8):
                if board[r, c] == 0 and is_legal(board, r, c, player):
                    moves.append((r, c))
        return moves

    def minmax(board, depth, maximizing_player):
        if depth == 0:
            return evaluate(board)
        player = 1 if maximizing_player else 2
        moves = get_legal_moves(board, player)
        if not moves:
            # If no moves, pass and evaluate the current board if depth allows
            return evaluate(board) if depth > 0 else evaluate(board)
        if maximizing_player:
            best = -np.inf
            for r, c in moves:
                new_b = make_move(board, player, r, c)
                result = minmax(new_b, depth - 1, False)
                best = max(best, result)
        else:
            best = np.inf
            for r, c in moves:
                new_b = make_move(board, player, r, c)
                result = minmax(new_b, depth - 1, True)
                best = min(best, result)
        return best

    board = get_board(you, opponent)
    legal_moves = get_legal_moves(board, 1)
    if not legal_moves:
        return "pass"
    
    best_score = -np.inf
    best_move = legal_moves[0]  # Default to first if all tied
    for r, c in legal_moves:
        new_board = make_move(board, 1, r, c)
        score = minmax(new_board, 2, False)
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    row_idx, col_idx = best_move
    col = chr(ord('a') + col_idx)
    row = str(row_idx + 1)
    return col + row
