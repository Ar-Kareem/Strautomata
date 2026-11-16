
import math

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Implements a move-selection policy for the game Kalah.

    The policy uses a simple minimax-like approach with a limited search depth.
    It prioritizes moves that lead to an immediate extra turn or a capture,
    and then tries to maximize the difference in stones.
    """

    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        return -1  # Should not happen based on problem description

    best_move = -1
    best_score = -math.inf

    for move in legal_moves:
        # Simulate the move
        new_you, new_opponent, extra_turn, captured_stones = simulate_move(you, opponent, move)

        current_score = new_you[6] - new_opponent[6]  # Score based on stone difference

        # Prioritize extra turns and captures heavily
        if extra_turn:
            current_score += 100  # Large bonus for an extra turn
            # If we get an extra turn, we want to consider the next best move from that state
            next_best_score_after_extra_turn = -math.inf
            for next_move in [i for i in range(6) if new_you[i] > 0]:
                next_new_you, next_new_opponent, _, _ = simulate_move(new_you, new_opponent, next_move)
                next_best_score_after_extra_turn = max(next_best_score_after_extra_turn, next_new_you[6] - next_new_opponent[6])
            current_score += next_best_score_after_extra_turn / 2 # Add half of the value of the next move
        elif captured_stones > 0:
            current_score += captured_stones * 2  # Bonus for captured stones

        # Basic lookahead: consider the opponent's best response to our move
        # We assume the opponent also plays optimally to maximize their score
        if not extra_turn:
            opponent_best_response_score = math.inf
            opponent_legal_moves = [i for i in range(6) if new_opponent[i] > 0]
            if not opponent_legal_moves:
                 # If opponent has no legal moves, game ends for them. We just count remaining stones.
                opponent_remaining_stones = sum(new_opponent[k] for k in range(6))
                opponent_best_response_score = -(new_you[6] - (new_opponent[6] + opponent_remaining_stones))
            else:
                for opp_move in opponent_legal_moves:
                    opp_new_opponent, opp_new_you, opp_extra_turn, opp_captured_stones = simulate_move(new_opponent, new_you, opp_move)
                    opp_score_after_response = opp_new_opponent[6] - opp_new_you[6]
                    if opp_extra_turn:
                        opp_score_after_response += 100 # Opponent gets an extra turn
                    elif opp_captured_stones > 0:
                        opp_score_after_response += opp_captured_stones * 2
                    opponent_best_response_score = min(opponent_best_response_score, opp_score_after_response)

            current_score -= opponent_best_response_score # Subtract opponent's maximum gain

        if current_score > best_score:
            best_score = current_score
            best_move = move

    return best_move


def simulate_move(you_state: list[int], opponent_state: list[int], move_idx: int) -> tuple[list[int], list[int], bool, int]:
    """
    Simulates a single move for the current player without modifying the original states.
    Returns the new `you` state, `opponent` state, a boolean indicating an extra turn,
    and the number of stones captured.
    """
    # Create copies to avoid modifying original state
    current_you = list(you_state)
    current_opponent = list(opponent_state)

    stones_to_sow = current_you[move_idx]
    current_you[move_idx] = 0
    current_pos = move_idx
    last_landed_house = -1  # To track where the last stone landed
    last_landed_player = None # 'you' or 'opponent'
    captured_stones = 0
    extra_turn = False

    while stones_to_sow > 0:
        current_pos += 1
        if current_pos < 6:  # Your houses
            current_you[current_pos] += 1
            last_landed_house = current_pos
            last_landed_player = 'you'
        elif current_pos == 6:  # Your store
            current_you[6] += 1
            last_landed_house = 6
            last_landed_player = 'you'
            extra_turn = (stones_to_sow == 1) # If this is the last stone
        elif current_pos > 6:  # Opponent's houses
            # Map current_pos > 6 to opponent's house indices 0-5
            opp_house_idx = (current_pos - 7) % 6
            # Skip opponent's store
            if (current_pos - 7) % 7 == 6: # This means it would land in opponent's store
                # Go back to your houses
                current_pos = -1 # Next iteration will make it 0
                stones_to_sow += 1 # Don't decrement for the skipped store
                # Note: This logic for skipping the opponent's store is crucial and complex.
                # A simpler way is to check the target position 'index' and 'player' before distributing.
                # Let's use a more robust distribution loop.
                # Reset current_pos to prepare for the next round of your houses
            else:
                current_opponent[opp_house_idx] += 1
                last_landed_house = opp_house_idx
                last_landed_player = 'opponent'

        stones_to_sow -= 1

        # More robust stone distribution loop
        if stones_to_sow > 0:
            # Need to find the next valid spot.
            # We iterate through the board in order: your houses, your store, opponent's houses, then loop.
            num_stones_left = stones_to_sow
            board_sequence = []
            for i in range(current_pos + 1, 7): # Your remaining houses + store
                board_sequence.append(('you', i))
            for i in range(6): # Opponent's houses
                board_sequence.append(('opponent', i))
            for i in range(6): # Your houses again
                board_sequence.append(('you', i))

            original_current_pos = current_pos
            original_last_landed_house = last_landed_house
            original_last_landed_player = last_landed_player

            full_board_len = 6 + 1 + 6 # Your houses + your store + opponent houses
            
            # Reset current_pos to the effective starting point after the initial `move_idx`
            # This is tricky because `current_pos` was updated incrementally.
            # We need to consider that the actual "start" for continuous sowing
            # is the spot *after* move_idx.

            # We'll just re-implement the sowing part for clarity and correctness
            current_board_ptr = move_idx # Initially points to the house from which seeds were taken
            stones_remaining = current_you[move_idx] = you_state[move_idx] # Restore stones for re-distribution
            current_you[move_idx] = 0 # Empty the house

            while stones_remaining > 0:
                current_board_ptr += 1
                if current_board_ptr < 7: # Your side (0-5 houses, 6 store)
                    current_you[current_board_ptr] += 1
                    last_landed_house = current_board_ptr
                    last_landed_player = 'you'
                    if current_board_ptr == 6 and stones_remaining == 1:
                        extra_turn = True
                elif current_board_ptr < 13: # Opponent's houses (7-12 maps to 0-5)
                    opp_idx = current_board_ptr - 7
                    current_opponent[opp_idx] += 1
                    last_landed_house = opp_idx
                    last_landed_player = 'opponent'
                else: # Loop back to your side, skipping opponent's store
                    current_board_ptr = 0
                    current_you[0] += 1
                    last_landed_house = 0
                    last_landed_player = 'you'
                stones_remaining -= 1

            # After the loop, the actual last_landed_house and last_landed_player are determined
            # No break here, simulation logic needs to be complete.
            # The 'while stones_to_sow > 0' part was flawed. Let's restart the simulation logic.
            break # Exit the outer (flawed) loop for full re-implementation of sowing


    # Corrected sowing logic:
    current_you = list(you_state)
    current_opponent = list(opponent_state)

    stones_in_hand = current_you[move_idx]
    current_you[move_idx] = 0 # Empty the source house

    sow_pointer = move_idx # The index of the house/store *before* putting the next stone
    last_landed_house = -1
    last_landed_player = None

    while stones_in_hand > 0:
        sow_pointer += 1
        
        # Determine where the stone lands
        if sow_pointer < 6: # Your houses 0-5
            current_you[sow_pointer] += 1
            last_landed_house = sow_pointer
            last_landed_player = 'you'
        elif sow_pointer == 6: # Your store
            current_you[6] += 1
            last_landed_house = 6
            last_landed_player = 'you'
            if stones_in_hand == 1: # Last stone lands in your store
                extra_turn = True
        elif sow_pointer > 6 and sow_pointer < 13: # Opponent's houses 0-5 (mapped from 7-12)
            opp_idx = sow_pointer - 7
            current_opponent[opp_idx] += 1
            last_landed_house = opp_idx
            last_landed_player = 'opponent'
        else: # Loop around, skip opponent's store
            sow_pointer = -1 # This will become 0 in the next iteration
            # This stone would land in opponent's store if it wasn't skipped.
            # Effectively, the stone goes to current_you[0] in the next iteration.
            continue # Don't decrement stones_in_hand yet

        stones_in_hand -= 1

    # Check for capture
    if last_landed_player == 'you' and \
       last_landed_house >= 0 and last_landed_house < 6 and \
       current_you[last_landed_house] == 1 and \
       current_opponent[5 - last_landed_house] > 0 and \
       not extra_turn: # Capture only if it's not an extra turn
        
        captured_stones = current_you[last_landed_house] + current_opponent[5 - last_landed_house]
        current_you[6] += captured_stones
        current_you[last_landed_house] = 0
        current_opponent[5 - last_landed_house] = 0

    return current_you, current_opponent, extra_turn, captured_stones

