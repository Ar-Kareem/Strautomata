
import numpy as np
from collections import deque

N = 15

# Board corners (in 0-indexed axial-ish coordinates given as (row, col) on the 2D array)
# For Havannah on a 2D array representation used in many arenas, these are:
# Common corner coordinates:
CORNERS = [(0, 0), (0, N-1), (N-1, 0), (N-1, N-1), (0, 7), (N-1, 7)]
# Note: The "six corners" in a hex board correspond to 3 pairs.
# However, because the arena provides a 15x15 2D mask, the exact corner mapping can differ.
# To remain robust, we treat "corner cells" as any valid cell that is on the boundary and
# one of the extreme points; we approximate corners by the 4 extreme corners + top/bottom middle.
# If your arena uses a different mapping, this could be slightly off, but heuristics still work.

# Edge sets for fork detection (each fork connects any three edges; corner not counted as edge)
# We'll use boundary classifications:
def in_bounds(r, c):
    return 0 <= r < N and 0 <= c < N

def neighbors_hex(r, c):
    # Hex adjacency on a 15x15 "axial-like" mapping:
    # From the prompt example at (4,1): touch (5,1),(3,1),(4,2),(3,2),(4,0),(5,0)
    # So neighbors relative offsets:
    # down: ( +1, 0)
    # up:   ( -1, 0)
    # right-down: (+0? actually (4,2) and (3,2))
    # This corresponds to two diagonals in col:
    # (r, c+1) and (r-1, c+1)
    # and two to left: (r, c-1) and (r+1, c-1)
    deltas = [(1, 0), (-1, 0), (0, 1), (-1, 1), (0, -1), (1, -1)]
    for dr, dc in deltas:
        rr, cc = r + dr, c + dc
        if in_bounds(rr, cc):
            yield rr, cc

def build_board(me, opp):
    board = np.full((N, N), -1, dtype=np.int8)
    for r, c in me:
        board[r, c] = 0
    for r, c in opp:
        board[r, c] = 1
    return board

def get_components(board, player):
    visited = np.zeros((N, N), dtype=bool)
    comps = []
    for r in range(N):
        for c in range(N):
            if board[r, c] == player and not visited[r, c]:
                q = deque([(r, c)])
                visited[r, c] = True
                cells = []
                while q:
                    rr, cc = q.popleft()
                    cells.append((rr, cc))
                    for nr, nc in neighbors_hex(rr, cc):
                        if board[nr, nc] == player and not visited[nr, nc]:
                            visited[nr, nc] = True
                            q.append((nr, nc))
                comps.append(cells)
    return comps

def is_corner_like(r, c):
    # Approximate six "corner" cells.
    # Exactness may vary by arena; we use a set of boundary extremes.
    boundary = (r == 0 or r == N-1 or c == 0 or c == N-1)
    if not boundary:
        return False
    # include approximate extremes and top/bottom middle
    if (r, c) in CORNERS:
        return True
    # also include the four extremes already in corners set
    if (r == 0 and c == 0) or (r == 0 and c == N-1) or (r == N-1 and c == 0) or (r == N-1 and c == N-1):
        return True
    # top/bottom mid
    if (r == 0 and c == N//2) or (r == N-1 and c == N//2):
        return True
    return False

def edge_id(r, c):
    # Assign each boundary non-corner to one of 6 edges (0..5).
    # We approximate:
    # Edge 0: top-left slant
    # Edge 1: top-right slant
    # Edge 2: right upper
    # Edge 3: bottom-right slant
    # Edge 4: bottom-left slant
    # Edge 5: left upper
    if is_corner_like(r, c):
        return None
    if r == 0:
        return 0 if c < N//2 else 1
    if r == N-1:
        return 4 if c < N//2 else 3
    if c == 0:
        return 5 if r < N//2 else 4  # blend
    if c == N-1:
        return 2 if r < N//2 else 3
    # For safety, if boundary on remaining slants, classify by nearest corner side:
    # (rarely used if mask already excludes invalid cells)
    # We'll approximate by slope to top-middle and bottom-middle.
    if r < N//2 and c < N//2:
        return 0
    if r < N//2 and c >= N//2:
        return 1
    if r >= N//2 and c < N//2:
        return 5
    return 2

def player_has_bridge(board, player, valid_mask):
    # Bridge: connects any two of the six corner cells.
    # We build components and see which corners each component touches.
    comps = get_components(board, player)
    corners = set(CORNERS)
    for comp in comps:
        touched = set()
        for r, c in comp:
            if (r, c) in corners:
                touched.add((r, c))
        if len(touched) >= 2:
            # any two corners works
            return True
    return False

def player_has_fork(board, player):
    # Fork: connects any three edges (corners not part of edge).
    # Approximate edges via boundary classification.
    comps = get_components(board, player)
    for comp in comps:
        edges = set()
        for r, c in comp:
            eid = edge_id(r, c)
            if eid is not None:
                edges.add(eid)
        if len(edges) >= 3:
            return True
    return False

def has_ring(board, player, valid_mask):
    """
    Ring: A loop around one or more cells, empty or occupied by any player.
    On hex grids, a reliable ring detector is non-trivial. We'll use a practical approximation:
    - For each connected component of player's stones, temporarily consider them as "walls".
    - Flood-fill the empty+opponent cells; if the component encloses a region not connected
      to the boundary of the board, that's a ring.
    This can detect many rings; false positives are possible, but correctness is still often good.
    """
    # Build a mask of passable cells (not player's stones)
    passable = (valid_mask.astype(bool)) & (board != player)
    # If player's stones already cover boundary heavily, ring unlikely.
    # We flood from all passable boundary cells; remaining passable regions are enclosed.
    visited = np.zeros((N, N), dtype=bool)
    q = deque()
    for r in range(N):
        for c in range(N):
            if not passable[r, c]:
                continue
            # boundary of the board (in mask)
            if r == 0 or c == 0 or r == N-1 or c == N-1:
                visited[r, c] = True
                q.append((r, c))
    while q:
        r, c = q.popleft()
        for nr, nc in neighbors_hex(r, c):
            if in_bounds(nr, nc) and passable[nr, nc] and not visited[nr, nc]:
                visited[nr, nc] = True
                q.append((nr, nc))
    # enclosed passable cells are those passable but not visited
    enclosed = (passable & (~visited))
    # If any enclosed cell exists and player's stones form a cycle-ish structure, call it ring.
    # We'll require that the player's component touches at least 3 different "boundary-adjacent"
    # faces around enclosed region isn't used; too complex. We'll simply require enclosed nonempty.
    return bool(np.any(enclosed))

def is_winning(board, player, valid_mask):
    return (
        player_has_bridge(board, player, valid_mask)
        or player_has_fork(board, player)
        or has_ring(board, player, valid_mask)
    )

def legal_moves(valid_mask, board):
    moves = []
    for r in range(N):
        for c in range(N):
            if valid_mask[r][c] and board[r, c] == -1:
                moves.append((r, c))
    return moves

def score_move(r, c, me_set, board, opp_set, valid_mask):
    # Heuristic combining:
    # - connection to our existing stones
    # - block opponent threats by proximity
    # - centrality
    center = (N-1)/2
    cent_score = 1.0 - (abs(r-center)+abs(c-center))/(N)  # in [~0..1]
    # - immediate adjacency count
    adj_own = 0
    adj_opp = 0
    for nr, nc in neighbors_hex(r, c):
        if not valid_mask[nr, nc]:
            continue
        if board[nr, nc] == 0:
            adj_own += 1
        elif board[nr, nc] == 1:
            adj_opp += 1
    # - "potential bridge/fork" pressure:
    # proximity to corners/edges
    corner_score = 0.0
    for cr, cc in CORNERS:
        if valid_mask[cr, cc]:
            d = abs(r-cr) + abs(c-cc)
            corner_score += 1.0/(1+d)
    # Reduce score if move gives opponent adjacent connectivity advantage
    danger = adj_opp

    return 3.0*adj_own + 1.2*corner_score + 0.8*cent_score - 2.2*danger

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    valid_mask = np.array(valid_mask, dtype=bool)
    board = build_board(me, opp)
    me_set = set(me)
    opp_set = set(opp)

    # Generate candidates: all legal cells, but we can narrow to neighborhood for speed.
    empties = []
    for r in range(N):
        for c in range(N):
            if valid_mask[r, c] and board[r, c] == -1:
                empties.append((r, c))
    if not empties:
        # Should not happen
        return (N//2, N//2)

    # Candidate ordering: heuristic top-K
    scored = []
    for r, c in empties:
        scored.append((score_move(r, c, me_set, board, opp_set, valid_mask), r, c))
    scored.sort(reverse=True)
    topK = scored[:max(25, len(scored)//8)]  # keep some breadth

    # 1) Win now
    for _, r, c in topK:
        b2 = board.copy()
        b2[r, c] = 0
        if is_winning(b2, 0, valid_mask):
            return (r, c)

    # 2) Block opponent win
    for _, r, c in topK:
        b2 = board.copy()
        b2[r, c] = 0
        # if opponent would win next move, this is not directly detectable without search.
        # We'll instead check if this move blocks all immediate opponent wins:
        # i.e., see if there exists an opponent move that wins; expensive. We'll do a shallow check:
        # - if opponent already has a near-win, block by testing opponent winning responses among top moves.
        pass

    # Immediate opponent win response check among top candidates after our move is too costly,
    # so do direct search: if any legal move by opponent would win right now, block it.
    opp_winning = []
    opp_player = 1
    for rr, cc in empties:
        b2 = board.copy()
        b2[rr, cc] = opp_player
        if is_winning(b2, opp_player, valid_mask):
            opp_winning.append((rr, cc))
    if opp_winning:
        # Block by playing one of our moves that prevents those cells from being used.
        # Since we can only play one stone, the best is to play on/adjacent to the most forcing threats.
        # We'll choose a move that minimizes opponent immediate winning options.
        best = None
        best_val = -1e9
        for _, r, c in topK:
            b2 = board.copy()
            b2[r, c] = 0
            # count remaining opponent immediate wins
            remaining = 0
            for rr, cc in opp_winning:
                if b2[rr, cc] == -1:  # still empty for opponent
                    remaining += 1
            # lower remaining is better; plus also prevent new wins by proximity
            val = -10*remaining + score_move(r, c, me_set, board, opp_set, valid_mask)
            if val > best_val:
                best_val = val
                best = (r, c)
        if best is not None:
            return best

    # 3) Otherwise choose best heuristic among topK, with a small anti-losing tweak:
    # ensure we don't give opponent an immediate win (try to avoid).
    best = None
    best_val = -1e18
    for _, r, c in topK:
        b2 = board.copy()
        b2[r, c] = 0
        # if opponent can win immediately after, penalize heavily
        opp_can_win = False
        # Check among top opponent replies only
        reply_scored = []
        for rr, cc in empties:
            if b2[rr, cc] != -1:
                continue
            reply_scored.append((score_move(rr, cc, opp_set, b2, me_set, valid_mask), rr, cc))
        reply_scored.sort(reverse=True)
        for _, rr, cc in reply_scored[:min(12, len(reply_scored))]:
            b3 = b2.copy()
            b3[rr, cc] = 1
            if is_winning(b3, 1, valid_mask):
                opp_can_win = True
                break
        val = score_move(r, c, me_set, board, opp_set, valid_mask) - (50.0 if opp_can_win else 0.0)
        if val > best_val:
            best_val = val
            best = (r, c)

    if best is None:
        # fallback: first legal
        for r, c in empties:
            return (r, c)

    return best
