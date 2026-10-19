
def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    # Winning combinations
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Horizontal
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Vertical
        [0, 4, 8], [2, 4, 6]              # Diagonal
    ]
    
    # Check for a winning move
    for combo in winning_combinations:
        if all(board[i // 3][i % 3] != 1 for i in combo) and sum(board[i // 3][i % 3] for i in combo) == 2:
            # Place our mark in the cell that is 0
            for i in combo:
                if board[i // 3][i % 3] == 0:
                    return (i // 3, i % 3)

    # Check for a blocking move
    for combo in winning_combinations:
        if all(board[i // 3][i % 3] != 1 for i in combo) and sum(board[i // 3][i % 3] for i in combo) == 0:
            # Place our mark in the cell that is 0 (to block opponent)
            for i in combo:
                if board[i // 3][i % 3] == 0:
                    return (i // 3, i % 3)

    # Prefer the center, then corners, then sides
    preferred_moves = [4, 0, 2, 6, 8, 1, 3, 5, 7]  # Center, corners, sides
    for move in preferred_moves:
        if move in legal_moves and board[move // 3][move % 3] != 1:
            return (move // 3, move % 3)
    
    # Fallback: return first legal move
    if legal_moves:
        return (legal_moves[0] // 3, legal_moves[0] % 3)

    # If no legal moves available (should not happen), return (0,0) gracefully
    return (0, 0)
