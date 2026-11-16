
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Helper function to check if a move is legal
    def is_legal(r, c):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            count = 0
            while 0 <= nr < 8 and 0 <= nc < 8:
                if opponent[nr][nc] == 1:
                    count += 1
                    nr += dr
                    nc += dc
                elif you[nr][nc] == 1:
                    return True
                else:
                    break
        return False

    # Helper function to count flips for a move
    def get_flips(r, c):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        total = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            count = 0
            while 0 <= nr < 8 and 0 <= nc < 8:
                if opponent[nr][nc] == 1:
                    count += 1
                    nr += dr
                    nc += dc
                elif you[nr][nc] == 1:
                    total += count
                    break
                else:
                    break
        return total

    # Generate all legal moves
    legal_moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                if is_legal(r, c):
                    legal_moves.append((r, c))
    
    # Check for corner moves (a1, h1, a8, h8)
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    for move in legal_moves:
        if move in corners:
            r, c = move
            letter = chr(ord('a') + c)
            row = r + 1
            return f"{letter}{row}"
    
    # Select move with the most flips if no corners available
    best_move = None
    best_flips = -1
    for move in legal_moves:
        r, c = move
        flips = get_flips(r, c)
        if flips > best_flips:
            best_flips = flips
            best_move = move
    
    if best_move is None:
        return "pass"
    
    r, c = best_move
    letter = chr(ord('a') + c)
    row = r + 1
    return f"{letter}{row}"
