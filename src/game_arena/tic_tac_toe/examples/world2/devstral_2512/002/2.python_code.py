
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Helper function to check if a move is valid
    def is_valid_move(row, col):
        return 0 <= row < 4 and 0 <= col < 4 and board[row][col] == 0

    # Helper function to check if a player has won
    def check_win(player):
        # Check rows
        for row in range(4):
            if all(cell == player for cell in board[row]):
                return True
        # Check columns
        for col in range(4):
            if all(board[row][col] == player for row in range(4)):
                return True
        # Check diagonals
        if all(board[i][i] == player for i in range(4)):
            return True
        if all(board[i][3-i] == player for i in range(4)):
            return True
        return False

    # Helper function to evaluate potential winning lines for a move
    def evaluate_move(row, col, player):
        score = 0
        # Check row
        row_count = sum(1 for c in range(4) if board[row][c] == player)
        if row_count == 3 and sum(1 for c in range(4) if board[row][c] == 0) == 1:
            score += 10
        # Check column
        col_count = sum(1 for r in range(4) if board[r][col] == player)
        if col_count == 3 and sum(1 for r in range(4) if board[r][col] == 0) == 1:
            score += 10
        # Check main diagonal
        if row == col:
            diag_count = sum(1 for i in range(4) if board[i][i] == player)
            if diag_count == 3 and sum(1 for i in range(4) if board[i][i] == 0) == 1:
                score += 10
        # Check anti-diagonal
        if row + col == 3:
            anti_diag_count = sum(1 for i in range(4) if board[i][3-i] == player)
            if anti_diag_count == 3 and sum(1 for i in range(4) if board[i][3-i] == 0) == 1:
                score += 10
        return score

    # Generate all valid moves
    valid_moves = [(r, c) for r in range(4) for c in range(4) if is_valid_move(r, c)]

    # First, check for immediate winning moves
    for move in valid_moves:
        row, col = move
        board[row][col] = 1  # Simulate move
        if check_win(1):
            board[row][col] = 0  # Undo move
            return move
        board[row][col] = 0  # Undo move

    # Then, check for opponent's immediate winning moves to block
    for move in valid_moves:
        row, col = move
        board[row][col] = -1  # Simulate opponent's move
        if check_win(-1):
            board[row][col] = 0  # Undo move
            return move
        board[row][col] = 0  # Undo move

    # If no immediate threats, evaluate moves based on potential
    best_moves = []
    max_score = -1
    for move in valid_moves:
        row, col = move
        score = evaluate_move(row, col, 1)
        if score > max_score:
            max_score = score
            best_moves = [move]
        elif score == max_score:
            best_moves.append(move)

    # If we found good moves, choose one randomly
    if best_moves:
        return random.choice(best_moves)

    # Fallback: choose center or random move
    center_moves = [(1, 1), (1, 2), (2, 1), (2, 2)]
    available_center = [move for move in center_moves if is_valid_move(*move)]
    if available_center:
        return random.choice(available_center)

    # If all else fails, choose a random valid move
    return random.choice(valid_moves)
