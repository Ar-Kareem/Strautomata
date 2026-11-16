
def policy(board: list[list[int]]) -> tuple[int, int]:
    def winning_move(player):
        # Check rows and columns for a potential winning move
        for i in range(3):
            if board[i].count(player) == 2 and board[i].count(0) == 1:
                return (i, board[i].index(0))
            col = [board[j][i] for j in range(3)]
            if col.count(player) == 2 and col.count(0) == 1:
                return (col.index(0), i)
        
        # Check diagonals for a potential winning move
        if [board[i][i] for i in range(3)].count(player) == 2 and [board[i][i] for i in range(3)].count(0) == 1:
            index = [i for i in range(3) if board[i][i] == 0][0]
            return (index, index)
        if [board[i][2-i] for i in range(3)].count(player) == 2 and [board[i][2-i] for i in range(3)].count(0) == 1:
            index = [i for i in range(3) if board[i][2-i] == 0][0]
            return (index, 2 - index)
        
        return None

    # Check for a winning move for myself
    move = winning_move(1)
    if move:
        return move

    # Check for a winning move for the opponent and block it
    move = winning_move(-1)
    if move:
        return move

    # Choose center if available
    if board[1][1] == 0:
        return (1, 1)

    # Choose corners if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for corner in corners:
        if board[corner[0]][corner[1]] == 0:
            return corner

    # Choose any empty space
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)
    
    # Fallback in case of an invalid board
    return (0, 0)
