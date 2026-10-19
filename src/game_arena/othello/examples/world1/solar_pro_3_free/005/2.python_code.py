
import numpy as np
import random

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Initialize 8x8 board: 1 for our discs, -1 for opponent, 0 for empty
    board = np.zeros_like(you)
    board[you == 1] = 1
    board[opponent == 1] = -1
    
    # 8 directions for flip check
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), 
                 (1, 1), (-1, -1), (1, -1), (-1, 1)]
    
    # Generate legal moves by checking flip possibility in all directions
    legal_moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != 0:  # Skip occupied cells
                continue
            if not is_legal_move(board, r, c):
                continue
            legal_moves.append((r, c))
    
    # No moves? Pass
    if not legal_moves:
        return "pass"
    
    best_score = -float('inf')
    best_flips = 0
    best_moves = []
    
    # Evaluate each legal move
    for move in legal_moves:
        r, c = move
        new_board, flips = simulate_move(board, r, c)
        material = np.sum(new_board == 1) - np.sum(new_board == -1)
        score = material + 0.1 * flips  # Material dominance + flip aggression
        
        if score > best_score:
            best_score = score
            best_flips = flips
            best_moves = [move]
        elif score == best_score:
            if flips > best_flips:
                best_flips = flips
                best_moves = [move]
            elif flips == best_flips:
                best_moves.append(move)
    
    # Select random best move if tie
    selected_move = random.choice(best_moves)
    r, c = selected_move
    return to_algebraic(r, c)

# Helper: Check if a move is legal (flips opponent discs in any direction)
def is_legal_move(board, r, c):
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < 8 and 0 <= nc < 8):
            continue
        if board[nr][nc] != -1:  # Not an opponent disc
            continue
        steps = 0
        # Count contiguous opponent discs in this direction
        while nr >= 0 and nr < 8 and nc >= 0 and nc < 8 and board[nr][nc] == -1:
            steps += 1
            nr += dr
            nc += dc
        # Must end at our disc for a valid flip
        if nr >= 0 and nr < 8 and nc >= 0 and nc < 8 and board[nr][nc] == 1:
            return True
    return False

# Helper: Simulate move result and count flips
def simulate_move(board, r, c):
    new_board = board.copy()
    new_board[r][c] = 1  # Place our disc
    flips = 0
    
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < 8 and 0 <= nc < 8):
            continue
        if new_board[nr][nc] != -1:  # Not an opponent disc
            continue
        
        # Count flip steps and check valid flip path
        steps = 0
        while nr >= 0 and nr < 8 and nc >= 0 and nc < 8 and new_board[nr][nc] == -1:
            steps += 1
            nr += dr
            nc += dc
        
        # Valid flip if path ends at our disc
        if nr >= 0 and nr < 8 and nc >= 0 and nc < 8 and new_board[nr][nc] == 1:
            flips += steps
            # Apply flips: turn all encountered opponent discs to ours
            nr1, nc1 = r + dr, c + dc
            for _ in range(steps):
                if new_board[nr1][nc1] == -1:
                    new_board[nr1][nc1] = 1
                nr1 += dr
                nc1 += dc
    
    return new_board, flips

# Helper: Convert (row, col) to algebraic notation (a1-h8)
def to_algebraic(r, c):
    return chr(ord('a') + c) + str(r + 1)
