
import random

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    """
    A Phantom Tic Tac Toe policy that prioritizes winning, blocking,
    and strategic moves while avoiding confirmed placements.
    """

    def to_row_col(move: int) -> tuple[int, int]:
        return move // 3, move % 3

    def to_move_num(row: int, col: int) -> int:
        return row * 3 + col
    
    def check_win(board_state, player):
        """Checks if a player has won."""
        for row in range(3):
            if all(board_state[row][col] == player for col in range(3)):
                return True
        for col in range(3):
            if all(board_state[row][col] == player for row in range(3)):
                return True
        if all(board_state[i][i] == player for i in range(3)):
            return True
        if all(board_state[i][2 - i] == player for i in range(3)):
            return True
        return False

    # 1. Win Check
    for move in legal_moves:
        row, col = to_row_col(move)
        temp_board = [row[:] for row in board]  # Create a copy
        temp_board[row][col] = 1  # Simulate placing the mark
        if check_win(temp_board, 1):
            return move

    # 2. Block Check (Hypothetical opponent move)
    for move in legal_moves:
        row, col = to_row_col(move)
        temp_board = [row[:] for row in board]  # Create a copy
        temp_board[row][col] = -1 # Simulate the opponent moving here
        
        #create hypothetical board which is the inverse of the current board to find opponent wins
        transformed_board = [[0]*3 for _ in range(3)]
        for i in range(3):
          for j in range(3):
            if board[i][j] == 1:
              transformed_board[i][j] = 0    # opponent cant move here
            else:
              transformed_board[i][j] = 1    # empty or opponent moved here
        transformed_board[row][col] = 1

        if check_win(transformed_board, 1): # if opponent wins, block it by returning the initial move
            return move

    # 3. Center Preference
    center_move = 4
    if center_move in legal_moves and board[1][1] != 1:
        return center_move

    # 4. Corner Preference
    corners = [0, 2, 6, 8]
    available_corners = [move for move in corners if move in legal_moves and board[to_row_col(move)[0]][to_row_col(move)[1]] != 1]
    if available_corners:
        return random.choice(available_corners)

    # 5. Edge Preference
    edges = [1, 3, 5, 7]
    available_edges = [move for move in edges if move in legal_moves and board[to_row_col(move)[0]][to_row_col(move)[1]] != 1]
    if available_edges:
        return random.choice(available_edges)

    # 6. Avoid Confirmed Moves, prioritize unconfirmed
    unconfirmed_moves = [move for move in legal_moves if board[to_row_col(move)[0]][to_row_col(move)[1]] != 1]
    if unconfirmed_moves:
        return random.choice(unconfirmed_moves)

    # 7. Random Legal Move (Fallback)
    return random.choice(legal_moves)
