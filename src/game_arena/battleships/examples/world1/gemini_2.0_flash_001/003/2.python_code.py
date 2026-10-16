
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    A Battleship policy that combines hunting and targeting strategies.
    """
    n = 10
    board_np = np.array(board)

    def get_valid_moves(board_np):
        """Returns a list of valid moves (cells with value 0)."""
        valid_moves = np.argwhere(board_np == 0)
        return valid_moves.tolist()

    def calculate_probability_map(board_np):
        """Calculates a probability map for ship placement."""
        probability_map = np.zeros((n, n))
        ship_lengths = [5, 4, 3, 3, 2]

        for length in ship_lengths:
            for row in range(n):
                for col in range(n - length + 1):
                    valid = True
                    for k in range(length):
                        if board_np[row, col + k] != 0:
                            valid = False
                            break
                    if valid:
                        for k in range(length):
                            probability_map[row, col + k] += 1

            for col in range(n):
                for row in range(n - length + 1):
                    valid = True
                    for k in range(length):
                        if board_np[row + k, col] != 0:
                            valid = False
                            break
                    if valid:
                        for k in range(length):
                            probability_map[row + k, col] += 1
        return probability_map

    def targeting(board_np):

        """Targeting strategy: explore adjacent cells to hits."""
        hit_cells = np.argwhere(board_np == 1)

        if len(hit_cells) > 0:
            # Prioritize cells around the last hit
            last_row, last_col = hit_cells[-1]

            neighbors = [(last_row - 1, last_col), (last_row + 1, last_col),
                         (last_row, last_col - 1), (last_row, last_col + 1)]

            valid_neighbors = [(r, c) for r, c in neighbors if 0 <= r < n and 0 <= c < n and board_np[r, c] == 0]

            if valid_neighbors:
                return valid_neighbors[0]  # Return the first valid neighbor

            #If all neighbors are explored, check surrounding hit cells.
            for row, col in hit_cells:
                neighbors = [(row - 1, col), (row + 1, col),
                             (row, col - 1), (row, col + 1)]
                valid_neighbors = [(r, c) for r, c in neighbors if 0 <= r < n and 0 <= c < n and board_np[r, c] == 0]

                if valid_neighbors:
                    return valid_neighbors[0]  #Return the first valid neighbor


        return None # No hit cells, return None

    # First, try targeting if there are any hits
    target_move = targeting(board_np)
    if target_move:
        return target_move

    # If no hits, use the probability map to hunt
    probability_map = calculate_probability_map(board_np)

    # Find the cell with the highest probability among valid moves
    valid_moves = get_valid_moves(board_np)

    if not valid_moves:
      # If no valid moves, return a random valid move (should not happen, but prevents crashes)
      return (0,0)

    best_move = valid_moves[0]
    max_probability = probability_map[best_move[0], best_move[1]]

    for row, col in valid_moves:
        if probability_map[row, col] > max_probability:
            max_probability = probability_map[row, col]
            best_move = (row, col)

    return (best_move[0], best_move[1])
