
import copy
import math

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return the best move (0-5) for the current player.
    Uses negamax search with alpha-beta pruning.
    """
    # Use iterative deepening with a time limit approximation (depth limit)
    # We'll search up to depth 8, which should be safe within 1 second.
    max_depth = 8
    
    def evaluate(state):
        """Heuristic evaluation of the board from the perspective of the player to move."""
        you_state, opp_state = state
        # Difference in stores plus a small weight for seeds on own side (potential)
        store_diff = you_state[6] - opp_state[6]
        seeds_diff = sum(you_state[0:6]) - sum(opp_state[0:6])
        return store_diff + 0.1 * seeds_diff
    
    def is_terminal(state):
        """Check if the game is over (one side's houses are all empty)."""
        you_state, opp_state = state
        return sum(you_state[0:6]) == 0 or sum(opp_state[0:6]) == 0
    
    def collect_remaining(state):
        """
        If one player has no seeds in houses, the other player collects all remaining seeds.
        Modifies the state in-place.
        """
        you_state, opp_state = state
        if sum(you_state[0:6]) == 0:
            # opponent collects remaining seeds
            opp_state[6] += sum(opp_state[0:6])
            for i in range(6):
                opp_state[i] = 0
        elif sum(opp_state[0:6]) == 0:
            # you collect remaining seeds
            you_state[6] += sum(you_state[0:6])
            for i in range(6):
                you_state[i] = 0
    
    def make_move(state, move):
        """
        Simulate a move for the player to move.
        state: (you, opponent) where 'you' is the player to move.
        move: index 0-5 (must be legal).
        Returns (new_state, extra_turn).
        """
        you_state, opp_state = state
        you = you_state.copy()
        opponent = opp_state.copy()
        
        seeds = you[move]
        you[move] = 0
        side = 0  # 0: current player's side, 1: opponent's side
        pos = move + 1
        
        last_was_store = False
        last_side = -1
        last_pos = -1
        
        # Track the count of the last house before dropping the seed (for capture)
        # We'll record the state just before the last seed is placed.
        # Instead, we can remember the house that received the last seed.
        while seeds > 0:
            if side == 0:
                if pos == 6:
                    you[6] += 1
                    seeds -= 1
                    if seeds == 0:
                        last_was_store = True
                        break
                    # after store, switch to opponent side
                    side = 1
                    pos = 0
                else:
                    you[pos] += 1
                    seeds -= 1
                    last_side = 0
                    last_pos = pos
                    pos += 1
                    if pos > 5:
                        # next is store (handled in next iteration)
                        pass
            else:
                if pos == 6:
                    # opponent's store is skipped
                    side = 0
                    pos = 0
                    continue
                else:
                    opponent[pos] += 1
                    seeds -= 1
                    last_side = 1
                    last_pos = pos
                    pos += 1
                    if pos > 5:
                        # after opponent's last house, go to player's side house 0
                        side = 0
                        pos = 0
        
        extra_turn = last_was_store
        
        # Capture rule
        if not last_was_store and last_side == 0:
            # last seed landed in player's own house
            if you[last_pos] == 1:  # it was empty before the drop (now has 1)
                opposite_index = 5 - last_pos
                if opponent[opposite_index] > 0:
                    # capture
                    you[6] += you[last_pos] + opponent[opposite_index]
                    you[last_pos] = 0
                    opponent[opposite_index] = 0
        
        # Check for endgame collection
        collect_remaining((you, opponent))
        
        return ((you, opponent), extra_turn)
    
    def negamax(state, depth, alpha, beta, color):
        """
        Negamax search with alpha-beta pruning.
        color: 1 for maximizing player (the player to move at root), -1 for minimizing.
        """
        you_state, opp_state = state
        
        # Terminal node or depth limit
        if depth == 0 or is_terminal(state):
            return color * evaluate(state)
        
        # Generate legal moves
        legal_moves = [i for i in range(6) if you_state[i] > 0]
        if not legal_moves:
            # no move, game over
            return color * evaluate(state)
        
        # Move ordering: extra move moves first, then captures, then others
        def move_priority(move):
            # simulate quickly to see if it gives extra move or capture
            # we can do a quick simulation without full board copy for ordering
            # but for simplicity, we'll just use the move index (heuristic: higher houses often better)
            # Actually, we can compute a simple heuristic: extra move if (you[move] == (6 - move))
            # because landing in store requires exact distance.
            # For capture: if you[move] leads to landing in empty house opposite non-empty.
            # We'll do a quick check without full simulation.
            seeds = you_state[move]
            # compute landing position if we skip opponent's store
            # The store is at index 6, but we need to consider the circular path.
            # We'll just use a simple priority: moves that are more likely to give extra move or capture.
            # For extra move: if (you_state[move] == (6 - move)) -> leads to store.
            if you_state[move] == (6 - move):
                return 2  # extra move
            # For capture: after distributing seeds, the last seed lands at (move + seeds) % 12 (skipping opponent store)
            # Actually, we need to compute modulo 13? Because there are 14 positions but opponent store is skipped.
            # Instead, we'll just return 1 for moves that are not obviously bad.
            return 0
        
        legal_moves.sort(key=move_priority, reverse=True)
        
        best_value = -math.inf
        for move in legal_moves:
            new_state, extra_turn = make_move(state, move)
            if extra_turn:
                # same player moves again
                value = negamax(new_state, depth-1, alpha, beta, color)
            else:
                # opponent's turn
                value = -negamax((new_state[1], new_state[0]), depth-1, -beta, -alpha, -color)
            
            if value > best_value:
                best_value = value
            
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        
        return best_value
    
    # Root call: find best move
    best_move = None
    best_value = -math.inf
    alpha = -math.inf
    beta = math.inf
    
    # Get legal moves
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    # If only one move, return it
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Try each move with negamax
    for move in legal_moves:
        new_state, extra_turn = make_move((you, opponent), move)
        if extra_turn:
            value = negamax(new_state, max_depth-1, alpha, beta, 1)
        else:
            value = -negamax((new_state[1], new_state[0]), max_depth-1, -beta, -alpha, -1)
        
        if value > best_value:
            best_value = value
            best_move = move
        
        alpha = max(alpha, value)
    
    return best_move
