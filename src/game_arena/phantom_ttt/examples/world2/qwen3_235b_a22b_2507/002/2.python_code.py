
def policy(board: list[list[int]]) -> tuple[int, int]:
    import numpy as np

    b = np.array(board)
    
    # Available moves: cells that are not confirmed as ours
    # Note: We never want to re-place on our confirmed cell (value 1)
    available_moves = []
    for i in range(3):
        for j in range(3):
            if b[i][j] != 1:
                available_moves.append((i, j))
    
    # If no move available (shouldn't happen), return center
    if not available_moves:
        return (1, 1)
    
    # Check for winning move: place our mark to complete a line
    for (i, j) in available_moves:
        b[i][j] = 1
        if (b[i].sum() == 3 or b[:, j].sum() == 3 or 
            (i == j and np.diag(b).sum() == 3) or 
            (i + j == 2 and np.diag(np.fliplr(b)).sum() == 3)):
            b[i][j] = 0  # restore
            return (i, j)
        b[i][j] = 0  # restore
    
    # No perfect win; now score each move
    scores = np.zeros((3, 3))
    
    # Base scores: center=3, corners=2, edges=1
    position_value = np.array([
        [2, 1, 2],
        [1, 3, 1],
        [2, 1, 2]
    ])
    
    for (i, j) in available_moves:
        # Add positional preference
        scores[i][j] += position_value[i][j]
        
        # Simulate placing our mark and count how many lines get two of our marks (close to win)
        b[i][j] = 1
        for line in [
            b[i],              # row
            b[:, j],           # col
            np.diag(b) if i == j else [],          # diag
            np.diag(np.fliplr(b)) if i + j == 2 else []
        ]:
            if len(line) > 0:
                if np.sum(line) == 2:
                    scores[i][j] += 10  # Strong incentive to create a near-win
        b[i][j] = 0
    
    # Additionally, try to block potential opponent wins
    # Since we can't see opponent marks, we assume symmetry and penalize cells that would complete opponent lines
    # But without memory, we use a proxy: if two non-our cells in a line, and we're the only other one, then maybe opponent is there
    # Instead: we use a defensive heuristic — avoid leaving lines open
    # Alternate idea: encourage moves that intersect opponent-heavy lines, but again, hidden information.

    # Approximate defense: in any line with 0 of our marks, if it has many '0's (unknown), assume opponent might be building
    # But we can't be sure. So keep focus on offense.

    # Find move with highest score
    best_move = available_moves[0]
    best_score = -1
    for (i, j) in available_moves:
        if scores[i][j] > best_score:
            best_score = scores[i][j]
            best_move = (i, j)
    
    return best_move
