
def policy(board):
    # Check for immediate win (AI placement)
    for x in range(4):
        for y in range(4):
            if board[x][y] == 0:
                temp = [row.copy() for row in board]
                temp[x][y] = 1
                # Check row
                if all(cell == 1 for cell in temp[x]):
                    return (x, y)
                # Check column
                if all(temp[i][y] == 1 for i in range(4)):
                    return (x, y)
                # Check main diagonal
                if x == y and all(temp[i][i] == 1 for i in range(4)):
                    return (x, y)
                # Check anti-diagonal
                if x + y == 3 and all(temp[i][3 - i] == 1 for i in range(4)):
                    return (x, y)
    
    # Block opponent's win
    for x in range(4):
        for y in range(4):
            if board[x][y] == 0:
                temp = [row.copy() for row in board]
                temp[x][y] = -1
                # Check row
                if all(cell == -1 for cell in temp[x]):
                    return (x, y)
                # Check column
                if all(temp[i][y] == -1 for i in range(4)):
                    return (x, y)
                # Check main diagonal
                if x == y and all(temp[i][i] == -1 for i in range(4)):
                    return (x, y)
                # Check anti-diagonal
                if x + y == 3 and all(temp[i][3 - i] == -1 for i in range(4)):
                    return (x, y)
    
    # Strategic priority (center → corners → edges)
    priority = [
        (1,1), (1,2), (2,1), (2,2),
        (0,0), (0,3), (3,0), (3,3),
        (0,1), (0,2),
        (1,0), (1,3),
        (2,0), (2,3),
        (3,1), (3,2)
    ]
    for x, y in priority:
        if board[x][y] == 0:
            return (x, y)
    
    # Fallback (unreachable in valid game states)
    for x in range(4):
        for y in range(4):
            if board[x][y] == 0:
                return (x, y)
    return (0, 0)  # Should never trigger
