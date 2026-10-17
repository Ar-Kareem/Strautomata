
import numpy as np
import time
import random
from collections import deque

def policy(board) -> str:
    """
    Amazons AI Policy for 6x6 board.
    Strategy: Territory control using Queen's Distance BFS and Iterative Deepening Minimax.
    """
    
    # -------------------------------------------------------------------------
    # CONFIGURATION
    # -------------------------------------------------------------------------
    TIME_LIMIT = 0.92  # Seconds. strict buffer to ensure return within 1s.
    start_time = time.time()
    
    # Board Constants
    ROWS, COLS = board.shape
    ME = 1
    OPP = 2
    EMPTY = 0
    ARROW = -1
    
    DIRECTIONS = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]

    # -------------------------------------------------------------------------
    # STATE MANAGEMENT
    # -------------------------------------------------------------------------
    
    def get_legal_moves_generator(current_board, player):
        """
        Generator that yields legal moves as ((r1,c1), (r2,c2), (r3,c3)).
        Optimized for 6x6 board traversal.
        """
        # Find player amazons
        # np.argwhere is fast enough for 6x6
        amazons = np.argwhere(current_board == player)
        
        for r_from, c_from in amazons:
            # 1. Move Phase
            for dr, dc in DIRECTIONS:
                r_to, c_to = r_from + dr, c_from + dc
                
                # Slide amazon
                while 0 <= r_to < ROWS and 0 <= c_to < COLS and current_board[r_to, c_to] == EMPTY:
                    
                    # 2. Shoot Phase
                    # Conceptually: Amazon is at (r_to, c_to), (r_from, c_from) is EMPTY.
                    # We iterate arrow shots from r_to, c_to.
                    
                    for adr, adc in DIRECTIONS:
                        r_arr, c_arr = r_to + adr, c_to + adc
                        
                        while 0 <= r_arr < ROWS and 0 <= c_arr < COLS:
                            val = current_board[r_arr, c_arr]
                            
                            # Check for blocking.
                            # Standard block: val != 0.
                            # Exception: Passing through the 'vacated' square (r_from, c_from) is allowed.
                            if val != EMPTY:
                                if r_arr == r_from and c_arr == c_from:
                                    # This is the vacated square, conceptually empty. Pass through.
                                    pass
                                else:
                                    # Genuine block
                                    break
                            
                            yield ((r_from, c_from), (r_to, c_to), (r_arr, c_arr))
                            
                            # Advance arrow
                            r_arr += adr
                            c_arr += adc
                    
                    # Advance amazon move
                    r_to += dr
                    c_to += dc

    def apply_move(current_board, move):
        """Returns a new board numpy array with the move applied."""
        (r1, c1), (r2, c2), (r3, c3) = move
        new_board = current_board.copy()
        p = new_board[r1, c1]
        
        # Execute move
        new_board[r1, c1] = 0        # Vacate start
        new_board[r2, c2] = p        # Land amazon
        new_board[r3, c3] = ARROW    # Place arrow
        return new_board

    # -------------------------------------------------------------------------
    # EVALUATION HARNESS
    # -------------------------------------------------------------------------
    
    def bfs_queen_distance(current_board, player):
        """
        Calculates the minimum number of turns (Queen moves) for 'player' to reach every square.
        Returns a (6,6) array of integers. 999 indicates unreachable.
        """
        dists = np.full((ROWS, COLS), 999, dtype=int)
        queue = deque()
        
        # Initialize sources
        amazons = np.argwhere(current_board == player)
        for r, c in amazons:
            dists[r, c] = 0
            queue.append((r, c))
            
        while queue:
            r, c = queue.popleft()
            d = dists[r, c]
            next_dist = d + 1
            
            # Slide in all directions
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                
                while 0 <= nr < ROWS and 0 <= nc < COLS:
                    if current_board[nr, nc] != EMPTY:
                        # Blocked
                        break
                    
                    if dists[nr, nc] > next_dist:
                        dists[nr, nc] = next_dist
                        queue.append((nr, nc))
                    elif dists[nr, nc] < next_dist:
                        # We reached a square that was already reached faster (or same) from elsewhere.
                        # Do NOT enqueue, but we must continue sliding because the line of sight might
                        # extend to unvisited squares beyond this one.
                        pass
                    
                    nr += dr
                    nc += dc
        return dists

    def evaluate(current_board):
        """
        Heuristic Score from perspective of the player whose turn it simply is not.
        Calculates: (ME Territory - OPP Territory)
        Returns: Positive if ME is winning.
        """
        my_dists = bfs_queen_distance(current_board, ME)
        opp_dists = bfs_queen_distance(current_board, OPP)
        
        # Determine ownership
        # Owned if dist(ME) < dist(OPP) and reachable
        # Unreachable squares map to 999, so 999 < 999 is False (Neutral)
        
        reachable = (my_dists < 999) | (opp_dists < 999)
        
        me_closer = (my_dists < opp_dists) & reachable
        opp_closer = (opp_dists < my_dists) & reachable
        
        territory_score = np.sum(me_closer) - np.sum(opp_closer)
        
        # Mobility tie-breaker (squares reachable in 1 move)
        # Weighting: Territory is primary (10x), Mobility secondary (1x)
        w_terr = 10.0
        w_mob = 0.5
        
        my_mobility = np.sum(my_dists == 1)
        opp_mobility = np.sum(opp_dists == 1)
        
        score = (territory_score * w_terr) + ((my_mobility - opp_mobility) * w_mob)
        return score

    # -------------------------------------------------------------------------
    # SEARCH ENGINE
    # -------------------------------------------------------------------------
    
    def negamax(current_board, depth, alpha, beta, player):
        # Time Interrupt
        if (time.time() - start_time) > TIME_LIMIT:
            raise TimeoutError
            
        if depth == 0:
            val = evaluate(current_board)
            return val if player == ME else -val

        # Move Generation
        # Note: Using generators helps save memory, but we need to iterate to score.
        moves = list(get_legal_moves_generator(current_board, player))
        
        if not moves:
            # No moves available -> Loss
            # Score: very large negative
            return -10000 + depth # Prefer losing later if inevitable

        # Sort moves?
        # For simplicity and speed in Python, we rely on random chance or natural order
        # unless we have a specific killer heuristic. On 6x6 depth is shallow anyway.
        
        best_val = -float('inf')
        
        next_player = OPP if player == ME else ME
        
        for move in moves:
            succ_board = apply_move(current_board, move)
            
            # Recurse
            val = -negamax(succ_board, depth - 1, -beta, -alpha, next_player)
            
            if val > best_val:
                best_val = val
            
            alpha = max(alpha, val)
            if alpha >= beta:
                break
                
        return best_val

    # -------------------------------------------------------------------------
    # ROOT STRATEGY
    # -------------------------------------------------------------------------
    
    # 1. Generate Root Moves
    root_moves = list(get_legal_moves_generator(board, ME))
    if not root_moves:
        # No legal moves, return strict format to fail gracefully/wait for disqualification
        return "0,0:0,0:0,0"

    # Default fallback (random legal move)
    best_move = random.choice(root_moves)
    
    # 2. Iterative Deepening
    # Try Depth 1, then Depth 2, etc.
    MAX_DEPTH = 10
    
    try:
        for depth in range(1, MAX_DEPTH + 1):
            if time.time() - start_time > 0.8:
                # Don't start a new depth if time is tight
                break
            
            current_depth_best_move = None
            max_val = -float('inf')
            
            alpha = -float('inf')
            beta = float('inf')
            
            # Root Alpha-Beta Loop
            for move in root_moves:
                # Check within loop for granular timeout handling
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError

                succ_board = apply_move(board, move)
                
                # Call Negamax
                val = -negamax(succ_board, depth - 1, -beta, -alpha, OPP)
                
                if val > max_val:
                    max_val = val
                    current_depth_best_move = move
                
                alpha = max(alpha, val)
                
            # If we completed the depth fully, update global best
            if current_depth_best_move:
                best_move = current_depth_best_move
                
    except TimeoutError:
        # Time ran out during search; stick with best result from previous completed depth
        pass
    except Exception:
        # Fallback to random move on any unexpected error
        pass

    # -------------------------------------------------------------------------
    # FORMAT OUTPUT
    # -------------------------------------------------------------------------
    (r1, c1), (r2, c2), (r3, c3) = best_move
    return f"{r1},{c1}:{r2},{c2}:{r3},{c3}"
