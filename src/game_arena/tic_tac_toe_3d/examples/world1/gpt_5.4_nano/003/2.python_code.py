
import math
from functools import lru_cache

# 3D Tic Tac Toe: coordinates (x,y,z) in {0,1,2}
SIZE = 3
PLAYER = 1
OPP = -1

# Generate all 49 winning lines in 3x3x3:
# Lines are any straight line of length 3 along one of the 13 directions through the grid.
def _generate_lines():
    dirs = []
    # All direction vectors (dx,dy,dz) with components in {-1,0,1} not all zero and normalized to primitive step.
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                # A "primitive" direction for length 3 in a unit grid must have gcd(|dx|,|dy|,|dz|)=1 already.
                dirs.append((dx, dy, dz))

    # To avoid duplicates, only take a canonical half-set: require first non-zero component > 0
    canonical_dirs = []
    for dx, dy, dz in dirs:
        if dx != 0:
            if dx > 0:
                canonical_dirs.append((dx, dy, dz))
        elif dy != 0:
            if dy > 0:
                canonical_dirs.append((dx, dy, dz))
        else:
            if dz > 0:
                canonical_dirs.append((dx, dy, dz))

    lines = []
    seen = set()
    for dx, dy, dz in canonical_dirs:
        for x in range(SIZE):
            for y in range(SIZE):
                for z in range(SIZE):
                    # Starting point must allow length-3 segment
                    x2, y2, z2 = x + 2*dx, y + 2*dy, z + 2*dz
                    if 0 <= x2 < SIZE and 0 <= y2 < SIZE and 0 <= z2 < SIZE:
                        coords = ((x, y, z), (x+dx, y+dy, z+dz), (x2, y2, z2))
                        # Canonical key (sorted coords) to remove accidental duplicates
                        key = tuple(sorted(coords))
                        if key not in seen:
                            seen.add(key)
                            lines.append(list(coords))
    return lines

LINES = _generate_lines()  # should be 49 lines

# Map 3D to linear index for hashing
def _idx(x, y, z):
    return x * 9 + y * 3 + z

def _board_to_tuple(board):
    # Return a hashable representation: tuple of 27 values
    flat = []
    for x in range(SIZE):
        for y in range(SIZE):
            for z in range(SIZE):
                flat.append(board[x][y][z])
    return tuple(flat)

def _check_winner_state(flat):
    # Returns 1 if PLAYER won, -1 if OPP won, 0 otherwise, and also whether board full.
    # We can check lines only.
    for line in LINES:
        vals = (flat[_idx(*line[0])], flat[_idx(*line[1])], flat[_idx(*line[2])])
        if vals[0] != 0 and vals[0] == vals[1] == vals[2]:
            return vals[0]
    return 0

def _terminal_value(flat, depth):
    w = _check_winner_state(flat)
    if w == PLAYER:
        return 1000 + depth  # sooner win => larger
    if w == OPP:
        return -1000 - depth # sooner loss => smaller
    # Draw if full
    if all(v != 0 for v in flat):
        return 0
    return None

def _possible_moves(flat):
    return [i for i, v in enumerate(flat) if v == 0]

# Heuristic scoring for move ordering:
# Prefer moves that (a) immediately win, (b) block opponent immediate win,
# (c) extend own lines / block opponent lines with two in line.
def _move_order(flat, player):
    opp = -player
    empties = _possible_moves(flat)

    # Precompute line membership by index for speed
    # For each index, list of line IDs that include it.
    if not hasattr(_move_order, "_line_ids"):
        line_ids = [[] for _ in range(27)]
        for lid, line in enumerate(LINES):
            for (x, y, z) in line:
                line_ids[_idx(x, y, z)].append(lid)
        _move_order._line_ids = line_ids
    line_ids = _move_order._line_ids

    # Helper to count in a line
    def line_triplet(lid):
        a, b, c = LINES[lid]
        return (flat[_idx(*a)], flat[_idx(*b)], flat[_idx(*c)])

    def score_move(mi):
        # place player at mi
        x, y, z = mi // 9, (mi % 9) // 3, mi % 3
        # quick immediate win check
        flat_tmp = list(flat)
        flat_tmp[mi] = player
        flat_tmp = tuple(flat_tmp)

        w = _check_winner_state(flat_tmp)
        if w == player:
            return 10_000

        # immediate block: if opponent would win next, prioritize
        flat_tmp2 = list(flat)
        flat_tmp2[mi] = player
        # simulate opponent immediate win
        # check if there exists a move for opponent that wins; equivalent to whether any winning line becomes all opp
        # We'll directly check all lines that include the placed cell: if any line becomes complete opp due to this move - but that’s complex.
        # Instead we use direct heuristic below on lines counts; also do one-ply exact for block.
        # One-ply: for each opponent empty, see if it wins.
        # Keep it cheap by only trying empties in neighborhood? We'll just do exact scan if few empties.
        # But for move ordering, we can just estimate by line threats.
        # Estimate via line counts for both player and opponent on lines through mi.
        s = 0
        for lid in line_ids[mi]:
            vals = line_triplet(lid)
            # convert to counts with virtual placement
            # update vals by replacing mi in that line to player; easiest: recompute explicitly
            line = LINES[lid]
            coords = [line[0], line[1], line[2]]
            v = []
            for (cx, cy, cz) in coords:
                idx = _idx(cx, cy, cz)
                v.append(player if idx == mi else flat[idx])
            a, b, c = v
            # line patterns
            own = sum(1 for t in v if t == player)
            oppc = sum(1 for t in v if t == opp)
            if own and not oppc:
                # open line
                if own == 2:
                    s += 500
                elif own == 1:
                    s += 50
                else:
                    s += 5
            if oppc and not own:
                # block threat
                if oppc == 2:
                    s += 700
                elif oppc == 1:
                    s += 60
                else:
                    s += 6
        return s

    ordered = sorted(empties, key=score_move, reverse=True)
    return ordered

# Minimax with alpha-beta pruning and memoization.
# Depth-first search can still be heavy late-game; we apply:
# - exact terminal detection
# - memoization by (flat, turn)
# - alpha-beta
# - move ordering
# Additionally, when many empty cells remain, we limit depth to keep runtime safe,
# but we still ensure legality; strong heuristics compensate.
MAX_EXACT_DEPTH = 10  # exact minimax until this depth from current state; beyond use heuristic cutoff

def _heuristic_eval(flat):
    # Static evaluation: sum over lines using counts for both players
    w = _check_winner_state(flat)
    if w == PLAYER:
        return 1000
    if w == OPP:
        return -1000
    total = 0
    for line in LINES:
        vals = []
        for (x, y, z) in line:
            vals.append(flat[_idx(x, y, z)])
        own = vals.count(PLAYER)
        opp = vals.count(OPP)
        if own and opp:
            continue
        if own:
            if own == 3:
                total += 1000
            elif own == 2:
                total += 50
            else:
                total += 5
        elif opp:
            if opp == 3:
                total -= 1000
            elif opp == 2:
                total -= 60
            else:
                total -= 6
    # slight preference for center-like cells (in 3D: (1,1,1) highest)
    center = flat[_idx(1,1,1)]
    if center == PLAYER:
        total += 8
    elif center == OPP:
        total -= 8
    return total

@lru_cache(maxsize=200000)
def _minimax(flat, turn, depth, alpha, beta):
    # turn: 1 means PLAYER to move, -1 means OPP to move in minimax from current perspective
    terminal = _terminal_value(flat, depth)
    if terminal is not None:
        return terminal

    # Heuristic cutoff for runtime
    empties = sum(1 for v in flat if v == 0)
    if depth >= MAX_EXACT_DEPTH:
        # evaluation from PLAYER perspective; if it's OPP's turn, minimax will handle sign through recursion,
        # so we always return heuristic from PLAYER perspective.
        return _heuristic_eval(flat)

    # order moves
    ordered = _move_order(flat, turn)

    if turn == PLAYER:
        best = -math.inf
        for mi in ordered:
            lst = list(flat)
            lst[mi] = PLAYER
            nxt = tuple(lst)
            val = _minimax(nxt, -turn, depth + 1, alpha, beta)
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = math.inf
        for mi in ordered:
            lst = list(flat)
            lst[mi] = OPP
            nxt = tuple(lst)
            val = _minimax(nxt, -turn, depth + 1, alpha, beta)
            best = min(best, val)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    flat = _board_to_tuple(board)

    # Determine whose turn it is by counting pieces.
    c1 = flat.count(PLAYER)
    c_opp = flat.count(OPP)
    turn = PLAYER if c1 == c_opp else OPP

    # Ensure we are always returning PLAYER's move (as required by arena).
    # If somehow it's opponent's turn, we still compute our move as if it's PLAYER to move
    # by flipping turn in minimax; but typically the arena calls policy on our turn.
    if turn != PLAYER:
        # Try to act as if we are to move anyway by switching perspective.
        # (This shouldn't happen in correct integration.)
        turn = PLAYER

    # If immediate winning move exists, take it.
    for mi in _possible_moves(flat):
        lst = list(flat)
        lst[mi] = PLAYER
        nxt = tuple(lst)
        if _check_winner_state(nxt) == PLAYER:
            x, y, z = mi // 9, (mi % 9) // 3, mi % 3
            return (x, y, z)

    # If immediate block exists (opponent can win next), block it.
    for mi in _possible_moves(flat):
        # after we play mi, does opponent have a winning move?
        lst = list(flat)
        lst[mi] = PLAYER
        nxt = tuple(lst)
        # check if opponent can win immediately
        for om in _possible_moves(nxt):
            lst2 = list(nxt)
            lst2[om] = OPP
            if _check_winner_state(tuple(lst2)) == OPP:
                # This mi blocks that immediate win.
                x, y, z = mi // 9, (mi % 9) // 3, mi % 3
                return (x, y, z)

    # Otherwise choose best minimax move.
    ordered = _move_order(flat, PLAYER)
    best_val = -math.inf
    best_move = None

    # Keep alpha-beta consistent: call minimax for each candidate at depth 1.
    for mi in ordered:
        lst = list(flat)
        lst[mi] = PLAYER
        nxt = tuple(lst)
        val = _minimax(nxt, OPP, 1, -math.inf, math.inf)
        if val > best_val or best_move is None:
            best_val = val
            best_move = mi

    # Fallback (should not happen): first empty
    if best_move is None:
        best_move = _possible_moves(flat)[0]

    x, y, z = best_move // 9, (best_move % 9) // 3, best_move % 3
    return (x, y, z)
