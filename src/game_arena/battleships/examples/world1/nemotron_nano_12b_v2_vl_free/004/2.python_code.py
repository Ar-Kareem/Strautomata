
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    unvisited = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
    
    candidates = []
    for r, c in unvisited:
        score = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                score += 1
        candidates.append((r, c, score))
    
    candidates.sort(key=lambda x: (-x[2], x[0], x[1]))
    max_score = candidates[0][2] if candidates else 0
    best_candidates = [(r, c) for r, c, score in candidates if score == max_score]
    
    return random.choice(best_candidates) if best_candidates else (0, 0)
