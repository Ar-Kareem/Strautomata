
import sys

def get_empty_cells(board):
    cells = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                cells.append((i, j))
    # Order by priority: center, corners, edges
    ordered = []
    # Center
    if (1, 1) in cells:
        ordered.append((1, 1))
    # Corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for corner in corners:
        if corner in cells:
            ordered.append(corner)
    # Edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for edge in edges:
        if edge in cells:
            ordered.append(edge)
    return ordered

def check_winner(board):
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] != 0:
            return row[0]
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != 0:
            return board[0][col]
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    return 0  # No winner

def minimax(board, depth, is_maximizing, alpha, beta):
    winner = check_winner(board)
    if winner == 1:  # AI wins
        return 10 - depth
    elif winner == -1:  # Opponent wins
        return -10 + depth
    empty_cells = get_empty_cells(board)
    if not empty_cells:  # Draw
        return 0

    if is_maximizing:
        best_score = -float('inf')
        for i, j in empty_cells:
            board[i][j] = 1
            score = minimax(board, depth + 1, False, alpha, beta)
            board[i][j] = 0
            best_score = max(score, best_score)
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break  # Beta pruning
        return best_score
    else:
        best_score = float('inf')
        for i, j in empty_cells:
            board[i][j] = -1
            score = minimax(board, depth + 1, True, alpha, beta)
            board[i][j] = 0
            best_score = min(score, best_score)
            beta = min(beta, best_score)
            if alpha >= beta:
                break  # Alpha pruning
        return best_score

def policy(board):
    # Check for immediate win
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_winner(board) == 1:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Check for opponent's immediate win and block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_winner(board) == -1:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Use minimax with alpha-beta pruning for optimal move
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    cells = get_empty_cells(board)
    for i, j in cells:
        board[i][j] = 1
        score = minimax(board, 0, False, alpha, beta)
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = (i, j)
        alpha = max(alpha, best_score)
    return best_move
