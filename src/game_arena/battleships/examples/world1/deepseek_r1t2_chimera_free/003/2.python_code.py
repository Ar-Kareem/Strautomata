
import numpy as np  # Ensure numpy is imported for potential future enhancements

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation (optional but can be useful)
    # board_np = np.array(board)
    
    hits = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
    
    # Target Mode: Process hits to find optimal next shots
    candidates = set()
    for r, c in hits:
        # Check horizontal line
        left = c
        while left - 1 >= 0 and board[r][left - 1] == 1:
            left -= 1
        right = c
        while right + 1 < 10 and board[r][right + 1] == 1:
            right += 1
        
        # Check vertical line
        up = r
        while up - 1 >= 0 and board[up - 1][c] == 1:
            up -= 1
        down = r
        while down + 1 < 10 and board[down + 1][c] == 1:
            down += 1
        
        h_length = right - left + 1
        v_length = down - up + 1
        
        # Determine ship direction and add end candidates
        if h_length > 1 and h_length >= v_length:
            if left > 0 and board[r][left - 1] == 0:
                candidates.add((r, left - 1))
            if right < 9 and board[r][right + 1] == 0:
                candidates.add((r, right + 1))
        elif v_length > 1:
            if up > 0 and board[up - 1][c] == 0:
                candidates.add((up - 1, c))
            if down < 9 and board[down + 1][c] == 0:
                candidates.add((down + 1, c))
        else:
            # Single hit, check all four directions
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    candidates.add((nr, nc))
    
    if candidates:
        # Prioritize candidates with the most adjacent hits
        candidate_list = list(candidates)
        candidate_scores = []
        for (r, c) in candidate_list:
            score = 0
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                    score += 1
            candidate_scores.append(score)
        
        max_score = max(candidate_scores)
        best_candidates = [candidate_list[i] for i in range(len(candidate_list)) if candidate_scores[i] == max_score]
        best_candidates.sort()  # Deterministic choice
        return best_candidates[0]
    
    # Hunt Mode: Checkerboard pattern targeting
    for parity in [0, 1]:  # First even parity (0), then odd (1)
        hunt_candidates = []
        for r in range(10):
            for c in range(10):
                if (r + c) % 2 == parity and board[r][c] == 0:
                    hunt_candidates.append((r, c))
        if hunt_candidates:
            hunt_candidates.sort()
            return hunt_candidates[0]
    
    # Fallback: Target any remaining unknown cell (shouldn't trigger in valid games)
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)  # Default if no cells left (game over)
