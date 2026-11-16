
import numpy as np

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    """
    A Tic Tac Toe policy that prioritizes winning, blocking, and maximizing potential winning lines.
    """
    board = np.array(board)

    def check_win(board):
        """Checks if the given board has a winner (1)."""
        for i in range(3):
            if board[i, 0] == board[i, 1] == board[i, 2] == 1:
                return True
            if board[0, i] == board[1, i] == board[2, i] == 1:
                return True
        if board[0, 0] == board[1, 1] == board[2, 2] == 1:
            return True
        if board[0, 2] == board[1, 1] == board[2, 0] == 1:
            return True
        return False

    def check_block(board):
        """Checks if the opponent has a winning move, assuming 0 can be opponent's mark and attempts to block"""
        for i in range(3):
            for j in range(3):
                if board[i,j] == 1:
                    continue
                temp_board = np.copy(board)
                temp_board[i, j] = -1 # Simulate opponent making a play. -1 will represent the opponent
                
                #Convert to 1's or 0's for the winning scenarios.
                temp_board[temp_board == -1] = 1
                temp_board[temp_board == 0] = 0
                
                if check_win(temp_board): 
                    return i * 3 + j
        return -1
            

    def calculate_potential(board, move):
        """Calculates the number of potential winning lines for a given move."""
        row = move // 3
        col = move % 3
        potential = 0
        temp_board = np.copy(board)
        temp_board[row, col] = 1

        # Check rows
        if np.sum(temp_board[row, :] == 1) > 0:
            potential += 1

        # Check columns
        if np.sum(temp_board[:, col] == 1) > 0:
            potential += 1

        # Check diagonals
        if row == col and np.sum(np.diag(temp_board) == 1) > 0:
            potential += 1
        if row + col == 2 and np.sum(np.diag(np.fliplr(temp_board)) == 1) > 0:
            potential += 1

        return potential

    # 1. Check for winning move
    for move in legal_moves:
        row = move // 3
        col = move % 3
        temp_board = np.copy(board)
        temp_board[row, col] = 1
        if check_win(temp_board):
            return move
    
    # 2. Check for blocking move
    blocking_move = -1
    temp_board = np.copy(board)
    for i in range(3):
        for j in range(3):
            if temp_board[i,j] == 1:
                temp_board[i,j] = 0

    blocking_move = check_block(temp_board)
    if blocking_move != -1 and blocking_move in legal_moves:
        return blocking_move

    # 3. Maximize potential winning lines
    best_move = -1
    max_potential = -1
    for move in legal_moves:
        potential = calculate_potential(board, move)
        if potential > max_potential:
            max_potential = potential
            best_move = move

    if best_move != -1:
        return best_move

    # 4. Default: pick the first available legal move
    return legal_moves[0]
