
import numpy as np

def has_win(board, player):
    # Check rows
    for r in range(6):
        for c in range(2):  # 0 and 1 are valid starting columns
            if np.all(board[r, c:c+5] == player):
                return True

    # Check columns
    for c in range(6):
        for r in range(2):  # 0 and 1 are valid starting rows
            if np.all(board[r:r+5, c] == player):
                return True

    # Check main diagonal (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            if np.all(np.diag(board[r:r+5, c:c+5]) == player):
                return True

    # Check anti-diagonal (top-right to bottom-left)
    for r in range(2):
        for c in range(4, 6):  # columns 4 and 5 are valid starting points
            matrix = board[r:r+5, c-4:c+1]
            flipped = np.flip(flip(matrix, axis=1))
            if np.all(np.diag(flipped) == player):
                return True

    return False

def policy(you, opponent):
    you = np.array(you, dtype=int)
    opp = np.array(opponent)
    empty = np.argwhere((you == 0) & (opp == 0))

    if empty.size == 0:
        raise ValueError("No empty cells available")

    # Step 1: Check for immediate win
    for (r, c) in empty:
        for quad in range(4):
            if quad == 0:
                sr, sc = 0, 0
            elif quad == 1:
                sr, sc = 0, 3
            elif quad == 2:
                sr, sc = 3, 0
            else:
                sr, sc = 3, 3

            for direction in ['L', 'R']:
                temp_you = you.copy()
                temp_opp = opp.copy()

                temp_you[r][c] = 1  # Place my marble

                # Extract quadrant content
                quad_you = temp_you[sr:sr+3, sc:sc+3]
                quad_opp = temp_opp[sr:sr+3, sc:sc+3]

                # Rotate quadrant
                if direction == 'R':
                    rotated_you = np.rot90(quad_you, k=-1)
                    rotated_opp = np.rot90(quad_opp, k=-1)
                else:
                    rotated_you = np.rot90(quad_you, k=1)
                    rotated_opp = np.rot90(quad_opp, k=1)

                # Apply rotation to the board
                temp_you[sr:sr+3, sc:sc+3] = rotated_you
                temp_opp[sr:sr+3, sc:sc+3] = rotated_opp

                if has_win(temp_you, 1):
                    return f"{r+1},{c+1},{quad},{direction}"

    # Step 2: If no immediate win, evaluate all moves using a heuristic
    max_score = -np.inf
    best_move = None

    for (r, c) in empty:
        placement_score = 0
        for quad in range(4):
            if quad == 0:
                sr, sc = 0, 0
            elif quad == 1:
                sr, sc = 0, 3
            elif quad == 2:
                sr, sc = 3, 0
            else:
                sr, sc = 3, 3

            for direction in ['R', 'L']:
                temp_you = you.copy()
                temp_opp = opp.copy()
                temp_you[r][c] = 1
                quad_you = temp_you[sr:sr+3, sc:sc+3]
                quad_opp = temp_opp[sr:sr+3, sc:sc+3]

                if direction == 'R':
                    rotated_you = np.rot90(quad_you, k=-1)
                    rotated_opp = np.rot90(quad_opp, k=-1)
                else:
                    rotated_you = np.rot90(quad_you, k=1)
                    rotated_opp = np.rot90(quad_opp, k=1)

                temp_you[sr:sr+3, sc:sc+3] = rotated_you
                temp_opp[sr:sr+3, sc:sc+3] = rotated_opp

                # Evaluate score
                my_lines = sum(1 for _ in range(4) if all(temp_you[i, j:j+2] == 1 for j in range(5)))
                opp_lines = sum(1 for _ in range(4) if all(temp_opp[i, j:j+2] == 1 for j in range(5)))

                current_score = my_lines - opp_lines

                if current_score > max_score:
                    max_score = current_score
                    best_move = f"{r+1},{c+1},{quad},{direction}"

    return best_move or f"{empty[0][0]+1},{empty[0][1]+1},0,R"
