
import random

def policy(board: list[list[int]], legal_moves: list[int]) -> tuple[int, int]:
    # Convert board to a flat list for easier manipulation
    flat_board = [cell for row in board for cell in row]

    # Function to check if a move would win the game
    def is_winning_move(move):
        # Create a temporary board with the move applied
        temp_board = flat_board.copy()
        temp_board[move] = 1

        # Check all possible winning lines
        winning_lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
            [0, 4, 8], [2, 4, 6]              # diagonals
        ]

        for line in winning_lines:
            if all(temp_board[pos] == 1 for pos in line):
                return True
        return False

    # Function to check if opponent might be about to win
    def is_blocking_move(move):
        # In Phantom Tic Tac Toe, we can't see opponent's moves directly
        # We'll assume opponent might be about to win if they have two in a line
        # and we're not blocking it

        # This is a simplified approach since we don't have full information
        # We'll look for lines where two cells are not confirmed as ours
        # and the third is our move

        temp_board = flat_board.copy()
        temp_board[move] = 1  # Our move

        winning_lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]

        for line in winning_lines:
            # Count how many cells in the line are not confirmed as ours
            unconfirmed = sum(1 for pos in line if flat_board[pos] != 1)
            if unconfirmed == 2 and move in line:
                # If two cells are unconfirmed and our move is in this line,
                # it might be blocking an opponent's potential win
                return True
        return False

    # First check for winning moves
    winning_moves = [move for move in legal_moves if is_winning_move(move)]
    if winning_moves:
        return divmod(winning_moves[0], 3)

    # Then check for blocking moves
    blocking_moves = [move for move in legal_moves if is_blocking_move(move)]
    if blocking_moves:
        return divmod(blocking_moves[0], 3)

    # Prefer center if available
    if 4 in legal_moves:
        return (1, 1)

    # Prefer corners over edges
    corners = [0, 2, 6, 8]
    available_corners = [c for c in corners if c in legal_moves]
    if available_corners:
        return divmod(random.choice(available_corners), 3)

    # If no strategic move, choose randomly from legal moves
    return divmod(random.choice(legal_moves), 3)
