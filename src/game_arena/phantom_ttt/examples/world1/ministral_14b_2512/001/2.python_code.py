
import random

def policy(board: list[list[int]], legal_moves: list[int]) -> tuple[int, int]:
    # Convert legal_moves to (row, col) pairs for easier processing
    legal_positions = [(move // 3, move % 3) for move in legal_moves]

    # Check for immediate winning move (3 in a row of 1s)
    def check_winning_move(positions):
        for (r, c) in positions:
            if board[r][c] == 1:
                # Check row, column, and diagonals
                if (board[r][0] == 1 and board[r][1] == 1 and board[r][2] == 1) or \
                   (board[0][c] == 1 and board[1][c] == 1 and board[2][c] == 1) or \
                   (r == c and board[0][0] == 1 and board[1][1] == 1 and board[2][2] == 1) or \
                   (r + c == 2 and board[0][2] == 1 and board[1][1] == 1 and board[2][0] == 1):
                    return True
        return False

    # Check if any legal move leads to a win
    for (r, c) in legal_positions:
        if board[r][c] == 0:  # Only consider unconfirmed cells
            # Simulate placing a 1 and check for win
            board[r][c] = 1
            if check_winning_move([(r, c)]):
                board[r][c] = 0
                return (r, c)
            board[r][c] = 0

    # Infer opponent's potential winning moves (blocking)
    # Since we don't observe opponent's marks, we assume opponent could win if we don't block
    # We look for 2 in a row of 0s (potential opponent's marks) and block the third
    def check_opponent_win(positions):
        for (r, c) in positions:
            if board[r][c] == 0:
                # Check row, column, and diagonals for 2 in a row of 0s
                row = [board[r][0], board[r][1], board[r][2]]
                col = [board[0][c], board[1][c], board[2][c]]
                diag1 = [board[0][0], board[1][1], board[2][2]]
                diag2 = [board[0][2], board[1][1], board[2][0]]

                for line in [row, col, diag1, diag2]:
                    if line.count(0) == 2 and line.count(1) == 0:
                        # Find the third position in the line
                        for i in range(3):
                            if line[i] == 0:
                                if i == 0:
                                    return (r if line == row else (0 if line == col else (0 if line == diag1 else 2)), c if line == col else (0 if line == diag1 else 2))
                                elif i == 1:
                                    return (r if line == row else (1 if line == col else 1), c if line == col else (1 if line == diag1 else 1))
                                else:
                                    return (r if line == row else (2 if line == col else (2 if line == diag1 else 0)), c if line == col else (2 if line == diag1 else 0))
        return None

    opponent_win_move = check_opponent_win(legal_positions)
    if opponent_win_move:
        return opponent_win_move

    # Prioritize center, then corners, then edges
    priorities = [
        (1, 1),  # center
        (0, 0), (0, 2), (2, 0), (2, 2),  # corners
        (0, 1), (1, 0), (1, 2), (2, 1)   # edges
    ]

    # Filter legal positions based on priorities
    for (r, c) in priorities:
        if (r, c) in legal_positions and board[r][c] == 0:
            return (r, c)

    # If no clear move, choose randomly among legal moves
    return random.choice(legal_positions)
