
import random
import numpy as np
from typing import List, Tuple, Dict, Set

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    # Convert to sets for easier manipulation
    me_set = set(me)
    opponent_set = set(opponent)
    
    # Initialize board state
    board_size = 19
    board = np.zeros((board_size, board_size), dtype=int)
    
    # Mark stones on board
    for r, c in me_set:
        board[r-1, c-1] = 1  # My stones
    for r, c in opponent_set:
        board[r-1, c-1] = -1  # Opponent stones
    
    # Helper function to check if position is on board
    def is_on_board(row, col):
        return 0 <= row < board_size and 0 <= col < board_size
    
    # Helper function to get neighbors
    def get_neighbors(row, col):
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_row, new_col = row + dr, col + dc
            if is_on_board(new_row, new_col):
                neighbors.append((new_row, new_col))
        return neighbors
    
    # Helper function to check if a move is legal
    def is_legal_move(row, col, current_player):
        # Check if position is empty
        if board[row, col] != 0:
            return False
        
        # Create temporary board to simulate move
        temp_board = board.copy()
        temp_board[row, col] = current_player
        
        # Check if move creates any liberties for captured groups
        opponent_groups = []
        opponent = -current_player
        for neighbor_row, neighbor_col in get_neighbors(row, col):
            if temp_board[neighbor_row, neighbor_col] == opponent:
                group = find_group(temp_board, neighbor_row, neighbor_col)
                if not has_liberties(temp_board, group):
                    opponent_groups.append(group)
        
        # If we have no liberties, but enemy groups are captured, move is valid
        if not has_liberties(temp_board, {(row, col)}):
            return len(opponent_groups) > 0
        
        return True
    
    # Helper to find connected group
    def find_group(board, start_row, start_col):
        group = set()
        stack = [(start_row, start_col)]
        piece = board[start_row, start_col]
        
        while stack:
            row, col = stack.pop()
            if (row, col) in group:
                continue
            group.add((row, col))
            
            for n_row, n_col in get_neighbors(row, col):
                if board[n_row, n_col] == piece and (n_row, n_col) not in group:
                    stack.append((n_row, n_col))
        
        return group
    
    # Helper to check if group has liberties
    def has_liberties(board, group):
        for row, col in group:
            for n_row, n_col in get_neighbors(row, col):
                if board[n_row, n_col] == 0:
                    return True
        return False
    
    # Get all possible moves (simplified evaluation)
    def get_possible_moves():
        moves = []
        # Get empty positions near stones
        for r, c in me_set.union(opponent_set):
            for dr, dc in [(-2, 0), (-1, -1), (-1, 0), (-1, 1), (0, -2), (0, -1), (0, 1), (0, 2), (1, -1), (1, 0), (1, 1), (2, 0)]:
                new_r, new_c = r + dr, c + dc
                if is_on_board(new_r, new_c) and board[new_r, new_c] == 0:
                    moves.append((new_r, new_c))
        # Also try center areas for opening
        center_positions = [(10, 10), (10, 9), (10, 11), (9, 10), (11, 10)]
        for r, c in center_positions:
            if is_on_board(r-1, c-1) and board[r-1, c-1] == 0:
                moves.append((r-1, c-1))
        # Remove duplicates
        return list(set(moves))
    
    # Evaluate move quality
    def evaluate_move(row, col):
        if board[row, col] != 0:
            return -1000
        
        score = 0
        
        # Prefer center positions
        if 8 <= row <= 10 and 8 <= col <= 10:
            score += 5
        
        # Prefer positions near existing stones (territory formation)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            n_row, n_col = row + dr, col + dc
            if is_on_board(n_row, n_col):
                if (n_row, n_col) in me_set:
                    score += 3
                elif (n_row, n_col) in opponent_set:
                    score += 1
        
        # Prefer safe moves that don't put stones in atari or make eyeless groups
        temp_board = board.copy()
        temp_board[row, col] = 1  # Assume we place our stone
        
        # Check if this move creates an eye (security) or captures opponent
        eye_like = 0
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            n_row, n_col = row + dr, col + dc
            if is_on_board(n_row, n_col) and board[n_row, n_col] == 0:
                eye_like += 1
        
        score += eye_like * 2
        
        # Prefer moves with good liberties (encouraging group health)
        liberties = 0
        group = find_group(temp_board, row, col)
        for g_row, g_col in group:
            for n_row, n_col in get_neighbors(g_row, g_col):
                if temp_board[n_row, n_col] == 0:
                    liberties += 1
                    
        score += liberties / 2
        
        # Preemptive blocking of opponent formation
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            n_row, n_col = row + dr, col + dc
            if is_on_board(n_row, n_col) and (n_row, n_col) in opponent_set:
                # Check if this would be effective in forming a 2-eye structure
                if sum(1 for n2_row, n2_col in get_neighbors(n_row, n_col) 
                       if (n2_row, n2_col) in opponent_set or ((n2_row, n2_col) == (row, col))) >= 3:
                    score += 10  # Encourage blocking good opponent moves
        
        # Prefer not placing stones that immediately lead to suicide
        if not has_liberties(temp_board, {(row, col)}):
            # This might be a suicide move, avoid it
            score -= 500
        
        return score
    
    # Main move selection logic
    possible_moves = get_possible_moves()
    
    # If no moves possible, pass
    if not possible_moves:
        return ((0, 0), memory)
    
    # Try to find a move that would be likely to win or block
    best_move = None
    best_score = -float('inf')
    
    # For any legal move that does not cause immediate suicide, we'll choose one
    # that maximizes heuristics above
    for move_row, move_col in possible_moves:
        if is_legal_move(move_row, move_col, 1):  # 1 represents our color
            score = evaluate_move(move_row, move_col)
            if score > best_score:
                best_score = score
                best_move = (move_row, move_col)
    
    # If we still don't have a move, try a random valid one
    if best_move is None:
        valid_moves = [m for m in possible_moves if is_legal_move(m[0], m[1], 1)]
        if valid_moves:
            best_move = random.choice(valid_moves)
        else:
            return ((0, 0), memory)
    
    # Now return the move with updated memory
    return (tuple([best_move[0] + 1, best_move[1] + 1]), memory)
