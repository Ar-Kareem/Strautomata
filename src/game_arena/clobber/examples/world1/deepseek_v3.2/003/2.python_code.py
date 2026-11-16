
import numpy as np
import time
import random

def policy(you, opponent):
    # Convert to numpy arrays
    you_board = np.array(you, dtype=int)
    opp_board = np.array(opponent, dtype=int)
    # Reshape if flat (30 elements)
    if you_board.ndim == 1 and you_board.size == 30:
        you_board = you_board.reshape(5, 6)
        opp_board = opp_board.reshape(5, 6)
    
    # Directions: (symbol, row delta, col delta)
    DIRECTIONS = [('U', -1, 0), ('D', 1, 0), ('L', 0, -1), ('R', 0, 1)]
    ROWS, COLS = 5, 6
    WIN_SCORE = 1000
    LOSS_SCORE = -1000
    
    def get_legal_moves(player, opponent):
        """Return list of (row, col, dir) for all legal moves for player."""
        moves = []
        for r in range(ROWS):
            for c in range(COLS):
                if player[r, c] == 1:
                    for d, dr, dc in DIRECTIONS:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS:
                            if opponent[nr, nc] == 1:
                                moves.append((r, c, d))
        return moves
    
    def make_move(player, opponent, move):
        """Apply move and return new state (new_player, new_opponent) with swapped turns."""
        r, c, d = move
        # Determine destination
        if d == 'U':
            nr, nc = r - 1, c
        elif d == 'D':
            nr, nc = r + 1, c
        elif d == 'L':
            nr, nc = r, c - 1
        else:  # 'R'
            nr, nc = r, c + 1
        new_player = player.copy()
        new_opponent = opponent.copy()
        new_player[r, c] = 0
        new_player[nr, nc] = 1
        new_opponent[nr, nc] = 0
        # Swap roles for next turn
        return new_opponent, new_player
    
    def evaluate(player, opponent):
        """Evaluation from the perspective of the player to move."""
        player_moves = len(get_legal_moves(player, opponent))
        if player_moves == 0:
            return LOSS_SCORE
        opp_moves = len(get_legal_moves(opponent, player))
        if opp_moves == 0:
            return WIN_SCORE
        return player_moves - opp_moves
    
    def negamax(player, opponent, depth, alpha, beta, start_time, time_limit):
        """Negamax with alpha-beta pruning. Returns score from current player's perspective."""
        if time.perf_counter() - start_time > time_limit:
            # Timeout: return a neutral score to stop search
            return 0
        
        moves = get_legal_moves(player, opponent)
        if len(moves) == 0:
            return LOSS_SCORE
        if depth == 0:
            return evaluate(player, opponent)
        
        best = -float('inf')
        # Simple move ordering: shuffle for randomness
        random.shuffle(moves)
        for move in moves:
            new_player, new_opponent = make_move(player, opponent, move)
            score = -negamax(new_player, new_opponent, depth - 1, -beta, -alpha, start_time, time_limit)
            if score > best:
                best = score
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best
    
    # Get all legal moves for us
    our_moves = get_legal_moves(you_board, opp_board)
    # Shuffle to randomize and improve move ordering
    random.shuffle(our_moves)
    
    # Check for immediate winning move
    for move in our_moves:
        new_opp, new_you = make_move(you_board, opp_board, move)
        if len(get_legal_moves(new_opp, new_you)) == 0:
            r, c, d = move
            return f"{r},{c},{d}"
    
    # Iterative deepening with time limit
    start_time = time.perf_counter()
    time_limit = 0.9  # seconds
    best_move_overall = our_moves[0]  # default
    max_depth = 10  # upper bound
    
    for depth in range(1, max_depth + 1):
        best_score = -float('inf')
        best_move = None
        for move in our_moves:
            if time.perf_counter() - start_time > time_limit:
                break
            new_opp, new_you = make_move(you_board, opp_board, move)
            score = -negamax(new_opp, new_you, depth - 1, -float('inf'), float('inf'), start_time, time_limit)
            if score > best_score:
                best_score = score
                best_move = move
            if score >= WIN_SCORE:
                # Winning move found at this depth
                best_move_overall = move
                r, c, d = best_move_overall
                return f"{r},{c},{d}"
            if time.perf_counter() - start_time > time_limit:
                break
        if best_move is not None:
            best_move_overall = best_move
        if time.perf_counter() - start_time > time_limit:
            break
    
    r, c, d = best_move_overall
    return f"{r},{c},{d}"
