
import random

# ----------------------------------------------------------------------
# Board utilities
# ----------------------------------------------------------------------
NEIGHBOUR_OFFSETS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def in_bounds(r: int, c: int) -> bool:
    return 1 <= r <= 19 and 1 <= c <= 19

def get_neighbors(r: int, c: int):
    """Return list of orthogonal neighbour coordinates inside the board."""
    nr = []
    for dr, dc in NEIGHBOUR_OFFSETS:
        r2, c2 = r + dr, c + dc
        if in_bounds(r2, c2):
            nr.append((r2, c2))
    return nr

def get_group_and_liberties(board, r: int, c: int):
    """Flood‑fill the group of the same colour at (r,c) and return
    (set of group positions, set of liberty positions)."""
    colour = board[r][c]
    if colour == 0:
        return set(), set()

    stack = [(r, c)]
    visited = set()
    group = set()
    liberties = set()

    while stack:
        cr, cc = stack.pop()
        if (cr, cc) in visited:
            continue
        visited.add((cr, cc))
        group.add((cr, cc))

        for nr, nc in get_neighbors(cr, cc):
            cell = board[nr][nc]
            if cell == 0:
                liberties.add((nr, nc))
            elif cell == colour and (nr, nc) not in visited:
                stack.append((nr, nc))

    return group, liberties

def simulate(board, r: int, c: int, colour: int):
    """Place a stone of the given colour on (r,c) and return
    (new_board, captured_stones).  If the move is illegal (suicide) the
    function returns (None, 0)."""
    new_board = [row[:] for row in board]          # shallow copy
    new_board[r][c] = colour
    opp = -colour
    captured = 0

    # Check each adjacent opponent group – capture if it has no liberties
    for nr, nc in get_neighbors(r, c):
        if new_board[nr][nc] == opp:
            group, libs = get_group_and_liberties(new_board, nr, nc)
            if len(libs) == 0:
                # remove the whole group
                for gr, gc in group:
                    new_board[gr][gc] = 0
                captured += len(group)

    # After possible captures, verify that our own group has liberties
    _, own_libs = get_group_and_liberties(new_board, r, c)
    if len(own_libs) == 0:
        return None, 0                     # illegal (suicide) move
    return new_board, captured

def is_legal(board, r: int, c: int, colour: int) -> bool:
    """True if the move is legal (does not violate the no‑suicide rule)."""
    new_board, _ = simulate(board, r, c, colour)
    return new_board is not None

# ----------------------------------------------------------------------
# Main policy
# ----------------------------------------------------------------------
def policy(me, opponent, memory):
    """Return a single move (row, col) and an updated memory dict."""
    # ------------------------------------------------------------------
    # Build board representation (1 = us, -1 = opponent)
    # ------------------------------------------------------------------
    board = [[0] * 20 for _ in range(20)]
    for r, c in me:
        board[r][c] = 1
    for r, c in opponent:
        board[r][c] = -1

    total_moves = len(me) + len(opponent)

    # ------------------------------------------------------------------
    # Collect empty intersections
    # ------------------------------------------------------------------
    empties = [(r, c) for r in range(1, 20) for c in range(1, 20) if board[r][c] == 0]

    if not empties:                     # board full → pass
        return (0, 0), {}

    # ------------------------------------------------------------------
    # 1) Try to capture opponent stones
    # ------------------------------------------------------------------
    best_capture = -1
    best_capture_moves = []

    for r, c in empties:
        new_board, captured = simulate(board, r, c, 1)
        if new_board is None:
            continue
        if captured > best_capture:
            best_capture = captured
            best_capture_moves = [(r, c)]
        elif captured == best_capture and captured > 0:
            best_capture_moves.append((r, c))

    if best_capture > 0:
        # Choose the capture move that connects to most of our own stones
        best_score = -1
        best_move = None
        for r, c in best_capture_moves:
            new_board, _ = simulate(board, r, c, 1)
            if new_board is None:
                continue
            adj_own = sum(1 for nr, nc in get_neighbors(r, c) if new_board[nr][nc] == 1)
            if adj_own > best_score:
                best_score = adj_own
                best_move = (r, c)
        if best_move is None:          # fallback (should not happen)
            best_move = random.choice(best_capture_moves)
        return best_move, {}

    # ------------------------------------------------------------------
    # 2) Opening play – occupy a star point if the game is still early
    # ------------------------------------------------------------------
    if total_moves <= 2:
        star_points = [(10, 10), (4, 4), (4, 10), (10, 4),
                       (16, 16), (16, 4), (4, 16), (16, 10)]
        for r, c in star_points:
            if board[r][c] == 0 and is_legal(board, r, c, 1):
                return (r, c), {}

    # ------------------------------------------------------------------
    # 3) Heuristic evaluation of all legal moves
    # ------------------------------------------------------------------
    best_score = -10**9
    best_move = None

    for r, c in empties:
        if not is_legal(board, r, c, 1):
            continue

        # Adjacency counts on the original board
        adj_own = adj_opp = 0
        for nr, nc in get_neighbors(r, c):
            if board[nr][nc] == 1:
                adj_own += 1
            elif board[nr][nc] == -1:
                adj_opp += 1

        # Liberties after the move
        new_board, _ = simulate(board, r, c, 1)
        if new_board is None:
            continue
        _, own_libs = get_group_and_liberties(new_board, r, c)
        own_liberties = len(own_libs)

        # Distance to the nearest edge (0 on the edge)
        edge_dist = min(r - 1, 19 - r, c - 1, 19 - c)

        # Distance to the centre (10,10)
        centre_dist = abs(r - 10) + abs(c - 10)

        # Weighted score
        score = (10 * adj_own +
                 5 * adj_opp +
                 3 * own_liberties +
                 2 * edge_dist -
                 0.5 * centre_dist +
                 random.random())

        if score > best_score:
            best_score = score
            best_move = (r, c)

    # ------------------------------------------------------------------
    # Fallback (should never be needed)
    # ------------------------------------------------------------------
    if best_move is None:
        best_move = empties[0]

    return best_move, {}
