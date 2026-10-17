
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def generate_lines():
        lines = []
        # Axis-aligned lines (x, y, z)
        for y in range(3):
            for z in range(3):
                lines.append([(x, y, z) for x in range(3)])
        for x in range(3):
            for z in range(3):
                lines.append([(x, y, z) for y in range(3)])
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        # Face diagonals
        for x in range(3):
            lines.append([(x, y, y) for y in range(3)])
            lines.append([(x, y, 2 - y) for y in range(3)])
        for y in range(3):
            lines.append([(x, y, x) for x in range(3)])
            lines.append([(x, y, 2 - x) for x in range(3)])
        for z in range(3):
            lines.append([(x, x, z) for x in range(3)])
            lines.append([(x, 2 - x, z) for x in range(3)])
        # Space diagonals
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2 - i) for i in range(3)])
        lines.append([(i, 2 - i, i) for i in range(3)])
        lines.append([(i, 2 - i, 2 - i) for i in range(3)])
        return lines

    lines = generate_lines()
    
    # Check for immediate win
    for line in lines:
        cells = [board[i][j][k] for (i, j, k) in line]
        if sum(cells) == 2:  # Two 1s and one empty
            for idx, val in enumerate(cells):
                if val == 0:
                    return line[idx]
    
    # Block opponent's win
    for line in lines:
        cells = [board[i][j][k] for (i, j, k) in line]
        if sum(cells) == -2:  # Two -1s and one empty
            for idx, val in enumerate(cells):
                if val == 0:
                    return line[idx]
    
    # Prefer center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Choose move with maximum influence (part of most lines)
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    cell_scores = {}
    
    for cell in empty_cells:
        score = 0
        for line in lines:
            if cell in line:
                score += 1
        cell_scores[cell] = score
    
    # Return best cell by score
    sorted_cells = sorted(empty_cells, key=lambda c: cell_scores[c], reverse=True)
    return sorted_cells[0]
