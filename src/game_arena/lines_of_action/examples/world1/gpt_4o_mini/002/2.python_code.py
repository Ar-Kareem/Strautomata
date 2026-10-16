
import numpy as np

def get_legal_moves(board):
    legal_moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    rows, cols = len(board), len(board[0])
    player = 1

    for r in range(rows):
        for c in range(cols):
            if board[r][c] == player:
                pieces_in_line = count_pieces_in_line(board, r, c)
                for dr, dc in directions:
                    length = pieces_in_line[r, c]
                    new_r, new_c = r + dr * length, c + dc * length
                    if is_valid_move(board, r, c, new_r, new_c):
                        legal_moves.append((r, c, new_r, new_c))

    return legal_moves

def count_pieces_in_line(board, r, c):
    rows, cols = len(board), len(board[0])
    count = np.zeros((rows, cols), dtype=int)
    
    # Verify horizontally, vertically, and diagonally
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), 
                   (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        line_count = 0
        for i in range(rows):
            new_r, new_c = r + dr*i, c + dc*i
            if 0 <= new_r < rows and 0 <= new_c < cols:
                if board[new_r][new_c] == 1:
                    line_count += 1
                else:
                    break
        count[r, c] += line_count
    return count

def is_valid_move(board, from_r, from_c, to_r, to_c):
    if not (0 <= to_r < 8 and 0 <= to_c < 8):
        return False
    if board[to_r][to_c] == 1:  # Can't move to your own piece
        return False
    if board[from_r][from_c] != 1:  # There must be your piece at from
        return False

    pieces_in_line = count_pieces_in_line(board, from_r, from_c)
    expected_move_length = pieces_in_line[from_r, from_c]

    actual_move_length = max(abs(to_r - from_r), abs(to_c - from_c))

    return expected_move_length == actual_move_length

def evaluate_board(board):
    # Evaluation based on number of connected components
    player_count, opponent_count = 0, 0
    
    # Count pieces for player (1) and opponent (-1)
    for row in board:
        player_count += np.sum(row == 1)
        opponent_count += np.sum(row == -1)
    
    return player_count - opponent_count

def policy(board) -> str:
    legal_moves = get_legal_moves(board)
    
    if not legal_moves:
        return None  # No move available (should not happen in valid play)
    
    best_move = None
    best_score = float('-inf')

    for r1, c1, r2, c2 in legal_moves:
        # Execute the move
        board[r2][c2] = board[r1][c1]
        board[r1][c1] = 0
        score = evaluate_board(board)
        
        # Undo the move for the next iteration
        board[r1][c1] = 1
        board[r2][c2] = 0
        
        if score > best_score:
            best_score = score
            best_move = f"{r1},{c1}:{r2},{c2}"

    return best_move
