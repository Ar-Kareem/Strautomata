
import copy

def is_win(board, player):
    # Check rows
    for i in range(4):
        if all(board[i][j] == player for j in range(4)):
            return True
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    # Check diagonals
    if all(board[k][k] == player for k in range(4)):
        return True
    if all(board[k][3-k] == player for k in range(4)):
        return True
    return False

def policy(board):
    possible_moves = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    valid_moves = []
    for r, c in possible_moves:
        temp_board = copy.deepcopy(board)
        temp_board[r][c] = 1
        if not is_win(temp_board, -1):
            valid_moves.append((r, c))
    if valid_moves:
        # Prefer winning moves
        for move in valid_moves:
            temp_board = copy.deepcopy(board)
            temp_board[move[0]][move[1]] = 1
            if is_win(temp_board, 1):
                return move
        # Otherwise, return the first valid move
        return valid_moves[0]
    else:
        # No valid moves, opponent might win; return the first possible move
        return possible_moves[0]
