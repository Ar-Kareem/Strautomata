
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Othello policy that prioritizes corners, edges, and maximizing flips.
    """
    board = np.zeros((8, 8), dtype=int)
    board[you == 1] = 1
    board[opponent == 1] = -1

    def get_legal_moves(board, player):
        """
        Find all legal moves for the given player on the board.
        """
        moves = []
        for r in range(8):
            for c in range(8):
                if board[r][c] == 0:
                    if is_legal_move(board, r, c, player):
                        moves.append((r, c))
        return moves

    def is_legal_move(board, row, col, player):
        """
        Check if placing a disc at (row, col) is a legal move for the player.
        """
        if board[row][col] != 0:
            return False

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue

                r, c = row + dr, col + dc
                if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == -player:
                    r += dr
                    c += dc
                    while 0 <= r < 8 and 0 <= c < 8:
                        if board[r][c] == 0:
                            break
                        if board[r][c] == player:
                            return True
                        r += dr
                        c += dc

        return False

    def flip_discs(board, row, col, player):
        """
        Flip the opponent's discs that are captured by placing a disc at (row, col).
        """
        flipped = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue

                r, c = row + dr, col + dc
                to_flip = []
                while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == -player:
                    to_flip.append((r, c))
                    r += dr
                    c += dc

                if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == player and to_flip:
                    flipped.extend(to_flip)

        return flipped

    def calculate_move_value(board, row, col, player):
          """Calculates a value for a potential move based on number of flips as well as positioning"""
          num_flips = len(flip_discs(board.copy(), row, col, player))

          positional_value = 0

          #Prioritze corner
          if (row == 0 and col == 0) or (row == 0 and col == 7) or (row == 7 and col == 0) or (row == 7 and col == 7):
            positional_value += 10

          #Prioritize edge
          elif row == 0 or row == 7 or col == 0 or col == 7:
            positional_value +=5
          
          return num_flips + positional_value
    def simulate_move(board, row, col, player):
      """Simulates a move and returns the resulting board."""
      new_board = board.copy()
      new_board[row, col] = player
      flipped = flip_discs(new_board, row, col, player)
      for r, c in flipped:
          new_board[r, c] = player
      return new_board
    
    def minimize_opponent_moves(board, row, col, player):
      """After making move at row, col, simulate this and return the number of opponent moves available"""
      new_board = simulate_move(board, row, col, player)
      opponent_moves = get_legal_moves(new_board, -player)
      return len(opponent_moves)


    legal_moves = get_legal_moves(board, 1)

    if not legal_moves:
        return "pass"

    best_move = None
    best_value = -1
    min_opponent_moves = float('inf')

    for row, col in legal_moves:
      move_value = calculate_move_value(board, row, col, 1)
      opponent_moves_after = minimize_opponent_moves(board, row, col, 1)

      if move_value > best_value:
        best_value = move_value
        best_move = (row, col)
        min_opponent_moves = opponent_moves_after
      elif move_value == best_value and opponent_moves_after < min_opponent_moves:
        best_move = (row, col)
        min_opponent_moves = opponent_moves_after

    if best_move is None:
        return "pass"
    else:
        row, col = best_move
        return chr(ord('a') + col) + str(row + 1)
