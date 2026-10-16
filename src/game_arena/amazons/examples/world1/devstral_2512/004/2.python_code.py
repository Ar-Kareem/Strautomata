
import numpy as np
from typing import List, Tuple

def policy(board) -> str:
    # Directions for queen-like movement (8 directions)
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0), (1, 1)]

    def is_valid_position(row, col):
        return 0 <= row < 6 and 0 <= col < 6

    def get_legal_moves(board, player):
        moves = []
        for row in range(6):
            for col in range(6):
                if board[row, col] == player:
                    for dr, dc in directions:
                        # Check move direction
                        for step in range(1, 6):
                            r, c = row + dr * step, col + dc * step
                            if not is_valid_position(r, c):
                                break
                            if board[r, c] != 0:
                                break
                            # Check arrow directions from (r, c)
                            for adr, adc in directions:
                                for a_step in range(1, 6):
                                    ar, ac = r + adr * a_step, c + adc * a_step
                                    if not is_valid_position(ar, ac):
                                        break
                                    if board[ar, ac] != 0:
                                        break
                                    moves.append((row, col, r, c, ar, ac))
        return moves

    def evaluate_board(board):
        # Simple heuristic: count mobility and center control
        my_moves = len(get_legal_moves(board, 1))
        opp_moves = len(get_legal_moves(board, 2))
        center_control = 0
        for row in range(2, 4):
            for col in range(2, 4):
                if board[row, col] == 1:
                    center_control += 1
                elif board[row, col] == 2:
                    center_control -= 1
        return my_moves - opp_moves + center_control * 2

    def minimax(board, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return evaluate_board(board)

        legal_moves = get_legal_moves(board, 1 if maximizing_player else 2)
        if not legal_moves:
            return -float('inf') if maximizing_player else float('inf')

        if maximizing_player:
            max_eval = -float('inf')
            for move in legal_moves:
                # Apply move
                new_board = board.copy()
                new_board[move[0], move[1]] = 0
                new_board[move[2], move[3]] = 1
                new_board[move[4], move[5]] = -1
                eval = minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                # Apply move
                new_board = board.copy()
                new_board[move[0], move[1]] = 0
                new_board[move[2], move[3]] = 2
                new_board[move[4], move[5]] = -1
                eval = minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    # Get all legal moves for the current player (1)
    legal_moves = get_legal_moves(board, 1)
    if not legal_moves:
        return "0,0:0,0:0,0"  # Should not happen per problem statement

    # Find the best move using minimax with depth 2
    best_move = None
    best_eval = -float('inf')
    for move in legal_moves:
        new_board = board.copy()
        new_board[move[0], move[1]] = 0
        new_board[move[2], move[3]] = 1
        new_board[move[4], move[5]] = -1
        eval = minimax(new_board, 2, -float('inf'), float('inf'), False)
        if eval > best_eval:
            best_eval = eval
            best_move = move

    # Format the best move
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}:{best_move[4]},{best_move[5]}"
