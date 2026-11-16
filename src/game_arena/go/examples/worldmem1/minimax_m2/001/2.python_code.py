
def find_groups(board, color):
    """Find all groups of stones of the given color on the board.
    Each group is a set of (i, j) tuples representing connected stones.
    """
    groups = []
    visited = set()
    for i in range(19):
        for j in range(19):
            if board[i][j] == color and (i, j) not in visited:
                group = set()
                queue = [(i, j)]
                while queue:
                    x, y = queue.pop(0)
                    if (x, y) in visited:
                        continue
                    visited.add((x, y))
                    group.add((x, y))
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:  # right, left, down, up
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < 19 and 0 <= ny < 19 and board[nx][ny] == color:
                            if (nx, ny) not in visited:
                                queue.append((nx, ny))
                groups.append(group)
    return groups

def get_liberties(board, group):
    """Calculate the number of liberties (adjacent empty points) for a group of stones."""
    liberties = set()
    for (x, y) in group:
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 19 and 0 <= ny < 19 and board[nx][ny] == 0:
                liberties.add((nx, ny))
    return len(liberties)

def find_group_containing(board, color, i, j):
    """Find the group containing the stone at (i, j) for the given color.
    Returns the group as a set of points, or None if not found.
    """
    if board[i][j] != color:
        return None
    visited = set()
    group = set()
    queue = [(i, j)]
    while queue:
        x, y = queue.pop(0)
        if (x, y) in visited:
            continue
        if board[x][y] != color:
            continue
        visited.add((x, y))
        group.add((x, y))
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 19 and 0 <= ny < 19 and board[nx][ny] == color:
                if (nx, ny) not in visited:
                    queue.append((nx, ny))
    return group if group else None

def compute_min_sq_dist(i, j):
    """Compute the minimum squared Euclidean distance from (i, j) to any corner.
    Corners are (0,0), (0,18), (18,0), (18,18) in 0-based indices.
    """
    corners = [(0, 0), (0, 18), (18, 0), (18, 18)]
    min_sq_dist = float('inf')
    for cx, cy in corners:
        sq_dist = (i - cx)**2 + (j - cy)**2
        if sq_dist < min_sq_dist:
            min_sq_dist = sq_dist
    return min_sq_dist

def policy(me, opponent, memory):
    """Determine the next move for the player.
    Args:
        me: List of (row, col) tuples for player's stones (1-based).
        opponent: List of (row, col) tuples for opponent's stones (1-based).
        memory: Dictionary for persistent data (unused in this policy).
    Returns:
        A tuple ((row, col), memory) where (row, col) is the move or (0,0) for pass.
    """
    # Initialize board from input
    board = [[0] * 19 for _ in range(19)]
    for r, c in me:
        board[r-1][c-1] = 1
    for r, c in opponent:
        board[r-1][c-1] = 2

    # Find all empty points
    empty_points = []
    for i in range(19):
        for j in range(19):
            if board[i][j] == 0:
                empty_points.append((i, j))

    if not empty_points:
        return ((0, 0), memory)

    best_score = -float('inf')
    best_move = None

    for i, j in empty_points:
        # Simulate placing a stone at (i, j)
        new_board = [row[:] for row in board]  # Deep copy
        new_board[i][j] = 1

        # Find opponent groups that are captured (no liberties)
        captured_stones = []
        opp_groups = find_groups(new_board, 2)  # Opponent groups before capture
        for group in opp_groups:
            if get_liberties(new_board, group) == 0:
                # Capture the group
                for (x, y) in group:
                    captured_stones.append((x, y))
                    new_board[x][y] = 0  # Remove captured stones

        # Check if the new player's group has liberties after capture
        my_new_group = find_group_containing(new_board, 1, i, j)
        if my_new_group is None or get_liberties(new_board, my_new_group) == 0:
            # Move is illegal due to suicide
            continue

        # Evaluate the board after the move
        my_groups = find_groups(new_board, 1)
        opp_groups_new = find_groups(new_board, 2)

        total_lib_my = sum(get_liberties(new_board, group) for group in my_groups)
        total_lib_opp = sum(get_liberties(new_board, group) for group in opp_groups_new)
        captures = len(captured_stones)

        # Calculate score with capture bonus
        score = total_lib_my - total_lib_opp + 10 * captures

        # Add location value based on distance to nearest corner
        min_sq_dist = compute_min_sq_dist(i, j)
        location_score = 10.0 / (1.0 + min_sq_dist)
        total_score = score + location_score

        if total_score > best_score:
            best_score = total_score
            best_move = (i, j)

    if best_move is None:
        return ((0, 0), memory)
    else:
        row, col = best_move
        return ((row + 1, col + 1), memory)  # Convert to 1-based
