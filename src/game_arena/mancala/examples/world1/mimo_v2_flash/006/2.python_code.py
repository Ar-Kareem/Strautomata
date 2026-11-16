
import time
import sys
from typing import List, Tuple

# ---------------------------------------------------------
# Configuration and Constants
# ---------------------------------------------------------

TIME_LIMIT = 0.90  # Seconds (leave buffer for execution overhead)
INF = 1000000

# ---------------------------------------------------------
# Board Logic and Simulation
# ---------------------------------------------------------

def get_next_state(board: Tuple[int, ...], move: int, player_idx: int) -> Tuple[Tuple[int, ...], bool]:
    """
    Simulates a move and returns the new board state and whether the player gets another turn.
    player_idx: 0 for 'you', 1 for 'opponent'.
    """
    # Unpack board for easier access
    # Indices: 0-5: Houses, 6: Store
    # Board structure: (you_h0..you_h5, you_store, opp_h0..opp_h5, opp_store)
    you = list(board[:7])
    opp = list(board[7:])
    
    # Working with the perspective of the current player
    curr_houses = you[:6]
    curr_store = you[6]
    opp_houses = opp[:6]
    # opp_store is opp[6], which is board[13]
    
    seeds = curr_houses[move]
    if seeds == 0:
        return board, False # Should not happen in valid calls
        
    curr_houses[move] = 0
    idx = move
    extra_turn = False
    
    # Sowing seeds
    while seeds > 0:
        idx += 1
        
        # Sequence: You Houses -> You Store -> Opp Houses -> Loop
        # Map idx to board coordinates relative to start of 'you' houses (index 0)
        # 0-5: You Houses
        # 6: You Store
        # 7-12: Opp Houses
        # 13: Opp Store (SKIPPED)
        
        # We need a generic index for the board tuple
        # Board: 0..5 (You H), 6 (You S), 7..12 (Opp H), 13 (Opp S)
        
        # Calculate position
        if idx <= 5:
            # Your house
            curr_houses[idx] += 1
            last_pos = idx
            last_owner = 0
        elif idx == 6:
            # Your store
            curr_store += 1
            last_pos = 6
            last_owner = 0
            seeds -= 1
            if seeds == 0:
                extra_turn = True
                continue # Loop will break naturally
        elif idx <= 12:
            # Opponent house
            opp_houses[idx - 7] += 1
            last_pos = idx - 7
            last_owner = 1
        elif idx == 13:
            # Opponent store (SKIP)
            idx = -1 # Reset to 0 for next loop iteration (houses 0..)
            continue 
            
        seeds -= 1
        if seeds > 0:
            continue
            
        # Capture Logic
        # If last seed landed in an empty house on the current player's side
        # AND the opposite enemy house has seeds
        if last_owner == 0 and last_pos < 6 and curr_houses[last_pos] == 1:
            opp_pos = 5 - last_pos
            if opp_houses[opp_pos] > 0:
                # Capture!
                captured = opp_houses[opp_pos] + 1 # Enemy seeds + the 1 just dropped
                curr_store += captured
                curr_houses[last_pos] = 0
                opp_houses[opp_pos] = 0
                
    # Reconstruct board
    new_you = tuple(curr_houses + [curr_store])
    new_opp = tuple(opp_houses + [opp[6]])
    
    if player_idx == 0:
        return (new_you + new_opp), extra_turn
    else:
        return (new_opp + new_you), extra_turn

def is_game_over(board: Tuple[int, ...]) -> bool:
    # Check if you or opponent has no seeds in houses
    you_houses = sum(board[:6])
    opp_houses = sum(board[7:13])
    return you_houses == 0 or opp_houses == 0

def get_final_score(board: Tuple[int, ...]) -> int:
    # Returns score difference (You - Opponent)
    you_store = board[6]
    opp_store = board[13]
    
    # If game over, remaining seeds go to respective owners
    you_houses = sum(board[:6])
    opp_houses = sum(board[7:13])
    
    final_you = you_store + you_houses
    final_opp = opp_store + opp_houses
    
    return final_you - final_opp

# ---------------------------------------------------------
# Evaluation and Search
# ---------------------------------------------------------

def evaluate_board(board: Tuple[int, ...], player_idx: int) -> int:
    """
    Heuristic evaluation.
    player_idx 0 is 'you' (maximizing).
    """
    if is_game_over(board):
        score = get_final_score(board)
        return score * 1000 # Large weight for winning
    
    if player_idx == 1:
        # If evaluating from opponent's perspective during recursion, 
        # we swap board halves conceptually for the heuristic logic,
        # but easier to just swap inputs to get_score_diff logic
        pass 

    you_store = board[6]
    opp_store = board[13]
    you_houses = board[:6]
    opp_houses = board[7:13]
    
    # 1. Score Advantage
    score_diff = you_store - opp_store
    
    # 2. Free Turn Potential
    # Count seeds that would land in store if sown immediately
    free_turns = 0
    for i in range(6):
        seeds = you_houses[i]
        if seeds == 0: continue
        if (i + seeds) % 15 == 6: # 15 is total slots (6 houses + 1 store + 6 opp houses). Wait, 14 slots?
            # Total pits = 6 + 6 = 12. Store is not a pit.
            # Sequence: H(i)..H(5), Store, OppH(0)..OppH(5), then loop.
            # Distance to store = (5 - i) + 1
            # Actually, let's use the simulation for precision or simple mod arithmetic.
            # Total steps to store = (5 - i) + 1
            # If seeds == (6 - i), lands in store.
            pass
    # Let's use a simpler check for move ordering: if seeds == (6-i), it's a free turn.
    # However, for strict evaluation, let's just count store landings potential.
    
    # 3. Capture Potential (Landing in empty house)
    capture_potential = 0
    for i in range(6):
        if you_houses[i] == 0:
            # If opponent has seeds opposite, it's a threat or opportunity if we can reach it
            if opp_houses[5-i] > 0:
                capture_potential -= 1 # Threat
    
    # 4. Mobility (Number of legal moves)
    mobility = sum(1 for x in you_houses if x > 0)
    opp_mobility = sum(1 for x in opp_houses if x > 0)
    mobility_diff = mobility - opp_mobility
    
    # Weighting
    # Weights: Score (High), Free Turn (Medium), Mobility (Low)
    heuristic = (score_diff * 10) + (mobility_diff * 2) + (capture_potential * 1)
    
    return heuristic

def get_ordered_moves(board: Tuple[int, ...], player_idx: int) -> List[int]:
    """
    Returns a list of legal moves (0-5) ordered by heuristic desirability.
    Prioritizes:
    1. Moves that land in the store (extra turn).
    2. Moves that capture seeds (landing in empty house with enemy seeds opposite).
    3. Moves with more seeds (generally better for spreading).
    """
    if player_idx == 0:
        houses = board[:6]
    else:
        houses = board[7:13]
        
    moves_with_score = []
    
    for i in range(6):
        if houses[i] == 0:
            continue
            
        # Calculate expected outcome logic for sorting
        seeds = houses[i]
        score = 0
        
        # 1. Extra turn check
        # Distance to store is (5 - i) + 1 = 6 - i
        if seeds == (6 - i):
            score += 100
            
        # 2. Capture check
        # If seeds land in empty house, check opposite
        # Effective landing index on my side (0..5)
        # We simulate just the landing logic
        landing_idx = (i + seeds) # relative to start of my houses
        
        # We need to account for passing the store and opponent houses
        # Total slots in cycle = 14 (6 houses + 1 store + 6 houses)
        # Wait, standard Kalah usually 6 houses + 1 store.
        # Sequence: My H -> My Store -> Opp H -> Opp Store (SKIP) -> Loop
        # Total distributed slots = 13 (6+1+6). Opp store is skipped.
        
        # Let's stick to the specific rules provided:
        # Sequence: you[i+1]..you[5], you[6], opponent[0]..opponent[5], you[0]..
        # Skips opponent[6].
        
        # Re-calculate exact landing for heuristic sorting
        curr_idx = i
        rem = seeds
        while rem > 0:
            curr_idx += 1
            if curr_idx == 6: # You store
                pass
            elif curr_idx == 13: # Opp store (Skip)
                curr_idx = 0 # Loop back to you[0] effectively
                # Actually logic is: "repeat as needed".
                # We can just modulo 14 and handle the skip? 
                # No, simpler to just trace.
                # Wait, if we hit opp store (index 13 in 0..13 mapping), we skip.
                # But the rule says "Skip opponent[6]".
                # Opponent indices are 0..6.
                # Let's just use the get_next_state logic to score the result?
                # Too expensive for sorting. Let's use a fast approx.
                pass
            
            # Approximation for sorting:
            # Just check if the move lands in store (score 100)
            # Or lands in empty house on my side (potential capture 50)
            # Or lands in empty house on opp side (prevents enemy capture? 10)
            
            # Simplified logic:
            final_owner = -1
            final_pos = -1
            temp_idx = i
            temp_rem = seeds
            while temp_rem > 0:
                temp_idx += 1
                if temp_idx == 6:
                    final_owner = 0 # My store
                    final_pos = 6
                    temp_rem -= 1
                    if temp_rem == 0: break
                    continue # Next is Opp H0
                if temp_idx == 13: # Opp Store (Skip)
                    temp_idx = 0 # Back to My H0
                    continue
                
                if temp_idx < 6:
                    final_owner = 0 # My house
                    final_pos = temp_idx
                else:
                    final_owner = 1 # Opp house
                    final_pos = temp_idx - 7
                temp_rem -= 1
            
            if final_owner == 0 and final_pos == 6:
                score += 200 # Extra turn is best
            elif final_owner == 0 and final_pos < 6:
                # Landed in my house
                if houses[final_pos] == 0: # Was empty (before adding 1)
                    if board[7 + (5 - final_pos)] > 0: # Opp house has seeds
                        score += 150 # Capture!
                    else:
                        score += 20 # Safe land
                else:
                    score += 10 # Just a move
            else:
                # Landed in opp house
                score += 5
                
            break # Only looking for last seed landing
            
        moves_with_score.append((i, score))
    
    # Sort by score descending
    moves_with_score.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in moves_with_score]

def minimax(board: Tuple[int, ...], depth: int, alpha: int, beta: int, player_idx: int, start_time: float) -> Tuple[int, int]:
    """
    Minimax with Alpha-Beta pruning.
    Returns (best_move, best_value).
    If depth == 0 or game over, returns (-1, eval).
    """
    if is_game_over(board):
        return -1, get_final_score(board) * 1000
        
    if depth == 0:
        return -1, evaluate_board(board, player_idx)
        
    # Time check
    if time.time() - start_time > TIME_LIMIT:
        return -1, evaluate_board(board, player_idx)

    # Determine current player's houses based on perspective
    # player_idx 0 = You (Max), player_idx 1 = Opponent (Min)
    
    # Get legal moves
    moves = get_ordered_moves(board, player_idx)
    
    best_move = -1
    
    if player_idx == 0: # Maximize
        max_eval = -INF
        for move in moves:
            new_board, extra_turn = get_next_state(board, move, player_idx)
            if extra_turn:
                # If extra turn, recurse with same player, depth not decreased
                # or decreased? Usually depth counts moves. Let's keep depth same for extra turn to see further.
                _, eval_val = minimax(new_board, depth, alpha, beta, 0, start_time)
            else:
                _, eval_val = minimax(new_board, depth - 1, alpha, beta, 1, start_time)
            
            if eval_val > max_eval:
                max_eval = eval_val
                best_move = move
            
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return best_move, max_eval
    else: # Minimize
        min_eval = INF
        for move in moves:
            new_board, extra_turn = get_next_state(board, move, player_idx)
            if extra_turn:
                _, eval_val = minimax(new_board, depth, alpha, beta, 1, start_time)
            else:
                _, eval_val = minimax(new_board, depth - 1, alpha, beta, 0, start_time)
            
            if eval_val < min_eval:
                min_eval = eval_val
                best_move = move # We don't really need best move from opponent except for tracking
            
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return best_move, min_eval

# ---------------------------------------------------------
# Main Policy Interface
# ---------------------------------------------------------

def policy(you: List[int], opponent: List[int]) -> int:
    """
    Main entry point for the agent.
    """
    start_time = time.time()
    
    # Convert input lists to internal board representation
    # Tuple is hashable and faster
    # Structure: You[0..6], Opp[0..6]
    board = tuple(you + opponent)
    
    # Check immediate win/capture to save time?
    # Let's rely on search.
    
    # Iterative Deepening
    best_move = -1
    current_depth = 1
    
    # Ensure at least one move is found (move 0 is default if something fails, but it should never fail)
    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        return 0 # Should not happen per constraints
    best_move = legal_moves[0]
    
    while True:
        # Check time before starting new depth
        if time.time() - start_time > TIME_LIMIT * 0.8: # Leave buffer
            break
            
        move, val = minimax(board, current_depth, -INF, INF, 0, start_time)
        
        if move != -1:
            best_move = move
        
        current_depth += 1
        
    return best_move
