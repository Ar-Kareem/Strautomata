
import numpy as np

directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]

def generate_moves(board, player):
    moves = []
    rows, cols = board.shape
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == player:
                for dr, dc in directions:
                    step = 1
                    while 0 <= r + step * dr < rows and 0 <= c + step * dc < cols and board[r + step * dr, c + step * dc] == 0:
                        to = (r + step * dr, c + step * dc)
                        arrow_targets = []
                        for dr2, dc2 in directions:
                            step2 = 1
                            while 0 <= to[0] + step2 * dr2 < rows and 0 <= to[1] + step2 * dc2 < cols:
                                r_a = to[0] + step2 * dr2
                                c_a = to[1] + step2 * dc2
                                if (r_a, c_a) == (r, c):
                                    val = 0
                                else:
                                    val = board[r_a, c_a]
                                if val != 0:
                                    break
                                arrow_targets.append((r_a, c_a))
                                step2 += 1
                        for arrow in arrow_targets:
                            moves.append(((r, c), to, arrow))
                        step += 1
    return moves

def count_moves(board, player):
    count = 0
    rows, cols = board.shape
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == player:
                for dr, dc in directions:
                    step = 1
                    while 0 <= r + step * dr < rows and 0 <= c + step * dc < cols and board[r + step * dr, c + step * dc] == 0:
                        to = (r + step * dr, c + step * dc)
                        for dr2, dc2 in directions:
                            step2 = 1
                            while 0 <= to[0] + step2 * dr2 < rows and 0 <= to[1] + step2 * dc2 < cols:
                                r_a = to[0] + step2 * dr2
                                c_a = to[1] + step2 * dc2
                                if (r_a, c_a) == (r, c):
                                    val = 0
                                else:
                                    val = board[r_a, c_a]
                                if val != 0:
                                    break
                                count += 1
                                step2 += 1
                        step += 1
    return count

def format_move(move):
    return f"{move[0][0]},{move[0][1]}:{move[1][0]},{move[1][1]}:{move[2][0]},{move[2][1]}"

def policy(board):
    moves = generate_moves(board, 1)
    if not moves:
        return "0,0:0,0:0,0"
    
    best_move = None
    best_score = -float('inf')
    
    for move in moves:
        new_board = board.copy()
        new_board[move[0][0], move[0][1]] = 0
        new_board[move[1][0], move[1][1]] = 1
        new_board[move[2][0], move[2][1]] = -1
        
        opponent_moves = count_moves(new_board, 2)
        if opponent_moves == 0:
            return format_move(move)
        
        our_moves = count_moves(new_board, 1)
        score = our_moves - opponent_moves
        
        if score > best_score:
            best_score = score
            best_move = move
            
    return format_move(best_move)
