
import numpy as np
from collections import deque

def policy(board):
    board = np.array(board)
    player = 1
    opponent = -1
    
    # Find all legal moves
    legal_moves = get_all_legal_moves(board, player)
    if not legal_moves:
        return "0,0:0,0"  # should not happen, but need to return something
    
    # Simple approach: try to connect pieces while considering captures
    # Implement a basic evaluation function to choose best move
    
    best_move = None
    best_score = -float('inf')
    
    for move in legal_moves:
        # Make a copy of the board to simulate the move
        new_board = board.copy()
        from_row, from_col, to_row, to_col = move
        new_board[to_row, to_col] = player
        new_board[from_row, from_col] = 0
        
        # Calculate score for this move
        score = evaluate_move(new_board, player)
        
        # Prefer moves that capture opponent's pieces
        if board[to_row, to_col] == opponent:
            score += 3
        
        # Prefer moves that connect our pieces
        groups = count_groups(new_board, player)
        score += (8 - groups) * 2
        
        # Prefer center positions
        center_dist = abs(to_row - 3.5) + abs(to_col - 3.5)
        score += (8 - center_dist) * 0.5
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"

def get_all_legal_moves(board, player):
    moves = []
    for row in range(8):
        for col in range(8):
            if board[row, col] == player:
                moves.extend(get_piece_moves(board, row, col, player))
    return moves

def get_piece_moves(board, row, col, player):
    opponent = -player
    moves = []
    
    # Check all 8 possible directions
    for dr, dc in [(-1,-1), (-1,0), (-1,1),
                   (0,-1),          (0,1),
                   (1,-1),  (1,0), (1,1)]:
        # Calculate pieces in this line (row, column or diagonal)
        count = count_pieces_in_direction(board, row, col, dr, dc)
        if count == 0:
            continue
        
        new_row = row + dr * count
        new_col = col + dc * count
        
        # Check if move is within bounds
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            can_move = True
            # Check all squares along the path except the destination
            for step in range(1, count):
                check_row = row + dr * step
                check_col = col + dc * step
                if board[check_row, check_col] == opponent:
                    can_move = False
                    break
            
            if can_move and board[new_row, new_col] != player:
                moves.append((row, col, new_row, new_col))
    
    return moves

def count_pieces_in_direction(board, row, col, dr, dc):
    count = 0
    current_row, current_col = row, col
    
    # Move in direction until we go off the board
    while True:
        current_row += dr
        current_col += dc
        if not (0 <= current_row < 8 and 0 <= current_col < 8):
            break
        if board[current_row, current_col] != 0:
            count += 1
    return count

def count_groups(board, player):
    visited = set()
    group_count = 0
    
    for row in range(8):
        for col in range(8):
            if board[row, col] == player and (row, col) not in visited:
                group_count += 1
                # BFS to mark all connected pieces
                queue = deque()
                queue.append((row, col))
                visited.add((row, col))
                
                while queue:
                    r, c = queue.popleft()
                    for dr, dc in [(-1,-1), (-1,0), (-1,1),
                                   (0,-1),          (0,1),
                                   (1,-1),  (1,0), (1,1)]:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < 8 and 0 <= nc < 8 and
                            board[nr, nc] == player and (nr, nc) not in visited):
                            visited.add((nr, nc))
                            queue.append((nr, nc))
    return group_count

def evaluate_move(board, player):
    opponent = -player
    
    # Base score
    score = 0
    
    # Number of groups (fewer is better)
    our_groups = count_groups(board, player)
    their_groups = count_groups(board, opponent)
    score += (8 - our_groups) * 2
    score -= their_groups * 1
    
    # Piece count
    our_pieces = np.count_nonzero(board == player)
    their_pieces = np.count_nonzero(board == opponent)
    score += (our_pieces - their_pieces) * 1
    
    return score
