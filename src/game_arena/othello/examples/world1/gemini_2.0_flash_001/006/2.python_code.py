
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Determines the next move for an Othello game.

    Args:
        you: A numpy array representing the current player's discs.
        opponent: A numpy array representing the opponent's discs.

    Returns:
        A string representing the next move in algebraic notation (e.g., "d3") 
        or "pass" if no legal moves are available.
    """

    def is_valid_move(row, col, you, opponent):
        if you[row][col] == 1 or opponent[row][col] == 1:
            return False

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue

                r, c = row + dr, col + dc
                if 0 <= r < 8 and 0 <= c < 8 and opponent[r][c] == 1:
                    r += dr
                    c += dc
                    while 0 <= r < 8 and 0 <= c < 8:
                        if you[r][c] == 1:
                            return True
                        elif opponent[r][c] == 0:
                            break
                        r += dr
                        c += dc
        return False

    def get_flips(row, col, you, opponent):
        flips = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue

                r, c = row + dr, col + dc
                to_flip = []
                if 0 <= r < 8 and 0 <= c < 8 and opponent[r][c] == 1:
                    to_flip.append((r,c))
                    r += dr
                    c += dc
                    while 0 <= r < 8 and 0 <= c < 8:
                        if you[r][c] == 1:
                            flips.extend(to_flip)
                            break
                        elif opponent[r][c] == 0:
                            break
                        else:
                            to_flip.append((r,c))
                        r += dr
                        c += dc
        return flips

    def get_legal_moves(you, opponent):
        moves = []
        for row in range(8):
            for col in range(8):
                if is_valid_move(row, col, you, opponent):
                    moves.append((row, col))
        return moves
    
    def calculate_mobility(you, opponent):
        temp_you = np.copy(opponent)
        temp_opponent = np.copy(you)
        return len(get_legal_moves(temp_you, temp_opponent))

    legal_moves = get_legal_moves(you, opponent)

    if not legal_moves:
        return "pass"
    
    # 1. Corner Prioritization
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    for corner in corners:
        if corner in legal_moves:
            row, col = corner
            return chr(ord('a') + col) + str(row + 1)

    # 2. Immediate Loss Prevention
    best_move = None
    min_opponent_moves = 65
    for row, col in legal_moves:
        
        temp_you = np.copy(you)
        temp_opponent = np.copy(opponent)
        flips = get_flips(row, col, you, opponent)
        temp_you[row, col] = 1
        for r, c in flips:
            temp_you[r, c] = 1
            temp_opponent[r, c] = 0

        opponent_moves = calculate_mobility(temp_you, temp_opponent)
        
        if opponent_moves < min_opponent_moves:
          min_opponent_moves = opponent_moves
          best_move = (row, col)


    if best_move is not None:
      row, col = best_move
      return chr(ord('a') + col) + str(row + 1)
