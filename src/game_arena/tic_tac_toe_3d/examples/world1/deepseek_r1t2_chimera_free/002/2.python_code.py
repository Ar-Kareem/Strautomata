
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def generate_lines():
        lines = []
        # Rows in layers (x varying)
        for z in range(3):
            for y in range(3):
                lines.append([(z, y, x) for x in range(3)])
        # Columns in layers (y varying)
        for z in range(3):
            for x in range(3):
                lines.append([(z, y, x) for y in range(3)])
        # Pillars (z varying)
        for x in range(3):
            for y in range(3):
                lines.append([(z, y, x) for z in range(3)])
        # Face diagonals in xy planes (z fixed)
        for z in range(3):
            lines.append([(z, 0, 0), (z, 1, 1), (z, 2, 2)])
            lines.append([(z, 0, 2), (z, 1, 1), (z, 2, 0)])
        # Face diagonals in xz planes (y fixed)
        for y in range(3):
            lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
            lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
        # Face diagonals in yz planes (x fixed)
        for x in range(3):
            lines.append([(0, 0, x), (1, 1, x), (2, 2, x)])
            lines.append([(0, 2, x), (1, 1, x), (2, 0, x)])
        # Space diagonals
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        return lines
    
    lines = generate_lines()
    cell_to_lines = {}
    for line in lines:
        for cell in line:
            if cell not in cell_to_lines:
                cell_to_lines[cell] = []
            cell_to_lines[cell].append(line)
    
    # Find all empty cells
    empty_cells = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    empty_cells.append((z, y, x))
    
    # Check for immediate win
    for cell in empty_cells:
        for line in cell_to_lines.get(cell, []):
            count = 0
            for (z, y, x) in line:
                if (z, y, x) == cell:
                    count += 1
                else:
                    if board[z][y][x] == 1:
                        count += 1
            if count == 3:
                return cell
    
    # Check for opponent's immediate win
    threats = []
    for cell in empty_cells:
        for line in cell_to_lines.get(cell, []):
            count = 0
            for (z, y, x) in line:
                if (z, y, x) == cell:
                    count += 1
                else:
                    if board[z][y][x] == -1:
                        count += 1
            if count == 3:
                threats.append(cell)
                break  # Only need one winning line
    
    if threats:
        return threats[0]
    
    # Calculate heuristic scores
    scores = {}
    for cell in empty_cells:
        score = 0
        for line in cell_to_lines.get(cell, []):
            my_count = 0
            opp_count = 0
            for (z, y, x) in line:
                if (z, y, x) == cell:
                    continue
                val = board[z][y][x]
                if val == 1:
                    my_count += 1
                elif val == -1:
                    opp_count += 1
            if opp_count == 0:
                score += (1 << my_count)  # 2^my_count
        scores[cell] = score
    
    max_score = max(scores.values())
    candidates = [cell for cell, s in scores.items() if s == max_score]
    
    center = (1, 1, 1)
    if center in candidates:
        return center
    return candidates[0]
