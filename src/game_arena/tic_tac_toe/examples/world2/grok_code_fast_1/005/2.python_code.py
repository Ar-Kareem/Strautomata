
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the best move for the player (represented by 1) in a 4x4 Tic Tac Toe game using minimax with alpha-beta pruning.
    """
    def get_empty(board):
        """Returns a list of tuples (i, j) for empty cells."""
        empty = []
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    empty.append((i, j))
        return empty
    
    def place(board, move, player):
        """Returns a new board with the move placed for the given player."""
        new_board = [row[:] for row in board]
        new_board[move[0]][move[1]] = player
        return new_board
    
    def get_lines(board):
        """Yields each possible winning line: rows, columns, main diagonal, anti-diagonal."""
        # Rows
        for i in range(4):
            yield board[i][:]
        # Columns
        for j in range(4):
            yield [board[i][j] for i in range(4)]
        # Main diagonal
        yield [board[i][i] for i in range(4)]
        # Anti-diagonal
        yield [board[i][3 - i] for i in range(4)]
    
    def is_win(board, player):
        """Checks if the player wins by having 4 in a row in any line."""
        for line in get_lines(board):
            if all(cell == player for cell in line):
                return True
        return False
    
    def is_full(board):
        """Checks if the board is full."""
        return all(cell != 0 for row in board for cell in row)
    
    def game_over(board):
        """Returns 1 if 1 wins, -1 if -1 wins, 0 if draw/full, None otherwise."""
        if is_win(board, 1):
            return 1
        if is_win(board, -1):
            return -1
        if is_full(board):
            return 0
        return None
    
    def evaluate(board):
        """Heuristic evaluation: sum rewards/penalties for each winning line's potential."""
        score = 0
        for line in get_lines(board):
            num_my = line.count(1)
            num_op = line.count(-1)
            if num_op == 0:
                score += 2 ** num_my  # Reward player's line potential
            if num_my == 0:
                score -= 2 ** num_op  # Penalize opponent's line potential
        return score
    
    def minimax(board, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        result = game_over(board)
        if result is not None or depth == 0:
            if depth == 0 and result is None:
                return evaluate(board)
            else:
                return result * 1000  # Win/loss/draw values
        if maximizing:
            max_eval = -math.inf
            for move in get_empty(board):
                new_board = place(board, move, 1)
                eval_score = minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for move in get_empty(board):
                new_board = place(board, move, -1)
                eval_score = minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Main logic for policy
    DEPTH = 4  # Depth limit for minimax
    moves = get_empty(board)
    best_score = -math.inf
    best_move = None
    for move in moves:
        new_board = place(board, move, 1)
        score = minimax(new_board, DEPTH, -math.inf, math.inf, False)
        if score > best_score:
            best_score = score
            best_move = move
    return best_move

# Note: The function ensures a legal move is always returned (from get_empty), and the board won't be modified (deep copies used).
