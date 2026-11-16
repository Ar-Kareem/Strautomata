
import time
import sys

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Returns the index (0-5) of a non-empty house to play.
    Uses a minimax search with alpha-beta pruning and iterative deepening.
    """
    # Helper functions
    def apply_move(player_state, opponent_state, move_idx):
        """
        Apply a move for the player whose state is given first.
        Returns (new_player_state, new_opponent_state, extra_move, game_ended)
        All states are tuples of 7 ints.
        """
        player = list(player_state)
        opponent = list(opponent_state)
        
        seeds = player[move_idx]
        if seeds == 0:
            raise ValueError("Cannot move from empty house")
        
        player[move_idx] = 0
        idx = move_idx + 1
        current = 'player'
        
        # Variables to remember where the last seed lands and if that house was empty before
        last_house = None
        last_was_empty = False
        
        while seeds > 0:
            if current == 'player':
                if idx == 6:  # player's store
                    if seeds == 1:
                        last_house = ('player', 6)
                    player[6] += 1
                    seeds -= 1
                    if seeds == 0:
                        break
                    idx += 1
                    if idx > 6:  # wrap to opponent
                        current = 'opponent'
                        idx = 0
                else:  # player's house 0-5
                    if seeds == 1:
                        last_house = ('player', idx)
                        last_was_empty = (player[idx] == 0)
                    player[idx] += 1
                    seeds -= 1
                    if seeds == 0:
                        break
                    idx += 1
                    if idx == 6:  # next is store
                        continue
                    if idx > 5:  # wrap to store
                        idx = 6
            else:  # current == 'opponent'
                if idx == 6:  # opponent's store -> skip
                    current = 'player'
                    idx = 0
                    continue
                else:  # opponent's house 0-5
                    if seeds == 1:
                        last_house = ('opponent', idx)
                        last_was_empty = (opponent[idx] == 0)
                    opponent[idx] += 1
                    seeds -= 1
                    if seeds == 0:
                        break
                    idx += 1
                    if idx == 6:  # reached opponent store -> wrap to player
                        current = 'player'
                        idx = 0
                        continue
        
        extra_move = False
        # Check for extra move
        if last_house and last_house[0] == 'player' and last_house[1] == 6:
            extra_move = True
        # Check for capture
        elif last_house and last_house[0] == 'player' and 0 <= last_house[1] <= 5:
            if last_was_empty and player[last_house[1]] == 1:
                opposite = 5 - last_house[1]
                if opponent[opposite] > 0:
                    player[6] += player[last_house[1]] + opponent[opposite]
                    player[last_house[1]] = 0
                    opponent[opposite] = 0
        
        # Check game over
        ended = False
        if all(s == 0 for s in player[:6]) or all(s == 0 for s in opponent[:6]):
            player[6] += sum(player[:6])
            opponent[6] += sum(opponent[:6])
            for i in range(6):
                player[i] = 0
                opponent[i] = 0
            ended = True
        
        return tuple(player), tuple(opponent), extra_move, ended
    
    def evaluate(you_state, opp_state):
        """Heuristic score from your perspective."""
        store_diff = you_state[6] - opp_state[6]
        # Potential seeds (weighted lightly)
        potential = (sum(you_state[:6]) - sum(opp_state[:6])) * 0.01
        return store_diff + potential
    
    def game_over(you_state, opp_state):
        return all(s == 0 for s in you_state[:6]) or all(s == 0 for s in opp_state[:6])
    
    # Minimax with alpha‑beta pruning
    def minimax(you_state, opp_state, depth, alpha, beta, player_to_move):
        """Returns the evaluation score from your perspective."""
        if depth == 0 or game_over(you_state, opp_state):
            return evaluate(you_state, opp_state)
        
        if player_to_move == 'you':
            legal_moves = [i for i in range(6) if you_state[i] > 0]
            if not legal_moves:
                return evaluate(you_state, opp_state)
            best = -float('inf')
            for move in legal_moves:
                new_you, new_opp, extra, ended = apply_move(you_state, opp_state, move)
                if ended:
                    val = evaluate(new_you, new_opp)
                else:
                    if extra:
                        next_player = 'you'
                    else:
                        next_player = 'opponent'
                    val = minimax(new_you, new_opp, depth-1, alpha, beta, next_player)
                if val > best:
                    best = val
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best
        else:  # opponent's turn
            legal_moves = [i for i in range(6) if opp_state[i] > 0]
            if not legal_moves:
                return evaluate(you_state, opp_state)
            best = float('inf')
            for move in legal_moves:
                # Apply move from opponent's perspective
                new_opp, new_you, extra, ended = apply_move(opp_state, you_state, move)
                if ended:
                    val = evaluate(new_you, new_opp)
                else:
                    if extra:
                        next_player = 'opponent'
                    else:
                        next_player = 'you'
                    val = minimax(new_you, new_opp, depth-1, alpha, beta, next_player)
                if val < best:
                    best = val
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best
    
    # Convert to tuples for immutability in search
    you_state = tuple(you)
    opp_state = tuple(opponent)
    
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    # If only one move, return it immediately
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Iterative deepening with time limit
    start_time = time.time()
    time_limit = 0.95  # seconds
    best_move = legal_moves[0]  # default
    max_depth = 1
    
    while time.time() - start_time < time_limit and max_depth <= 20:
        depth = max_depth
        max_depth += 1
        move_scores = {}
        for move in legal_moves:
            new_you, new_opp, extra, ended = apply_move(you_state, opp_state, move)
            if ended:
                score = evaluate(new_you, new_opp)
            else:
                if extra:
                    score = minimax(new_you, new_opp, depth-1, -float('inf'), float('inf'), 'you')
                else:
                    score = minimax(new_you, new_opp, depth-1, -float('inf'), float('inf'), 'opponent')
            move_scores[move] = score
        
        # Find best move for this depth
        current_best = max(move_scores, key=move_scores.get)
        # Only update if we have a valid score (should always)
        best_move = current_best
    
    return best_move
