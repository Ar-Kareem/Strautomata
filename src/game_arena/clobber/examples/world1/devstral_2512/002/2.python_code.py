
import random

def policy(you: list[int], opponent: list[int]) -> str:
    # Directions: Up, Right, Down, Left
    directions = [('U', -1, 0), ('R', 0, 1), ('D', 1, 0), ('L', 0, -1)]
    legal_moves = []

    # Iterate over each cell on the board
    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:
                for dir_name, dr, dc in directions:
                    new_row, new_col = row + dr, col + dc
                    # Check if the new position is within bounds and contains an opponent's piece
                    if 0 <= new_row < 5 and 0 <= new_col < 6 and opponent[new_row][new_col] == 1:
                        legal_moves.append((row, col, dir_name))

    if not legal_moves:
        # If no legal moves, return a dummy move (though this should not happen as per game rules)
        return "0,0,U"

    # Prioritize moves that are closer to the center
    center_row, center_col = 2, 2.5  # Center of the 5x6 grid
    def distance_to_center(row, col):
        return abs(row - center_row) + abs(col - center_col)

    # Sort moves by distance to center (ascending) and then randomly
    legal_moves.sort(key=lambda move: distance_to_center(move[0], move[1]))
    best_moves = [move for move in legal_moves if distance_to_center(move[0], move[1]) == distance_to_center(legal_moves[0][0], legal_moves[0][1])]

    # Randomly select among the best moves
    selected_move = random.choice(best_moves)
    return f"{selected_move[0]},{selected_move[1]},{selected_move[2]}"
