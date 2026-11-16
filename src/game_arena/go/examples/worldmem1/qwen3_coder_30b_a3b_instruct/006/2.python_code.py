
import numpy as np
from collections import deque
import random

def is_legal(board, row, col):
    if row < 0 or row >= 19 or col < 0 or col >= 19:
        return False
    return board[row][col] == 0

def get_neighbors(row, col):
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 19 and 0 <= new_col < 19:
            neighbors.append((new_row, new_col))
    return neighbors

def get_liberties(board, row, col, visited=None):
    if visited is None:
        visited = set()
    
    if (row, col) in visited:
        return set()
    
    if board[row][col] == 0:
        return {(row, col)}
    
    visited.add((row, col))
    
    liberties = set()
    for n_row, n_col in get_neighbors(row, col):
        if board[n_row][n_col] == 0:
            liberties.add((n_row, n_col))
        elif board[n_row][n_col] == board[row][col]:
            liberties.update(get_liberties(board, n_row, n_col, visited))
    
    return liberties

def count_liberties(board, row, col):
    return len(get_liberties(board, row, col))

def get_group(board, row, col, visited=None):
    if visited is None:
        visited = set()
    
    if (row, col) in visited:
        return set()
    
    if board[row][col] == 0:
        return set()
    
    visited.add((row, col))
    group = {(row, col)}
    
    for n_row, n_col in get_neighbors(row, col):
        if board[n_row][n_col] == board[row][col]:
            group.update(get_group(board, n_row, n_col, visited))
    
    return group

def would_cause_suicide(board, row, col, player):
    if board[row][col] != 0:
        return False
    
    board[row][col] = player
    
    # Check if any neighboring opponent groups have no liberties
    for n_row, n_col in get_neighbors(row, col):
        if board[n_row][n_col] != 0 and board[n_row][n_col] != player:
            group = get_group(board, n_row, n_col)
            liberties = get_liberties(board, n_row, n_col)
            if len(liberties) == 0:
                board[row][col] = 0
                return False
    
    # Check if the new stone has liberties
    liberties = get_liberties(board, row, col)
    if len(liberties) == 0:
        board[row][col] = 0
        return True
    
    board[row][col] = 0
    return False

def get_capturable_stones(board, row, col, player):
    """Get stones that would be captured if a stone was placed at (row, col)"""
    if board[row][col] != 0:
        return set()
    
    # Temporarily place the stone
    board[row][col] = player
    
    captured = set()
    # Check opponent neighbors
    for n_row, n_col in get_neighbors(row, col):
        if board[n_row][n_col] != 0 and board[n_row][n_col] != player:
            group = get_group(board, n_row, n_col)
            liberties = get_liberties(board, n_row, n_col)
            if len(liberties) == 0:
                captured.update(group)
    
    board[row][col] = 0
    return captured

def evaluate_position(board, row, col, me_stones, opp_stones, player):
    # Positional evaluation factors
    score = 0
    
    # Prefer center positions
    center = (9, 9)
    distance = abs(row - center[0]) + abs(col - center[1])
    score -= distance * 0.5
    
    # Prefer positions near existing stones
    for stone_row, stone_col in me_stones:
        dist = abs(row - stone_row) + abs(col - stone_col)
        if dist <= 3:  # Close to existing stones
            score += 1.0
    
    # Prefer positions near opponent stones to create pressure
    for stone_row, stone_col in opp_stones:
        dist = abs(row - stone_row) + abs(col - stone_col)
        if dist <= 2:  # Near opponent stones
            score += 0.5
    
    # Prefer capturing stones over other moves
    captured = get_capturable_stones(board, row, col, player)
    if captured:
        score += len(captured) * 5.0
    
    # Prevent suicide moves and give liberties to own groups
    if not would_cause_suicide(board, row, col, player):
        group = get_group(board, row, col)
        if group:
            liberties = get_liberties(board, row, col)
            score += len(liberties) * 0.5
    
    return score

def next_move_heuristic(board, me_stones, opp_stones, player):
    # Convert data to board representation for evaluation
    temp_board = [row[:] for row in board]  # Deep copy
    
    best_score = -float('inf')
    best_move = (0, 0)
    
    # Try all empty positions
    for row in range(19):
        for col in range(19):
            if temp_board[row][col] == 0:
                # Check for suicide
                if would_cause_suicide(temp_board, row, col, player):
                    continue
                
                # Evaluate this move
                score = evaluate_position(temp_board, row, col, me_stones, opp_stones, player)
                
                # Bonus for potentially creating eyes or capturing stones
                captured = get_capturable_stones(temp_board, row, col, player)
                if captured:
                    score += 10.0  # Strong tactical value
                
                # Bonus for center control
                if (row, col) in [(9, 9), (8, 8), (10, 10), (8, 10), (10, 8)]:
                    score += 2.0
                
                if score > best_score:
                    best_score = score
                    best_move = (row + 1, col + 1)  # Convert 0-indexed to 1-indexed
    
    return best_move if best_score > -float('inf') else (0, 0)

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Convert lists to board representation
    board = [[0 for _ in range(19)] for _ in range(19)]
    
    me_stones = [(row - 1, col - 1) for row, col in me]  # Convert to 0-indexed
    opponent_stones = [(row - 1, col - 1) for row, col in opponent]
    
    for row, col in me_stones:
        board[row][col] = 1
    
    for row, col in opponent_stones:
        board[row][col] = 2
    
    # Handle the case where both players pass (game ended)
    move = next_move_heuristic(board, me_stones, opponent_stones, 1)
    
    # If we can't make a good move, pass
    if move == (0, 0):
        return (0, 0), memory
        
    return move, memory
