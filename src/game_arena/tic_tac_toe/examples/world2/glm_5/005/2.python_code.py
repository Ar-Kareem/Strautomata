
import math
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determines the next move for a 4x4 Tic Tac Toe game using Minimax with Alpha-Beta pruning.
    
    Args:
        board: A 4x4 list of lists representing the game state.
               0: empty, 1: AI, -1: Opponent.
               
    Returns:
        A tuple (row, col) representing the chosen move.
    """
    
    # Predefined move order for efficient pruning: Center > Corners > Edges
    # Indices: (1,1), (1,2), (2,1), (2,2) are center.
    move_order = [
        (1, 1), (1, 2), (2, 1), (2, 2),
        (0, 0), (0, 3), (3, 0), (3, 3),
        (0, 1), (0, 2), (1, 0), (2, 0), (1, 3), (2, 3), (3, 1), (3, 2)
    ]

    def get_valid_moves(b: List[List[int]]) -> List[Tuple[int, int]]:
        """Returns valid moves sorted by strategic priority (center/corners first)."""
        return [(r, c) for r, c in move_order if b[r][c] == 0]

    def check_winner(b: List[List[int]]) -> Optional[int]:
        """Checks for a winner. Returns 1, -1, or None."""
        # Check rows
        for r in range(4):
            if b[r][0] != 0 and b[r][0] == b[r][1] == b[r][2] == b[r][3]:
                return b[r][0]
        # Check cols
        for c in range(4):
            if b[0][c] != 0 and b[0][c] == b[1][c] == b[2][c] == b[3][c]:
                return b[0][c]
        # Check diagonals
        if b[0][0] != 0 and b[0][0] == b[1][1] == b[2][2] == b[3][3]:
            return b[0][0]
        if b[0][3] != 0 and b[0][3] == b[1][2] == b[2][1] == b[3][0]:
            return b[0][3]
        return None

    def is_full(b: List[List[int]]) -> bool:
        """Checks if the board is full."""
        return all(b[r][c] != 0 for r in range(4) for c in range(4))

    def evaluate(b: List[List[int]]) -> int:
        """
        Heuristic evaluation of the board state.
        Scores based on potential winning lines.
        """
        score = 0
        # Lines to check: 4 rows, 4 cols, 2 diagonals
        lines = []
        for r in range(4): lines.append([b[r][c] for c in range(4)])
        for c in range(4): lines.append([b[r][c] for r in range(4)])
        lines.append([b[i][i] for i in range(4)])
        lines.append([b[i][3-i] for i in range(4)])

        for line in lines:
            friend = line.count(1)
            enemy = line.count(-1)
            
            if friend > 0 and enemy > 0:
                continue # Mixed line, no value
            
            # Weight lines heavily based on count
            # 3 marks is a serious threat or advantage
            if friend == 3: score += 100
            elif friend == 2: score += 10
            elif friend == 1: score += 1
            elif enemy == 3: score -= 100
            elif enemy == 2: score -= 10
            elif enemy == 1: score -= 1
                
        return score

    def minimax(b: List[List[int]], depth: int, alpha: float, beta: float, maximizing: bool) -> int:
        """Minimax algorithm with Alpha-Beta pruning."""
        winner = check_winner(b)
        if winner == 1: return 10000 + depth # Prefer faster wins
        if winner == -1: return -10000 - depth # Prefer slower losses
        if is_full(b): return 0 # Draw
        if depth == 0: return evaluate(b)

        moves = get_valid_moves(b)
        
        if maximizing:
            max_eval = -math.inf
            for r, c in moves:
                b[r][c] = 1
                eval_val = minimax(b, depth - 1, alpha, beta, False)
                b[r][c] = 0
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = math.inf
            for r, c in moves:
                b[r][c] = -1
                eval_val = minimax(b, depth - 1, alpha, beta, True)
                b[r][c] = 0
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha: break
            return min_eval

    # --- Main Logic ---
    
    empty_count = sum(row.count(0) for row in board)
    
    # Adjust depth based on game stage
    # 4x4 board has depth 16 max. Deeper search takes longer.
    if empty_count > 10: search_depth = 4
    elif empty_count > 5: search_depth = 6
    else: search_depth = 8

    # 1. Check for immediate win
    for r, c in get_valid_moves(board):
        board[r][c] = 1
        if check_winner(board) == 1:
            board[r][c] = 0
            return r, c
        board[r][c] = 0

    # 2. Check for immediate block
    for r, c in get_valid_moves(board):
        board[r][c] = -1
        if check_winner(board) == -1:
            board[r][c] = 0
            return r, c
        board[r][c] = 0

    # 3. Opening move: Take center if available
    if board[1][1] == 0: return (1, 1)
    if board[1][2] == 0: return (1, 2)
    if board[2][1] == 0: return (2, 1)
    if board[2][2] == 0: return (2, 2)

    # 4. Minimax search
    best_score = -math.inf
    best_move = None
    
    for r, c in get_valid_moves(board):
        board[r][c] = 1
        score = minimax(board, search_depth, -math.inf, math.inf, False)
        board[r][c] = 0
        
        if score > best_score:
            best_score = score
            best_move = (r, c)

    # Fallback (should ideally not be reached if logic is correct)
    if best_move is None:
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return r, c

    return best_move
