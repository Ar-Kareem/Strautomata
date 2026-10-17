
import numpy as np
from typing import Tuple, List
import math

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    n = len(board)
    best_score = -math.inf
    best_move = None

    # Iterate through all empty cells to evaluate possible moves
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board[x][y][z] == 0:  # Cell is empty
                    # Make the move temporarily
                    board[x][y][z] = 1
                    move_score = minimax(board, 0, False, -math.inf, math.inf)
                    # Undo the move
                    board[x][y][z] = 0

                    if move_score > best_score:
                        best_score = move_score
                        best_move = (x, y, z)

    return best_move if best_move is not None else (0, 0, 0)

def minimax(board: List[List[List[int]]], depth: int, is_maximizing: bool, alpha: float, beta: float) -> int:
    n = len(board)
    result = check_win(board)

    if result is not None:
        return result * (10 - depth)  # Prefer faster wins/losses

    if all(board[x][y][z] != 0 for x in range(n) for y in range(n) for z in range(n)):
        return 0  # Draw

    if is_maximizing:
        best_score = -math.inf
        for x in range(n):
            for y in range(n):
                for z in range(n):
                    if board[x][y][z] == 0:
                        board[x][y][z] = 1
                        score = minimax(board, depth + 1, False, alpha, beta)
                        board[x][y][z] = 0
                        best_score = max(score, best_score)
                        alpha = max(alpha, best_score)
                        if beta <= alpha:
                            break
        return best_score
    else:
        best_score = math.inf
        for x in range(n):
            for y in range(n):
                for z in range(n):
                    if board[x][y][z] == 0:
                        board[x][y][z] = -1
                        score = minimax(board, depth + 1, True, alpha, beta)
                        board[x][y][z] = 0
                        best_score = min(score, best_score)
                        beta = min(beta, best_score)
                        if beta <= alpha:
                            break
        return best_score

def check_win(board: List[List[List[int]]]) -> None:
    n = len(board)
    
    # Check straight lines along x, y, z axes
    for x in range(n):
        for y in range(n):
            if abs(sum(board[x][y][z] for z in range(n))) == n:
                return board[x][y][0]
    for x in range(n):
        for z in range(n):
            if abs(sum(board[x][y][z] for y in range(n))) == n:
                return board[x][0][z]
    for y in range(n):
        for z in range(n):
            if abs(sum(board[x][y][z] for x in range(n))) == n:
                return board[0][y][z]
    
    # Check 4 main diagonals in each face
    for x in range(n):
        if abs(board[x][0][0] + board[x][1][1] + board[x][2][2]) == n:
            return board[x][0][0]
        if abs(board[x][2][0] + board[x][1][1] + board[x][0][2]) == n:
            return board[x][2][0]
    for y in range(n):
        if abs(board[0][y][0] + board[1][y][1] + board[2][y][2]) == n:
            return board[0][y][0]
        if abs(board[2][y][0] + board[1][y][1] + board[0][y][2]) == n:
            return board[2][y][0]
    for z in range(n):
        if abs(board[0][0][z] + board[1][1][z] + board[2][2][z]) == n:
            return board[0][0][z]
        if abs(board[2][0][z] + board[1][1][z] + board[0][2][z]) == n:
            return board[2][0][z]
    
    # Check 4 space diagonals
    if abs(board[0][0][0] + board[1][1][1] + board[2][2][2]) == n:
        return board[0][0][0]
    if abs(board[2][0][0] + board[1][1][1] + board[0][2][2]) == n:
        return board[2][0][0]
    if abs(board[0][2][0] + board[1][1][1] + board[2][0][2]) == n:
        return board[0][2][0]
    if abs(board[0][0][2] + board[1][1][1] + board[2][2][0]) == n:
        return board[0][0][2]
    
    return None  # No winner yet
