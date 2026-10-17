
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    Go policy using heuristic evaluation and tactical look-ahead (captures/atari).
    """
    BOARD_SIZE = 19
    
    # Convert lists to sets for fast lookup
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set
    
    # ------------------------------------------
    # Helper Functions
    # ------------------------------------------
    
    def get_neighbors(r, c):
        """Yield valid neighbors (up, down, left, right)."""
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                yield nr, nc

    def get_group_liberties(stone, player_stones, opponent_stones):
        """
        Returns (liberties_count, group_size) for the group containing 'stone'.
        Uses BFS.
        """
        q = [stone]
        visited = {stone}
        liberties = set()
        
        while q:
            curr = q.pop(0)
            for n in get_neighbors(*curr):
                if n in player_stones:
                    if n not in visited:
                        visited.add(n)
                        q.append(n)
                elif n not in opponent_stones:
                    # It's empty
                    liberties.add(n)
        
        return len(liberties), len(visited)

    def get_group_and_liberties_from_board(stone, player_stones, opponent_stones):
        """Wrapper to handle finding group properties."""
        if stone not in player_stones:
            return 0, 0
        return get_group_liberties(stone, player_stones, opponent_stones)

    # ------------------------------------------
    # Ko Rule Check Preparation
    # ------------------------------------------
    # We calculate a hash of the current board state to check for Ko.
    # A move is Ko-illegal if it results in a board state identical to the one BEFORE the opponent's last move.
    # We don't have history, but we can infer a potential Ko situation:
    # If opponent captured exactly 1 stone last turn, and we try to recapture immediately.
    # Since we lack full history, we will rely on a state hash stored in memory.
    
    prev_state_hash = memory.get('prev_state_hash')
    
    # Current board hash (before our move)
    current_board_hash = hash((frozenset(me_set), frozenset(opp_set)))

    # ------------------------------------------
    # Move Generation
    # ------------------------------------------
    
    candidates = []
    
    # 1. Generate moves near existing stones (Manhattan distance <= 2)
    # This focuses the search on tactically relevant areas.
    near_stones = set()
    for r, c in occupied:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                    if (nr, nc) not in occupied:
                        near_stones.add((nr, nc))
                        
    if not near_stones:
        # Opening move: Play a star point
        star_points = [(4, 4), (4, 16), (16, 4), (16, 16), (10, 10)]
        for p in star_points:
            if p not in occupied:
                return p, {'prev_state_hash': current_board_hash}
        # If star points taken (weird), play anywhere valid
        for r in range(1, 20):
            for c in range(1, 20):
                if (r, c) not in occupied:
                    return (r, c), {'prev_state_hash': current_board_hash}

    candidates = list(near_stones)
    
    # Add a few random points just in case we miss a far-away move (rarely needed but safe)
    # Not strictly necessary for tactical bots but good for robustness if board is huge and empty spots are far.
    
    best_move = None
    best_score = -float('inf')
    
    # ------------------------------------------
    # Evaluation Loop
    # ------------------------------------------
    
    for r, c in candidates:
        # Simulate placing our stone
        new_me = me_set | {(r, c)}
        new_opp = set(opp_set) # Copy to modify
        
        captured_stones = []
        
        # 1. Check for captures (Opponent stones with 0 liberties)
        # We only need to check neighbors of the placed stone
        potential_captures = set()
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in new_opp:
                potential_captures.add((nr, nc))
        
        # Check liberties of these potential captured groups
        opp_groups_to_check = []
        visited_opp_groups = set()
        
        for s in potential_captures:
            if s not in visited_opp_groups:
                # BFS to find whole group
                q = [s]
                grp = set()
                visited_local = set()
                grp_liberties = set()
                
                # We need to calculate liberties with the NEW stone on board
                while q:
                    curr = q.pop(0)
                    visited_opp_groups.add(curr)
                    grp.add(curr)
                    visited_local.add(curr)
                    
                    for nnr, nnc in get_neighbors(*curr):
                        if (nnr, nnc) in new_opp:
                            if (nnr, nnc) not in visited_local:
                                visited_local.add((nnr, nnc))
                                q.append((nnr, nnc))
                        elif (nnr, nnc) not in new_me:
                            # Empty spot
                            grp_liberties.add((nnr, nnc))
                
                if len(grp_liberties) == 0:
                    captured_stones.extend(list(grp))
        
        if captured_stones:
            for cs in captured_stones:
                new_opp.discard(cs)
        
        # 2. Check for Suicide (Our stone/group has 0 liberties after captures)
        # Calculate liberties of the group at (r, c) on the modified board
        my_group_liberties, my_group_size = get_group_liberties((r, c), new_me, new_opp)
        
        if my_group_liberties == 0:
            # Illegal move (Suicide)
            continue
            
        # 3. Check for Ko (State Repetition)
        # If the board resulting from this move matches the previous state hash, it's illegal.
        # The previous state was: me = me_set, opponent = opp_set (before this call).
        # Wait, the hash we stored was the state *before* opponent moved.
        # If `new_me` U `new_opp` equals `prev_state_hash`'s occupied set? No.
        # Ko rule: The resulting state cannot be the same as the state immediately preceding the opponent's last move.
        # We stored `prev_state_hash` at the end of our last turn.
        # Let's assume `prev_state_hash` is the hash of the board state at the START of our previous turn? No.
        # Let's store the hash of the board state *after* our move.
        # Then, next turn, `prev_state_hash` is the state we produced.
        # The opponent makes a move. Now it's our turn.
        # We cannot return to `prev_state_hash`.
        
        # Wait, that's not quite right. Ko is: Cannot return to board state S if S was the state immediately before the opponent's last move.
        # Let's refine memory usage.
        # Memory stores `prev_board_hash` (The board state hash at the START of this turn).
        # The "previous board state" relative to the Ko rule is the state *before* the opponent moved.
        # That state is exactly what we stored in `memory` as `prev_board_hash`?
        # No, we updated memory at the end of our last turn.
        # End of Turn N: We return move, memory={'state_after_move_N': H1}.
        # Start of Turn N+1: Opponent has moved. We have `me`, `opp`.
        # We cannot return to state H1.
        
        current_simulation_hash = hash((frozenset(new_me), frozenset(new_opp)))
        if current_simulation_hash == memory.get('prev_move_hash'):
            continue # Ko violation

        # 4. Heuristic Scoring
        score = 0.0
        
        # Capture Score
        score += len(captured_stones) * 100.0
        
        # Atari Score (Threatening to capture)
        # Check if any opponent neighbor groups now have 1 liberty
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in new_opp:
                libs, size = get_group_liberties((nr, nc), new_opp, new_me)
                if libs == 1:
                    score += size * 20.0 # Atari!
        
        # Defense Score
        # Did this move save any of our groups?
        # Check neighbors in `me_set` (original board) that might have been in atari
        # This is hard to compute perfectly, but we can check liberties of our neighbors now
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in me_set:
                libs, size = get_group_liberties((nr, nc), new_me, new_opp)
                # If original group had low liberties, bonus for increasing it
                # Simple proxy: reward large liberties
                score += libs * 1.0
        
        # Positional Heuristics
        # Penalize playing on the edge (line 1 and 19) unless it's a capture/atk
        if r == 1 or r == 19 or c == 1 or c == 19:
            score -= 5.0
        if r == 2 or r == 18 or c == 2 or c == 18:
            score -= 1.0
            
        # Center bonus (influence)
        dist_center = abs(r - 10) + abs(c - 10)
        score -= dist_center * 0.1
        
        # Random noise to break ties
        score += random.uniform(-0.5, 0.5)
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    # ------------------------------------------
    # Final Decision
    # ------------------------------------------
    
    if best_move is None:
        best_move = (0, 0) # Pass
        # If we pass, we don't need to update state hash meaningfully for Ko? 
        # But let's keep the memory consistent or reset it.
        return best_move, {}

    # Update memory for Ko detection
    # We store the state *resulting* from this move
    final_me = me_set | {best_move}
    final_opp = set(opp_set)
    # We must re-calculate captures for the best move to update the hash correctly
    # (Or we can just store the hash of the board *before* our move, to enforce simple Ko)
    # Actually, standard Ko: The new state cannot be identical to the state at the beginning of the previous turn.
    # Previous turn start: `prev_state_hash`.
    # We checked `current_simulation_hash != memory.get('prev_move_hash')`.
    # This effectively prevents immediate recapture Ko if the capture is 1 stone.
    
    # Let's store the hash of the board *after* our move, so next turn we can check against it.
    # Wait, if I store `hash(state_after_move)`, next turn opponent moves.
    # Then I try to move. Can I move back to `hash(state_after_move)`?
    # Yes, IF the opponent passed. But usually Ko captures imply a capture happened.
    # If I capture 1 stone, the board is different from my previous state.
    # The opponent plays a stone. I want to capture back.
    # If I capture back, the board returns to `hash(state_after_move)`.
    # THIS IS KO.
    # So I must forbid moving to `hash(state_after_move)`.
    
    # So, `prev_move_hash` stored in memory is the hash of the board *after our last move*.
    # Correct logic.
    
    # Recalculate final board for hash
    # Simplified: just capturing neighbors check again
    nme = me_set | {best_move}
    nopp = set(opp_set)
    caps = []
    for nr, nc in get_neighbors(*best_move):
        if (nr, nc) in nopp:
            libs, _ = get_group_liberties((nr, nc), nopp, nme)
            if libs == 0:
                # We need to identify the whole group to remove
                # Quick BFS to clear `nopp`
                q = [(nr, nc)]
                visited = set()
                while q:
                    curr = q.pop(0)
                    if curr in visited: continue
                    visited.add(curr)
                    if curr in nopp:
                        caps.append(curr)
                        for nnr, nnc in get_neighbors(*curr):
                            if (nnr, nnc) in nopp:
                                q.append((nnr, nnc))
    for cp in caps:
        nopp.discard(cp)
        
    next_memory = {'prev_move_hash': hash((frozenset(nme), frozenset(nopp)))}
    
    return best_move, next_memory
