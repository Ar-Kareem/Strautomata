
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Policy for 3D Tic Tac Toe (3x3x3). 
    Return the coordinates (x, y, z) of the best move.
    """
    # Precomputed 49 winning lines for 3x3x3 Tic Tac Toe
    # Each line is a tuple of 3 (x, y, z) coordinates
    lines = []
    
    # 27 axial lines
    for y in range(3):
        for z in range(3):
            lines.append(((0, y, z), (1, y, z), (2, y, z)))  # x-line
    for x in range(3):
        for z in range(3):
            lines.append(((x, 0, z), (x, 1, z), (x, 2, z)))  # y-line
    for x in range(3):
        for y in range(3):
            lines.append(((x, y, 0), (x, y, 1), (x, y, 2)))  # z-line
    
    # 18 planar diagonals
    # xy-planes (z fixed)
    for z in range(3):
        lines.append(((0, 0, z), (1, 1, z), (2, 2, z)))
        lines.append(((0, 2, z), (1, 1, z), (2, 0, z)))
    # xz-planes (y fixed)
    for y in range(3):
        lines.append(((0, y, 0), (1, y, 1), (2, y, 2)))
        lines.append(((0, y, 2), (1, y, 1), (2, y, 0)))
    # yz-planes (x fixed)
    for x in range(3):
        lines.append(((x, 0, 0), (x, 1, 1), (x, 2, 2)))
        lines.append(((x, 0, 2), (x, 1, 1), (x, 2, 0)))
    
    # 4 space diagonals
    lines.append(((0, 0, 0), (1, 1, 1), (2, 2, 2)))
    lines.append(((0, 0, 2), (1, 1, 1), (2, 2, 0)))
    lines.append(((0, 2, 0), (1, 1, 1), (2, 0, 2)))
    lines.append(((0, 2, 2), (1, 1, 1), (2, 0, 0)))
    
    # Convert board to numpy array for easier manipulation (optional, but we'll use list)
    board_np = np.array(board)
    
    # Step 1: Check for an immediate winning move for me (player 1)
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board_np[x, y, z] == 0:
                    # Try placing my mark
                    # Check all lines containing (x,y,z)
                    for line in lines:
                        if (x, y, z) in line:
                            # Count how many 1's and 0's (empty) in this line
                            count_1 = 0
                            count_0 = 0
                            for (lx, ly, lz) in line:
                                if board_np[lx, ly, lz] == 1:
                                    count_1 += 1
                                elif board_np[lx, ly, lz] == 0:
                                    count_0 += 1
                            # If two are mine and one is empty (this cell), then placing here wins
                            if count_1 == 2 and count_0 == 1:
                                return (x, y, z)
    
    # Step 2: Check if opponent can win on next move, and block
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board_np[x, y, z] == 0:
                    # Check if opponent playing here would win
                    for line in lines:
                        if (x, y, z) in line:
                            count_minus1 = 0
                            count_0 = 0
                            for (lx, ly, lz) in line:
                                if board_np[lx, ly, lz] == -1:
                                    count_minus1 += 1
                                elif board_np[lx, ly, lz] == 0:
                                    count_0 += 1
                            # If opponent has two and one empty, they can win
                            if count_minus1 == 2 and count_0 == 1:
                                return (x, y, z)
    
    # Step 3: Take center if available
    if board_np[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Step 4: Take a corner (corners are the 8 positions where each coordinate is 0 or 2)
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for corner in corners:
        x, y, z = corner
        if board_np[x, y, z] == 0:
            return (x, y, z)
    
    # Step 5: Take an edge (edge centers: positions with exactly one coordinate in the middle (1) and others 0 or 2)
    # Edge cells: (x,y,z) with exactly one of x,y,z == 1 and the other two in {0,2}
    edges = []
    for x in [0,2]:
        for y in [0,2]:
            edges.append((1, x, y))   # x=1, y in {0,2}, z in {0,2}
            edges.append((x, 1, y))   # y=1, x in {0,2}, z in {0,2}
            edges.append((x, y, 1))   # z=1, x in {0,2}, y in {0,2}
    # But we might have duplicates? Let's generate properly:
    edges = []
    # Edges: two of the coordinates are 0 or 2, one is 1
    for i in range(3): # which axis is the middle (1)
        for j in [0,2]:
            for k in [0,2]:
                if i == 0:
                    edges.append((1, j, k))
                elif i == 1:
                    edges.append((j, 1, k))
                else: # i==2
                    edges.append((j, k, 1))
    # Remove duplicates? Actually, we generated each once.
    for edge in edges:
        x, y, z = edge
        if board_np[x, y, z] == 0:
            return (x, y, z)
    
    # Step 6: Take a face center (exactly one coordinate 0 or 2, and the other two 1) - these are the face centers
    face_centers = [
        (0, 1, 1), (2, 1, 1),  # left and right face centers
        (1, 0, 1), (1, 2, 1),  # front and back (y-direction)
        (1, 1, 0), (1, 1, 2)   # top and bottom (z-direction)
    ]
    for fc in face_centers:
        x, y, z = fc
        if board_np[x, y, z] == 0:
            return (x, y, z)
    
    # Step 7: Any remaining empty cell (shouldn't happen with 27 cells, but just in case)
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board_np[x, y, z] == 0:
                    return (x, y, z)
    
    # If no empty cell (game over), return any (shouldn't happen)
    return (0, 0, 0)
