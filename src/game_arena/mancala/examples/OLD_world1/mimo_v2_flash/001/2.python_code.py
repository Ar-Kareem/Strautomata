
import sys

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Implements a move-selection policy for the game Kalah.
    The policy prioritizes moves in this order:
    1. Capture moves (landing in an empty house to capture opponent seeds).
    2. Extra move moves (landing in own store).
    3. Moves that do not give the opponent a free turn (avoid landing in opponent's empty house).
    4. Otherwise, selects the move that captures the most seeds (approximation).
    5. Default to the longest move (furthest index).
    """
    
    # Heuristic weights for evaluating board states (if search depth > 0)
    # 1 seed in store is worth 1 point.
    # 1 seed in a house is worth slightly less than 1 point (because it is not yet secured).
    # Keeping seeds in the store prevents the opponent from capturing them.
    # Giving the opponent a free turn is very bad.
    H_STORE = 1.0
    H_HOUSE = 0.9
    
    def evaluate_state_internal(you_arr, opp_arr):
        # Evaluate the net score difference
        score = (you_arr[6] * H_STORE + sum(you_arr[:6]) * H_HOUSE) - \
                (opp_arr[6] * H_STORE + sum(opp_arr[:6]) * H_HOUSE)
        
        # Penalty if it is opponent's turn and they have moves (if we could accurately track turns, 
        # but strictly we are evaluating a child board state where it is implicitly opponent's turn or not).
        # In this simplified evaluation, we assume the state passed is after our move, 
        # but before the opponent's move (unless extra turn).
        # Actually, if we land in our store, it's still our turn. 
        # If not, it's opponent's turn.
        # We cannot know if it's opponent's turn in this function without passing a flag.
        # So we just use raw material difference.
        return score

    def simulate_move(you_src, opp_src, move_idx):
        # Returns (result: tuple, extra_turn: bool, captured: int)
        # result: (you_next, opp_next) lists
        # This simulation accounts for the rules: sowing and capture.
        
        # Deep copy
        you = list(you_src)
        opp = list(opp_src)
        
        seeds = you[move_idx]
        if seeds == 0:
            return None, False, 0
            
        you[move_idx] = 0
        idx = move_idx
        capture_amount = 0
        is_extra_turn = False
        
        # Sowing loop
        while seeds > 0:
            idx += 1
            # Skip opponent's store
            if idx == 7: # Currently in you
                # Next is opp[0]
                idx = 10 # Marker for opp start
            elif idx == 17: # Currently in opp (hypothetical)
                # Next is you[0]
                idx = 0
                
            if idx == 10:
                # In opponent range
                if seeds == 1 and (10 - 10) <= 5: # Last seed in opp house
                    last_pos = 10 - 10 # 0 to 5
                    # Check Capture Condition:
                    # 1. Last seed lands in your empty house? No, lands in opp house.
                    # Wait, capture rule: "If the last seed lands in one of your houses..."
                    # So we only check capture if the last seed lands in 'you'.
                    # If we distribute into 'opp', we never capture immediately.
                    pass
                if seeds > 0:
                    opp[idx - 10] += 1
                    seeds -= 1
                    # If we continue sowing, idx increments. 
                    # But logic above handles loop increment.
                    # We need to manually increment because loop adds +1.
                    # Let's rewrite loop to be cleaner.
                    pass
            elif idx < 7:
                # In you
                if seeds == 1 and move_idx != idx: # Avoid landing back in start house (if looped)
                    # Check Extra Move
                    if idx == 6:
                        is_extra_turn = True
                    # Check Capture
                    else:
                        # 0 <= idx <= 5
                        if you[idx] == 0 and opp[5-idx] > 0:
                            # Capture!
                            # Add seed just placed + seeds from opponent house
                            capture_amount = 1 + opp[5-idx]
                            you[6] += capture_amount
                            opp[5-idx] = 0
                            # We do not update 'you[idx]' here because it was empty, we added 1, then removed it? 
                            # No, rules: "capture the seed in you[i] and all seeds from opp..."
                            # The seed in you[i] is the one just placed.
                            # The ones in opp[5-i] are captured.
                            # Total added to store.
                            # We must remove the seed from you[idx] to calculate final state?
                            # No, we added it to store.
                            # So we must NOT have added it to you[idx] in the sowing phase yet, 
                            # or remove it now.
                            # Let's handle sowing carefully.
                            pass
                if seeds > 0:
                    you[idx] += 1
                    seeds -= 1
        
        # Redoing the sowing loop for correctness to avoid off-by-one errors with the index
        # Reset
        you = list(you_src)
        opp = list(opp_src)
        seeds = you[move_idx]
        you[move_idx] = 0
        
        current_idx = move_idx
        last_idx = -1
        
        while seeds > 0:
            current_idx += 1
            if current_idx < 7:
                # Your side
                pass
            elif current_idx == 7:
                # Your store
                pass
            elif current_idx < 14:
                # Opponent side
                pass
            elif current_idx == 14:
                # Opponent store (skip)
                current_idx += 1
                # Now go to your side
                # If we are at 15, it maps to you[0]
                # Logic: The board is circular. 
                # Let's map continuous index to actual array slots.
                # We can use modulo arithmetic or just check ranges.
                
                # Simpler manual loop:
                # 1. You (0-5), You Store (6), Opp (0-5), Skip Opp Store, Repeat.
                pass

        # Let's use the step-by-step distribution logic directly
        you = list(you_src)
        opp = list(opp_src)
        seeds = you[move_idx]
        if seeds == 0: return None, False, 0
        you[move_idx] = 0
        
        current_i = move_idx
        
        while seeds > 0:
            current_i += 1
            
            if current_i < 7:
                # Your house/store
                if current_i < 7:
                    # It's a house or store
                    if seeds == 1 and current_i == 6:
                        # Last seed in store
                        you[6] += 1
                        seeds -= 1
                        last_pos = 'store'
                        break # Done sowing
                    elif seeds == 1 and current_i < 6:
                        # Last seed in your house
                        if you[current_i] == 0 and opp[5 - current_i] > 0:
                            # Capture
                            # We haven't incremented you[current_i] yet
                            you[6] += (1 + opp[5 - current_i])
                            opp[5 - current_i] = 0
                            you[current_i] = 0 # Ensure it's 0 (it was empty)
                            seeds -= 1
                            last_pos = 'capture'
                            break
                        else:
                            you[current_i] += 1
                            seeds -= 1
                            last_pos = ('you', current_i)
                            break
                    else:
                        # Not last seed
                        you[current_i] += 1
                        seeds -= 1
                else:
                    # Shouldn't happen given current_i < 7
                    pass
            elif current_i == 7:
                # Opponent Store (skip)
                # We increment current_i again in the loop, effectively skipping
                # But we need to consume a loop iteration or handle carefully
                # Actually, we just loop again.
                # If we simply increment current_i in loop, this index passes instantly.
                pass
            elif current_i < 14:
                # Opponent house
                opp_idx = current_i - 8 # 0 to 5? No.
                # 8->0, 9->1, 10->2, 11->3, 12->4, 13->5
                opp_idx = current_i - 8
                if seeds == 1:
                    # Last seed
                    opp[opp_idx] += 1
                    seeds -= 1
                    last_pos = ('opp', opp_idx)
                    break
                else:
                    opp[opp_idx] += 1
                    seeds -= 1
            else:
                # Wrap around to you[0]
                # current_i becomes 14, which is Opponent Store (skip), so loop does 15 -> you[0]
                # Let's just implement the wrap manually
                current_i = -1 # So it becomes 0 next
                # But loop adds 1, so it becomes 0.
        # Wait, the loop structure `current_i += 1` implies 0, 1, 2...
        # But we started at `move_idx`.
        # Let's restart the sowing loop with a simpler index counter.
        
        # --- Robust Sowing Loop ---
        you = list(you_src)
        opp = list(opp_src)
        seeds = you[move_idx]
        you[move_idx] = 0
        
        # Create a list of slots in order
        # The cycle is: [you[0], ... you[5], you[6], opp[0], ... opp[5]]
        # (Note: opp[6] is skipped)
        # We need to start sowing from the slot after `move_idx`.
        
        # Define slots 0 to 13
        # 0-5: you houses
        # 6: you store
        # 7-12: opp houses
        # (13 would be opp store, but we skip it. In modulo 13 arithmetic, this aligns. 
        #  Actually, total slots in cycle is 13: 0..12.
        #  0..5: You House
        #  6: You Store
        #  7..12: Opp House)
        
        start_slot = -1
        if move_idx == 6: 
            start_slot = 6
        else: 
            start_slot = move_idx # 0..5
        
        # We need to distribute seeds into slots (start_slot+1) % 13, ...
        
        last_slot = -1
        
        for k in range(seeds):
            # Calculate next slot
            # We iterate 1 step from current position
            # Note: We simulate drops one by one to handle capture on the last one
            # But we can optimize if not last seed.
            
            # To handle the loop, let's maintain a current position pointer
            pass

        # --- Finalized Robust Sowing Loop ---
        you = list(you_src)
        opp = list(opp_src)
        seeds = you[move_idx]
        if seeds == 0: return None, False, 0
        you[move_idx] = 0
        
        # Map move_idx (0..6) to slot (0..12)
        # 0..5 -> 0..5
        # 6 -> 6
        slot = move_idx
        
        # Function to add seed to slot
        def add_to_slot(s):
            if s <= 5:
                you[s] += 1
            elif s == 6:
                you[6] += 1
            else:
                # 7..12 -> opp 0..5
                opp[s-7] += 1
        
        # Function to check value of slot (before placing last seed)
        def peek_slot(s):
            if s <= 5:
                return you[s]
            elif s == 6:
                return 0 # Store is never empty in the sense of capture? Capture doesn't happen in store.
            else:
                return opp[s-7]
        
        # Function to get opp house index corresponding to your house index s (0..5)
        def get_opp_house(s):
            # if s is 0, opp is 5 (which is slot 12)
            # if s is 5, opp is 0 (which is slot 7)
            return 12 - s
        
        last_slot = -1
        
        for i in range(seeds):
            # Determine next slot
            next_slot = slot + 1
            if next_slot == 7:
                next_slot = 8 # Skip opp store? No, logic is:
                # Sowing order: you[i+1]...you[5], you[6], opp[0]...opp[5]
                # So after you[5] (slot 5), go to you[6] (6). 
                # After you[6] (6), go to opp[0] (7).
                # After opp[5] (12), go to you[0] (0).
                # So we don't skip opp store during sowing? 
                # The prompt says: "skipping opponent[6]"
                # This usually means we ignore it as a target. 
                # So if we land on it, we skip it.
                # But standard Mancala rules: sowing goes:
                # ... opp[5], then you[0] (loop). 
                # Opponent store is skipped by definition of the sequence.
                # The sequence explicitly lists opp[0]..opp[5] then you[0]...
                # So we don't hit opp[6].
                # So we just use modulo 13 logic with 0..12.
                pass
            
            # Calculate next slot using modulo 13
            # Slots 0..12 (13 slots)
            # 0-5: You houses
            # 6: You store
            # 7-12: Opp houses
            
            # We need to advance one step.
            # If we are at 5 (you[5]), next is 6 (you[6]).
            # If we are at 6 (you[6]), next is 7 (opp[0]).
            # If we are at 12 (opp[5]), next is 0 (you[0]).
            
            slot = (slot + 1) % 13
            if i == seeds - 1:
                # Last seed
                last_slot = slot
                if slot == 6:
                    # Extra move
                    add_to_slot(slot)
                    # Capture doesn't happen in store
                    return (tuple(you), tuple(opp)), True, 0
                elif slot <= 5:
                    # Your house
                    if you[slot] == 0 and opp[5-slot] > 0:
                        # Capture
                        # The seed just placed (1) + seeds in opposite house
                        captured = 1 + opp[5-slot]
                        you[6] += captured
                        opp[5-slot] = 0
                        # We DO NOT add to you[slot] because it goes straight to store?
                        # No, the prompt says: "capture the seed in you[i] and all seeds from opp..."
                        # This implies the seed lands in you[i], then moves.
                        # So we add 1, then remove 1 (plus opp seeds) to store.
                        # Or just add to store directly.
                        # Since we want final state:
                        # we just add to store.
                        # we do not increment you[slot].
                        # we clear opp.
                        pass
                    else:
                        you[slot] += 1
                else:
                    # Opponent house
                    opp[slot-7] += 1
            else:
                # Not last seed, just distribute
                if slot == 6:
                    you[6] += 1
                elif slot <= 5:
                    you[slot] += 1
                else:
                    opp[slot-7] += 1
        
        # Return state, extra turn (False here because we handled it in loop if it was last), capture count
        # We need to distinguish "Capture happened" for the heuristic.
        # If capture happened, we already updated the state.
        # Let's return the new state and a flag indicating if capture occurred.
        # If capture occurred, we return (state, False, capt_amt) or just check if store increased relative to seed count.
        # Actually, capture check logic above: we didn't use a flag, we mutated.
        # So if last_slot <= 5 and condition met, we know it was capture.
        
        # Let's refine the return for capture detection in main loop
        return (tuple(you), tuple(opp)), False, last_slot # We need to know if capture happened. 
        # Actually, let's pass a flag.
        
    # --- Main Policy Logic ---
    
    best_move = -1
    best_score = -float('inf')
    
    # 1. Identify moves that are immediately winning or beneficial
    candidates = []
    
    for i in range(6):
        if you[i] == 0:
            continue
        
        # Simulate move i
        # We need a reliable simulation function.
        # Let's define a proper simulation here to avoid closure issues.
        
        def get_next_state(you_src, opp_src, move_idx):
            you = list(you_src)
            opp = list(opp_src)
            seeds = you[move_idx]
            if seeds == 0: return None, False, False, 0
            you[move_idx] = 0
            
            slot = move_idx # 0..6 mapped to 0..6
            # Map to 0..12 logic as described above
            # 0..5 -> 0..5
            # 6 -> 6
            
            last_slot = -1
            capture_happened = False
            capture_amount = 0
            
            for k in range(seeds):
                # Advance slot
                slot += 1
                # Handle skips/wraps
                if slot == 7:
                    # Just moved from you[6] (6) to opp[0] (7)
                    pass
                elif slot == 13:
                    # Wrap around from opp[5] (12) to you[0] (0)
                    slot = 0
                
                # Note: We need to handle the skip of Opponent Store.
                # The sequence is: 0..5, 6, 7..12, 0..
                # Opp store is at index 13 in a 0..13 count, but we map it to 7..12 for houses.
                # Wait, if slot is 12 (opp[5]), next is 13. 
                # But prompt: "opponent[0] through opponent[5] ... you[0]"
                # This implies we never visit opponent[6].
                # In our 0..12 mapping, we have 0..5 (you), 6 (you store), 7..12 (opp houses).
                # 13 would be opp store. 
                # So if slot becomes 13, we treat it as wrap to 0? 
                # No, standard Mancala sowing: 
                # If we have 7 houses (0..5 + store), total 7 slots.
                # Stores are skipped.
                # Let's use the list approach to be safe.
                
                # List of slots: 
                # [you[0], you[1], ..., you[5], you[6], opp[0], ..., opp[5]]
                # Total 13 items.
                # Indices 0..12.
                
                # If we are at 12, next is 0.
                # So modulo 13 works.
                # Does it skip opp store?
                # In this list, opp store is NOT included.
                # So we are safe.
                
                # Wait, in this list, we have 13 items. 
                # 0..5: You houses
                # 6: You store
                # 7..12: Opp houses
                
                # If we are at 12 (opp[5]), next is (12+1)%13 = 0 (you[0]).
                # Correct.
                
                # So we use modulo 13.
                slot = (slot) % 13 # We incremented at start of loop, so current slot is correct.
                
                is_last = (k == seeds - 1)
                
                if slot == 6:
                    # You store
                    if is_last:
                        return (tuple(you), tuple(opp)), True, False, 0
                    you[6] += 1
                elif slot <= 5:
                    # You house
                    if is_last:
                        if you[slot] == 0 and opp[5-slot] > 0:
                            # Capture
                            you[6] += (1 + opp[5-slot])
                            opp[5-slot] = 0
                            # Note: we don't add to you[slot] because it goes to store.
                            # But wait, the seed lands in you[slot] then moves.
                            # Visually, you[slot] gets 1, then immediately removed.
                            # Since we update state directly to store, we leave you[slot] as 0.
                            # But we might want to reflect the temporary 1 for animation? No.
                            # Just update store and opp.
                            capture_happened = True
                            capture_amount = 1 + opp[5-slot] # Calculate exactly
                        else:
                            you[slot] += 1
                    else:
                        you[slot] += 1
                else:
                    # Opp house (7..12)
                    opp_idx = slot - 7
                    if is_last:
                        opp[opp_idx] += 1
                    else:
                        opp[opp_idx] += 1
                        
            return (tuple(you), tuple(opp)), False, capture_happened, capture_amount

        you_next, opp_next, extra, captured = get_next_state(you, opp, i)
        
        if you_next is None:
            continue
            
        # --- Scoring ---
        
        # 1. Immediate Extra Move
        if extra:
            candidates.append((i, 10000, "extra")) # High priority
            continue
            
        # 2. Capture Move
        if captured:
            # Value capture by amount.
            # Also check if this leaves us vulnerable?
            # For now, simple value.
            score = 1000 + captured * 10
            candidates.append((i, score, "capture"))
            continue
            
        # 3. Normal Move: Check if we leave opponent a free turn
        # If we land in an empty house of opponent, they get a free turn.
        # We can only land in opponent houses 0..5.
        # The last seed lands at index `last_slot` from simulation logic.
        # But we didn't return `last_slot` explicitly in the tuple above.
        # Let's infer it or add it to return tuple.
        # In the loop, for non-capture, non-store, the last seed adds to a slot.
        # If it adds to opp[0..5], that's where it landed.
        # We can modify `get_next_state` to return the last slot, or we can check manually.
        # Actually, we can check: if `you_next` and `opp_next` are same as `you` and `opp` except for the move?
        # No.
        # Let's quickly compute the last slot again or just check the resulting board.
        # If the move was not capture/extra, the last seed added 1 to either you house or opp house.
        # If it added to opp house `idx` (0..5), then `opp_next[idx]` is `opp[idx] + 1`.
        # If `opp[idx]` was 0, it's a free turn.
        
        # To do this efficiently, let's find the last slot.
        # We can just re-run the simulation logic slightly to get the last slot.
        # Or, we can check the difference.
        
        # Let's check difference to find where the last seed went (if no capture/extra)
        # We know `you[i]` was decremented by `you[i]`.
        # The seeds are distributed.
        # Let's just do a quick re-calc of the last slot index.
        # It is: `(i + you[i] + 1) % 13` ? No.
        # It is: `(i + seeds) % 13` but adjusted for the skip of opp store if it falls exactly on it?
        # No, we use modulo 13 on the 13-slot board.
        # If we start at i (0..6), add seeds.
        # Wait, we start at i, then sow seeds.
        # The first seed goes to i+1.
        # The last seed goes to i + seeds.
        # But modulo 13.
        # However, if i + seeds lands on 13 (opp store), we skip it? 
        # In our 13-slot board (no opp store), 13 wraps to 0.
        # So if it lands exactly on 13, it wraps to 0.
        # But standard rules say: if you pass the store, you skip it.
        # If you land exactly on the store, you put it in.
        # Wait, our 13-slot model:
        # 0..5: You houses
        # 6: You store
        # 7..12: Opp houses
        # If we start at i=0, seeds=7.
        # Path: 0->1->2->3->4->5->6 (store).
        # That's 7 seeds. Last one is 6. Correct.
        # If seeds=8: 0..5->6->7. Last is 7.
        # So last slot = (i + seeds) % 13? No.
        # Start at i, distribute seeds.
        # The slots filled are (i+1)%13, (i+2)%13, ..., (i+seeds)%13.
        # So last slot is `(i + seeds) % 13`.
        # But wait, if we hit the opponent store (index 13 in a 0..13 board), we skip.
        # In our 0..12 board, we don't have opp store.
        # So we don't skip anything.
        # This is correct for the *destination*.
        # So last slot = (i + seeds) % 13.
        # Exception: if i=6 (store), we start sowing from there.
        # `you[6]` is never selected as a move (houses only).
        # So i is 0..5.
        
        last_slot_calc = (i + you[i]) % 13
        
        # Check if last_slot_calc is opp house (7..12)
        if 7 <= last_slot_calc <= 12:
            opp_idx = last_slot_calc - 7
            if opp[opp_idx] == 0:
                # Free turn for opponent -> Bad
                score = -1000 + sum(you_next[:6]) # Avoid, but maybe necessary
                candidates.append((i, score, "bad"))
                continue
        
        # 4. Safe Move
        # Score based on material difference
        # We want to maximize our store and minimize opp store.
        # Also, we want to avoid leaving captures for opponent.
        # Check if we land in our own empty house? 
        # If we land in our own empty house (i.e. capture happens), we handled it.
        # If we land in our own non-empty house, safe.
        
        # Evaluate the state
        # Let's use the simple evaluation
        mat_score = (you_next[6] - opp_next[6]) * 10 + sum(you_next[:6]) - sum(opp_next[:6])
        
        # Add penalty if opponent can capture us next turn?
        # This is depth 2 search. We can check if opponent has a capture.
        # If we leave an empty house (i.e. we landed in one that became empty? No, we just added one).
        # We land in a house, so it becomes non-empty (unless capture).
        # So we don't leave empty houses for opponent to capture, unless we allow them to capture by landing in a house with 1 seed?
        # No, capture requires opponent to land in *our* empty house.
        # So if we leave any of *our* houses empty, opponent might capture.
        # Wait, our houses: we just sowed. 
        # If we landed in `you[j]`, it got +1.
        # If we didn't land in `you[j]`, it might be empty if we scooped from it.
        # If we scooped from `you[j]` (start house), it becomes 0.
        # If we didn't fill it back, it is empty.
        # So we need to check if we left an empty house in `you_next`.
        
        empty_vulnerable = False
        for h in range(6):
            if you_next[h] == 0:
                # Check if opponent can reach it.
                # Opponent can reach it if they can land in it.
                # Opponent house `k` corresponds to our house `5-k`.
                # If opp lands in `k`, they fill `k`. 
                # If opp lands in our house `h`, they must come from their house `5-h`.
                # They need to have enough seeds to reach `h`.
                # Distance from opp house `k` to your house `h`:
                # Opp houses (0..5). Your houses (0..5).
                # If opp at k, lands at slot `h`.
                # Path: opp[k], ... opp[5], you[0], ... you[h].
                # Distance is (5 - k) + 1 + h.
                # They need `distance == seeds`.
                # We can't check all permutations easily.
                # Heuristic: if `you_next[h] == 0` and `opp[5-h] > 0`, it's risky?
                # No, `opp[5-h]` is the house directly opposite.
                # If we are empty, and opp opposite is non-empty, they can capture if they land exactly.
                # If `opp[5-h]` has seeds, and opp lands in `h`, they capture.
                # Can they land in `h`?
                # Distance from opp[5-h] to you[h] is just 1 step (if they are in the correct house).
                # Wait, sowing from opp[5-h]: first seed goes to you[h]? 
                # Yes, if they are in house 5-h, they sow into you[h] immediately.
                # If you[h] is empty, they capture!
                # So we must check: did we leave `you_next[h] == 0`?
                # If we did, and `opp[5-h] > 0`, opponent can capture by playing `5-h`.
                # So we should avoid leaving empty houses if opposite house is non-empty.
                if opp[5-h] > 0:
                    empty_vulnerable = True
        
        if empty_vulnerable:
            mat_score -= 500
            
        candidates.append((i, mat_score, "safe"))
    
    # Sort candidates by score
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Pick the best
    if candidates:
        # If multiple have same high score, pick smallest index (deterministic)
        # But we want to maximize score.
        # We should pick the one with max score.
        best = candidates[0]
        # If there's a tie, we could pick the one that gives extra move or capture, but they are handled.
        # Just pick first.
        return best[0]
    
    # Fallback
    for i in range(6):
        if you[i] > 0:
            return i

    return 0 # Should not happen
