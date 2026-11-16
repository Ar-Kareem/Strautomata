
import sys

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determine the best move for the AI in Tic Tac Toe using minimax algorithm with alpha-beta pruning.
    
    Args:
        board: A 3x3 list of lists with 0 (empty), 1 (AI), and -1 (opponent).
    
    Returns:
        A tuple (row, col) representing the move to make.
    """
    
    # Convert board to a hashable tuple for memoization
    def board_to_tuple(board):
        return tuple(tuple(row) for row in board)
    
    # Create a new board after making a move
    def make_new_board(board, move, player):
        new_board = [row[:] for row in board]  # Deep copy of the board
        new_board[move[0]][move[1]] = player
        return new_board
    
    # Get all possible moves from the board
    def get_moves(board):
        moves = []
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    moves.append((i, j))
        return moves
    
    # Evaluate the board state: return score if terminal, else None
    def evaluate(board):
        # Check rows and columns for wins
        for i in range(3):
            # Check row i
            if board[i][0] == board[i][1] == board[i][2] == 1:
                return 10
            if board[i][0] == board[i][1] == board[i][2] == -1:
                return -10
            # Check column i
            if board[0][i] == board[1][i] == board[2][i] == 1:
                return 10
            if board[0][i] == board[1][i] == board[2][i] == -1:
                return -10
        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] == 1:
            return 10
        if board[0][0] == board[1][1] == board[2][2] == -1:
            return -10
        if board[0][2] == board[1][1] == board[2][0] == 1:
            return 10
        if board[0][2] == board[1][1] == board[2][0] == -1:
            return -10
        # Check for draw
        if all(cell != 0 for row in board for cell in row):
            return 0
        # Game not over
        return None
    
    # Memoization dictionary to cache results
    memo = {}
    
    # Minimax function with memoization
    def minimax(board, player):
        key = (board_to_tuple(board), player)
        if key in memo:
            return memo[key]
        
        score = evaluate(board)
        if score is not None:
            memo[key] = score
            return score
        
        moves = get_moves(board)
        if not moves:
            memo[key] = 0  # Should not happen, but safe
            return 0
        
        if player == 1:
            best_score = -10**9
            for move in moves:
                new_board = make_new_board(board, move, player)
                s = minimax(new_board, -player)
                if s > best_score:
                    best_score = s
            memo[key] = best_score
            return best_score
        else:
            best_score = 10**9
            for move in moves:
                new_board = make_new_board(board, move, player)
                s = minimax(new_board, 1)
                if s < best_score:
                    best_score = s
            memo[key] = best_score
            return best_score
    
    # Find the best move for the AI
    moves = get_moves(board)
    if not moves:
        return (0, 0)  # Should not happen if board is valid
    
    best_move = None
    best_score = -10**9
    for move in moves:
        new_board = make_new_board(board, move, 1)
        score = minimax(new_board, -1)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
