
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Othello policy function.

    Args:
        you: 8x8 numpy array representing your discs.
        opponent: 8x8 numpy array representing opponent's discs.

    Returns:
        A string representing the next move in algebraic notation (e.g., "d3") or "pass".
    """

    def get_legal_moves(board, player, opponent):
        """
        Find all legal moves for the given player.
        """
        moves = []
        for r in range(8):
            for c in range(8):
                if board[r, c] == 0:
                    if is_legal_move(board, player, opponent, r, c):
                        moves.append((r, c))
        return moves

    def is_legal_move(board, player, opponent, row, col):
        """
        Check if a move is legal.
        """
        if board[row, col] != 0:
            return False

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if 0 <= r < 8 and 0 <= c < 8 and opponent[r, c] == 1:
                    r += dr
                    c += dc
                    while 0 <= r < 8 and 0 <= c < 8:
                        if player[r, c] == 1:
                            return True
                        elif opponent[r, c] == 0:
                            break
                        r += dr
                        c += dc
        return False

    def flip_discs(board, player, opponent, row, col):
        """
        Flip the discs after a valid move.
        """
        flipped = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                to_flip = []
                while 0 <= r < 8 and 0 <= c < 8 and opponent[r, c] == 1:
                    to_flip.append((r, c))
                    r += dr
                    c += dc
                if 0 <= r < 8 and 0 <= c < 8 and player[r, c] == 1:
                    flipped.extend(to_flip)
        return flipped

    def evaluate_move(row, col, flipped_discs):
      """
      Evaluate a move based on its strategic value.
      """
      score = len(flipped_discs)

      # Prioritize corners
      if (row == 0 or row == 7) and (col == 0 or col == 7):
          score += 100

      # Prioritize edges
      elif row == 0 or row == 7 or col == 0 or col == 7:
        score += 10

      return score

    board = np.zeros((8, 8), dtype=int)
    board[you == 1] = 1
    board[opponent == 1] = -1

    legal_moves = get_legal_moves(board, you, opponent)

    if not legal_moves:
        return "pass"

    best_move = None
    best_score = -1

    for row, col in legal_moves:
        flipped = flip_discs(board, you, opponent, row, col)
        score = evaluate_move(row, col, flipped)

        if score > best_score:
            best_score = score
            best_move = (row, col)

    if best_move is None:
      #Fallback to return first available move if evaluation fails
      row, col = legal_moves[0]
    else:
      row, col = best_move

    return chr(ord('a') + col) + str(row + 1)
