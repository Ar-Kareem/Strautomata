
import copy
import math
import time

def policy(you: list[int], opponent: list[int]) -> int:
    """Return the best move (0-5) according to a depth-limited minimax search."""
    # Use iterative deepening with time limit for robustness
    start_time = time.time()
    time_limit = 0.9  # seconds, leave some margin
    
    # Helper functions
    def game_over(player, opp):
        """Check if game is over (one side has no seeds in houses)."""
        return all(s == 0 for s in player[:6]) or all(s == 0 for s in opp[:6])
    
    def collect_remaining(player, opp):
        """If game is over, collect all remaining seeds to respective stores."""
        p = player.copy()
        o = opp.copy()
        if all(s == 0 for s in p[:6]):
            # Player has no seeds, opponent collects all their seeds
            o[6] += sum(o[:6])
            for i in range(6):
                o[i] = 0
        elif all(s == 0 for s in o[:6]):
            # Opponent has no seeds, player collects
            p[6] += sum(p[:6])
            for i in range(6):
                p[i] = 0
        return p, o
    
    def evaluate(player, opp, is_maximizing=True):
        """Evaluation function from perspective of the original player."""
        # If game is over, collect remaining seeds first
        if game_over(player, opp):
            p_final, o_final = collect_remaining(player, opp)
            score_diff = p_final[6] - o_final[6]
            if score_diff > 0:
                return 10000 + score_diff  # winning
            elif score_diff < 0:
                return -10000 + score_diff  # losing
            else:
                return 0  # draw
        
        # Heuristic: store difference is most important, plus potential from houses
        store_diff = player[6] - opp[6]
        house_diff = sum(player[:6]) - sum(opp[:6])
        return store_diff * 10 + house_diff
    
    def simulate_move(player, opp, house):
        """
        Simulate a move from the given player's perspective.
        Returns (new_player, new_opp, extra_move)
        """
        # Make copies to avoid modifying original
        player = player.copy()
        opp = opp.copy()
        
        seeds = player[house]
        if seeds == 0:
            raise ValueError("Illegal move: empty house")
        
        player[house] = 0
        current = 'player'
        idx = house + 1
        
        while seeds > 0:
            if current == 'player':
                if idx < 7:  # player's side including store
                    if idx == 6:  # player's store
                        player[6] += 1
                        seeds -= 1
                        if seeds == 0:
                            # Last seed in store -> extra move
                            return player, opp, True
                        idx += 1
                    else:  # player's house
                        # Check if this house is empty before sowing the last seed
                        last_seed = (seeds == 1)
                        was_empty = (player[idx] == 0)
                        
                        player[idx] += 1
                        seeds -= 1
                        
                        if seeds == 0 and last_seed and was_empty:
                            # Capture condition
                            opposite_idx = 5 - idx
                            if opp[opposite_idx] > 0:
                                # Capture both the last seed and opposite seeds
                                player[6] += player[idx] + opp[opposite_idx]
                                player[idx] = 0
                                opp[opposite_idx] = 0
                        
                        if seeds == 0:
                            return player, opp, False
                        
                        idx += 1
                else:
                    # Switch to opponent's side
                    current = 'opponent'
                    idx = 0
            else:  # current == 'opponent'
                if idx < 6:  # opponent's houses only (skip store)
                    opp[idx] += 1
                    seeds -= 1
                    if seeds == 0:
                        return player, opp, False
                    idx += 1
                else:
                    # Back to player's side
                    current = 'player'
                    idx = 0
        
        # Should never reach here
        return player, opp, False
    
    def minimax(player, opp, depth, alpha, beta, maximizing, start_time, time_limit):
        """Minimax with alpha-beta pruning from perspective of original player."""
        # Check time limit occasionally
        if depth % 3 == 0 and time.time() - start_time > time_limit:
            raise TimeoutError
        
        if depth == 0 or game_over(player, opp):
            return evaluate(player, opp, maximizing)
        
        legal_moves = [i for i in range(6) if player[i] > 0]
        
        if maximizing:
            max_eval = -math.inf
            for move in legal_moves:
                new_player, new_opp, extra = simulate_move(player, opp, move)
                
                if extra:
                    # Same player moves again
                    eval = minimax(new_player, new_opp, depth-1, alpha, beta, True, start_time, time_limit)
                else:
                    # Switch perspective for opponent's turn
                    eval = minimax(new_opp, new_player, depth-1, alpha, beta, False, start_time, time_limit)
                
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for move in legal_moves:
                new_player, new_opp, extra = simulate_move(player, opp, move)
                
                if extra:
                    # Same player (now minimizing) moves again
                    eval = minimax(new_player, new_opp, depth-1, alpha, beta, False, start_time, time_limit)
                else:
                    # Switch perspective for opponent's turn (now maximizing)
                    eval = minimax(new_opp, new_player, depth-1, alpha, beta, True, start_time, time_limit)
                
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    # Root: find best move
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    # Quick check for immediate extra move or capture (greedy)
    # These are often good and can save search time
    best_move = None
    best_score = -math.inf
    
    # Try iterative deepening
    depth = 1
    final_move = legal_moves[0]  # default
    
    try:
        while time.time() - start_time < time_limit:
            current_best_move = None
            current_best_score = -math.inf
            
            for move in legal_moves:
                new_you, new_opp, extra = simulate_move(you, opponent, move)
                
                if extra:
                    score = minimax(new_you, new_opp, depth-1, -math.inf, math.inf, True, start_time, time_limit)
                else:
                    score = minimax(new_opp, new_you, depth-1, -math.inf, math.inf, False, start_time, time_limit)
                
                if score > current_best_score:
                    current_best_score = score
                    current_best_move = move
            
            if current_best_move is not None:
                final_move = current_best_move
                best_score = current_best_score
            
            depth += 1
            
            # If we found a winning move (score very high), break early
            if best_score > 9000:
                break
                
    except (TimeoutError, KeyboardInterrupt):
        # Time's up, use the best found so far
        pass
    
    return final_move
