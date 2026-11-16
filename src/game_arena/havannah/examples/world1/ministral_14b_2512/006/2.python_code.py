
import numpy as np
from collections import deque

# Directions for hexagonal grid (row, col) offsets
HEX_DIRS = [
    (0, 1),   # Right
    (1, 0),   # Down-right
    (1, -1),  # Down-left
    (0, -1),  # Left
    (-1, 0),  # Up-left
    (-1, 1)   # Up-right
]

def is_valid_move(board, row, col):
    """Check if a move is within bounds and not blocked."""
    return 0 <= row < len(board) and 0 <= col < len(board[0]) and board[row][col] == 0

def get_hex_neighbors(row, col):
    """Get all 6 hexagonal neighbors of (row, col)."""
    neighbors = []
    for dr, dc in HEX_DIRS:
        r, c = row + dr, col + dc
        if is_valid_move(np.zeros((15, 15)), r, c):  # Dummy check for bounds
            neighbors.append((r, c))
    return neighbors

def build_board(me, opp):
    """Construct a 15x15 board representation with player stones."""
    board = np.zeros((15, 15), dtype=int)
    for r, c in me:
        board[r][c] = 1
    for r, c in opp:
        board[r][c] = -1
    return board

def is_corner(r, c):
    """Check if a position is a corner (0,0), (0,14), (14,0), (14,14)."""
    return (r == 0 and c == 0) or (r == 0 and c == 14) or (r == 14 and c == 0) or (r == 14 and c == 14)

def is_edge(r, c):
    """Check if a position is on an edge (but not a corner)."""
    return (r == 0 or r == 14 or c == 0 or c == 14) and not is_corner(r, c)

def is_bridge(board, r, c, player):
    """Check if placing a stone at (r,c) completes a bridge (connects two corners)."""
    if not is_edge(r, c):
        return False

    # BFS to find all connected stones of the player
    visited = set()
    queue = deque()
    queue.append((r, c))
    visited.add((r, c))
    connected = []

    while queue:
        x, y = queue.popleft()
        connected.append((x, y))
        for dx, dy in HEX_DIRS:
            nx, ny = x + dx, y + dy
            if (nx, ny) in visited:
                continue
            if is_valid_move(board, nx, ny) and board[nx][ny] == player:
                visited.add((nx, ny))
                queue.append((nx, ny))

    # Check if at least two corners are connected
    corners_connected = 0
    for (x, y) in connected:
        if is_corner(x, y):
            corners_connected += 1
            if corners_connected >= 2:
                return True
    return False

def is_fork(board, r, c, player):
    """Check if placing a stone at (r,c) completes a fork (connects three edges)."""
    if not is_edge(r, c):
        return False

    # BFS to find all connected stones of the player
    visited = set()
    queue = deque()
    queue.append((r, c))
    visited.add((r, c))
    connected = []

    while queue:
        x, y = queue.popleft()
        connected.append((x, y))
        for dx, dy in HEX_DIRS:
            nx, ny = x + dx, y + dy
            if (nx, ny) in visited:
                continue
            if is_valid_move(board, nx, ny) and board[nx][ny] == player:
                visited.add((nx, ny))
                queue.append((nx, ny))

    # Check if at least three edges are connected (excluding corners)
    edges_connected = set()
    for (x, y) in connected:
        if is_edge(x, y):
            edges_connected.add((x, y))

    return len(edges_connected) >= 3

def is_ring(board, r, c, player):
    """Check if placing a stone at (r,c) completes a ring (loop around one or more cells)."""
    # BFS to find all connected stones of the player
    visited = set()
    queue = deque()
    queue.append((r, c))
    visited.add((r, c))
    connected = []

    while queue:
        x, y = queue.popleft()
        connected.append((x, y))
        for dx, dy in HEX_DIRS:
            nx, ny = x + dx, y + dy
            if (nx, ny) in visited:
                continue
            if is_valid_move(board, nx, ny) and board[nx][ny] == player:
                visited.add((nx, ny))
                queue.append((nx, ny))

    # Check if the connected stones form a loop (ring)
    # This is a simplified check; a full implementation would require graph cycle detection
    # For now, we assume a ring is formed if the connected group is large enough and has a closed shape
    # (This is a placeholder; a more robust method would be needed for a real implementation)
    return False  # Will be improved in future versions

def find_winning_move(board, me, opp, player):
    """Find if any move completes a winning structure (ring, bridge, or fork)."""
    for r in range(15):
        for c in range(15):
            if not valid_mask[r][c]:
                continue
            if board[r][c] != 0:
                continue  # Cell is already occupied

            # Simulate placing the stone
            board[r][c] = player

            # Check for winning conditions
            if is_bridge(board, r, c, player) or is_fork(board, r, c, player) or is_ring(board, r, c, player):
                board[r][c] = 0  # Undo the move
                return (r, c)

            board[r][c] = 0  # Undo the move
    return None

def find_blocking_move(board, me, opp, player):
    """Find if any move blocks the opponent from winning on their next turn."""
    opponent = -player
    for r in range(15):
        for c in range(15):
            if not valid_mask[r][c]:
                continue
            if board[r][c] != 0:
                continue  # Cell is already occupied

            # Simulate placing the stone
            board[r][c] = player

            # Check if opponent cannot win in one move
            can_opponent_win = False
            for or_ in range(15):
                for oc in range(15):
                    if not valid_mask[or_][oc]:
                        continue
                    if board[or_][oc] != 0:
                        continue  # Cell is already occupied

                    # Simulate opponent's move
                    board[or_][oc] = opponent
                    if is_bridge(board, or_, oc, opponent) or is_fork(board, or_, oc, opponent) or is_ring(board, or_, oc, opponent):
                        can_opponent_win = True
                        break
                    board[or_][oc] = 0  # Undo opponent's move
                if can_opponent_win:
                    break

            if not can_opponent_win:
                board[r][c] = 0  # Undo the move
                return (r, c)

            board[r][c] = 0  # Undo the move
    return None

def find_largest_group(board, player):
    """Find the largest connected group of stones for the player."""
    visited = set()
    max_group = []

    for r in range(15):
        for c in range(15):
            if board[r][c] != player:
                continue
            if (r, c) in visited:
                continue

            # BFS to find connected stones
            queue = deque()
            queue.append((r, c))
            visited.add((r, c))
            current_group = []

            while queue:
                x, y = queue.popleft()
                current_group.append((x, y))
                for dx, dy in HEX_DIRS:
                    nx, ny = x + dx, y + dy
                    if (nx, ny) in visited:
                        continue
                    if is_valid_move(board, nx, ny) and board[nx][ny] == player:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

            if len(current_group) > len(max_group):
                max_group = current_group

    return max_group

def expand_group(board, me, opp, player):
    """Find the best move to expand the player's largest group."""
    largest_group = find_largest_group(board, player)
    if not largest_group:
        return None

    # Collect all possible moves adjacent to the largest group
    possible_moves = []
    for r, c in largest_group:
        for dr, dc in HEX_DIRS:
            nr, nc = r + dr, c + dc
            if valid_mask[nr][nc] and board[nr][nc] == 0:
                possible_moves.append((nr, nc))

    # If no moves, return None
    if not possible_moves:
        return None

    # Choose the move with the highest "potential" (simplified: random for now)
    return np.random.choice(possible_moves)

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """Generate the next move for Havannah."""
    global board
    board = build_board(me, opp)

    # Step 1: Check if we can win immediately
    winning_move = find_winning_move(board, me, opp, 1)
    if winning_move:
        return winning_move

    # Step 2: Block opponent's winning moves
    blocking_move = find_blocking_move(board, me, opp, 1)
    if blocking_move:
        return blocking_move

    # Step 3: Expand the largest connected group
    expansion_move = expand_group(board, me, opp, 1)
    if expansion_move:
        return expansion_move

    # Step 4: Fallback to a random valid move
    valid_moves = [(r, c) for r in range(15) for c in range(15) if valid_mask[r][c] and board[r][c] == 0]
    return np.random.choice(valid_moves)
