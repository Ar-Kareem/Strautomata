
import numpy as np
import time
from collections import deque

def policy(board):
    start_time = time.time()
    board = np.array(board)
    player = 1
    opponent = -1
    
    # Generate all legal moves
    def get_legal_moves(b, player):
        moves = []
        pieces = np.argwhere(b == player)
        
        for (r, c) in pieces:
            # Check all 8 directions
            for dr, dc in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                # Calculate pieces in this line
                line_pieces = 0
                for i in range(1, 8):
                    nr, nc = r + i*dr, c + i*dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        if b[nr, nc] != 0:
                            line_pieces += 1
                    else:
                        break
                
                # Check if move distance equals line pieces
                move_dist = line_pieces
                if move_dist == 0:
                    continue
                
                # Check landing position
                nr, nc = r + move_dist*dr, c + move_dist*dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    # Check if path is clear (no opponent pieces in between)
                    valid = True
                    for i in range(1, move_dist):
                        tr, tc = r + i*dr, c + i*dc
                        if b[tr, tc] == opponent:
                            valid = False
                            break
                    if valid:
                        moves.append(f"{r},{c}:{nr},{nc}")
        return moves
    
    # Evaluation function
    def evaluate(b):
        # Count pieces
        my_pieces = np.sum(b == player)
        opp_pieces = np.sum(b == opponent)
        piece_diff = my_pieces - opp_pieces
        
        # Calculate connectivity
        def get_connectivity(p):
            pieces = np.argwhere(b == p)
            if len(pieces) == 0:
                return 0
            visited = set()
            groups = 0
            for (r, c) in pieces:
                if (r, c) in visited:
                    continue
                groups += 1
                queue = deque([(r, c)])
                while queue:
                    cr, cc = queue.popleft()
                    if (cr, cc) in visited:
                        continue
                    visited.add((cr, cc))
                    for dr, dc in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and b[nr, nc] == p:
                            queue.append((nr, nc))
            return len(pieces) - groups
        
        my_connectivity = get_connectivity(player)
        opp_connectivity = get_connectivity(opponent)
        
        # Central control
        center = b[2:6, 2:6]
        center_control = np.sum(center == player) - np.sum(center == opponent)
        
        # Mobility
        my_mobility = len(get_legal_moves(b, player))
        opp_mobility = len(get_legal_moves(b, opponent))
        
        # Weighted evaluation
        return (10 * piece_diff + 20 * (my_connectivity - opp_connectivity) + 
                5 * center_control + 2 * (my_mobility - opp_mobility))
    
    # Simple search with time limit
    def search(b, depth, alpha, beta, maximizing_player, start_time):
        if time.time() - start_time > 0.95:
            return evaluate(b)
        
        if depth == 0:
            return evaluate(b)
        
        moves = get_legal_moves(b, player if maximizing_player else opponent)
        if not moves:
            return evaluate(b)
        
        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                # Make move
                from_pos, to_pos = move.split(':')
                fr, fc = map(int, from_pos.split(','))
                tr, tc = map(int, to_pos.split(','))
                new_b = b.copy()
                new_b[fr, fc] = 0
                new_b[tr, tc] = player
                
                eval = search(new_b, depth-1, alpha, beta, False, start_time)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                # Make move
                from_pos, to_pos = move.split(':')
                fr, fc = map(int, from_pos.split(','))
                tr, tc = map(int, to_pos.split(','))
                new_b = b.copy()
                new_b[fr, fc] = 0
                new_b[tr, tc] = opponent
                
                eval = search(new_b, depth-1, alpha, beta, True, start_time)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    # Iterative deepening
    best_move = None
    best_score = -float('inf')
    legal_moves = get_legal_moves(board, player)
    
    if not legal_moves:
        return "0,0:0,0"  # Shouldn't happen
    
    # Check for immediate win
    for move in legal_moves:
        from_pos, to_pos = move.split(':')
        fr, fc = map(int, from_pos.split(','))
        tr, tc = map(int, to_pos.split(','))
        new_b = board.copy()
        new_b[fr, fc] = 0
        new_b[tr, tc] = player
        
        # Check if all pieces are connected
        pieces = np.argwhere(new_b == player)
        if len(pieces) == 0:
            continue
        visited = set()
        queue = deque([(pieces[0][0], pieces[0][1])])
        count = 0
        while queue:
            r, c = queue.popleft()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            count += 1
            for dr, dc in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and new_b[nr, nc] == player:
                    queue.append((nr, nc))
        if count == len(pieces):
            return move
    
    depth = 1
    while time.time() - start_time < 0.95 and depth <= 4:
        for move in legal_moves:
            from_pos, to_pos = move.split(':')
            fr, fc = map(int, from_pos.split(','))
            tr, tc = map(int, to_pos.split(','))
            new_b = board.copy()
            new_b[fr, fc] = 0
            new_b[tr, tc] = player
            
            score = search(new_b, depth-1, -float('inf'), float('inf'), False, start_time)
            if score > best_score:
                best_score = score
                best_move = move
        depth += 1
    
    return best_move if best_move else legal_moves[0]
