
winning_lines = []

# Lines within a layer: fixed z
for z in range(3):
    for x in range(3):
        winning_lines.append([(z, x, 0), (z, x, 1), (z, x, 2)])
    for y in range(3):
        winning_lines.append([(z, 0, y), (z, 1, y), (z, 2, y)])
    winning_lines.append([(z, 0, 0), (z, 1, 1), (z, 2, 2)])
    winning_lines.append([(z, 0, 2), (z, 1, 1), (z, 2, 0)])

# Vertical lines: fixed (x,y)
for x in range(3):
    for y in range(3):
        winning_lines.append([(0, x, y), (1, x, y), (2, x, y)])

# Face diagonals: fixed y, along z and x
for y in range(3):
    winning_lines.append([(0, 0, y), (1, 1, y), (2, 2, y)])
    winning_lines.append([(0, 2, y), (1, 1, y), (2, 0, y)])

# Face diagonals: fixed x, along z and y
for x in range(3):
    winning_lines.append([(0, x, 0), (1, x, 1), (2, x, 2)])
    winning_lines.append([(0, x, 2), (1, x, 1), (2, x, 0)])

# Space diagonals
winning_lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
winning_lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
winning_lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
winning_lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])

def wins(board, player):
    for line in winning_lines:
        all_equal = True
        for (z, x, y) in line:
            if board[z][x][y] != player:
                all_equal = False
                break
        if all_equal:
            return True
    return False

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Step 1: Check if we can win now
    for z in range(3):
        for x in range(3):
            for y in range(3):
                if board[z][x][y] == 0:
                    new_board = [[[board[i][j][k] for k in range(3)] for j in range(3)] for i in range(3)]
                    new_board[z][x][y] = 1
                    if wins(new_board, 1):
                        return (z, x, y)
    
    # Step 2: Check for blocking moves (moves that don't allow opponent to win immediately)
    candidate_moves = []
    for z in range(3):
        for x in range(3):
            for y in range(3):
                if board[z][x][y] == 0:
                    new_board = [[[board[i][j][k] for k in range(3)] for j in range(3)] for i in range(3)]
                    new_board[z][x][y] = 1
                    opponent_can_win = False
                    for z2 in range(3):
                        for x2 in range(3):
                            for y2 in range(3):
                                if new_board[z2][x2][y2] == 0:
                                    new_board[z2][x2][y2] = -1
                                    if wins(new_board, -1):
                                        opponent_can_win = True
                                        new_board[z2][x2][y2] = 0
                                        break
                                    new_board[z2][x2][y2] = 0
                            if opponent_can_win:
                                break
                        if opponent_can_win:
                            break
                    if not opponent_can_win:
                        candidate_moves.append((z, x, y))
    
    # If candidate moves are available, choose the best one
    if candidate_moves:
        if (1, 1, 1) in candidate_moves:
            return (1, 1, 1)
        corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2), (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
        for move in corners:
            if move in candidate_moves:
                return move
        return candidate_moves[0]
    
    # If no candidate moves, pick any empty cell
    for z in range(3):
        for x in range(3):
            for y in range(3):
                if board[z][x][y] == 0:
                    return (z, x, y)
