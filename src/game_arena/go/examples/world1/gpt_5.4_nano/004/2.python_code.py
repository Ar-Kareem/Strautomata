
import random
from collections import deque

N = 19

def _inb(r, c):
    return 1 <= r <= N and 1 <= c <= N

def _neighbors(r, c):
    for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
        rr, cc = r + dr, c + dc
        if _inb(rr, cc):
            yield rr, cc

def _build_board(me, opponent):
    # 0 empty, 1 me, 2 opp
    b = [[0]*(N+1) for _ in range(N+1)]
    for r,c in me:
        b[r][c] = 1
    for r,c in opponent:
        b[r][c] = 2
    return b

def _group_and_liberties(board, r, c):
    """Return (group_cells, liberties_set) for the stone at (r,c)."""
    color = board[r][c]
    if color == 0:
        return set(), set()
    seen = set([(r,c)])
    q = deque([(r,c)])
    group = set([(r,c)])
    libs = set()
    while q:
        cr, cc = q.popleft()
        for nr, nc in _neighbors(cr, cc):
            v = board[nr][nc]
            if v == 0:
                libs.add((nr,nc))
            elif v == color and (nr,nc) not in seen:
                seen.add((nr,nc))
                group.add((nr,nc))
                q.append((nr,nc))
    return group, libs

def _remove_captured(board, placed_color, opp_color, last_move=None):
    """Remove any opponent groups with 0 liberties. Mutates board; returns total removed count."""
    removed = 0
    # If last_move provided, only check neighboring groups (speed).
    if last_move is not None:
        r0, c0 = last_move
        to_check = set()
        for nr, nc in _neighbors(r0, c0):
            if board[nr][nc] == opp_color:
                to_check.add((nr,nc))
        checked_groups = set()
        for sr, sc in to_check:
            if (sr,sc) in checked_groups:
                continue
            grp, libs = _group_and_liberties(board, sr, sc)
            checked_groups |= grp
            if len(libs) == 0:
                for rr, cc in grp:
                    board[rr][cc] = 0
                removed += len(grp)
    else:
        for r in range(1, N+1):
            for c in range(1, N+1):
                if board[r][c] == opp_color:
                    grp, libs = _group_and_liberties(board, r, c)
                    if len(libs) == 0:
                        for rr, cc in grp:
                            board[rr][cc] = 0
                        removed += len(grp)
    return removed

def _is_legal_move(board, r, c, color):
    """Check legality for placing color at (r,c). Does not modify original board."""
    if not _inb(r,c) or board[r][c] != 0:
        return False
    opp = 2 if color == 1 else 1

    # Simulate
    b2 = [row[:] for row in board]
    b2[r][c] = color

    # Captures first
    _remove_captured(b2, color, opp, last_move=(r,c))

    # Then check suicide: the placed stone's group must have >=1 liberty
    grp, libs = _group_and_liberties(b2, r, c)
    if len(libs) == 0:
        return False
    return True

def _try_move(board, r, c, color):
    """Simulate move; return (new_board, removed_count, libs_of_new_group)."""
    opp = 2 if color == 1 else 1
    b2 = [row[:] for row in board]
    b2[r][c] = color
    removed = _remove_captured(b2, color, opp, last_move=(r,c))
    grp, libs = _group_and_liberties(b2, r, c)
    return b2, removed, len(libs)

def _nearby_candidates(board):
    """Generate candidate empty points near existing stones to reduce branching."""
    empties = set()
    stones = []
    for r in range(1, N+1):
        for c in range(1, N+1):
            if board[r][c] != 0:
                stones.append((r,c))
    if not stones:
        # Opening: play center
        return [(10,10)]
    for r,c in stones:
        for nr,nc in _neighbors(r,c):
            if board[nr][nc] == 0:
                empties.add((nr,nc))
    # If board is sparse, fallback to all empties in a radius around center
    if not empties:
        for r in range(1,N+1):
            for c in range(1,N+1):
                if board[r][c] == 0:
                    empties.add((r,c))
    # Convert to list
    return list(empties)

def policy(me, opponent):
    board = _build_board(me, opponent)
    my_color = 1
    opp_color = 2

    # Precompute opponent groups in atari for urgent defense/capture heuristics
    opp_atari_libs = {}  # liberty_point -> count of groups that would be captured if filled
    opp_groups = set()
    for r in range(1, N+1):
        for c in range(1, N+1):
            if board[r][c] == opp_color:
                if (r,c) in opp_groups:
                    continue
                grp, libs = _group_and_liberties(board, r, c)
                opp_groups |= grp
                if len(libs) == 1:
                    lp = next(iter(libs))
                    opp_atari_libs[lp] = opp_atari_libs.get(lp, 0) + 1

    # Candidate moves near stones
    candidates = _nearby_candidates(board)
    # Deterministic shuffle-ish for variety
    random.seed(0)

    # Scoring
    center = (10,10)
    def dist_center(p):
        return abs(p[0]-center[0]) + abs(p[1]-center[1])

    best = None
    best_score = -10**9

    # If opponent has atari points, capturing them is usually best
    # We'll prioritize moves that fill those liberties and are legal.
    urgent_caps = [pt for pt in candidates if pt in opp_atari_libs]
    urgent_caps.sort(key=lambda p: -opp_atari_libs[p])

    considered = urgent_caps + [pt for pt in candidates if pt not in set(urgent_caps)]
    for r,c in considered:
        if not _is_legal_move(board, r, c, my_color):
            continue
        b2, removed, libs_new = _try_move(board, r, c, my_color)

        # Additional tactical check: does this move capture?
        cap_bonus = 2000 * removed

        # If it fills an atari liberty of opponent, super-bonus
        fill_bonus = 1200 * opp_atari_libs.get((r,c), 0)

        # Safety: penalize moves that would leave our group in atari unless we captured
        suicide_risk = 0
        if removed == 0 and libs_new == 1:
            suicide_risk -= 800
        if libs_new == 0:
            suicide_risk -= 2000

        # Encourage connecting to existing friendly stones/groups:
        connect = 0
        for nr,nc in _neighbors(r,c):
            if board[nr][nc] == my_color:
                connect += 1

        # Avoid immediate recapture threats: if move does not capture, and it gives opponent an atari of us.
        # Check by seeing if any adjacent opponent group is in position to capture our new group next move.
        # We approximate by checking our liberties after move and whether any adjacent opponent group would have 1 liberty at (r,c) area.
        # Simple: penalize if our new group liberties are small.
        liberty_pref = 50 * libs_new

        # Positional: prefer closer to center and slightly prefer higher local mobility
        pos = -3 * dist_center((r,c))
        local_empty = 0
        for nr,nc in _neighbors(r,c):
            if b2[nr][nc] == 0:
                local_empty += 1

        score = (
            cap_bonus +
            fill_bonus +
            suicide_risk +
            120 * connect +
            liberty_pref +
            10 * local_empty +
            pos
        )

        # Tie-break randomness
        score += random.uniform(-5, 5)

        if score > best_score:
            best_score = score
            best = (r,c)

    # If no legal move among candidates, try any empty point (should be rare)
    if best is None:
        for r in range(1,N+1):
            for c in range(1,N+1):
                if board[r][c] == 0 and _is_legal_move(board, r, c, my_color):
                    best = (r,c)
                    break
            if best is not None:
                break

    if best is None:
        return (0,0)  # pass if truly no legal move

    return best
