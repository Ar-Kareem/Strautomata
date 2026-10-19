
import numpy as np
from collections import deque
import time

def policy(board):
    start_time = time.time()
    board = np.array(board)
    player = 1
    opponent = -1
    
    def is_valid_move(from_row, from_col, to_row, to_col):
        if not (0 <= to_row < 8 and 0 <= to_col < 8):
            return False
        if board[from_row, from_col] != player:
            return False
        if board[to_row, to_col] == player:
            return False
            
        # Calculate direction and distance
        dr = to_row - from_row
        dc = to_col - from_col
        distance = max(abs(dr), abs(dc))
        
        # Must be moving in straight line
        if not (dr == 0 or dc == 0 or abs(dr) == abs(dc)):
            return False
            
        # Calculate number of pieces in the line
        line_pieces = 0
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
        
        r, c = from_row + step_r, from_col + step_c
        for _ in range(distance - 1):
            if 0 <= r < 8 and 0 <= c < 8:
                if board[r, c] != 0:
                    line_pieces += 1
                    if board[r, c] == opponent:
                        return False  # can't jump over opponent
            else:
                break
            r += step_r
            c += step_c
        
        total_pieces = np.count_nonzero(board != 0)
        line_pieces += 1  # counting our own piece
        return line_pieces == distance
    
    def generate_moves():
        moves = []
        my_pieces = np.argwhere(board == player)
        for (r, c) in my_pieces:
            # Check all possible directions
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    # Calculate max possible distance
                    max_dist = 0
                    if dr == 0:  # horizontal
                        max_dist = 7 - c if dc > 0 else c
                    elif dc == 0:  # vertical
                        max_dist = 7 - r if dr > 0 else r
                    else:  # diagonal
                        max_dist = min(7 - r if dr > 0 else r,
                                      7 - c if dc > 0 else c)
                    
                    for dist in range(1, max_dist + 1):
                        to_r = r + dr * dist
                        to_c = c + dc * dist
                        if is_valid_move(r, c, to_r, to_c):
                            moves.append(f"{r},{c}:{to_r},{to_c}")
        return moves
    
    def evaluate_position():
        # Count connected components
        def count_connected(pieces):
            if len(pieces) == 0:
                return 0
            visited = set()
            count = 0
            for piece in pieces:
                if tuple(piece) not in visited:
                    count += 1
                    queue = deque([tuple(piece)])
                    visited.add(tuple(piece))
                    while queue:
                        r, c = queue.popleft()
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                if dr == 0 and dc == 0:
                                    continue
                                nr, nc = r + dr, c + dc
                                if (nr, nc) in pieces and (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    queue.append((nr, nc))
            return count
        
        my_pieces = [tuple(p) for p in np.argwhere(board == player)]
        opp_pieces = [tuple(p) for p in np.argwhere(board == opponent)]
        
        my_connected = count_connected(my_pieces)
        opp_connected = count_connected(opp_pieces)
        
        # Calculate average distance between pieces
        def avg_distance(pieces):
            if len(pieces) <= 1:
                return 0
            total = 0
            count = 0
            for i in range(len(pieces)):
                for j in range(i+1, len(pieces)):
                    r1, c1 = pieces[i]
                    r2, c2 = pieces[j]
                    dist = max(abs(r1 - r2), abs(c1 - c2))
                    total += dist
                    count += 1
            return total / count if count > 0 else 0
        
        my_avg_dist = avg_distance(my_pieces)
        opp_avg_dist = avg_distance(opp_pieces)
        
        # Piece count
        piece_diff = len(my_pieces) - len(opp_pieces)
        
        # Central control
        center_value = 0
        for r in range(3, 6):
            for c in range(3, 6):
                if board[r, c] == player:
                    center_value += 1
                elif board[r, c] == opponent:
                    center_value -= 1
        
        # Mobility
        my_mobility = len(generate_moves())
        
        # Weighted evaluation
        score = 0
        score += -100 * my_connected  # we want fewer connected components
        score += 50 * opp_connected   # opponent should have more components
        score += -5 * my_avg_dist     # smaller average distance is better
        score += 2 * opp_avg_dist     # opponent should have larger distances
        score += 10 * piece_diff      # piece advantage is good
        score += 3 * center_value     # center control is valuable
        score += 0.1 * my_mobility    # more options are better
        
        return score
    
    def minimax(depth, alpha, beta, maximizing_player):
        if depth == 0 or time.time() - start_time > 0.9:
            return evaluate_position()
        
        moves = generate_moves()
        if not moves:
            return evaluate_position()
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in moves:
                # Make move
                from_coords, to_coords = move.split(':')
                fr, fc = map(int, from_coords.split(','))
                tr, tc = map(int, to_coords.split(','))
                original = board[tr, tc]
                board[fr, fc] = 0
                board[tr, tc] = player
                
                eval = minimax(depth-1, alpha, beta, False)
                
                # Undo move
                board[fr, fc] = player
                board[tr, tc] = original
                
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                # Make move (from opponent's perspective)
                from_coords, to_coords = move.split(':')
                fr, fc = map(int, from_coords.split(','))
                tr, tc = map(int, to_coords.split(','))
                original = board[tr, tc]
                board[fr, fc] = 0
                board[tr, tc] = opponent
                
                eval = minimax(depth-1, alpha, beta, True)
                
                # Undo move
                board[fr, fc] = opponent
                board[tr, tc] = original
                
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    # Get all legal moves
    moves = generate_moves()
    if not moves:
        return "0,0:0,0"  # should never happen
    
    # If we can win immediately, do it
    for move in moves:
        from_coords, to_coords = move.split(':')
        fr, fc = map(int, from_coords.split(','))
        tr, tc = map(int, to_coords.split(','))
        
        # Make the move temporarily
        original = board[tr, tc]
        board[fr, fc] = 0
        board[tr, tc] = player
        
        # Check if all pieces are connected
        my_pieces = [tuple(p) for p in np.argwhere(board == player)]
        visited = set()
        if my_pieces:
            queue = deque([my_pieces[0]])
            visited.add(my_pieces[0])
            while queue:
                r, c = queue.popleft()
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if (nr, nc) in my_pieces and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
        
        # Undo the move
        board[fr, fc] = player
        board[tr, tc] = original
        
        if len(visited) == len(my_pieces) and len(my_pieces) > 0:
            return move
    
    # Use minimax with iterative deepening
    best_move = moves[0]
    best_score = float('-inf')
    depth = 1
    
    while time.time() - start_time < 0.9 and depth <= 3:
        current_best = None
        current_score = float('-inf')
        
        for move in moves:
            from_coords, to_coords = move.split(':')
            fr, fc = map(int, from_coords.split(','))
            tr, tc = map(int, to_coords.split(','))
            original = board[tr, tc]
            board[fr, fc] = 0
            board[tr, tc] = player
            
            score = minimax(depth-1, float('-inf'), float('inf'), False)
            
            board[fr, fc] = player
            board[tr, tc] = original
            
            if score > current_score:
                current_score = score
                current_best = move
        
        if current_best is not None and current_score > best_score:
            best_move = current_best
            best_score = current_score
        
        depth += 1
    
    return best_move
