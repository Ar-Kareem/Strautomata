
lines = []
# Generate all possible winning lines (axes)
for y in range(3):
    for z in range(3):
        lines.append([(0, y, z), (1, y, z), (2, y, z)])
for x in range(3):
    for z in range(3):
        lines.append([(x, 0, z), (x, 1, z), (x, 2, z)])
for x in range(3):
    for y in range(3):
        lines.append([(x, y, 0), (x, y, 1), (x, y, 2)])
# Face diagonals
for z in range(3):
    lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
    lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
for y in range(3):
    lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
    lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
for x in range(3):
    lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
    lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
# Space diagonals
space_diag = [
    [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
    [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
    [(0, 2, 0), (1, 1, 1), (2, 0, 2)],
    [(0, 2, 2), (1, 1, 1), (2, 0, 0)],
]
lines.extend(space_diag)

def check_line(cell, player, board):
    for line in lines:
        if cell not in line:
            continue
        other = [c for c in line if c != cell]
        if all(board[c[0]][c[1]][c[2]] == player for c in other):
            return True
    return False

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Check for AI's winning move
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    if check_line((x, y, z), 1, board):
                        return (x, y, z)
    # Block opponent's winning move
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    if check_line((x, y, z), -1, board):
                        return (x, y, z)
    # Heuristic selection based on priority
    def is_corner(cell):
        return all(c in {0, 2} for c in cell)
    
    def is_edge(cell):
        cnt = sum(1 for c in cell if c in {0, 2})
        return cnt == 2
    
    def is_face_center(cell):
        cnt = sum(1 for c in cell if c in {0, 2})
        return cnt == 1 and sum(1 for c in cell if c == 1) == 2
    
    priority_order = [ (1,1,1) ]  # Center
    # Add corners, edges, face_centers
    corners = []
    edges = []
    face_centers = [ (0,1,1), (2,1,1), (1,0,1), (1,2,1), (1,1,0), (1,1,2) ]
    for cell in [(x,y,z) for x in range(3) for y in range(3) for z in range(3)]:
        if cell == (1,1,1):
            continue
        elif is_edge(cell):
            edges.append(cell)
        elif is_face_center(cell):
            face_centers.append(cell)
        elif all(c in {0,2} for c in cell):
            corners.append(cell)
    priority_order += corners + edges + face_centers
    # Select first empty cell in priority order
    for x, y, z in priority_order:
        if board[x][y][z] == 0:
            return (x, y, z)
    # Fallback (shouldn't happen)
    return (0, 0, 0)
