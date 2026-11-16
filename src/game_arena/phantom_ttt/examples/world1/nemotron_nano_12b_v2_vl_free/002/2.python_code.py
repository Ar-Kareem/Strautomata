
import random

def policy(board, legal_moves):
    # Check if any legal move can result in a win
    winning_moves = []
    for cell in legal_moves:
        row, col = cell // 3, cell % 3
        if check_win(board, row, col):
            winning_moves.append(cell)
    
    if winning_moves:
        return (random.choice(winning_moves) // 3, random.choice(winning_moves) % 3)
    
    # Define cell priorities based on their strategic importance
    cell_weights = [3, 2, 3, 2, 4, 2, 3, 2, 3]
    candidates = sorted(legal_moves, key=lambda x: (-cell_weights[x], x))
    
    # Select the highest priority cell
    chosen_cell = candidates[0]
    return (chosen_cell // 3, chosen_cell % 3)

def check_win(board, row, col):
    # Check if placing a mark at (row, col) would complete a three-in-a-row
    # Check row
    win = True
    for j in range(3):
        if j != col and board[row][j] != 1:
            win = False
    if win:
        return True
    
    # Check column
    win = True
    for i in range(3):
        if i != row and board[i][col] != 1:
            win = False
    if win:
        return True
    
    # Check main diagonal (if applicable)
    if row == col:
        win = True
        for i in range(3):
            if i != row and board[i][i] != 1:
                win = False
        if win:
            return True
    
    # Check anti-diagonal (if applicable)
    if row + col == 2:
        win = True
        for i in range(3):
            if i != row and board[i][2 - i] != 1:
                win = False
        if win:
            return True
    
    return False
