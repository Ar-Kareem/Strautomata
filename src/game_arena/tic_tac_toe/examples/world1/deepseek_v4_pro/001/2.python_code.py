
import math
import copy

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Tic Tac Toe policy using Minimax with Alpha-Beta pruning.
    Returns the best move (row, col) for the AI (player 1).
    """
    player = 1
    opponent = -1
    
    # Check if board is empty (first move)
    empty_count = sum(cell == 0 for row in board for cell in row)
    if empty_count == 9:
        # Optimal first move: center
        if board[1][1] == 0:
            return (1, 1)
        # Fallback to corner
        for r, c in [(0,0), (0,2), (2,0), (2,2)]:
            if board[r][c] == 0:
                return (r, c)
    
    def check_winner(state, p):
        """Check if player p has won."""
        # Rows
        for row in state:
            if all(cell == p for cell in row):
                return True
        # Columns
        for col in range(3):
            if all(state[row][col] == p for row in range(3)):
                return True
        # Diagonals
        if all(state[i][i] == p for i in range(3)):
            return True
        if all(state[i][2-i] == p for i in range(3)):
            return True
        return False
    
    def is_full(state):
        """Check if board is full."""
        return all(cell != 0 for row in state for cell in row)
    
    def get_empty_cells(state):
        """Return list of empty cell coordinates."""
        return [(r, c) for r in range(3) for c in range(3) if state[r][c] == 0]
    
    def minimax(state, depth, alpha, beta, maximizing_player):
        """
        Minimax with alpha-beta pruning.
        Returns (score, best_move).
        """
        if check_winner(state, player):
            return (10 - depth, None)  # Prefer faster wins
        if check_winner(state, opponent):
            return (-10 + depth, None)  # Prefer slower losses
        if is_full(state):
            return (0, None)
        
        empty_cells = get_empty_cells(state)
        
        if maximizing_player:
            max_eval = -math.inf
            best_move = None
            
            # Evaluate moves: corners and center first for better pruning
            move_priority = []
            for move in empty_cells:
                r, c = move
                # Priority: center, then corners, then edges
                if r == 1 and c == 1:
                    priority = 0
                elif (r + c) % 2 == 0:  # corners
                    priority = 1
                else:  # edges
                    priority = 2
                move_priority.append((priority, move))
            move_priority.sort()
            
            for _, move in move_priority:
                r, c = move
                state[r][c] = player
                eval_score, _ = minimax(state, depth + 1, alpha, beta, False)
                state[r][c] = 0
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return (max_eval, best_move)
        else:
            min_eval = math.inf
            best_move = None
            
            move_priority = []
            for move in empty_cells:
                r, c = move
                if r == 1 and c == 1:
                    priority = 0
                elif (r + c) % 2 == 0:
                    priority = 1
                else:
                    priority = 2
                move_priority.append((priority, move))
            move_priority.sort()
            
            for _, move in move_priority:
                r, c = move
                state[r][c] = opponent
                eval_score, _ = minimax(state, depth + 1, alpha, beta, True)
                state[r][c] = 0
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return (min_eval, best_move)
    
    # Create a deep copy to avoid modifying the original board
    board_copy = copy.deepcopy(board)
    score, best_move = minimax(board_copy, 0, -math.inf, math.inf, True)
    
    # Fallback: if no best move found (shouldn't happen), pick first empty cell
    if best_move is None:
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    return (r, c)
    
    return best_move
