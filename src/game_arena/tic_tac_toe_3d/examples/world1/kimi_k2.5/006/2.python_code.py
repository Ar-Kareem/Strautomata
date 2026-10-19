
import numpy as np
from typing import List, Tuple

# Precompute all 49 winning lines in 3x3x3
# 27 axis-aligned (9 per direction), 18 face diagonals (6 per axis plane), 4 space diagonals
LINES = []

# Axis-aligned lines (varying one coordinate)
for j in range(3):
    for k in range(3):
        LINES.append([(i, j, k) for i in range(3)])  # Varying x
for i in range(3):
    for k in range(3):
        LINES.append([(i, j, k) for j in range(3)])  # Varying y
for i in range(3):
    for j in range(3):
        LINES.append([(i, j, k) for k in range(3)])  # Varying z

# Face diagonals (2 per fixed plane)
# XY planes (fixed z)
for k in range(3):
    LINES.append([(i, i, k) for i in range(3)])
    LINES.append([(i, 2-i, k) for i in range(3)])
# XZ planes (fixed y)
for j in range(3):
    LINES.append([(i, j, i) for i in range(3)])
    LINES.append([(i, j, 2-i) for i in range(3)])
# YZ planes (fixed x)
for i in range(3):
    LINES.append([(i, j, j) for j in range(3)])
    LINES.append([(i, j, 2-j) for j in range(3)])

# Space diagonals
LINES.append([(i, i, i) for i in range(3)])
LINES.append([(i, i, 2-i) for i in range(3)])
LINES.append([(i, 2-i, i) for i in range(3)])
LINES.append([(i, 2-i, 2-i) for i in range(3)])


def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    board_arr = np.array(board)
    empty_cells = list(zip(*np.where(board_arr == 0)))
    
    if not empty_cells:
        return (0, 0, 0)  # Should not occur in valid game
    
    # Helper to count threats (2 in a row with empty 3rd) after placing at pos
    def count_new_threats(pos: Tuple[int, int, int], player: int) -> int:
        i, j, k = pos
        threats = 0
        for line in LINES:
            if (i, j, k) not in line:
                continue
            player_count = 0
            empty_count = 0
            for (x, y, z) in line:
                if (x, y, z) == (i, j, k):
                    player_count += 1
                else:
                    val = board_arr[x, y, z]
                    if val == player:
                        player_count += 1
                    elif val == 0:
                        empty_count += 1
            if player_count == 2 and empty_count == 1:
                threats += 1
        return threats
    
    # 1. Check for immediate winning move
    for line in LINES:
        values = [board_arr[pos] for pos in line]
        if values.count(1) == 2 and values.count(0) == 1:
            for pos in line:
                if board_arr[pos] == 0:
                    return pos
    
    # 2. Check for opponent immediate win and block
    urgent_blocks = []
    for line in LINES:
        values = [board_arr[pos] for pos in line]
        if values.count(-1) == 2 and values.count(0) == 1:
            for pos in line:
                if board_arr[pos] == 0:
                    urgent_blocks.append(pos)
                    break
    
    if urgent_blocks:
        # If multiple threats exist, opponent wins regardless, but block one
        return urgent_blocks[0]
    
    # 3. Look for fork opportunity (create two simultaneous threats)
    for pos in empty_cells:
        if count_new_threats(pos, 1) >= 2:
            return pos
    
    # 4. Block opponent fork (prevent them from creating two threats)
    opp_fork_blocks = []
    for pos in empty_cells:
        if count_new_threats(pos, -1) >= 2:
            opp_fork_blocks.append(pos)
    
    if opp_fork_blocks:
        # Prefer blocks that also create our own threat
        best_block = opp_fork_blocks[0]
        best_threat_count = -1
        for pos in opp_fork_blocks:
            our_threats = count_new_threats(pos, 1)
            if our_threats > best_threat_count:
                best_threat_count = our_threats
                best_block = pos
        return best_block
    
    # 5. Heuristic evaluation for remaining moves
    def evaluate(pos: Tuple[int, int, int]) -> int:
        i, j, k = pos
        score = 0
        
        # Positional value based on number of lines passing through cell
        # Center: 13, Corner: 7, Edge: 5, Face: 4
        border_coords = sum(1 for x in (i, j, k) if x in (0, 2))
        if border_coords == 0:  # Center
            score += 1000
        elif border_coords == 3:  # Corner
            score += 100
        elif border_coords == 2:  # Edge
            score += 50
        else:  # Face center (1 border coord)
            score += 30
        
        # Value of creating potential threats and blocking opponent potentials
        for line in LINES:
            if pos not in line:
                continue
            vals = [board_arr[p] for p in line]
            
            # Skip if opponent already blocks this line
            if -1 in vals:
                continue
            
            our_count = vals.count(1)
            if our_count == 1:
                score += 10  # Building on existing piece
            elif our_count == 2:
                score += 100  # Creating a threat (should be rare here due to fork check)
        
        return score
    
    best_move = empty_cells[0]
    best_score = -float('inf')
    
    for pos in empty_cells:
        s = evaluate(pos)
        if s > best_score:
            best_score = s
            best_move = pos
    
    return best_move
