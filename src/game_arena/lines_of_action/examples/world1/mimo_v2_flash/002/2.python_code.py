
import numpy as np
import sys

# Increase recursion depth to ensure the search can complete
sys.setrecursionlimit(2000)

def policy(board) -> str:
    """
    AI Policy for Lines of Action.
    Uses Alpha-Beta search with a heuristic focusing on connectivity, center control, and mobility.
    """
    
    # --- 1. CONSTANTS & STATE ---
    MAX_DEPTH = 3
    INF = 100000
    
    # Convert board to numpy array for easier processing
    # board is list of lists or np array. Ensure it's int.
    board = np.array(board, dtype=np.int8)
    height, width = board.shape
    
    my_piece = 1
    opp_piece = -1
    empty = 0
    
    # --- 2. HELPER FUNCTIONS ---
    
    def get_valid_moves(player, current_board):
        """
        Generates all valid moves for the given player on the current board.
        Returns list of (from_r, from_c, to_r, to_c).
        """
        moves = []
        # Find all pieces of the current player
        pieces = np.argwhere(current_board == player)
        
        for (r, c) in pieces:
            # Check 8 directions: (dr, dc)
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
            
            for dr, dc in directions:
                # Count pieces on the line (row, col, or diag)
                # We iterate along the line until we hit the board edge
                count = 0
                curr_r, curr_c = r + dr, c + dc
                
                # Count strictly along the line until edge
                while 0 <= curr_r < height and 0 <= curr_c < width:
                    # Count friendly or enemy pieces
                    if current_board[curr_r, curr_c] != 0:
                        count += 1
                    curr_r += dr
                    curr_c += dc
                
                # The move distance must be exactly equal to the count
                # Move destination is count steps from the current position
                dest_r = r + dr * (count + 1) # +1 because we start looking from adjacent cell
                dest_c = c + dc * (count + 1)
                
                # Boundary check for the calculated destination
                if 0 <= dest_r < height and 0 <= dest_c < width:
                    # Check if path is blocked by enemy
                    # We must ensure all cells between (r,c) and (dest_r,dest_c) are NOT enemy.
                    # Actually, the rule says "may jump over friendly but may not jump over enemy".
                    # Since we count ALL pieces on the line, the path cells are those strictly between.
                    path_blocked = False
                    for step in range(1, count + 1):
                        check_r = r + dr * step
                        check_c = c + dc * step
                        if current_board[check_r, check_c] == -player: # Enemy piece blocks
                            path_blocked = True
                            break
                    
                    if not path_blocked:
                        # Check if destination is valid (empty or enemy)
                        target = current_board[dest_r, dest_c]
                        if target == 0 or target == -player:
                            moves.append((r, c, dest_r, dest_c))
                            
        return moves

    def get_groups(player, current_board):
        """
        Calculates disjoint groups of player's pieces using 8-way connectivity.
        Returns list of sets of coordinates.
        """
        visited = set()
        groups = []
        pieces = set(map(tuple, np.argwhere(current_board == player)))
        
        for start in pieces:
            if start in visited:
                continue
            
            # BFS to find connected component
            group = set()
            stack = [start]
            visited.add(start)
            
            while stack:
                r, c = stack.pop()
                group.add((r, c))
                
                # Check 8 neighbors
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0: continue
                        nr, nc = r + dr, c + dc
                        if (nr, nc) in pieces and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            stack.append((nr, nc))
            
            groups.append(group)
            
        return groups

    def check_win_loss(player, current_board):
        """
        Returns (is_win, is_loss) for the player who just moved (or current state).
        """
        # Win: All pieces connected in one group
        my_pieces = np.count_nonzero(current_board == player)
        if my_pieces > 0:
            my_groups = get_groups(player, current_board)
            if len(my_groups) == 1:
                return True, False # Win
        
        # Loss: Opponent has no pieces (rare but possible) or opponent has >0 pieces but we can't move?
        # Actually, "connect all your pieces" is the primary win. 
        # Capturing all pieces is also a win.
        opp_pieces = np.count_nonzero(current_board == -player)
        if opp_pieces == 0:
            return True, False # Win
        
        # If we have no pieces (captured entirely)
        if my_pieces == 0:
            return False, True
            
        return False, False

    def get_score(player, current_board):
        """
        Heuristic Evaluation Function.
        """
        opp = -player
        
        # 1. Check Win/Loss (immediate)
        is_win, is_loss = check_win_loss(player, current_board)
        if is_loss: return -INF
        if is_win: return INF
        
        # 2. Mobility (Legal moves count)
        my_moves = len(get_valid_moves(player, current_board))
        if my_moves == 0:
            return -INF # Stuck -> Loss
            
        # 3. Connectivity Metric
        # We want 1 group (score 1.0). We want to merge groups.
        my_groups = get_groups(player, current_board)
        my_count = sum(len(g) for g in my_groups)
        
        # Connectivity Score: Heuristic to encourage merging
        # Base: 1.0 if connected. Penalty for every extra group.
        # More refined: Bonus for reducing number of groups.
        conn_score = 0.0
        if len(my_groups) > 0:
            if len(my_groups) == 1:
                conn_score = 10.0 # Good
            else:
                # Calculate sum of squared distances between group centers to encourage merging distant groups
                # Or simple penalty: -2 per group
                conn_score = -2.0 * (len(my_groups) - 1)
                
                # Add "inverse distance" heuristic between groups to encourage merging
                if len(my_groups) >= 2:
                    centers = []
                    for g in my_groups:
                        r_vals = [x[0] for x in g]
                        c_vals = [x[1] for x in g]
                        centers.append((sum(r_vals)/len(g), sum(c_vals)/len(g)))
                    
                    dist_penalty = 0
                    for i in range(len(centers)):
                        for j in range(i+1, len(centers)):
                            dist = abs(centers[i][0] - centers[j][0]) + abs(centers[i][1] - centers[j][1])
                            dist_penalty += dist * 0.1
                    conn_score -= dist_penalty

        # 4. Center Control / Coordination
        # Manhattan distance from center (3.5, 3.5). Closer is better.
        # This helps pieces stay mobile and connected.
        center_r, center_c = 3.5, 3.5
        center_score = 0
        pieces = np.argwhere(current_board == player)
        for r, c in pieces:
            center_score -= (abs(r - center_r) + abs(c - center_c))
        
        # 5. Opponent Mobility (Negative)
        opp_moves = len(get_valid_moves(opp, current_board))
        opp_score = 0
        if opp_moves == 0:
            opp_score = INF # Opponent stuck -> Win
        else:
            opp_score = -opp_moves * 0.1 # Slight penalty if opponent has many options
        
        # 6. Material (Capture)
        # Fewer opponent pieces is better
        mat_score = (np.count_nonzero(current_board == opp) - np.count_nonzero(current_board == player)) * 2.0
        
        # Combine
        # Weights: Connectivity (Primary), Center (Support), Mobility (Safety)
        total = conn_score * 5.0 + center_score * 0.5 + mat_score + my_moves * 0.1 + opp_score * 0.1
        
        return total

    # --- 3. SEARCH (ALPHA-BETA) ---

    def alpha_beta(current_board, depth, alpha, beta, maximizing_player, player):
        """
        Recursive Alpha-Beta search.
        maximizing_player: True if we are evaluating from current player's perspective in this node.
        """
        # Leaf node
        if depth == 0:
            return get_score(player, current_board) if maximizing_player else get_score(player, current_board)
        
        # Note: The logic here is slightly tricky.
        # We are 'player' (the AI).
        # The root call is maximizing_player=True.
        # Recursive calls alternate maximizing_player.
        
        current_moves = get_valid_moves(player if maximizing_player else -player, current_board)
        
        # If no moves, it's a terminal state
        if not current_moves:
            # If it's our turn and no moves, bad.
            # If it's opponent turn and no moves, good for us.
            if maximizing_player:
                return -INF
            else:
                return INF

        if maximizing_player:
            max_eval = -INF
            for move in current_moves:
                r, c, nr, nc = move
                # Make move
                old_val = current_board[r, c]
                target_val = current_board[nr, nc]
                current_board[r, c] = 0
                current_board[nr, nc] = old_val
                
                # Check immediate win
                is_win, _ = check_win_loss(player, current_board)
                if is_win:
                    eval = INF
                else:
                    eval = alpha_beta(current_board, depth - 1, alpha, beta, False, player)
                
                # Undo move
                current_board[r, c] = old_val
                current_board[nr, nc] = target_val
                
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = INF
            for move in current_moves:
                r, c, nr, nc = move
                # Make move (Opponent)
                old_val = current_board[r, c]
                target_val = current_board[nr, nc]
                current_board[r, c] = 0
                current_board[nr, nc] = old_val
                
                # Check opponent win
                _, is_loss = check_win_loss(-player, current_board)
                if is_loss:
                    eval = -INF # Opponent won, bad for us
                else:
                    eval = alpha_beta(current_board, depth - 1, alpha, beta, True, player)
                
                # Undo move
                current_board[r, c] = old_val
                current_board[nr, nc] = target_val
                
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    # --- 4. MAIN EXECUTION ---

    # Root Search
    best_move = None
    best_value = -INF
    
    # Get legal moves for root
    root_moves = get_valid_moves(my_piece, board)
    
    if not root_moves:
        # Should not happen if we are playing, but handle gracefully
        # Return a dummy move or let timeout handle it? 
        # We must return a legal move string. If no moves, we can't. 
        # But if no moves, the game is over. We shouldn't be called.
        # Let's try to return something safe or let it crash (illegal state).
        # Actually, rules say "return a legal move string". If none exist, we are stuck.
        # Let's return a dummy string, hoping the arena handles game over.
        return "0,0:0,0" 

    # Sort moves slightly by immediate heuristic to improve Alpha-Beta pruning
    # (Basic optimization)
    root_moves.sort(key=lambda m: heuristic_sort(board, m, my_piece), reverse=True)

    for move in root_moves:
        r, c, nr, nc = move
        
        # Execute Move
        old_val = board[r, c]
        target_val = board[nr, nc]
        board[r, c] = 0
        board[nr, nc] = old_val
        
        # Check Immediate Win
        is_win, _ = check_win_loss(my_piece, board)
        if is_win:
            best_move = move
            board[r, c] = old_val
            board[nr, nc] = target_val
            break # Found a winning move, take it
            
        # Recursive Search
        val = alpha_beta(board, MAX_DEPTH - 1, -INF, INF, False, my_piece)
        
        # Undo Move
        board[r, c] = old_val
        board[nr, nc] = target_val
        
        if val > best_value:
            best_value = val
            best_move = move

    # Fallback if something weird happens (shouldn't)
    if best_move is None and root_moves:
        best_move = root_moves[0]

    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"


def heuristic_sort(board, move, player):
    """Quick heuristic for sorting root moves."""
    r, c, nr, nc = move
    # Prefer captures
    if board[nr, nc] != 0:
        return 10
    # Prefer moves towards center (3.5, 3.5)
    dist_after = abs(nr - 3.5) + abs(nc - 3.5)
    return -dist_after
