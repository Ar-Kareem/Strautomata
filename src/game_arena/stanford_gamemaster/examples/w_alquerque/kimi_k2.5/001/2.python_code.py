
import sys
from typing import List, Tuple

# 8 directions: orthogonal and diagonal
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

def parse_state(state: List[List[object]]):
    """Parse the proposition list into a grid and metadata."""
    # 1-indexed grid (indices 1-5), 0-th index unused
    grid = [['blank' for _ in range(6)] for _ in range(6)]
    scores = {}
    control = None
    step = 0
    for prop in state:
        pred = prop[0]
        if pred == 'cell':
            r, c, val = int(prop[1]), int(prop[2]), prop[3]
            grid[r][c] = val
        elif pred == 'score':
            scores[prop[1]] = int(prop[2])
        elif pred == 'control':
            control = prop[1]
        elif pred == 'step':
            step = int(prop[1])
    return grid, scores, control, step

def generate_moves(grid, role: str) -> List[Tuple]:
    """Generate all legal moves for the given role."""
    opponent = 'black' if role == 'red' else 'red'
    moves = []
    for r in range(1, 6):
        for c in range(1, 6):
            if grid[r][c] == role:
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    # Simple move
                    if 1 <= nr <= 5 and 1 <= nc <= 5:
                        if grid[nr][nc] == 'blank':
                            moves.append(('move', r, c, nr, nc))
                        # Jump move
                        jr, jc = r + 2*dr, c + 2*dc
                        if 1 <= jr <= 5 and 1 <= jc <= 5:
                            if grid[nr][nc] == opponent and grid[jr][jc] == 'blank':
                                moves.append(('jump', r, c, nr, nc, jr, jc))
    return moves

def apply_move(grid, scores, role: str, move: Tuple):
    """Apply a move to the grid and return new state."""
    new_grid = [row[:] for row in grid]  # Deep copy
    new_scores = dict(scores)
    
    if move[0] == 'move':
        _, r, c, nr, nc = move
        new_grid[r][c] = 'blank'
        new_grid[nr][nc] = role
    else:  # jump
        _, r, c, mr, mc, jr, jc = move
        new_grid[r][c] = 'blank'
        new_grid[mr][mc] = 'blank'  # Capture
        new_grid[jr][jc] = role
        new_scores[role] = new_scores.get(role, 0) + 10
    return new_grid, new_scores

def format_move(move: Tuple) -> str:
    """Convert move tuple to Stanford syntax string."""
    if move[0] == 'move':
        return f"move({move[1]},{move[2]},{move[3]},{move[4]})"
    else:
        return f"jump({move[1]},{move[2]},{move[3]},{move[4]},{move[5]},{move[6]})"

def evaluate(grid, scores, role: str) -> float:
    """Static evaluation of the position from the perspective of role."""
    opponent = 'black' if role == 'red' else 'red'
    # Material difference (each capture is worth 10 points in score)
    val = scores.get(role, 0) - scores.get(opponent, 0)
    
    # Positional factors
    for r in range(1, 6):
        for c in range(1, 6):
            cell = grid[r][c]
            if cell == role:
                # Advancement bonus: red wants small r, black wants large r
                if role == 'red':
                    val += (6 - r) * 0.2
                else:
                    val += (r - 1) * 0.2
                # Center proximity (Chebyshev distance to center (3,3))
                dist = max(abs(r - 3), abs(c - 3))
                val -= dist * 0.05
            elif cell == opponent:
                if opponent == 'red':
                    val -= (6 - r) * 0.2
                else:
                    val -= (r - 1) * 0.2
                dist = max(abs(r - 3), abs(c - 3))
                val += dist * 0.05
    return val

def minimax(grid, scores, player: str, depth: int, alpha: float, beta: float, root_role: str):
    """Alpha-beta minimax search. Returns (score, move)."""
    if depth == 0:
        return evaluate(grid, scores, root_role), None
    
    moves = generate_moves(grid, player)
    
    # Move ordering: captures (jumps) first to improve pruning
    moves.sort(key=lambda m: 0 if m[0] == 'jump' else 1)
    
    if not moves:
        # No legal moves - terminal or stuck
        return evaluate(grid, scores, root_role), None
    
    opponent = 'black' if player == 'red' else 'red'
    best_move = moves[0]  # Fallback
    
    if player == root_role:
        # Maximize
        max_eval = -float('inf')
        for move in moves:
            new_grid, new_scores = apply_move(grid, scores, player, move)
            eval_score, _ = minimax(new_grid, new_scores, opponent, depth - 1, alpha, beta, root_role)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        # Minimize
        min_eval = float('inf')
        for move in moves:
            new_grid, new_scores = apply_move(grid, scores, player, move)
            eval_score, _ = minimax(new_grid, new_scores, opponent, depth - 1, alpha, beta, root_role)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(state: list[list[object]], role: str) -> str:
    """Main policy function."""
    grid, scores, control, step = parse_state(state)
    
    # Generate all legal moves for the current role
    moves = generate_moves(grid, role)
    
    if not moves:
        # Should not happen in a valid game state, but return a dummy to crash gracefully
        return "move(1,1,1,1)"
    
    if len(moves) == 1:
        return format_move(moves[0])
    
    # Search with alpha-beta at depth 3
    try:
        _, best_move = minimax(grid, scores, role, 3, -float('inf'), float('inf'), role)
        if best_move is None:
            best_move = moves[0]
        return format_move(best_move)
    except:
        # In case of any error, return the first capture if available, else first move
        jumps = [m for m in moves if m[0] == 'jump']
        if jumps:
            return format_move(jumps[0])
        return format_move(moves[0])
