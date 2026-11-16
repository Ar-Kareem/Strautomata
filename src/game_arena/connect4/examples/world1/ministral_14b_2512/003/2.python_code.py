
import numpy as np
from typing import List

def check_win(board: List[List[int]], player: int) -> bool:
    """
    Check if the player has won by having four discs in a row horizontally, vertically, or diagonally.
    """
    # Convert the list to a numpy array for easier manipulation
    board_np = np.array(board, dtype=int)

    # Check vertical lines
    for col in range(7):
        for row in range(3):  # Only need to check up to the third row to avoid index errors
            if board_np[row][col] == player and board_np[row+1][col] == player and board_np[row+2][col] == player and board_np[row+3][col] == player:
                return True

    # Check horizontal lines
    for row in range(6):
        for col in range(4):  # Only need to check up to the fourth column
            if board_np[row][col] == player and board_np[row][col+1] == player and board_np[row][col+2] == player and board_np[row][col+3] == player:
                return True

    # Check diagonal lines (top-left to bottom-right)
    for row in range(3):
        for col in range(4):
            if board_np[row][col] == player and board_np[row+1][col+1] == player and board_np[row+2][col+2] == player and board_np[row+3][col+3] == player:
                return True

    # Check diagonal lines (top-right to bottom-left)
    for row in range(3):
        for col in range(3, 7):
            if board_np[row][col] == player and board_np[row+1][col-1] == player and board_np[row+2][col-2] == player and board_np[row+3][col-3] == player:
                return True

    return False

def simulate_move(board: List[List[int]], col: int, player: int) -> List[List[int]]:
    """
    Simulate dropping a disc in the specified column for the given player.
    """
    # Create a copy of the board
    new_board = [row[:] for row in board]

    # Find the lowest available row in the column
    for row in range(6):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            break

    return new_board

def policy(board: List[List[int]]) -> int:
    """
    Choose the best column to drop the current player's disc based on the board state.
    """
    # Check for immediate winning move
    for col in range(7):
        new_board = simulate_move(board, col, 1)
        if check_win(new_board, 1):
            return col

    # Check for opponent's winning move and block it
    for col in range(7):
        # Check if the column is not full
        if board[5][col] != 0:
            continue
        new_board = simulate_move(board, col, -1)
        if check_win(new_board, -1):
            return col

    # If no immediate win or block, evaluate potential moves using a heuristic
    scores = []
    for col in range(7):
        # Skip full columns
        if board[5][col] != 0:
            continue

        # Simulate dropping my disc in this column
        new_board = simulate_move(board, col, 1)

        # Score based on potential lines of four
        score = 0

        # Check for potential vertical lines
        for row in range(6):
            if new_board[row][col] == 1:
                # Count consecutive discs below
                consecutive = 1
                for next_row in range(row + 1, 6):
                    if new_board[next_row][col] == 1:
                        consecutive += 1
                    else:
                        break
                # If we have three consecutive discs below, and the next row is empty, it's a potential win
                if row + 3 < 6 and new_board[row + 3][col] == 0 and consecutive >= 3:
                    score += 10  # High potential for vertical win

        # Check for potential horizontal lines
        for row in range(6):
            if new_board[row][col] == 1:
                # Check left and right for consecutive discs
                consecutive_left = 0
                for c_left in range(col - 1, -1, -1):
                    if new_board[row][c_left] == 1:
                        consecutive_left += 1
                    else:
                        break

                consecutive_right = 0
                for c_right in range(col + 1, 7):
                    if new_board[row][c_right] == 1:
                        consecutive_right += 1
                    else:
                        break

                # If we have three consecutive discs in a row (left + right + current)
                if consecutive_left + consecutive_right >= 2:
                    score += 5 * (consecutive_left + consecutive_right)  # Potential for horizontal win

        # Check for potential diagonal lines (top-left to bottom-right)
        for row in range(6):
            if new_board[row][col] == 1:
                # Check top-left diagonal
                consecutive_tl = 0
                c_tl = col - 1
                r_tl = row - 1
                while c_tl >= 0 and r_tl >= 0 and new_board[r_tl][c_tl] == 1:
                    consecutive_tl += 1
                    c_tl -= 1
                    r_tl -= 1

                # Check bottom-right diagonal
                consecutive_br = 0
                c_br = col + 1
                r_br = row + 1
                while c_br < 7 and r_br < 6 and new_board[r_br][c_br] == 1:
                    consecutive_br += 1
                    c_br += 1
                    r_br += 1

                # If we have three consecutive discs in a diagonal
                if consecutive_tl + consecutive_br >= 2:
                    score += 5 * (consecutive_tl + consecutive_br)  # Potential for diagonal win

        # Check for potential diagonal lines (top-right to bottom-left)
        for row in range(6):
            if new_board[row][col] == 1:
                # Check top-right diagonal
                consecutive_tr = 0
                c_tr = col - 1
                r_tr = row + 1
                while c_tr >= 0 and r_tr < 6 and new_board[r_tr][c_tr] == 1:
                    consecutive_tr += 1
                    c_tr -= 1
                    r_tr += 1

                # Check bottom-left diagonal
                consecutive_bl = 0
                c_bl = col + 1
                r_bl = row - 1
                while c_bl < 7 and r_bl >= 0 and new_board[r_bl][c_bl] == 1:
                    consecutive_bl += 1
                    c_bl += 1
                    r_bl -= 1

                # If we have three consecutive discs in a diagonal
                if consecutive_tr + consecutive_bl >= 2:
                    score += 5 * (consecutive_tr + consecutive_bl)  # Potential for diagonal win

        # Center bias: prefer columns 3 and 4
        if col == 3 or col == 4:
            score += 2

        # Avoid columns with opponent's discs adjacent unless necessary
        for row in range(6):
            if new_board[row][col] == 1:
                # Check adjacent cells for opponent's discs
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        new_row = row + dr
                        new_col = col + dc
                        if 0 <= new_row < 6 and 0 <= new_col < 7 and new_board[new_row][new_col] == -1:
                            score -= 1

        scores.append(score)

    # Find the column with the highest score that is not full
    max_score = -1
    best_col = 0
    for col in range(7):
        if board[5][col] == 0 and scores[col] > max_score:
            max_score = scores[col]
            best_col = col

    return best_col
