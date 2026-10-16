
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible winning lines
    lines = []
    # Axis-aligned lines
    for y in range(3):
        for z in range(3):
            lines.append([(x, y, z) for x in range(3)])
    for x in range(3):
        for z in range(3):
            lines.append([(x, y, z) for y in range(3)])
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])
    # Face diagonals (xy-plane)
    for z in range(3):
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    # Face diagonals (xz-plane)
    for y in range(3):
        lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    # Face diagonals (yz-plane)
    for x in range(3):
        lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    # Space diagonals
    space_diagonals = [
        [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
        [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
        [(0, 2, 0), (1, 1, 1), (2, 0, 2)],
        [(0, 2, 2), (1, 1, 1), (2, 0, 0)]
    ]
    lines.extend(space_diagonals)
    
    # Step 1: Check for immediate winning move
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    for line in lines:
                        if (i, j, k) in line:
                            ones_count = 0
                            for (x, y, z) in line:
                                if (x, y, z) == (i, j, k):
                                    continue
                                if board[x][y][z] == 1:
                                    ones_count += 1
                                else:
                                    break
                            if ones_count == 2:
                                return (i, j, k)
    
    # Step 2: Block opponent's immediate winning move
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    for line in lines:
                        if (i, j, k) in line:
                            neg_ones_count = 0
                            for (x, y, z) in line:
                                if (x, y, z) == (i, j, k):
                                    continue
                                if board[x][y][z] == -1:
                                    neg_ones_count += 1
                                else:
                                    break
                            if neg_ones_count == 2:
                                return (i, j, k)
    
    # Step 3: Heuristic-based move selection
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    best_score = -float('inf')
    best_moves = []
    
    for (i, j, k) in empty_cells:
        score = 0
        for line in lines:
            if (i, j, k) in line:
                my_count = 0
                opp_count = 0
                for (x, y, z) in line:
                    if (x, y, z) == (i, j, k):
                        continue
                    val = board[x][y][z]
                    if val == 1:
                        my_count += 1
                    elif val == -1:
                        opp_count += 1
                # Calculate score based on potential
                if my_count == 2 and opp_count == 0:
                    score += 1000  # Should have been handled in step 1, extra safety
                elif my_count == 1 and opp_count == 0:
                    score += 5
                elif my_count == 0 and opp_count == 0:
                    score += 1
                # Opponent's potential
                if opp_count == 2 and my_count == 0:
                    score -= 8
                elif opp_count == 1 and my_count == 0:
                    score -= 1
        # Add bonus for center cell
        if (i, j, k) == (1, 1, 1):
            score += 3
        # Update best moves
        if score > best_score:
            best_score = score
            best_moves = [(i, j, k)]
        elif score == best_score:
            best_moves.append((i, j, k))
    
    # Tie-breaking: prefer center, then first in list
    if best_moves:
        if (1, 1, 1) in best_moves:
            return (1, 1, 1)
        return best_moves[0]
    else:
        # Fallback (should never happen)
        return empty_cells[0]
