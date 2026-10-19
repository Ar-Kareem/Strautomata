
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Map board to an immutable representation for caching
    flat = tuple(board[r][c] for r in range(3) for c in range(3))
    
    # Determine whose turn it is:
    # In typical arenas, you are '1' and opponent is '-1', and
    # board updates are consistent with legal play.
    ones = sum(1 for v in flat if v == 1)
    negs = sum(1 for v in flat if v == -1)
    # If equal, it's our turn; else opponent's turn
    turn = 1 if ones == negs else -1

    # Precompute all winning lines (triples of indices)
    lines = [
        (0,1,2),(3,4,5),(6,7,8),
        (0,3,6),(1,4,7),(2,5,8),
        (0,4,8),(2,4,6)
    ]
    
    def winner(state):
        for a,b,c in lines:
            s = state[a] + state[b] + state[c]
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0
    
    def moves(state):
        # Return list of empty indices
        return [i for i, v in enumerate(state) if v == 0]
    
    def is_full(state):
        return all(v != 0 for v in state)
    
    # We'll return scores from the perspective of player 1 (us)
    # +1 win for us, -1 loss for us, 0 draw
    @lru_cache(maxsize=None)
    def minimax(state, player, alpha, beta):
        w = winner(state)
        if w != 0:
            return w  # +1 or -1
        if is_full(state):
            return 0
        
        # player is either 1 (our turn) or -1 (opponent turn)
        if player == 1:
            best = -2
            for i in moves(state):
                new_state = list(state)
                new_state[i] = 1
                score = minimax(tuple(new_state), -1, alpha, beta)
                if score > best:
                    best = score
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best
        else:
            best = 2
            for i in moves(state):
                new_state = list(state)
                new_state[i] = -1
                score = minimax(tuple(new_state), 1, alpha, beta)
                if score < best:
                    best = score
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break
            return best
    
    # If it's not our turn (shouldn't happen in correct usage), still handle safely:
    # We choose a move for ourselves if possible.
    if turn != 1:
        # It's opponent's turn in the given state; but we must return a legal move for our side.
        # We'll assume we always move as '1' regardless; recompute legal move by evaluating as if we are to play.
        pass
    
    best_score = -2
    best_move = None
    for i in moves(flat):
        new_state = list(flat)
        new_state[i] = 1  # our move
        score = minimax(tuple(new_state), -1, -2, 2)
        if score > best_score:
            best_score = score
            best_move = i
    
    # Convert index to (row, col)
    r, c = divmod(best_move, 3)
    return (r, c)
