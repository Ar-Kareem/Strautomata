
import random

def policy(board: list[list[int]]) -> int:
    """
    A Connect 4 policy that attempts to win, block opponent wins, and then chooses randomly.
    """
    def check_win(board, player):
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if (board[row][col] == player and
                    board[row][col+1] == player and
                    board[row][col+2] == player and
                    board[row][col+3] == player):
                    return True

        # Check vertical
        for row in range(3):
            for col in range(7):
                if (board[row][col] == player and
                    board[row+1][col] == player and
                    board[row+2][col] == player and
                    board[row+3][col] == player):
                    return True

        # Check positive diagonal
        for row in range(3):
            for col in range(4):
                if (board[row][col] == player and
                    board[row+1][col+1] == player and
                    board[row+2][col+2] == player and
                    board[row+3][col+3] == player):
                    return True

        # Check negative diagonal
        for row in range(3):
            for col in range(3, 7):
                if (board[row][col] == player and
                    board[row+1][col-1] == player and
                    board[row+2][col-2] == player and
                    board[row+3][col-3] == player):
                    return True
        return False

    def get_possible_moves(board):
        possible_moves = []
        for col in range(7):
            if board[0][col] == 0:
                possible_moves.append(col)
        return possible_moves
    
    def apply_move(board, col, player):
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                board[row][col] = player
                return board #Modified board inline!
        return board #If column is full, this should never happen due to previous checks.


    # 1. Check if there's a winning move
    possible_moves = get_possible_moves(board)
    for col in possible_moves:
        temp_board = [row[:] for row in board] #create a DEEP copy of the board.
        
        temp_board = apply_move(temp_board, col, 1)
        if check_win(temp_board, 1):
            return col

    # 2. Check if the opponent has a winning move, and block it
    for col in possible_moves:
        temp_board = [row[:] for row in board] #create a DEEP copy of the board.
        temp_board = apply_move(temp_board, col, -1)
        if check_win(temp_board, -1):
            return col

    # 3. If no winning or blocking move, choose a random valid move
    return random.choice(possible_moves)
