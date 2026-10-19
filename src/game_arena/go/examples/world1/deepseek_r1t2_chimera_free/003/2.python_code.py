
import collections

def find_group(board, r, c, player):
    """Find all connected stones of the same player and their liberties."""
    visited = set()
    queue = collections.deque()
    group = []
    liberties = set()
    if board[r][c] != player:
        return group, liberties
    queue.append((r, c))
    visited.add((r, c))
    while queue:
        x, y = queue.popleft()
        group.append((x, y))
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 1 <= nx <= 19 and 1 <= ny <= 19:
                if board[nx][ny] == 0:
                    liberties.add((nx, ny))
                elif board[nx][ny] == player and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
    return group, liberties

def positional_score(r, c):
    """Calculate positional score favoring corners, edges, and key opening points."""
    key_points = {
        (4,4): 100, (4,16): 100, (16,4): 100, (16,16): 100,
        (3,3): 90, (3,17): 90, (17,3): 90, (17,17): 90,
        (10,10): 80
    }
    if (r, c) in key_points:
        return key_points[(r, c)]
    edge_dist = min(r-1, 19-r, c-1, 19-c)
    return 50 - edge_dist * 10

def policy(me, opponent):
    # Initialize 19x19 board (1-based index)
    board = [[0]*20 for _ in range(20)]  # Indices 1-19 used
    for r, c in me:
        board[r][c] = 1
    for r, c in opponent:
        board[r][c] = 2

    # First move in corner if board is empty
    if not me and not opponent:
        return (4, 4)

    legal_moves = []
    capture_scores = {}
    save_scores = {}

    # Collect all empty points adjacent to existing stones
    all_stones = set(me + opponent)
    candidates = set()
    for r in range(1, 20):
        for c in range(1, 20):
            if board[r][c] == 0:
                any_adjacent = False
                for dr, dc in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 19 and 1 <= nc <= 19 and board[nr][nc] in (1, 2):
                        any_adjacent = True
                        break
                if any_adjacent:
                    candidates.add((r, c))
    candidates = list(candidates) if candidates else [(r, c) for r in range(1, 20) for c in range(1, 20) if board[r][c] == 0]

    for r, c in candidates:
        # Simulate placing stone
        board[r][c] = 1
        captured = 0
        opponent_neighbors = set()

        # Check adjacent opponent groups
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19 and board[nr][nc] == 2:
                opponent_neighbors.add((nr, nc))

        visited_opponent = set()
        for nr, nc in opponent_neighbors:
            if (nr, nc) not in visited_opponent:
                group, liberties = find_group(board, nr, nc, 2)
                if not liberties:
                    captured += len(group)
                visited_opponent.update(group)

        # Check if move is legal (captures or has liberties)
        if captured > 0:
            legal_moves.append((r, c))
            capture_scores[(r, c)] = captured
        else:
            own_group, liberties = find_group(board, r, c, 1)
            if liberties:
                legal_moves.append((r, c))

        board[r][c] = 0  # Revert

    # Select move with highest capture score
    if capture_scores:
        max_captured = max(capture_scores.values())
        best_captures = [move for move in legal_moves if capture_scores.get(move, 0) == max_captured]
        # Choose best positional capture move
        best_move = max(best_captures, key=lambda move: positional_score(move[0], move[1]))
        return best_move

    # If no captures, choose best positional move
    if legal_moves:
        best_move = max(legal_moves, key=lambda move: positional_score(move[0], move[1]))
        return best_move

    # Pass if no legal moves
    return (0, 0)
