
import copy

def policy(board: list[list[int]]) -> int:
    def can_play(col):
        return board[0][col] == 0
    
    def play_move(curr_board, col, player):
        new_board = [row.copy() for row in curr_board]
        for row in reversed(range(6)):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                break
        return new_board
    
    def has_won(curr_board, player):
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if curr_board[row][col] == player and curr_board[row][col+1] == player and curr_board[row][col+2] == player and curr_board[row][col+3] == player:
                    return True
        # Check vertical
        for col in range(7):
            for row in range(3):
                if curr_board[row][col] == player and curr_board[row+1][col] == player and curr_board[row+2][col] == player and curr_board[row+3][col] == player:
                    return True
        # Check diagonal right
        for row in range(3):
            for col in range(4):
                if curr_board[row][col] == player and curr_board[row+1][col+1] == player and curr_board[row+2][col+2] == player and curr_board[row+3][col+3] == player:
                    return True
        # Check diagonal left
        for row in range(3):
            for col in range(3, 7):
                if curr_board[row][col] == player and curr_board[row+1][col-1] == player and curr_board[row+2][col-2] == player and curr_board[row+3][col-3] == player:
                    return True
        return False
    
    def evaluate(curr_board):
        score = 0
        # Precompute all possible lines
        lines = []
        # Horizontal
        for row in range(6):
            for col in range(4):
                lines.append([(row, col+i) for i in range(4)])
        # Vertical
        for col in range(7):
            for row in range(3):
                lines.append([(row+i, col) for i in range(4)])
        # Diagonal right
        for row in range(3):
            for col in range(4):
                lines.append([(row+i, col+i) for i in range(4)])
        # Diagonal left
        for row in range(3):
            for col in range(3, 7):
                lines.append([(row+i, col-i) for i in range(4)])
        
        for line in lines:
            cnt_1, cnt_neg1 = 0, 0
            for (r, c) in line:
                if curr_board[r][c] == 1:
                    cnt_1 += 1
                elif curr_board[r][c] == -1:
                    cnt_neg1 += 1
            if cnt_neg1 == 0:
                if cnt_1 == 3:
                    score += 100
                elif cnt_1 == 2:
                    score += 5
                elif cnt_1 == 4:
                    score += 1000
            elif cnt_1 == 0:
                if cnt_neg1 == 3:
                    score -= 100
                elif cnt_neg1 == 2:
                    score -= 5
                elif cnt_neg1 == 4:
                    score -= 1000
        return score
    
    def minimax(curr_board, depth, alpha, beta, maximizing):
        if depth == 0 or has_won(curr_board, 1) or has_won(curr_board, -1):
            return evaluate(curr_board)
        valid_cols = [col for col in [3,2,4,1,5,0,6] if curr_board[0][col] == 0]
        if maximizing:
            value = -float('inf')
            for col in valid_cols:
                child = play_move(curr_board, col, 1)
                value = max(value, minimax(child, depth-1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for col in valid_cols:
                child = play_move(curr_board, col, -1)
                value = min(value, minimax(child, depth-1, alpha, beta, True))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value
    
    # Check immediate win
    for col in [3,2,4,1,5,0,6]:
        if can_play(col):
            new_board = play_move(board, col, 1)
            if has_won(new_board, 1):
                return col
    
    # Check opponent's immediate win
    for col in [3,2,4,1,5,0,6]:
        if can_play(col):
            new_board = play_move(board, col, -1)
            if has_won(new_board, -1):
                if can_play(col):
                    return col
    
    # Minimax with depth 4
    best_score = -float('inf')
    best_col = 3  # Default to center column
    for col in [3,2,4,1,5,0,6]:
        if can_play(col):
            new_board = play_move(board, col, 1)
            score = minimax(new_board, 4, -float('inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_col = col
    return best_col
