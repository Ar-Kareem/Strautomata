
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    Havannah policy for a 15x15 hexagonal board.
    Returns the next best move as (row, col).
    """
    board_size = 15
    # Convert valid_mask to a numpy array for easier manipulation
    valid = np.array(valid_mask, dtype=bool)
    # Create a board representation (0: empty, 1: me, 2: opponent)
    board = np.zeros((board_size, board_size), dtype=int)
    for r, c in me:
        board[r, c] = 1
    for r, c in opp:
        board[r, c] = 2

    # Phase 1: Check if current move can win (ring, bridge, or fork)
    for r, c in me:
        if valid[r, c]:
            # Simulate removing this stone (since we're checking if placing it wins)
            temp_board = board.copy()
            temp_board[r, c] = 0
            if can_win(temp_board, (r, c), 1):
                return (r, c)

    # Phase 2: Block opponent's immediate win
    for r, c in opp:
        if valid[r, c]:
            temp_board = board.copy()
            temp_board[r, c] = 0
            if can_win(temp_board, (r, c), 2):
                return (r, c)

    # Phase 3: Hexagonal edge connectivity (left-right or top-bottom)
    best_move = None
    best_score = -float('inf')

    # Evaluate all valid moves
    for r in range(board_size):
        for c in range(board_size):
            if valid[r, c] and board[r, c] == 0:
                # Simulate placing the stone
                temp_board = board.copy()
                temp_board[r, c] = 1
                # Score the move based on Hex-like edge connectivity
                score = evaluate_hex_move(temp_board, (r, c), 1, 2)
                # Also consider opponent's edge connectivity (defensive)
                opp_score = evaluate_hex_move(temp_board, (r, c), 2, 1)
                # Prefer moves that improve our position more than the opponent's
                net_score = score - opp_score
                if net_score > best_score:
                    best_score = net_score
                    best_move = (r, c)

    if best_move is not None:
        return best_move

    # Phase 4: Potential rings or bridges
    best_move = None
    best_score = -float('inf')

    for r in range(board_size):
        for c in range(board_size):
            if valid[r, c] and board[r, c] == 0:
                # Simulate placing the stone
                temp_board = board.copy()
                temp_board[r, c] = 1
                # Score based on potential rings or bridges
                ring_potential = count_potential_rings(temp_board, (r, c), 1)
                bridge_potential = count_potential_bridges(temp_board, (r, c), 1)
                score = ring_potential + bridge_potential
                if score > best_score:
                    best_score = score
                    best_move = (r, c)

    if best_move is not None:
        return best_move

    # Phase 5: Potential forks
    best_move = None
    best_score = -float('inf')

    for r in range(board_size):
        for c in range(board_size):
            if valid[r, c] and board[r, c] == 0:
                # Simulate placing the stone
                temp_board = board.copy()
                temp_board[r, c] = 1
                # Score based on potential forks
                fork_potential = count_potential_forks(temp_board, (r, c), 1)
                score = fork_potential
                if score > best_score:
                    best_score = score
                    best_move = (r, c)

    if best_move is not None:
        return best_move

    # Phase 6: Symmetry or center control
    best_move = find_symmetry_or_center_move(board, valid, me, opp)
    if best_move is not None:
        return best_move

    # Phase 7: Fallback to random valid move
    valid_moves = [(r, c) for r in range(board_size) for c in range(board_size) if valid[r, c] and board[r, c] == 0]
    return np.random.choice(valid_moves)

def get_hex_neighbors(r, c, board_size):
    """Returns the 6 hexagonal neighbors of (r, c) on a 15x15 board."""
    neighbors = []
    # Up (same column, row-1)
    if r > 0:
        neighbors.append((r-1, c))
    # Down (same column, row+1)
    if r < board_size - 1:
        neighbors.append((r+1, c))
    # Left (column-1, rows r-1 and r)
    if c > 0:
        neighbors.append((r, c-1))
        neighbors.append((r+1, c-1))
    # Right (column+1, rows r-1 and r)
    if c < board_size - 1:
        neighbors.append((r, c+1))
        neighbors.append((r+1, c+1))
    return neighbors

def is_connected(board, start, end, player):
    """Checks if start and end are connected via stones of player using BFS."""
    visited = set()
    queue = deque([start])
    visited.add(start)

    while queue:
        r, c = queue.popleft()
        if (r, c) == end:
            return True
        for nr, nc in get_hex_neighbors(r, c, board.shape[0]):
            if 0 <= nr < board.shape[0] and 0 <= nc < board.shape[1]:
                if board[nr, nc] == player and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
    return False

def can_win(board, move, player):
    """Checks if placing a stone at move completes a ring, bridge, or fork for player."""
    r, c = move
    board[r, c] = player

    # Check for ring (loop around any cell)
    if has_ring(board, r, c, player):
        return True

    # Check for bridge (connects two corners)
    if has_bridge(board, player):
        return True

    # Check for fork (connects three edges)
    if has_fork(board, player):
        return True

    return False

def has_ring(board, r, c, player):
    """Checks if placing a stone at (r, c) completes a ring for player."""
    # A ring requires at least 5 stones forming a loop around a cell
    # We'll check all possible loops of size 5 or 6
    # This is a simplified check; a full implementation would require more complex logic
    # For now, we'll check if the move connects 5 stones in a hexagonal loop
    neighbors = get_hex_neighbors(r, c, board.shape[0])
    # Check all 6 neighbors for potential loops
    for i in range(6):
        nr1, nc1 = neighbors[i]
        nr2, nc2 = neighbors[(i+1) % 6]
        if board[nr1, nc1] == player and board[nr2, nc2] == player:
            # Check if the other 4 neighbors are connected via player's stones
            # This is a placeholder; actual ring detection would require BFS/DFS
            pass
    # Placeholder: Assume no ring for now (simplified)
    return False

def has_bridge(board, player):
    """Checks if player has a bridge (connects two corners)."""
    corners = [(0,0), (0,14), (14,0), (14,14), (0,7), (14,7)]  # All 6 corners
    for i in range(len(corners)):
        for j in range(i+1, len(corners)):
            if is_connected(board, corners[i], corners[j], player):
                return True
    return False

def has_fork(board, player):
    """Checks if player has a fork (connects three edges)."""
    # Edges are non-corner cells on the perimeter
    edges = []
    # Top edge (row 0, columns 1..13)
    for c in range(1, board.shape[1]-1):
        edges.append((0, c))
    # Bottom edge (row 14, columns 1..13)
    for c in range(1, board.shape[1]-1):
        edges.append((board.shape[0]-1, c))
    # Left edge (column 0, rows 1..13)
    for r in range(1, board.shape[0]-1):
        edges.append((r, 0))
    # Right edge (column 14, rows 1..13)
    for r in range(1, board.shape[0]-1):
        edges.append((r, board.shape[1]-1))
    # Check all combinations of three edges
    for i in range(len(edges)):
        for j in range(i+1, len(edges)):
            for k in range(j+1, len(edges)):
                if is_connected(board, edges[i], edges[j], player) and is_connected(board, edges[i], edges[k], player):
                    return True
    return False

def evaluate_hex_move(board, move, me_player, opp_player):
    """Evaluates a move's Hex-like potential (left-right or top-bottom connectivity)."""
    r, c = move
    board[r, c] = me_player

    # Check left-right connectivity
    left_edge = (r, 0)
    right_edge = (r, board.shape[1]-1)
    if is_connected(board, left_edge, right_edge, me_player):
        return float('inf')  # Win

    # Check top-bottom connectivity
    top_edge = (0, c)
    bottom_edge = (board.shape[0]-1, c)
    if is_connected(board, top_edge, bottom_edge, me_player):
        return float('inf')  # Win

    # Score based on distance to edges
    score = 0
    # Distance to left edge
    score += (c + 1) * 0.1
    # Distance to right edge
    score += (board.shape[1] - c) * 0.1
    # Distance to top edge
    score += (r + 1) * 0.1
    # Distance to bottom edge
    score += (board.shape[0] - r) * 0.1

    # Check if the move improves connectivity to any edge
    for edge in [(r, 0), (r, board.shape[1]-1), (0, c), (board.shape[0]-1, c)]:
        if board[edge[0], edge[1]] == me_player:
            # Already connected to this edge
            pass
        else:
            # Check if the move connects us to this edge
            if is_connected(board, move, edge, me_player):
                score += 10  # Strong connection

    return score

def count_potential_rings(board, move, player):
    """Counts potential rings that can be formed by placing a stone at move."""
    # Simplified: Count how many 5-stone loops are close to completion
    r, c = move
    neighbors = get_hex_neighbors(r, c, board.shape[0])
    count = 0
    for i in range(6):
        nr1, nc1 = neighbors[i]
        nr2, nc2 = neighbors[(i+1) % 6]
        if board[nr1, nc1] == player and board[nr2, nc2] == player:
            # Check if the other 4 neighbors are connected via player's stones
            # This is a placeholder; actual ring detection would require BFS/DFS
            count += 1
    return count

def count_potential_bridges(board, move, player):
    """Counts potential bridges that can be formed by placing a stone at move."""
    # Simplified: Count how many corner pairs are close to being connected
    r, c = move
    corners = [(0,0), (0,14), (14,0), (14,14), (0,7), (14,7)]
    count = 0
    for i in range(len(corners)):
        for j in range(i+1, len(corners)):
            if is_connected(board, corners[i], corners[j], player):
                count += 1
            elif is_connected(board, corners[i], move, player) or is_connected(board, corners[j], move, player):
                # Check if the opponent can block this bridge
                if not can_win(board, move, 2):  # Opponent cannot win by blocking
                    count += 0.5  # Partial bridge potential
    return count

def count_potential_forks(board, move, player):
    """Counts potential forks that can be formed by placing a stone at move."""
    # Simplified: Count how many edge pairs are connected, leaving room for a third
    r, c = move
    edges = []
    # Top edge (row 0, columns 1..13)
    for c in range(1, board.shape[1]-1):
        edges.append((0, c))
    # Bottom edge (row 14, columns 1..13)
    for c in range(1, board.shape[1]-1):
        edges.append((board.shape[0]-1, c))
    # Left edge (column 0, rows 1..13)
    for r in range(1, board.shape[0]-1):
        edges.append((r, 0))
    # Right edge (column 14, rows 1..13)
    for r in range(1, board.shape[0]-1):
        edges.append((r, board.shape[1]-1))

    count = 0
    for i in range(len(edges)):
        for j in range(i+1, len(edges)):
            if is_connected(board, edges[i], edges[j], player):
                # Check if the move connects to a third edge
                for k in range(j+1, len(edges)):
                    if is_connected(board, edges[i], edges[k], player) or is_connected(board, edges[j], edges[k], player):
                        count += 1
    return count

def find_symmetry_or_center_move(board, valid, me, opp):
    """Finds a move that maintains symmetry or plays toward the center."""
    board_size = board.shape[0]
    center = (board_size // 2, board_size // 2)

    # Check if the board is symmetric and mirror the opponent's last move
    if len(me) > len(opp):
        opp_last_move = opp[-1]
    else:
        opp_last_move = me[-1] if len(me) > 0 else None

    if opp_last_move is not None:
        mirrored_r = board_size - 1 - opp_last_move[0]
        mirrored_c = board_size - 1 - opp_last_move[1]
        if valid[mirrored_r, mirrored_c] and board[mirrored_r, mirrored_c] == 0:
            return (mirrored_r, mirrored_c)

    # Play toward the center if no symmetry
    best_move = None
    best_score = -float('inf')
    for r in range(board_size):
        for c in range(board_size):
            if valid[r, c] and board[r, c] == 0:
                # Score based on distance to center (closer is better)
                score = -(abs(r - center[0]) + abs(c - center[1]))
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    return best_move
