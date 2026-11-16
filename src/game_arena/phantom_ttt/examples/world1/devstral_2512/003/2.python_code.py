
import random

def policy(board: list[list[int]], legal_moves: list[int]) -> tuple[int, int]:
    # Convert legal moves to (row, col) format
    legal_positions = [(move // 3, move % 3) for move in legal_moves]

    # Check for immediate winning move
    for move in legal_positions:
        row, col = move
        # Simulate placing our mark
        temp_board = [row[:] for row in board]
        temp_board[row][col] = 1

        # Check if this move wins
        if check_win(temp_board, 1):
            return move

    # Try to block opponent's potential wins
    # We need to consider possible opponent positions
    opponent_positions = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:  # Could be opponent's mark
                opponent_positions.append((i, j))

    # Generate all possible opponent configurations (with 1 or 2 marks)
    from itertools import combinations
    for opp_marks in combinations(opponent_positions, 2):
        # Create a board with our marks and these opponent marks
        temp_board = [row[:] for row in board]
        for i, j in opp_marks:
            temp_board[i][j] = -1  # -1 represents opponent

        # Check if opponent has a winning move
        for move in legal_positions:
            row, col = move
            if temp_board[row][col] == 0:  # Only consider empty cells
                temp_board[row][col] = -1
                if check_win(temp_board, -1):
                    return move
                temp_board[row][col] = 0  # Undo

    # If no immediate win or block, use strategic positioning
    # Prefer center, then corners, then edges
    center = (1, 1)
    if center in legal_positions:
        return center

    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [c for c in corners if c in legal_positions]
    if available_corners:
        return random.choice(available_corners)

    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    available_edges = [e for e in edges if e in legal_positions]
    if available_edges:
        return random.choice(available_edges)

    # Fallback: return any legal move
    return random.choice(legal_positions)

def check_win(board, player):
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True

    # Check columns
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] == player:
        return True
    if board[0][2] == board[1][1] == board[2][0] == player:
        return True

    return False
