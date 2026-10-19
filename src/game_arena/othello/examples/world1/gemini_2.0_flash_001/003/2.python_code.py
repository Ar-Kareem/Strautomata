
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Othello (Reversi) policy function.

    Args:
        you: A numpy array representing your discs on the board (1 for disc, 0 for empty).
        opponent: A numpy array representing the opponent's discs on the board (1 for disc, 0 for empty).

    Returns:
        A string representing the next move in algebraic notation (e.g., "d3") or "pass" if no legal moves exist.
    """

    def get_legal_moves(board, player, opponent):
        """Finds all legal moves for the given player on the board."""
        moves = []
        for r in range(8):
            for c in range(8):
                if board[r][c] == 0:
                    if is_valid_move(board, player, opponent, r, c):
                        moves.append((r, c))
        return moves

    def is_valid_move(board, player, opponent, row, col):
        """Checks if a move is valid."""
        if board[row][col] != 0:
            return False

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == opponent[r][c]:
                while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == opponent[r][c]:
                    r += dr
                    c += dc
                if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == player[r][c]:
                    return True
        return False

    def flip_discs(board, player, opponent, row, col):
        """Flips the discs after a valid move."""
        flipped = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            to_flip = []
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == opponent[r][c]:
                to_flip.append((r, c))
                r += dr
                c += dc
            if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == player[r][c]:
                flipped.extend(to_flip)
        return flipped


    def get_board_representation(you, opponent):
        board = np.zeros((8, 8), dtype=int)
        board[you == 1] = 1
        board[opponent == 1] = -1
        return board

    board = get_board_representation(you, opponent)
    legal_moves = get_legal_moves(board, you, opponent)

    if not legal_moves:
        return "pass"
    
    def evaluate_move(row, col, board, player, opponent):
        """Evaluates the quality of a move."""
        
        valuation = 0
        
        # Corner priority
        if (row == 0 and col == 0) or (row == 0 and col == 7) or (row == 7 and col == 0) or (row == 7 and col == 7):
            valuation += 100
        # Edge priority
        elif row == 0 or row == 7 or col == 0 or col == 7:
            valuation += 10
            
        # Count how many pieces this move will flip instantly
        valuation += len(flip_discs(board, player, opponent, row, col)) * 5

       # Create a copy of the board
        temp_board = board.copy()
        temp_you = you.copy()
        temp_opponent = opponent.copy()

        # Apply the move to this temporary board
        temp_board[row, col] = 1    

        flipped = flip_discs(temp_board, you, opponent, row, col)

        for r, c in flipped:
            temp_board[r, c] = 1  # Change the value to 1 (your disc color)
            # Flip the discs on the temp numpy boards too
            temp_you[r, c] = 1
            temp_opponent[r, c] = 0
            
        # Update the original move on the board too
        temp_you[row, col] = 1

        # Evaluate the opponent's potential moves after this move
        opponent_legal_moves = get_legal_moves(temp_board, opponent, you)
        valuation -= len(opponent_legal_moves) * 2 # Give a penality so the opponent wouldn't get much moves

        your_legal_moves = get_legal_moves(temp_board, you, opponent)
        valuation += len(your_legal_moves) # Reward it so you would get more moves
            
        return valuation

    best_move = None
    best_score = float('-inf')

    for row, col in legal_moves:
        score = evaluate_move(row, col, board, you, opponent)
        if score > best_score:
            best_score = score
            best_move = (row, col)

    if best_move is None:
        return "pass"

    row, col = best_move
    return chr(ord('a') + col) + str(row + 1)
