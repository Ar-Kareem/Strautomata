
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    # Convert to numpy arrays for easier handling
    you_arr = np.array(you, dtype=int)
    opponent_arr = np.array(opponent, dtype=int)
    
    # Get legal moves (houses with seeds)
    legal_moves = [i for i in range(6) if you_arr[i] > 0]
    if not legal_moves:
        return 0  # Should not happen per problem statement
    
    # If only one move, return it immediately
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Evaluation function: difference in stores + slight bias for having seeds on board
    def evaluate_state(you_board, opp_board):
        my_store = you_board[6]
        opp_store = opp_board[6]
        my_seeds_on_board = np.sum(you_board[:6])
        opp_seeds_on_board = np.sum(opp_board[:6])
        # Weight board seeds lightly to encourage active play
        return (my_store - opp_store) + (my_seeds_on_board - opp_seeds_on_board) * 0.1
    
    # Simulate a move and return new state (you, opponent) after move and any captures
    # Also returns whether player gets an extra move
    def simulate_move(you_board, opp_board, move_index):
        # Make a copy of the board
        new_you = you_board.copy()
        new_opp = opp_board.copy()
        
        seeds = new_you[move_index]
        new_you[move_index] = 0  # Empty the house
        
        current_player = 'you'
        current_index = move_index + 1
        distributed = 0
        
        # Distribute seeds one by one
        while distributed < seeds:
            if current_player == 'you':
                if current_index < 6:  # My house (not store)
                    new_you[current_index] += 1
                    distributed += 1
                    if distributed == seeds:
                        last_position = ('you', current_index)
                        break
                    current_index += 1
                elif current_index == 6:  # My store
                    new_you[current_index] += 1
                    distributed += 1
                    if distributed == seeds:
                        last_position = ('you', 6)
                        break
                    current_index = 0
                    current_player = 'opponent'
                else:
                    current_index = 0
                    current_player = 'opponent'
            else:  # opponent
                if current_index < 6:  # Opponent's house
                    new_opp[current_index] += 1
                    distributed += 1
                    if distributed == seeds:
                        last_position = ('opponent', current_index)
                        break
                    current_index += 1
                else:  # Opponent's store (skip)
                    current_index = 0
                    current_player = 'you'
        
        # Check for extra move: last seed lands in your store
        extra_move = False
        if last_position == ('you', 6):
            extra_move = True
        
        # Check for capture: last seed landed in your house (0-5), it was empty before, and opponent's opposite has seeds
        if last_position[0] == 'you' and 0 <= last_position[1] <= 5:
            # Check if the house was empty before (in the original board state before this move)
            # But note: we are using new_you after putting the last seed.
            # So to know if it was empty before, we need to check the state just before this seed was added.
            # Since we only added one seed, the house was empty if new_you[last_position[1]] == 1
            if new_you[last_position[1]] == 1:  # Was empty before, now has one
                opposite_index = 5 - last_position[1]
                if new_opp[opposite_index] > 0:
                    # Capture: take the seed in your house and all in opponent's opposite house
                    captured = 1 + new_opp[opposite_index]
                    new_you[6] += captured
                    new_you[last_position[1]] = 0
                    new_opp[opposite_index] = 0
        
        return new_you, new_opp, extra_move
    
    # We'll do a depth-2 minimax with alpha-beta pruning
    # But given time, we'll use depth=2 with full expansion (6 moves max at each level => 36 total, feasible)
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        # Simulate our move
        new_you, new_opp, extra_move = simulate_move(you_arr, opponent_arr, move)
        
        # Evaluate immediate state after our move
        if extra_move:
            # We get another move immediately. We need to simulate the best next move (depth=2)
            # But we can now choose any of our (new) non-zero moves in the new state.
            # We simulate the best possible response for us from the new state (then opponent moves)
            # So it's a two-ply look ahead
            our_legal_moves_after = [i for i in range(6) if new_you[i] > 0]
            if not our_legal_moves_after:
                score = evaluate_state(new_you, new_opp)
            else:
                # Simulate our second move (the best move we can make after the extra move)
                best_score_after = float('-inf')
                for next_move in our_legal_moves_after:
                    next_you, next_opp, _ = simulate_move(new_you, new_opp, next_move)
                    score_after = evaluate_state(next_you, next_opp)
                    best_score_after = max(best_score_after, score_after)
                score = best_score_after
        else:
            # Opponent gets a turn in response. We look at their best move
            opp_legal_moves = [i for i in range(6) if new_opp[i] > 0]
            if not opp_legal_moves:
                score = evaluate_state(new_you, new_opp)
            else:
                # Simulate opponent's best move (minimizing our score)
                worst_score_for_us = float('inf')
                for opp_move in opp_legal_moves:
                    opp_new_you, opp_new_opp, _ = simulate_move(new_opp, new_you, opp_move)
                    # Note: After opponent moves, it's our turn again. We swap the roles: 
                    # The state becomes: opponent_new_opp is now "you" (because we are now the next player)
                    # and opponent_new_you is now "opponent"
                    # But we are in the perspective of the original player (you)
                    # So we evaluate from the perspective of the original "you"
                    final_you = opp_new_opp
                    final_opp = opp_new_you
                    opp_score = evaluate_state(final_you, final_opp)
                    worst_score_for_us = min(worst_score_for_us, opp_score)
                score = worst_score_for_us
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
