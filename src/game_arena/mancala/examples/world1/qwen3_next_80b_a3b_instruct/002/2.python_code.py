
import copy
import sys

def policy(you: list[int], opponent: list[int]) -> int:
    # Get all legal moves (non-empty houses)
    legal_moves = [i for i in range(6) if you[i] > 0]
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # For performance, use minimax with alpha-beta pruning
    # Depth limit based on total seeds to avoid deep search with many seeds
    total_seeds = sum(you) + sum(opponent)
    depth = 4 if total_seeds > 36 else 6  # Deeper when fewer seeds
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    # Try each legal move and evaluate with minimax
    for move in legal_moves:
        # Simulate the move
        new_you, new_opponent, extra_move = simulate_move(you, opponent, move)
        
        # Evaluate the resulting state
        score = minimax(new_you, new_opponent, depth - 1, -float('inf'), float('inf'), False, extra_move)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def simulate_move(you, opponent, move_idx):
    # Create deep copies to avoid modifying original
    new_you = you.copy()
    new_opponent = opponent.copy()
    
    seeds = new_you[move_idx]
    new_you[move_idx] = 0  # Empty the chosen house
    
    current_player = 'you'
    current_index = move_idx + 1
    remaining_seeds = seeds
    
    # Distribute seeds
    while remaining_seeds > 0:
        if current_player == 'you':
            if current_index < 6:  # Your houses
                new_you[current_index] += 1
                remaining_seeds -= 1
            elif current_index == 6:  # Your store
                new_you[6] += 1
                remaining_seeds -= 1
            # When we reach the end of your houses, move to opponent
            if current_index >= 6:
                current_player = 'opponent'
                current_index = 0
                continue  # Skip the opponent's store for now
        else:  # opponent's turn to distribute
            if current_index < 6:  # Opponent's houses
                new_opponent[current_index] += 1
                remaining_seeds -= 1
            # We're skipping opponent's store (index 6) during distribution
            if current_index >= 5:  # Reached end of opponent's houses
                current_player = 'you'
                current_index = 0
                continue  # Go back to your houses
        
        current_index += 1
        # Wrap around if needed
        if current_index >= 6 and current_player == 'you':
            current_player = 'opponent'
            current_index = 0
        elif current_index >= 6 and current_player == 'opponent':
            current_player = 'you'
            current_index = 0
    
    # Now determine the last seed's location and handle special rules
    # We need to know exactly where the last seed was dropped
    # Re-simulate to track last seed position
    temp_you = you.copy()
    temp_opponent = opponent.copy()
    seeds = temp_you[move_idx]
    temp_you[move_idx] = 0
    current_player = 'you'
    current_index = move_idx + 1
    remaining_seeds = seeds
    
    last_position = None  # (player, index)
    
    while remaining_seeds > 0:
        if current_player == 'you':
            if current_index < 6:
                temp_you[current_index] += 1
                last_position = ('you', current_index)
                remaining_seeds -= 1
            elif current_index == 6:
                temp_you[6] += 1
                last_position = ('you', 6)
                remaining_seeds -= 1
            if current_index >= 6:
                current_player = 'opponent'
                current_index = 0
                continue
        else:
            if current_index < 6:
                temp_opponent[current_index] += 1
                last_position = ('opponent', current_index)
                remaining_seeds -= 1
            if current_index >= 5:
                current_player = 'you'
                current_index = 0
                continue
        
        current_index += 1
        if current_index >= 6 and current_player == 'you':
            current_player = 'opponent'
            current_index = 0
        elif current_index >= 6 and current_player == 'opponent':
            current_player = 'you'
            current_index = 0
    
    # Check for extra move: last seed in own store
    extra_move = False
    if last_position == ('you', 6):
        extra_move = True
    
    # Check for capture: last seed in own house (0-5) and it was empty before, and opposite has seeds
    if last_position[0] == 'you' and 0 <= last_position[1] <= 5:
        # Check if that house was empty before we dropped the seed
        original_seeds_in_house = you[move_idx]
        # We need to know the state before we made the move
        # But we're tracking the final state, so we need to simulate the final drop to see if it was 0 before
        # Instead, let's simulate just the final step to calculate what the seed count was before the last drop
        
        # Recompute state before the last seed drop
        pre_last_you = you.copy()
        pre_last_opponent = opponent.copy()
        seeds = pre_last_you[move_idx]
        pre_last_you[move_idx] = 0
        
        # Drop seeds except the last one
        current_player = 'you'
        current_index = move_idx + 1
        remaining_seeds = seeds - 1  # All except the last one
        
        while remaining_seeds > 0:
            if current_player == 'you':
                if current_index < 6:
                    pre_last_you[current_index] += 1
                    remaining_seeds -= 1
                elif current_index == 6:
                    pre_last_you[6] += 1
                    remaining_seeds -= 1
                if current_index >= 6:
                    current_player = 'opponent'
                    current_index = 0
                    continue
            else:
                if current_index < 6:
                    pre_last_opponent[current_index] += 1
                    remaining_seeds -= 1
                if current_index >= 5:
                    current_player = 'you'
                    current_index = 0
                    continue
            
            current_index += 1
            if current_index >= 6 and current_player == 'you':
                current_player = 'opponent'
                current_index = 0
            elif current_index >= 6 and current_player == 'opponent':
                current_player = 'you'
                current_index = 0
        
        # Check if the house where last seed lands was empty
        last_house_index = last_position[1]
        if pre_last_you[last_house_index] == 0:
            # Check if opponent's opposite house has seeds
            opponent_opposite_index = 5 - last_house_index
            if pre_last_opponent[opponent_opposite_index] > 0:
                # Capture! Move both seeds to your store
                new_you[6] += 1 + pre_last_opponent[opponent_opposite_index]
                new_opponent[opponent_opposite_index] = 0
                new_you[last_house_index] = 0  # The captured seed is now in store
    
    return new_you, new_opponent, extra_move

def minimax(you, opponent, depth, alpha, beta, maximizing_player, extra_move):
    # Check if game is over
    if sum(you[0:6]) == 0 or sum(opponent[0:6]) == 0:
        # End of game: move remaining seeds to stores
        final_you = you.copy()
        final_opponent = opponent.copy()
        final_you[6] += sum(final_you[0:6])
        final_opponent[6] += sum(final_opponent[0:6])
        return final_you[6] - final_opponent[6]
    
    # Depth limit reached
    if depth == 0:
        return you[6] - opponent[6]
    
    if maximizing_player:
        best_score = -float('inf')
        legal_moves = [i for i in range(6) if you[i] > 0]
        
        for move in legal_moves:
            new_you, new_opponent, new_extra_move = simulate_move(you, opponent, move)
            
            # If extra move, it's still your turn (maximizing player)
            if new_extra_move:
                score = minimax(new_you, new_opponent, depth, alpha, beta, True, True)
            else:
                # Switch to minimizing player (opponent's turn)
                score = minimax(new_you, new_opponent, depth - 1, alpha, beta, False, False)
             
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break  # Beta cutoff
        
        return best_score
    else:
        best_score = float('inf')
        legal_moves = [i for i in range(6) if opponent[i] > 0]
        
        for move in legal_moves:
            # Swap roles for opponent's move: opponent becomes the "you" state
            new_opponent, new_you, new_extra_move = simulate_move(opponent, you, move)
            
            # If opponent gets extra move, it's still their turn (minimizing)
            if new_extra_move:
                score = minimax(new_you, new_opponent, depth, alpha, beta, False, True)
            else:
                # Switch to maximizing player (your turn)
                score = minimax(new_you, new_opponent, depth - 1, alpha, beta, True, False)
            
            best_score = min(best_score, score)
            beta = min(beta, best_score)
            if beta <= alpha:
                break  # Alpha cutoff
        
        return best_score
