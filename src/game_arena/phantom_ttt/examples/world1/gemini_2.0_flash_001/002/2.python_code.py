
import random

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    """
    A smart policy for Phantom Tic Tac Toe.

    Args:
        board: A 3x3 list of lists representing the game board.
               1 indicates a cell confirmed to be yours.
               0 indicates a cell that is not confirmed to be yours.
        legal_moves: A list of integers in 0-8 representing allowed actions.

    Returns:
        An integer in 0-8 representing the chosen move.
    """

    def to_row_col(move):
        return move // 3, move % 3

    def check_win(board, player):
        """Check for a win for the given player."""
        for i in range(3):
            if all(board[i][j] >= 0 for j in range(3)) and sum(board[i][j] for j in range(3)) == player * 3:  # Row
                return True
            if all(board[j][i] >= 0 for j in range(3)) and sum(board[j][i] for j in range(3)) == player * 3:  # Col
                return True
        if all(board[i][i] >= 0 for i in range(3)) and sum(board[i][i] for i in range(3)) == player * 3:  # Diagonal
            return True
        if all(board[i][2 - i] >= 0 for i in range(3)) and sum(board[i][2 - i] for i in range(3)) == player * 3:  # Anti-diagonal
            return True
        return False

    def find_winning_move(board, legal_moves, player):
        """Find a winning move for the given player."""
        for move in legal_moves:
            r, c = to_row_col(move)
            temp_board = [row[:] for row in board]  # Create a copy
            temp_board[r][c] = 1 if player == 1 else -1  # Assume we can place our move
            if check_win(temp_board, player):
                return move
        return None

    def find_blocking_move(board, legal_moves):
        """Find a move to block the opponent from winning (assuming opponent is -1)."""
        # Since we only have partial information, we can only attempt to block sequences where all cells are
        # confirmed free for us to place using policy.
        for move in legal_moves:
            r, c = to_row_col(move)
            temp_board = [row[:] for row in board]
            temp_board[r][c] = -1  # Simulate opponent's move
            if check_win(temp_board, -1):

                # Check cells in the potentially winning row/col/diag. They must not be confirmed ours.
                possible = True

                
                if possible:
                    return move
        return None

    # 1. Check for winning move
    winning_move = find_winning_move(board, legal_moves, 1)
    if winning_move is not None:
        return winning_move

    # 2. Check for blocking move
    blocking_move = find_blocking_move(board, legal_moves)
    if blocking_move is not None:
        return blocking_move


    # 3. Play strategically (center, edges, corners)
    if 4 in legal_moves and board[1][1] == 0:
        return 4  # Center

    edge_moves = [1, 3, 5, 7]
    available_edges = [move for move in edge_moves if move in legal_moves and to_row_col(move) != (1,1) and board[to_row_col(move)[0]][to_row_col(move)[1]] == 0]

    if available_edges:
        return random.choice(available_edges)  # Edges

    corner_moves = [0, 2, 6, 8]
    available_corners = [move for move in corner_moves if move in legal_moves and board[to_row_col(move)[0]][to_row_col(move)[1]] == 0]
    if available_corners:
        return random.choice(available_corners)  # Corners

    # 4. If all else fails, pick a random legal move
    return random.choice(legal_moves)
