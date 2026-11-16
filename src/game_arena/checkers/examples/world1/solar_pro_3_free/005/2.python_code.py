
import copy
from typing import List, Tuple

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def opponent(color: str) -> str:
    """Return the opposite player colour."""
    return 'w' if color == 'b' else 'b'

def is_dark(r: int, c: int) -> bool:
    """True if a square is a dark square in an 8‑board."""
    return (r % 2 == 0) and (c % 2 == 0)

def build_board(my_men: List[Tuple[int, int]],
                my_kings: List[Tuple[int, int]],
                opp_men: List[Tuple[int, int]],
                opp_kings: List[Tuple[int, int]]) -> List[List[int]]:
    """Create the 8×8 board matrix from the piece lists."""
    board = [[0 for _ in range(8)] for _ in range(8)]
    for r, c in my_men:
        board[r][c] = 1          # my men
    for r, c in my_kings:
        board[r][c] = 2          # my kings
    for r, c in opp_men:
        board[r][c] = -1         # opponent men
    for r, c in opp_kings:
        board[r][c] = -2         # opponent kings
    return board

def all_dark_squares() -> List[Tuple[int, int]]:
    """List of all dark‑square coordinates."""
    return [(r, c) for r in range(8) for c in range(8) if is_dark(r, c)]

def count_simple_slides(board: List[List[int]], color: str) -> int:
    """Count legal slide moves for a given colour."""
    slides = []
    forward = 1 if color == 'w' else -1
    directions = [(forward, -1), (forward, 1)]
    if color == 'w':
        piece_vals = [(r, c) for r, c in all_dark_squares()
                     if board[r][c] in (1, 2)]
    else:
        piece_vals = [(r, c) for r, c in all_dark_squares()
                     if board[r][c] in (1, 2)]  # my men/kings are positive
    for (r, c) in piece_vals:
        piece_type = board[r][c]  # 1 or 2
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if not is_dark(nr, nc) or board[nr][nc] != 0:
                continue
            slides.append(((r, c), (nr, nc)))
    return slides

# ----------------------------------------------------------------------
# Capture recursion (generates all multi‑jump paths)
# ----------------------------------------------------------------------
def capture_recursive(board: List[List[int]], color: str,
                     start_r: int, start_c: int, piece_type: int) -> List[List[Tuple[int, int]]]:
    """
    Starting from a location that already contains a piece of `piece_type`,
    generate every possible capture path (including zero‑capture continuations).
    Returns a list of full paths; each path starts with the start square.
    """
    forward = 1 if color == 'w' else -1
    dirs = [(forward, -1), (forward, 1)]
    if piece_type == 2:                     # king can go backward as well
        dirs += [(-forward, -1), (-forward, 1)]

    paths: List[List[Tuple[int, int]]] = []

    for dr, dc in dirs:
        # Ensure intermediate and landing squares stay on dark squares
        if not is_dark(start_r + dr, start_c + dc) or not is_dark(start_r + 2 * dr, start_c + 2 * dc):
            continue
        mid_r, mid_c = start_r + dr, start_c + dc
        far_r, far_c = start_r + 2 * dr, start_c + 2 * dc
        if not (0 <= mid_r < 8 and 0 <= mid_c < 8 and
                0 <= far_r < 8 and 0 <= far_c < 8):
            continue

        # Opponent piece must be at the mid square
        if board[mid_r][mid_c] == 0:
            continue
        # Landing square must be empty
        if board[far_r][far_c] != 0:
            continue

        # Immediate capture possible
        new_piece_type = piece_type
        if (color == 'b' and far_r == 0) or (color == 'w' and far_r == 7):
            new_piece_type = 2   # promotion to king

        # Temporarily move the piece to far and recurse
        tmp = copy.deepcopy(board)
        tmp[start_r][start_c] = 0                     # source becomes empty
        tmp[mid_r][mid_c] = 0                         # captured piece removed
        tmp[far_r][far_c] = new_piece_type            # piece lands

        deeper = capture_recursive(tmp, color,
                                  far_r, far_c, new_piece_type)

        if deeper:
            for d_path in deeper:
                # deeper already starts with the square we just landed on
                full_path = [(start_r, start_c)] + d_path
                paths.append(full_path)
        else:
            # No further captures after this jump
            paths.append([(start_r, start_c), (far_r, far_c)])

    return paths

def generate_moves(board: List[List[int]], color: str) -> List[dict]:
    """Return a list of all legal slide and capture moves for `color`."""
    moves: List[dict] = []

    # Scan every dark square that holds an own piece (value > 0)
    own_pieces = [(r, c) for r, c in all_dark_squares()
                 if board[r][c] in (1, 2)]

    for (r, c) in own_pieces:
        piece_type = board[r][c]                # 1 or 2

        forward = 1 if color == 'w' else -1
        dirs = [(forward, -1), (forward, 1)]
        if piece_type == 2:
            dirs += [(-forward, -1), (-forward, 1)]

        for dr, dc in dirs:
            # ---- Slide (simple) ----
            nr, nc = r + dr, c + dc
            if not is_dark(nr, nc) or board[nr][nc] != 0:
                continue
            # Simple slide move
            moves.append({
                'type': 'slide',
                'from': (r, c),
                'to': (nr, nc),
                'path': []                     # no jumps
            })

            # ---- Capture (jump) ----
            mid_r, mid_c = nr, nc
            far_r, far_c = r + 2 * dr, c + 2 * dc
            # The capture may be a multi‑jump sequence starting from far
            if (0 <= mid_r < 8 and 0 <= mid_c < 8 and
                0 <= far_r < 8 and 0 <= far_c < 8):
                if board[mid_r][mid_c] == 0 or board[far_r][far_c] != 0:
                    continue

                new_piece_type = piece_type
                if (color == 'b' and far_r == 0) or (color == 'w' and far_r == 7):
                    new_piece_type = 2

                tmp = copy.deepcopy(board)
                tmp[r][c] = 0
                tmp[mid_r][mid_c] = 0
                tmp[far_r][far_c] = new_piece_type

                deeper = capture_recursive(tmp, color,
                                          far_r, far_c, new_piece_type)

                # Every deeper path already starts with (far_r, far_c)
                for d_path in deeper:
                    # d_path includes the landing square as first element
                    full_path = [(r, c)] + d_path
                    moves.append({
                        'type': 'capture',
                        'from': (r, c),
                        'to': full_path[-1],
                        'path': full_path,
                        'jumps': full_path   # for easy copy‑back during evaluation
                    })
                else:
                    # No further jumps possible after this single jump
                    moves.append({
                        'type': 'capture',
                        'from': (r, c),
                        'to': (far_r, far_c),
                        'path': [(r, c), (far_r, far_c)],
                        'jumps': [(mid_r, mid_c), (far_r, far_c)]
                    })
    return moves

# ----------------------------------------------------------------------
# Move application helpers
# ----------------------------------------------------------------------
def apply_move(board: List[List[int]], move: dict) -> List[List[int]]:
    """Copy the board and apply `move`, returning the new board."""
    if move['type'] == 'capture':
        # walk through jumps, removing opponent pieces and updating promotion
        b = copy.deepcopy(board)
        src = move['from']
        src_val = board[src[0]][src[1]]
        b[src] = 0                     # source becomes empty

        cur_piece_type = src_val
        for i in range(len(move['jumps'])):
            src_jump = move['jumps'][i]
            dest_jump = move['jumps'][i+1]
            mid_row = (src_jump[0] + dest_jump[0]) // 2
            mid_col = (src_jump[1] + dest_jump[1]) // 2
            # Capture the opponent piece (mid square becomes empty)
            b[mid_row][mid_col] = 0

            # Place own piece on destination square
            b[dest_jump] = cur_piece_type
            # Promote if landing square is a promotion row
            if (move['color'] == 'b' and dest_jump[0] == 0) or \
               (move['color'] == 'w' and dest_jump[0] == 7):
                cur_piece_type = 2   # king
            # For next jump the promotion status may change again (already handled)
        return b
    else:  # slide
        b = copy.deepcopy(board)
        src = move['from']
        dest = move['to']
        piece_type = board[src[0]][src[1]]
        b[src] = 0
        if (move['color'] == 'b' and dest[0] == 0) or \
           (move['color'] == 'w' and dest[0] == 7):
            piece_type = 2
        b[dest] = piece_type
        return b

# ----------------------------------------------------------------------
# Evaluation function
# ----------------------------------------------------------------------
def evaluate(board: List[List[int]], color: str) -> float:
    """Static heuristic: material advantage + mobility."""
    # Own pieces
    own_men = sum(1 for r, c in all_dark_squares()
                 if board[r][c] == (1 if color == 'w' else -1))
    own_kings = sum(1 for r, c in all_dark_squares()
                   if board[r][c] == (2 if color == 'w' else -2))
    own_material = own_kings * 10 + own_men

    # Opponent pieces
    opp_men = sum(1 for r, c in all_dark_squares()
                 if board[r][c] == (-1 if color == 'w' else 1))
    opp_kings = sum(1 for r, c in all_dark_squares()
                   if board[r][c] == (-2 if color == 'w' else 2))
    opp_material = opp_kings * 10 + opp_men

    # Mobility (slide moves only)
    own_moves = count_simple_slides(board, color)
    opp_moves = count_simple_slides(board, opponent(color))
    mobility = len(own_moves) - len(opp_moves)

    # Combine with simple weighting
    return own_material - opp_material + 10 * mobility

# ----------------------------------------------------------------------
# Minimax (depth‑limited)
# ----------------------------------------------------------------------
def minimax(board: List[List[int]], depth: int, maximizing: bool, color: str) -> float:
    """Depth‑limited minimax using the same move generation logic."""
    if depth == 0 or len(generate_moves(board, color)) == 0:
        return evaluate(board, color)

    moves = generate_moves(board, color)
    if maximizing:
        best = -float('inf')
        for m in moves:
            new_board = apply_move(board, m)
            val = minimax(new_board, depth - 1, False, opponent(color))
            best = max(best, val)
        return best
    else:
        best = float('inf')
        for m in moves:
            new_board = apply_move(board, m)
            val = minimax(new_board, depth - 1, True, opponent(color))
            best = min(best, val)
        return best

# ----------------------------------------------------------------------
# Main policy
# ----------------------------------------------------------------------
def policy(my_men: List[Tuple[int, int]],
           my_kings: List[Tuple[int, int]],
           opp_men: List[Tuple[int, int]],
           opp_kings: List[Tuple[int, int]],
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Return a legal move as ((from_row, from_col), (to_row, to_col)).
    Captures are mandatory when available.
    """
    # Build board
    board = build_board(my_men, my_kings, opp_men, opp_kings)

    # Generate all legal moves for the current player
    all_moves = generate_moves(board, color)

    # Separate captures from slides
    capture_moves = [m for m in all_moves if m['type'] == 'capture']
    slide_moves = [m for m in all_moves if m['type'] == 'slide']

    if capture_moves:
        # Evaluate every capture path (including multi‑jumps) with the heuristic
        best_move = None
        best_val = -float('inf')
        for m in capture_moves:
            # Copy board, apply the capture path, then evaluate
            new_board = apply_move(board, m)
            val = evaluate(new_board, color)
            if val > best_val:
                best_val = val
                best_move = m
        # best_move is guaranteed to exist because capture_moves non‑empty
        return ((best_move['from'][0], best_move['from'][1]),
                (best_move['to'][0], best_move['to'][1]))
    else:
        # No captures – use a shallow minimax to pick the slide that leads
        # to the best minimax value (up to depth 2).
        best_move = None
        best_val = -float('inf')
        depth = 2   # enough depth for typical checkers positions
        for m in slide_moves:
            new_board = apply_move(board, m)
            val = minimax(new_board, depth, False, opponent(color))
            if val > best_val:
                best_val = val
                best_move = m
        # best_move is guaranteed to exist because slide_moves non‑empty unless game over
        return ((best_move['from'][0], best_move['from'][1]),
                (best_move['to'][0], best_move['to'][1]))
