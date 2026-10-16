
import numpy as np

def get_possible_moves(board):
    possible_moves = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]  # Horizontal, vertical, diagonal
    n = board.shape[0]

    for row in range(n):
        for col in range(n):
            if board[row, col] == 1:  # Your amazon
                for dr, dc in directions:  # Move in all directions
                    r, c = row + dr, col + dc
                    while 0 <= r < n and 0 <= c < n:
                        if board[r, c] == 0:  # Can move here
                            # Valid move found, now look for arrow placements
                            for ar in range(n):
                                for ac in range(n):
                                    if board[ar, ac] == 0:  # Empty for arrow
                                        # Add the move and arrow placement
                                        possible_moves.append((row, col, r, c, ar, ac))
                        elif board[r, c] == 2 or board[r, c] == 1 or board[r, c] == -1:
                            break  # Blocked by another amazon or arrow
                        r += dr
                        c += dc

    return possible_moves

def policy(board) -> str:
    possible_moves = get_possible_moves(board)

    if not possible_moves:
        return ""  # Ideally should never occur as per problem statement

    best_move = None
    best_score = -float('inf')

    for move in possible_moves:
        # Extract move details
        from_row, from_col, to_row, to_col, arrow_row, arrow_col = move

        # Calculate score for the move (for simplicity here, just mobility)
        score = abs(to_row - 2.5) + abs(to_col - 2.5)  # Encourages centralization
        
        # Check if this move is better than the best found so far
        if score > best_score:
            best_score = score
            best_move = move

    # Return the best move in the required format
    from_row, from_col, to_row, to_col, arrow_row, arrow_col = best_move
    return f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}"
