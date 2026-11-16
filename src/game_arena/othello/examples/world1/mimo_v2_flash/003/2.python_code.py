
import numpy as np
import time

# Precomputed board weights for positional play
# 1000: Corner (C-squares)
# -100: Adjacent to corner (X-squares) - dangerous
# 10: Center squares
# 5: Edge squares
WEIGHTS = np.array([
    [1000, -100,  10,  5,  5,  10, -100, 1000],
    [-100, -200, -5, -5, -5, -5, -200, -100],
    [  10,   -5,  1,  2,  2,  1,   -5,   10],
    [   5,   -5,  2,  2,  2,  2,   -5,    5],
    [   5,   -5,  2,  2,  2,  2,   -5,    5],
    [  10,   -5,  1,  2,  2,  1,   -5,   10],
    [-100, -200, -5, -5, -5, -5, -200, -100],
    [1000, -100,  10,  5,  5,  10, -100, 1000]
], dtype=np.int32)

# Directions: (dr, dc) for 8 neighbors
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0),  (1, 1)]

class OthelloAgent:
    def __init__(self):
        self.TIME_LIMIT = 0.85  # Seconds (leave buffer for overhead)
        self.max_depth = 1
        self.transposition_table = {}

    def get_legal_moves(self, board, player, opponent):
        """Returns a list of (r, c) coordinates for legal moves."""
        moves = []
        empty = ~(player | opponent).astype(bool)
        
        # Optimization: Only check empty cells
        indices = np.argwhere(empty)
        for r, c in indices:
            if self.is_valid_move(board, r, c, player, opponent):
                moves.append((r, c))
        return moves

    def is_valid_move(self, board, r, c, player, opponent):
        """Check if a move is valid by scanning all 8 directions."""
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc]:
                # Found an opponent disc, keep going
                while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc]:
                    nr += dr
                    nc += dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and player[nr][nc]:
                        return True
        return False

    def make_move(self, board, r, c, player, opponent):
        """Simulates a move and returns the new board state."""
        new_player = board.copy()
        new_opponent = opponent.copy()
        new_player[r][c] = 1
        
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            flips = []
            if 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc]:
                while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc]:
                    flips.append((nr, nc))
                    nr += dr
                    nc += dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and player[nr][nc]:
                        for fr, fc in flips:
                            new_player[fr][fc] = 1
                            new_opponent[fr][fc] = 0
                        break
        return new_player, new_opponent

    def evaluate(self, you, opponent, moves_left):
        """Heuristic evaluation function."""
        # 1. Disc Parity (Endgame focus)
        disc_count = np.sum(you) - np.sum(opponent)
        
        # 2. Positional Weighting
        pos_score = np.sum(you * WEIGHTS) - np.sum(opponent * WEIGHTS)
        
        # 3. Mobility (Current move advantage)
        my_mobility = len(self.get_legal_moves(you, you, opponent))
        opp_mobility = len(self.get_legal_moves(opponent, opponent, you))
        mobility_score = (my_mobility - opp_mobility) * 10  # Weight multiplier
        
        # Dynamic weighting based on game phase
        # If few moves left, rely heavily on disc count
        if moves_left < 15:
            return disc_count * 100 + mobility_score + pos_score * 0.5
        else:
            # Early/Mid game: prioritize position and mobility over raw count
            return pos_score * 2 + mobility_score * 2 + disc_count * 5

    def order_moves(self, moves, you, opponent):
        """Order moves by heuristic value to improve pruning."""
        scored_moves = []
        for r, c in moves:
            # Quick heuristic: prefer corners and edges
            score = WEIGHTS[r][c]
            # Check if move flips opponent discs (stability)
            scored_moves.append((score, r, c))
        # Sort descending (highest score first)
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return [(r, c) for _, r, c in scored_moves]

    def alpha_beta(self, you, opponent, depth, alpha, beta, maximizing, moves_left, start_time):
        """Minimax with Alpha-Beta pruning."""
        # Time check
        if time.time() - start_time > self.TIME_LIMIT:
            return None, 0

        if depth == 0 or moves_left == 0:
            return None, self.evaluate(you, opponent, moves_left)

        valid_moves = self.get_legal_moves(you, you, opponent) if maximizing else self.get_legal_moves(opponent, opponent, you)
        
        # Ordering moves improves search speed significantly
        valid_moves = self.order_moves(valid_moves, you, opponent) if maximizing else self.order_moves(valid_moves, opponent, you)

        if not valid_moves:
            # Pass logic
            if maximizing:
                # If current player (maximizing) has no moves, but opponent does, switch turns
                # If neither has moves, game over
                opp_moves = self.get_legal_moves(opponent, opponent, you)
                if not opp_moves:
                    return None, self.evaluate(you, opponent, moves_left) # Game over
                # Pass turn
                return self.alpha_beta(you, opponent, depth, alpha, beta, False, moves_left, start_time)
            else:
                # Opponent (minimizing) has no moves
                my_moves = self.get_legal_moves(you, you, opponent)
                if not my_moves:
                    return None, self.evaluate(you, opponent, moves_left) # Game over
                # Pass turn
                return self.alpha_beta(you, opponent, depth, alpha, beta, True, moves_left, start_time)

        best_move = valid_moves[0]

        if maximizing:
            max_eval = -float('inf')
            for r, c in valid_moves:
                new_you, new_opponent = self.make_move(you, r, c, you, opponent)
                _, eval_score = self.alpha_beta(new_you, new_opponent, depth - 1, alpha, beta, False, moves_left - 1, start_time)
                
                if eval_score is None: return None, 0 # Timeout return

                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (r, c)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return best_move, max_eval
        else:
            min_eval = float('inf')
            for r, c in valid_moves:
                new_opponent, new_you = self.make_move(opponent, r, c, opponent, you)
                # Note: we swap arguments because roles reverse in recursion
                _, eval_score = self.alpha_beta(new_you, new_opponent, depth - 1, alpha, beta, True, moves_left - 1, start_time)
                
                if eval_score is None: return None, 0

                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (r, c)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return best_move, min_eval

    def search(self, you, opponent):
        start_time = time.time()
        moves_left = np.sum(1 - (you | opponent)) # Empty cells
        legal_moves = self.get_legal_moves(you, you, opponent)
        
        if not legal_moves:
            return "pass"
        
        # If only one move, take it immediately
        if len(legal_moves) == 1:
            return self.to_algebraic(legal_moves[0])

        best_move = legal_moves[0]
        
        # Iterative Deepening
        # Start depth at 1, increase until time runs out
        current_depth = 1
        while True:
            if time.time() - start_time > self.TIME_LIMIT * 0.8: # Leave buffer
                break
            
            move, score = self.alpha_beta(you, opponent, current_depth, -float('inf'), float('inf'), True, moves_left, start_time)
            
            if move is not None:
                best_move = move
            
            current_depth += 1
            # Safety break for max depth
            if current_depth > 12:
                break
                
        return self.to_algebraic(best_move)

    def to_algebraic(self, move):
        r, c = move
        return f"{chr(ord('a') + c)}{r + 1}"

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    agent = OthelloAgent()
    return agent.search(you, opponent)
