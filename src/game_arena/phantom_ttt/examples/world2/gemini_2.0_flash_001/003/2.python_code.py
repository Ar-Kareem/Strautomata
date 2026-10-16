
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    A Tic Tac Toe policy that attempts to win, block, and then chooses strategically.
    """

    def check_win(board):
        """Checks if the board has a winning condition."""
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] == 1:
                return True
            if board[0][i] == board[1][i] == board[2][i] == 1:
                return True
        if board[0][0] == board[1][1] == board[2][2] == 1:
            return True
        if board[0][2] == board[1][1] == board[2][0] == 1:
            return True
        return False

    def get_possible_moves(board):
        """Returns a list of possible moves (row, col)."""
        moves = []
        for row in range(3):
            for col in range(3):
                if board[row][col] == 0:  # Only consider unknown cells
                    moves.append((row, col))
        return moves

    # 1. Check for winning move
    possible_moves = get_possible_moves(board)
    for row, col in possible_moves:
        temp_board = [row[:] for row in board]  # Create a copy
        temp_board[row][col] = 1
        if check_win(temp_board):
            return (row, col)

    # 2. Check for opponent's potential win and block (considering zeros as opponent's)
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                 board[row][col] = -1 # Assume the zero values are opponent's for blocking purposes.
    
    def check_loss(board):
        """Checks if the board has a losing condition for our agent, where opponent has three in a row"""
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] == -1:
                return True
            if board[0][i] == board[1][i] == board[2][i] == -1:
                return True
        if board[0][0] == board[1][1] == board[2][2] == -1:
            return True
        if board[0][2] == board[1][1] == board[2][0] == -1:
            return True
        return False
    
    possible_moves = get_possible_moves(board)
    for row, col in possible_moves:
            temp_board = [r[:] for r in board]
            temp_board[row][col] = 1
            for r in range(3):
                for c in range(3):
                    if temp_board[r][c] == 0:
                        temp_board[r][c] = -1
            
            if check_loss(temp_board):
                for r in range(3):
                    for c in range(3):
                        if board[r][c] == -1:
                            board[r][c] = 0 # Restore original board state
                return (row, col)

            for r in range(3):
                for c in range(3):
                    if board[r][c] == -1:
                        board[r][c] = 0 # Restore original board state


    # Restore board
    for row in range(3):
        for col in range(3):
            if board[row][col] == -1:
                 board[row][col] = 0

    # 3. Center Preference
    if board[1][1] == 0:
        return (1, 1)

    # 4. Corner Preference
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [corner for corner in corners if board[corner[0]][corner[1]] == 0]
    if available_corners:
        return random.choice(available_corners)

    # 5. Edge Preference
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    available_edges = [edge for edge in edges if board[edge[0]][edge[1]] == 0]
    if available_edges:
        return random.choice(available_edges)

    # 6. Fallback: Random available cell
    available_cells = []
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0 or board[row][col] != 1:
                available_cells.append((row, col))

    if available_cells:
        return random.choice(available_cells)

    # 7. If somehow no moves are available: Return (0,0) to avoid issues.
    return (0, 0)
