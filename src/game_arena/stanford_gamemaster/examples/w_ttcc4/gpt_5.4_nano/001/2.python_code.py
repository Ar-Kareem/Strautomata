
import re

def policy(state: list[list[object]], role: str) -> str:
    # Helpers to parse state
    # State facts look like ["cell", x, y, piece]
    # Also includes ["control", "white"/"black"] and ["step", n]
    def get_control(s):
        for f in s:
            if isinstance(f, list) and len(f) >= 2 and f[0] == "control":
                return f[1]
        return None

    def pieces_by_role(s):
        # map (x,y) -> piece string like "whiteknight", "whitedisk", "blackdisk", etc.
        cells = {}
        for f in s:
            if isinstance(f, list) and len(f) == 4 and f[0] == "cell":
                x, y, p = f[1], f[2], f[3]
                try:
                    xi = int(x)
                    yi = int(y)
                except Exception:
                    continue
                cells[(xi, yi)] = p
        return cells

    def role_color(r):
        return "white" if r == "white" else "black"

    # Middle 9 squares = 3x3 center. In examples disks appear at x,y in [1..7] with center around (4,4).
    # We assume board is 7x7 and middle 3x3 is x=3..5, y=3..5.
    MID = [(x, y) for x in range(3, 6) for y in range(3, 6)]

    def lines_in_mid():
        lines = []
        # rows/cols/diagonals among MID
        for y in range(3, 6):
            lines.append([(x, y) for x in range(3, 6)])
        for x in range(3, 6):
            lines.append([(x, y) for y in range(3, 6)])
        lines.append([(3,3),(4,4),(5,5)])
        lines.append([(3,5),(4,4),(5,3)])
        return lines

    MID_LINES = lines_in_mid()

    def is_cell_occupied(cells, coord):
        return coord in cells

    def cell_owner(piece_str):
        if not isinstance(piece_str, str):
            return None
        if piece_str.startswith("white"):
            return "white"
        if piece_str.startswith("black"):
            return "black"
        return None

    # Evaluate immediate win threat for a hypothetical drop into chute column.
    # We don't know exact mapping from drop(chute) to (x,y). But from samples, drop(3), drop(4), drop(5)
    # populate cells at y=3 (e.g., drop(3) -> ["cell","3","3","whitedisk"] appears).
    # Thus we assume drop(k) places at (k,3) for white and (k,5) for black? However samples show
    # both colors can have disks at y=3 (and blackdisk at y=3 also exists). We'll instead aim to
    # choose drop positions whose resulting disk cell is in the center region at y=3 and y=4/5
    # are already filled in trajectories; legality is uncertain.
    #
    # Because we must return a legal move, and we are not given legal actions,
    # we make a conservative choice: when we see existing disks in the mid region for this role,
    # we prefer dropping in an already-mid x column that seems to correspond to mid completion.
    #
    # Additionally, we can directly choose a move known to be legal from examples:
    # - pawnmove(fromx,fromy,tox,toy)
    # - knightmove(fromx,fromy,tox,toy)
    # - checkermove(fromx,fromy,tox,toy)
    # - drop(col)
    # - noop
    # We'll attempt in order: winning/blocking via drop on available mid squares, else use a known
    # piece move if it matches an adjacent occupied/unoccupied pattern; else fallback to noop.
    color = role_color(role)
    control = get_control(state)
    # If role input doesn't match control, still act as role input.
    cells = pieces_by_role(state)

    # Identify any current disks for both sides in mid
    my_cells = set()
    opp_cells = set()
    for (x,y), p in cells.items():
        own = cell_owner(p)
        if (x,y) in MID:
            if own == color:
                my_cells.add((x,y))
            elif own and own != color:
                opp_cells.add((x,y))

    def winning_if_add(coord, who_cells):
        # if we add coord to who_cells, does it complete any mid line?
        s = set(who_cells)
        s.add(coord)
        for line in MID_LINES:
            if all(c in s for c in line):
                return True
        return False

    def best_block_for_drop_candidate(coord):
        # Return True if opponent would win by placing at coord in mid.
        return winning_if_add(coord, opp_cells)

    # Determine candidate drop columns from mid x positions that are empty at y=3..5.
    # Try mapping drop(col) to (col,3) first (matches example drop(3) -> (3,3) disk).
    # If that square is occupied, try (col,4) and (col,5) as additional heuristics.
    drop_candidates = []
    for x in range(1, 8):
        if (x, 3) in MID and not is_cell_occupied(cells, (x, 3)):
            drop_candidates.append((x, (x, 3)))
        if (x, 4) in MID and not is_cell_occupied(cells, (x, 4)):
            drop_candidates.append((x, (x, 4)))
        if (x, 5) in MID and not is_cell_occupied(cells, (x, 5)):
            drop_candidates.append((x, (x, 5)))

    # Prefer candidates that give immediate win
    for col, coord in drop_candidates:
        if winning_if_add(coord, my_cells):
            # choose drop(col)
            return f"drop({col})"

    # Otherwise block opponent's immediate win
    for col, coord in drop_candidates:
        if best_block_for_drop_candidate(coord):
            return f"drop({col})"

    # If no drop-based win/block found, attempt a deterministic move based on known patterns.
    # Try to find a pawnmove for this role:
    # In examples, white pawn at (5,1) moved to (5,2) via pawnmove(5,1,5,2).
    # black pawn at (3,7) moved to (3,6) via pawnmove(3,7,3,6).
    # We'll try to move any pawn one step forward if that destination is empty.
    pawn_piece = f"{color}pawn"
    knight_piece = f"{color}knight"
    checker_piece = f"{color}checker"

    # Determine pawn directions (assumption):
    # white moves +1 in y (towards center), black moves -1 in y.
    pawn_dir = 1 if color == "white" else -1

    my_pawns = [(x,y) for (x,y),p in cells.items() if p == pawn_piece]
    for x,y in my_pawns:
        ny = y + pawn_dir
        if (x, ny) not in cells:
            # attempt forward move within 1..7
            if 1 <= ny <= 7:
                return f"pawnmove({x},{y},{x},{ny})"

    # Try knightmove: from examples, whiteknight at (3,1) to (2,3) or (4,3)
    # We'll attempt any legal-looking knight jump to empty target within board.
    knight_moves = [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]
    my_knights = [(x,y) for (x,y),p in cells.items() if p == knight_piece]
    for x,y in my_knights:
        for dx,dy in knight_moves:
            nx, ny = x+dx, y+dy
            if 1 <= nx <= 7 and 1 <= ny <= 7 and (nx, ny) not in cells:
                return f"knightmove({x},{y},{nx},{ny})"

    # Try checkermove: examples show checkermove(4,7,3,6) for black checker.
    # We'll attempt a simple forward-diagonal one step (direction depends on color).
    checker_dir = -1 if color == "white" else 1  # heuristically
    my_checkers = [(x,y) for (x,y),p in cells.items() if p == checker_piece]
    for x,y in my_checkers:
        for dx in (-1,1):
            nx, ny = x+dx, y+checker_dir
            if 1 <= nx <= 7 and 1 <= ny <= 7 and (nx, ny) not in cells:
                return f"checkermove({x},{y},{nx},{ny})"

    # Fallback: if noop is a legal action in many late-game examples.
    return "noop"
