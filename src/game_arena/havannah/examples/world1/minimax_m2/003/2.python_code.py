
# Define the neighbor offsets for the hex grid
DIRS = [ (-1,0), (1,0), (-1,-1), (0,-1), (0,1), (-1,1) ]

def get_valid_neighbors(r, c, valid_mask):
    """Return list of valid neighbors for a cell."""
    neighbors = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 15 and 0 <= nc < 15 and valid_mask[nr][nc]:
            neighbors.append((nr, nc))
    return neighbors

def find_corners(valid_mask):
    """Find the six corner cells based on valid_mask."""
    min_neighbors = float('inf')
    cell_counts = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c]:
                count = len(get_valid_neighbors(r, c, valid_mask))
                cell_counts.append((r, c, count))
                if count < min_neighbors:
                    min_neighbors = count
    corners = [(r, c) for r, c, count in cell_counts if count == min_neighbors]
    # Ensure exactly six corners by taking the first six if more are found
    if len(corners) > 6:
        corners = corners[:6]
    return corners

def has_bridge_won(player, board, corners):
    """Check if the player has won by forming a bridge between two corners."""
    occupied_corners = [(r, c) for r, c in corners if board[r][c] == player]
    if len(occupied_corners) < 2:
        return False
    # Build set of player's stones
    stones = set()
    for r in range(15):
        for c in range(15):
            if board[r][c] == player:
                stones.add((r, c))
    # Check each pair of occupied corners for connectivity
    for i in range(len(occupied_corners)):
        start = occupied_corners[i]
        visited = set()
        queue = [start]
        visited.add(start)
        while queue:
            cell = queue.pop(0)
            for neighbor in get_valid_neighbors(cell[0], cell[1], [[valid_mask[r][c] for c in range(15)] for r in range(15)]):
                if neighbor in stones and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        # Check if any other corner is in the visited set
        for j in range(i+1, len(occupied_corners)):
            if occupied_corners[j] in visited:
                return True
    return False

def policy(me, opp, valid_mask):
    """Determine the next move for the player."""
    # Create board: 1 for me, 2 for opp, 0 for empty, -1 for invalid
    board = [[-1 for _ in range(15)] for _ in range(15)]
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c]:
                if (r, c) in me:
                    board[r][c] = 1
                elif (r, c) in opp:
                    board[r][c] = 2
                else:
                    board[r][c] = 0
    # Find corners
    corners = find_corners(valid_mask)
    # Get list of valid empty cells
    valid_empty_cells = [(r, c) for r in range(15) for c in range(15) if valid_mask[r][c] and board[r][c] == 0]
    # Check if I can win immediately
    for cell in valid_empty_cells:
        r, c = cell
        board[r][c] = 1
        if has_bridge_won(1, board, corners):
            return cell
        board[r][c] = 0
    # Check if opponent can win and block
    if has_bridge_won(2, board, corners):
        opponent_winning_moves = []
        for cell in valid_empty_cells:
            r, c = cell
            board[r][c] = 2
            if has_bridge_won(2, board, corners):
                opponent_winning_moves.append(cell)
            board[r][c] = 0
        if opponent_winning_moves:
            return opponent_winning_moves[0]
    # Choose a boundary cell to control edges
    boundary_cells = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c]:
                if get_valid_neighbors(r, c, valid_mask):
                    has_invalid = False
                    for dr, dc in DIRS:
                        nr, nc = r + dr, c + dc
                        if not (0 <= nr < 15 and 0 <= nc < 15 and valid_mask[nr][nc]):
                            has_invalid = True
                            break
                    if has_invalid:
                        boundary_cells.append((r, c))
    for cell in boundary_cells:
        if board[cell[0]][cell[1]] == 0:
            return cell
    # Fallback to any valid empty cell
    if valid_empty_cells:
        return valid_empty_cells[0]
    else:
        # Should not happen, but return first valid cell if any
        for r in range(15):
            for c in range(15):
                if valid_mask[r][c]:
                    return (r, c)
