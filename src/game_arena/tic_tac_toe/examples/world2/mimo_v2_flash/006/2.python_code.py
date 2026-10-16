
import sys
import time
import random
from copy import deepcopy

# Increase recursion depth to ensure we can search deep enough
sys.setrecursionlimit(2000)

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Implements a Minimax policy with Alpha-Beta pruning for 4x4 Tic Tac Toe.
    Prioritizes immediate wins, blocks immediate threats, and uses depth-limited
    search to determine the best move based on board control.
    """
    
    # --- Helper Functions ---

    def get_all_moves(b):
        """Returns a list of (r, c) for all empty cells."""
        moves = []
        for r in range(4):
            for c in range(4):
                if b[r][c] == 0:
                    moves.append((r, c))
        return moves

    def is_winner(b, player):
        """
        Checks if the specified player has 4 in a row.
        Since the board is 4x4, any 4 cells in a line constitute a win.
        """
        # Rows
        for r in range(4):
            if all(b[r][c] == player for c in range(4)): return True
        # Cols
        for c in range(4):
            if all(b[r][c] == player for r in range(4)): return True
        # Diagonals
        if all(b[i][i] == player for i in range(4)): return True
        if all(b[i][3-i] == player for i in range(4)): return True
        return False

    def evaluate_board(b, player):
        """
        Heuristic evaluation.
        Returns a score from the perspective of the 'player'.
        """
        opponent = -player
        
        # Check for terminal states first
        if is_winner(b, player): return 1000
        if is_winner(b, opponent): return -1000
        
        # Control Heuristic:
        # Center cells (1,1), (1,2), (2,1), (2,2) are most valuable.
        score = 0
        center_weight = 2
        edge_weight = 1
        
        for r in range(4):
            for c in range(4):
                if b[r][c] == player:
                    if 1 <= r <= 2 and 1 <= c <= 2:
                        score += center_weight
                    else:
                        score += edge_weight
                elif b[r][c] == opponent:
                    if 1 <= r <= 2 and 1 <= c <= 2:
                        score -= center_weight
                    else:
                        score -= edge_weight
        return score

    def minimax(b, depth, alpha, beta, is_maximizing_player):
        """
        Minimax with Alpha-Beta Pruning.
        Returns the best score for the current node.
        """
        # Base cases
        if is_winner(b, 1): return 1000
        if is_winner(b, -1): return -1000
        
        if depth == 0:
            return evaluate_board(b, 1)
            
        moves = get_all_moves(b)
        if not moves:
            # Draw
            return 0

        if is_maximizing_player:
            max_eval = -float('inf')
            for r, c in moves:
                b[r][c] = 1
                eval_score = minimax(b, depth - 1, alpha, beta, False)
                b[r][c] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in moves:
                b[r][c] = -1
                eval_score = minimax(b, depth - 1, alpha, beta, True)
                b[r][c] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Logic ---

    # 1. Immediate Win
    empty_cells = get_all_moves(board)
    for r, c in empty_cells:
        board[r][c] = 1
        if is_winner(board, 1):
            board[r][c] = 0 # Reset before returning
            return (r, c)
        board[r][c] = 0

    # 2. Immediate Block
    for r, c in empty_cells:
        board[r][c] = -1
        if is_winner(board, -1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 3. Depth-limited search for the best move
    # Depth 6 is sufficient for 4x4 board to look ahead within time limits
    # We randomize the order of moves to avoid getting stuck in loops if scores are tied
    random.shuffle(empty_cells)
    
    best_score = -float('inf')
    best_moves = []
    
    for r, c in empty_cells:
        board[r][c] = 1
        score = minimax(board, 5, -float('inf'), float('inf'), False) # Depth 5
        board[r][c] = 0
        
        if score > best_score:
            best_score = score
            best_moves = [(r, c)]
        elif score == best_score:
            best_moves.append((r, c))
    
    # Tie-breaker: Prefer center
    if len(best_moves) > 1:
        center_moves = []
        for move in best_moves:
            r, c = move
            if 1 <= r <= 2 and 1 <= c <= 2:
                center_moves.append(move)
        if center_moves:
            return center_moves[0]
            
    return best_moves[0]
