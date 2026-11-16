
import copy

def policy(board):
    valid_moves = [c for c in range(7) if board[0][c] == 0]
    if not valid_moves:
        return -1  # Invalid case, board is full
    
    # Check for any immediate winning move
    for move in valid_moves:
        new_board = copy.deepcopy(board)
        r = 5
        while r >= 0 and new_board[r][move] != 0:
            r -= 1
        new_board[r][move] = 1
        if check_win(new_board, 1):
            return move
    
    # Use Minimax with alpha-beta pruning to choose the best move
    best_col = valid_moves[0]
    best_eval = -float('inf')
    alpha, beta = -float('inf'), float('inf')
    
    for move in valid_moves:
        new_board = copy.deepcopy(board)
        r = 5
        while r >= 0 and new_board[r][move] != 0:
            r -= 1
        new_board[r][move] = 1
        current_eval = minimax(new_board, 4, -float('inf'), float('inf'), False)
        if current_eval > best_eval:
            best_eval = current_eval
            best_col = move
        if best_eval >= beta:
            break  # Alpha-beta pruning
        alpha = max(alpha, current_eval)
    
    return best_col

def check_win(board):
    # Check all horizontal lines
    for r in range(6):
        for c in range(4):
            if board[r][c] != 0 and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                return board[r][c]
    # Check all vertical lines
    for c in range(7):
        for r in range(3):
            if board[r][c] != 0 and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                return board[r][c]
    # Check diagonal down-right
    for r in range(3):
        for c in range(4):
            if board[r][c] != 0 and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                return board[r][c]
    # Check diagonal down-left
    for r in range(3):
        for c in range(3, 7):
            if board[r][c] != 0 and board[r][c] == board[r+1][c-1] == board[r+2][c-2] == board[r+3][c-3]:
                return board[r][c]
    return 0

def apply_move(board, col, player):
    new_board = [row.copy() for row in board]
    for r in reversed(range(6)):
        if new_board[r][col] == 0:
            new_board[r][col] = player
            return new_board
    return new_board  # Column is full, but should not happen here

def evaluate(board):
    score = 0
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    
    for dr, dc in directions:
        for r in range(6):
            for c in range(7):
                if dr == 1 and dc == 0:  # Vertical
                    if r > 3:
                        continue
                elif dr == 1 and dc == 1:  # Down-right diagonal
                    if r > 2 or c > 3:
                        continue
                elif dr == 1 and dc == -1:  # Down-left diagonal
                    if r > 2 or c < 3:
                        continue
                # Collect cells in the line
                line = []
                valid = True
                for i in range(4):
                    nr, nc = r + dr*i, c + dc*i
                    if nr < 0 or nr >= 6 or nc < 0 or nc >= 7:
                        valid = False
                        break
                if not valid:
                    continue
                for i in range(4):
                    line.append(board[r + dr*i][c + dc*i])
                my = line.count(1)
                opp = line.count(-1)
                empty = 4 - my - opp
                
                # Evaluate the line
                if my == 3:
                    if empty == 1:
                        score += 3
                elif my == 2:
                    if opp < 1 and empty in (2, 3):
                        score += 1
                elif my == 1 and opp == 0 and empty >= 3:
                    score += 0.5
                
                if opp == 3 and empty >= 1:
                    score -= 3
                elif opp == 2 and empty >= 1:
                    score -= 1
                elif opp == 1 and empty >= 2:
                    score -= 0.2
    
    # Bonus for position in the middle columns
    for c in range(7):
        for r in range(6):
            if board[r][c] == 1:
                score += 1 if r >= 2 else 0.5
    
    return score

def minimax(board, depth, alpha, beta, is_max):
    winner = check_win(board)
    if winner == 1:
        return 1000000  # AI wins
    if winner == -1:
        return -1000000  # Opponent wins
    
    valid_moves = [c for c in range(7) if board[0][c] == 0]
    if not valid_moves:
        return 0  # Draw
    
    if depth == 0:
        return evaluate(board)
    
    if is_max:
        best_val = -float('inf')
        for move in valid_moves:
            new_board = copy.deepcopy(board)
            apply_move(new_board, move, 1)
            current_eval = minimax(new_board, depth - 1, alpha, beta, False)
            best_val = max(best_val, current_eval)
            alpha = max(alpha, current_eval)
            if alpha >= beta:
                break
        return best_val
    else:
        best_val = float('inf')
        for move in valid_moves:
            new_board = copy.deepcopy(board)
            apply_move(new_board, move, -1)
            current_eval = minimax(new_board, depth - 1, alpha, beta, True)
            best_val = min(best_val, current_eval)
            beta = min(beta, current_eval)
            if alpha >= beta:
                break
        return best_val

# Sample usage (for testing purposes)
if __name__ == "__main__":
    board = [[0 for _ in range(7)] for _ in range(6)]
    print(policy(board))  # Example output: best column move
