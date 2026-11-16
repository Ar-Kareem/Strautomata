
def policy(board):
    # Collect all possible moves (cells with 0)
    possible_moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                possible_moves.append((i, j))

    # Check if any of the possible moves would result in a win
    for move in [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]:
        if move not in possible:
            continue

        # Simulate placing move
        temp = [row.copy() for row in board]
        temp[move[0]][move[1]] = 1

        # Check row
        if all(temp[move[0]][x] == 1 for x in range(3)):
            return move
        # Check column
        col = [temp[x][move[1]] for x in range(3)]
        if all(cell == 1 for cell in col):
            return move
        # Check diagonals
        if move[0] == move[1]:  # Main diagonal
            diag = [temp[x][x] for x in range(3)]
            if all(cell == 1 for cell in diag):
                return move
        if move[0] + move[1] == 2:  # Anti-diagonal
            diag = [temp[x][2 - x] for x in range(3)]
            if all(cell == 1 for cell in diag):
                return move

    # If no winning move, choose the highest priority available cell
    for move in [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]:
        if move in possible:
            return move

    # Fallback (shouldn't happen if there are possible moves)
    return possible[0]
