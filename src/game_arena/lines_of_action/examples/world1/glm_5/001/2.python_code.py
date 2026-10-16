
import sys
import collections

def policy(board):
    """
    Main policy function to determine the next move for Lines of Action.
    Uses Minimax with Alpha-Beta pruning.
    """
    # Game Constants
    PLAYER = 1
    OPPONENT = -1
    SIZE = 8
    
    # Directions for movement lines (Horizontal, Vertical, Diagonals)
    LINE_DIRS = [(0, 1), (1, 0), (1, 1), (1, -1)]
    # Directions for connectivity check (8-way adjacency)
    CONN_DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    def count_pieces_on_line(r, c, dr, dc):
        """Count total pieces on the line passing through (r,c) with direction (dr,dc)."""
        count = 0
        # Explore positive direction
        nr, nc = r + dr, c + dc
        while 0 <= nr < SIZE and 0 <= nc < SIZE:
            if board[nr][nc] != 0:
                count += 1
            nr += dr
            nc += dc
        # Explore negative direction
        nr, nc = r - dr, c - dc
        while 0 <= nr < SIZE and 0 <= nc < SIZE:
            if board[nr][nc] != 0:
                count += 1
            nr -= dr
            nc -= dc
        return count + 1  # Include the piece itself

    def get_legal_moves(player):
        """Generate all legal moves for the given player."""
        moves = []
        for r in range(SIZE):
            for c in range(SIZE):
                if board[r][c] == player:
                    for dr, dc in LINE_DIRS:
                        dist = count_pieces_on_line(r, c, dr, dc)
                        
                        # Move positive direction
                        tr, tc = r + dr * dist, c + dc * dist
                        if 0 <= tr < SIZE and 0 <= tc < SIZE:
                            # Check path blocking (cannot jump over opponent)
                            blocked = False
                            cr, cc = r + dr, c + dc
                            while (cr, cc) != (tr, tc):
                                if board[cr][cc] == -player:
                                    blocked = True
                                    break
                                cr += dr
                                cc += dc
                            
                            if not blocked:
                                # Check landing spot (cannot land on own piece)
                                if board[tr][tc] != player:
                                    moves.append(((r, c), (tr, tc)))
                        
                        # Move negative direction
                        tr, tc = r - dr * dist, c - dc * dist
                        if 0 <= tr < SIZE and 0 <= tc < SIZE:
                            blocked = False
                            cr, cc = r - dr, c - dc
                            while (cr, cc) != (tr, tc):
                                if board[cr][cc] == -player:
                                    blocked = True
                                    break
                                cr -= dr
                                cc -= dc
                            
                            if not blocked:
                                if board[tr][tc] != player:
                                    moves.append(((r, c), (tr, tc)))
        return moves

    def get_components(player):
        """Calculate number of connected components for a player using BFS."""
        visited = [[False] * SIZE for _ in range(SIZE)]
        components = 0
        
        for r in range(SIZE):
            for c in range(SIZE):
                if board[r][c] == player and not visited[r][c]:
                    components += 1
                    # BFS
                    queue = collections.deque([(r, c)])
                    visited[r][c] = True
                    while queue:
                        ur, uc = queue.popleft()
                        for dr, dc in CONN_DIRS:
                            vr, vc = ur + dr, uc + dc
                            if 0 <= vr < SIZE and 0 <= vc < SIZE:
                                if not visited[vr][vc] and board[vr][vc] == player:
                                    visited[vr][vc] = True
                                    queue.append((vr, vc))
        return components

    def evaluate():
        """Evaluate board state. Higher score is better for PLAYER (1)."""
        my_comps = get_components(PLAYER)
        opp_comps = get_components(OPPONENT)
        
        # Win/Loss checks
        if my_comps == 1:
            return 100000
        if opp_comps == 1:
            return -100000
        
        # Heuristic: Minimize my components, maximize opponent components (fragmentation)
        # Weight connectivity heavily
        return (opp_comps - my_comps) * 100

    def minimax(depth, alpha, beta, maximizing_player):
        """Minimax algorithm with Alpha-Beta pruning."""
        # Terminal condition: depth limit or game over
        # We evaluate at every node to check for wins
        score = evaluate()
        if abs(score) >= 100000:
            return score
        if depth == 0:
            return score
            
        current_player = PLAYER if maximizing_player else OPPONENT
        moves = get_legal_moves(current_player)
        
        # If no moves, pass (evaluate current state)
        if not moves:
            return evaluate()

        if maximizing_player:
            max_eval = -float('inf')
            for (r1, c1), (r2, c2) in moves:
                # Make move
                original_dest = board[r2][c2]
                board[r1][c1] = 0
                board[r2][c2] = PLAYER
                
                eval_val = minimax(depth - 1, alpha, beta, False)
                
                # Unmake move
                board[r1][c1] = PLAYER
                board[r2][c2] = original_dest
                
                if eval_val > max_eval:
                    max_eval = eval_val
                if eval_val > alpha:
                    alpha = eval_val
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for (r1, c1), (r2, c2) in moves:
                # Make move
                original_dest = board[r2][c2]
                board[r1][c1] = 0
                board[r2][c2] = OPPONENT
                
                eval_val = minimax(depth - 1, alpha, beta, True)
                
                # Unmake move
                board[r1][c1] = OPPONENT
                board[r2][c2] = original_dest
                
                if eval_val < min_eval:
                    min_eval = eval_val
                if eval_val < beta:
                    beta = eval_val
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Execution ---
    best_move = None
    max_val = -float('inf')
    
    # Generate moves for the current player (PLAYER = 1)
    moves = get_legal_moves(PLAYER)
    
    if not moves:
        return "0,0:0,0" # Fallback, should not happen if game is not over

    # Depth 3 is a safe balance for 1 second time limit in Python
    search_depth = 3
    
    # Iterate through all possible moves to find the best one
    for move in moves:
        (r1, c1), (r2, c2) = move
        
        # Make move
        original_dest = board[r2][c2]
        board[r1][c1] = 0
        board[r2][c2] = PLAYER
        
        # Evaluate move (next turn is minimizing player)
        val = minimax(search_depth - 1, -float('inf'), float('inf'), False)
        
        # Unmake move
        board[r1][c1] = PLAYER
        board[r2][c2] = original_dest
        
        if val > max_val:
            max_val = val
            best_move = move

    if best_move:
        return f"{best_move[0][0]},{best_move[0][1]}:{best_move[1][0]},{best_move[1][1]}"
    else:
        # Fallback if something went wrong
        m = moves[0]
        return f"{m[0][0]},{m[0][1]}:{m[1][0]},{m[1][1]}"
