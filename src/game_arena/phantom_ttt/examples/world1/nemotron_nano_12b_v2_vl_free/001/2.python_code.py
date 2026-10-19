
def priority_order():
    return [4, 0, 2, 6, 8, 1, 3, 5, 7]

def check_win(board):
    for row in board:
        if row[0] + row[1] + row[2] == 3:
            return True
    for i in range(3):
        if board[0][i] + board[1][i] + board[2][i] == 3:
            return True
    if (board[0][0] + board[1][1] + board[2][2]) == 3:
        return True
    if (board[0][2] + board[1][1] + board[2][0]) == 3:
        return True
    return False

def policy(board, legal_moves):
    winning_moves = []
    for move in legal_moves:
        row = move // 3
        col = move % 3
        board_copy = [row_list[:] for row_list in board]
        board_copy[row][col] = 1
        if check_win(board_copy):
            winning_moves.append(move)
    
    if winning_moves:
        for move in priority_order():
            if move in winning_moves:
                return (move // 3, move % 3)
    
    for move in priority_order():
        if move in legal_moves:
            return (move // 3, move % 3)
    return (legal_moves[0] // 3, legal_moves[0] % 3)
