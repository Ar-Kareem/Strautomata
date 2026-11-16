
import time

# ---------------------------------------------------------------------------
# Board geometry and precomputed data
# ---------------------------------------------------------------------------

BOARD_SIZE = 6
CELL_COUNT = 36
FULL_BOARD = (1 << CELL_COUNT) - 1

WIN_SCORE = 10_000_000
INF = 100_000_000

# Scores for an unblocked five-cell window containing this many marbles.
LINE_SCORES = (0, 2, 14, 100, 1100, 0)

DIRECTION_NAMES = ("L", "R")


def _bit(r, c):
    return 1 << (r * 6 + c)


# All length-five horizontal, vertical, and diagonal windows.
WIN_MASKS = []
for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
    for r in range(6):
        for c in range(6):
            er = r + 4 * dr
            ec = c + 4 * dc
            if 0 <= er < 6 and 0 <= ec < 6:
                mask = 0
                for k in range(5):
                    mask |= _bit(r + k * dr, c + k * dc)
                WIN_MASKS.append(mask)

WIN_MASKS = tuple(WIN_MASKS)

# Positional weights. Quadrant centers are stable under rotation and are
# particularly valuable. The four cells nearest the board center also get
# an additional bonus.
_weight_masks_dict = {}
for r in range(6):
    for c in range(6):
        weight = 1

        # Center of one of the four 3x3 quadrants.
        if r % 3 == 1 and c % 3 == 1:
            weight += 8

        # Central four cells of the whole board.
        if r in (2, 3) and c in (2, 3):
            weight += 4

        _weight_masks_dict.setdefault(weight, 0)
        _weight_masks_dict[weight] |= _bit(r, c)

WEIGHT_MASKS = tuple(_weight_masks_dict.items())

# Quadrant masks, extraction positions, and all 512 possible local rotations.
QUAD_MASKS = []
QUAD_BASES = []
ROTATED_LOCAL = []

for q in range(4):
    br = 0 if q < 2 else 3
    bc = 0 if q % 2 == 0 else 3
    base = br * 6 + bc
    QUAD_BASES.append(base)

    qmask = 0
    for rr in range(3):
        for cc in range(3):
            qmask |= _bit(br + rr, bc + cc)
    QUAD_MASKS.append(qmask)

    direction_tables = []
    for direction in range(2):
        table = [0] * 512

        for local in range(512):
            rotated = 0

            for rr in range(3):
                for cc in range(3):
                    local_index = rr * 3 + cc
                    if local & (1 << local_index):
                        if direction == 0:       # Anticlockwise
                            nr, nc = 2 - cc, rr
                        else:                    # Clockwise
                            nr, nc = cc, 2 - rr

                        rotated |= _bit(br + nr, bc + nc)

            table[local] = rotated

        direction_tables.append(tuple(table))

    ROTATED_LOCAL.append(tuple(direction_tables))

QUAD_MASKS = tuple(QUAD_MASKS)
QUAD_BASES = tuple(QUAD_BASES)
ROTATED_LOCAL = tuple(ROTATED_LOCAL)
OUTSIDE_QUAD_MASKS = tuple(FULL_BOARD ^ m for m in QUAD_MASKS)


# ---------------------------------------------------------------------------
# Time management
# ---------------------------------------------------------------------------

class _OutOfTime(Exception):
    pass


_DEADLINE = 0.0
_TIME_TICKS = 0


def _time_check():
    global _TIME_TICKS
    _TIME_TICKS += 1
    if (_TIME_TICKS & 7) == 0 and time.perf_counter() >= _DEADLINE:
        raise _OutOfTime


# ---------------------------------------------------------------------------
# Fast board operations
# ---------------------------------------------------------------------------

def _extract_local(board, q):
    """Extract a quadrant into a contiguous nine-bit integer."""
    base = QUAD_BASES[q]
    return (
        ((board >> base) & 7)
        | (((board >> (base + 6)) & 7) << 3)
        | (((board >> (base + 12)) & 7) << 6)
    )


def _rotate(board, q, direction):
    local = _extract_local(board, q)
    return (
        (board & OUTSIDE_QUAD_MASKS[q])
        | ROTATED_LOCAL[q][direction][local]
    )


def _assess(ours, theirs):
    """
    Return (terminal_status, heuristic).

    terminal_status:
         2: ours alone has won
        -2: theirs alone has won
         1: terminal draw
         0: nonterminal
    """
    ours_wins = False
    theirs_wins = False
    heuristic = 0

    for mask in WIN_MASKS:
        a = (ours & mask).bit_count()
        b = (theirs & mask).bit_count()

        if a == 5:
            ours_wins = True
        if b == 5:
            theirs_wins = True

        if b == 0:
            heuristic += LINE_SCORES[a]
        elif a == 0:
            heuristic -= LINE_SCORES[b]

    if ours_wins:
        if theirs_wins:
            return 1, 0
        return 2, WIN_SCORE

    if theirs_wins:
        return -2, -WIN_SCORE

    if (ours | theirs) == FULL_BOARD:
        return 1, 0

    # Positional control.
    for weight, mask in WEIGHT_MASKS:
        heuristic += weight * (
            (ours & mask).bit_count() - (theirs & mask).bit_count()
        )

    return 0, heuristic


def _terminal_value(status, ply):
    if status == 2:
        return WIN_SCORE - ply
    if status == -2:
        return -WIN_SCORE + ply
    return 0


# Move tuple:
# (ordering_score, status, new_ours, new_theirs, cell, quadrant, direction)

def _generate_moves(ours, theirs):
    """Generate unique resulting legal positions and their original actions."""
    _time_check()

    occupied = ours | theirs
    empty = FULL_BOARD ^ occupied
    result = []
    seen = set()

    while empty:
        placement_bit = empty & -empty
        empty ^= placement_bit
        cell = placement_bit.bit_length() - 1
        placed = ours | placement_bit

        for q in range(4):
            placed_local = _extract_local(placed, q)
            theirs_local = _extract_local(theirs, q)
            placed_outside = placed & OUTSIDE_QUAD_MASKS[q]
            theirs_outside = theirs & OUTSIDE_QUAD_MASKS[q]

            for direction in range(2):
                new_ours = (
                    placed_outside
                    | ROTATED_LOCAL[q][direction][placed_local]
                )
                new_theirs = (
                    theirs_outside
                    | ROTATED_LOCAL[q][direction][theirs_local]
                )

                key = (new_ours, new_theirs)
                if key in seen:
                    continue
                seen.add(key)

                status, heuristic = _assess(new_ours, new_theirs)

                if status == 2:
                    ordering_score = WIN_SCORE
                elif status == -2:
                    ordering_score = -WIN_SCORE
                elif status == 1:
                    ordering_score = 0
                else:
                    ordering_score = heuristic

                result.append((
                    ordering_score,
                    status,
                    new_ours,
                    new_theirs,
                    cell,
                    q,
                    direction,
                ))

    return result


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def _search(ours, theirs, depth, alpha, beta, ply, selective):
    """
    Negamax search. 'ours' is always the side to move at this node.
    """
    _time_check()

    if depth <= 0:
        return _assess(ours, theirs)[1]

    moves = _generate_moves(ours, theirs)

    if not moves:
        return 0

    # At depth one the precomputed ordering score is exactly the static
    # value of a nonterminal child from the current player's perspective.
    if depth == 1:
        best = -INF

        for move in moves:
            ordering_score, status = move[0], move[1]

            if status:
                value = _terminal_value(status, ply + 1)
            else:
                value = ordering_score

            if value > best:
                best = value
            if best >= beta:
                return best

        return best

    moves.sort(key=lambda m: m[0], reverse=True)

    # The full two-ply search is unpruned by this rule. Selective truncation
    # is used only by the optional third-ply iteration.
    if selective and len(moves) > 72:
        moves = moves[:72]

    best = -INF

    for move in moves:
        _, status, new_ours, new_theirs = move[:4]

        if status:
            value = _terminal_value(status, ply + 1)
        else:
            value = -_search(
                new_theirs,
                new_ours,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
                selective,
            )

        if value > best:
            best = value
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    return best


def _move_to_string(move):
    cell = move[4]
    q = move[5]
    direction = move[6]

    row = cell // 6 + 1
    col = cell % 6 + 1
    return "{},{},{},{}".format(
        row, col, q, DIRECTION_NAMES[direction]
    )


# ---------------------------------------------------------------------------
# Required API
# ---------------------------------------------------------------------------

def policy(you, opponent) -> str:
    global _DEADLINE, _TIME_TICKS

    # Convert the supplied arrays to compact bitboards.
    ours = 0
    theirs = 0
    fallback_cell = None

    for r in range(6):
        for c in range(6):
            index = r * 6 + c
            if int(you[r][c]):
                ours |= 1 << index
            elif int(opponent[r][c]):
                theirs |= 1 << index
            elif fallback_cell is None:
                fallback_cell = index

    # Guaranteed legal fallback. Rotating any quadrant is always legal.
    fallback_row = fallback_cell // 6 + 1
    fallback_col = fallback_cell % 6 + 1
    fallback = "{},{},0,L".format(fallback_row, fallback_col)

    # Keep a safety margin below the one-second arena limit.
    _DEADLINE = time.perf_counter() + 0.92
    _TIME_TICKS = 0

    best_string = fallback

    try:
        root_moves = _generate_moves(ours, theirs)
        if not root_moves:
            return fallback

        best_move = root_moves[0]

        # Never postpone a guaranteed sole win.
        for move in root_moves:
            if move[1] == 2:
                return _move_to_string(move)

        # One-ply static ordering gives an immediate safe answer.
        depth_one_ranked = []
        for move in root_moves:
            if move[1]:
                value = _terminal_value(move[1], 1)
            else:
                value = move[0]
            depth_one_ranked.append((value, move))

        depth_one_ranked.sort(key=lambda item: item[0], reverse=True)
        best_move = depth_one_ranked[0][1]
        best_string = _move_to_string(best_move)

        if time.perf_counter() >= _DEADLINE:
            return best_string

        # Complete two-ply minimax. Every legal opponent response is checked,
        # so immediate rotational wins and forced tactical threats are seen.
        depth_two_ranked = []

        for _, move in depth_one_ranked:
            _time_check()

            if move[1]:
                value = _terminal_value(move[1], 1)
            else:
                value = -_search(
                    move[3],
                    move[2],
                    1,
                    -INF,
                    INF,
                    1,
                    False,
                )

            depth_two_ranked.append((value, move))

        depth_two_ranked.sort(key=lambda item: item[0], reverse=True)
        best_move = depth_two_ranked[0][1]
        best_string = _move_to_string(best_move)

        if time.perf_counter() >= _DEADLINE:
            return best_string

        # Selective third ply. Restrict root analysis to candidates already
        # rated strongly by the complete two-ply search.
        root_candidates = depth_two_ranked[:18]
        third_best_value = -INF
        third_best_move = root_candidates[0][1]
        alpha = -INF

        for _, move in root_candidates:
            _time_check()

            if move[1]:
                value = _terminal_value(move[1], 1)
            else:
                value = -_search(
                    move[3],
                    move[2],
                    2,
                    -INF,
                    -alpha,
                    1,
                    True,
                )

            if value > third_best_value:
                third_best_value = value
                third_best_move = move

            if value > alpha:
                alpha = value

        best_string = _move_to_string(third_best_move)

    except _OutOfTime:
        pass
    except Exception:
        # Preserve the guaranteed legal move even if an unusual array-like
        # implementation or runtime condition causes an internal failure.
        pass

    return best_string
