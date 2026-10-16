
import numpy as np
import time
from collections import deque
from typing import List, Tuple, Optional, Dict

# --- Precompute rays for a 6x6 board (queen directions) ---
N = 6
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)]

RAYS = [[[] for _ in range(N)] for __ in range(N)]
for r in range(N):
    for c in range(N):
        rays = []
        for dr, dc in DIRS:
            line = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < N and 0 <= cc < N:
                line.append((rr, cc))
                rr += dr
                cc += dc
            rays.append(line)
        RAYS[r][c] = rays

CENTER = (N - 1) / 2.0  # 2.5 for 6x6


Move = Tuple[int, int, int, int, int, int]  # fr,fc,tr,tc,ar,ac


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def _ray_empty_squares(board: np.ndarray, r: int, c: int, vacated: Optional[Tuple[int, int]] = None) -> List[Tuple[int, int]]:
    """All empty squares reachable by a queen ray from (r,c).
    If vacated is provided, that square is treated as empty (useful for arrow after move)."""
    out = []
    for line in RAYS[r][c]:
        for rr, cc in line:
            if (vacated is not None) and (rr == vacated[0] and cc == vacated[1]):
                out.append((rr, cc))
                continue
            if board[rr, cc] != 0:
                break
            out.append((rr, cc))
    return out


def _has_any_move(board: np.ndarray, player: int) -> bool:
    """In Amazons, if any amazon can move at all, it can also shoot an arrow (at least back along the path),
    so checking movement-only is sufficient to detect no-legal-move positions."""
    positions = np.argwhere(board == player)
    for r, c in positions:
        # Any reachable empty square means a legal move exists.
        for line in RAYS[r][c]:
            for rr, cc in line:
                if board[rr, cc] != 0:
                    break
                return True
    return False


def _apply_move(board: np.ndarray, move: Move, player: int) -> np.ndarray:
    fr, fc, tr, tc, ar, ac = move
    b = board.copy()
    b[fr, fc] = 0
    b[tr, tc] = player
    b[ar, ac] = -1
    return b


def _reachable_count(board: np.ndarray, player: int) -> int:
    """Mobility proxy: total number of empty squares visible by queen rays from all amazons."""
    total = 0
    positions = np.argwhere(board == player)
    for r, c in positions:
        for line in RAYS[r][c]:
            for rr, cc in line:
                if board[rr, cc] != 0:
                    break
                total += 1
    return total


def _queen_distance(board: np.ndarray, sources: List[Tuple[int, int]]) -> np.ndarray:
    """Shortest path distances in number of queen moves, restricted to empty squares, from any source."""
    INF = 10**9
    dist = np.full((N, N), INF, dtype=np.int32)
    q = deque()

    for r, c in sources:
        dist[r, c] = 0
        q.append((r, c))

    while q:
        r, c = q.popleft()
        nd = dist[r, c] + 1
        # From (r,c), you can reach any empty square along each ray until blocked.
        for line in RAYS[r][c]:
            for rr, cc in line:
                if board[rr, cc] != 0:
                    break
                if dist[rr, cc] > nd:
                    dist[rr, cc] = nd
                    q.append((rr, cc))
    return dist


def _territory_voronoi(board: np.ndarray) -> int:
    """Voronoi-like territory: for each empty square, award +1 if closer (queen-distance) to us, -1 if closer to opp."""
    my_src = [tuple(x) for x in np.argwhere(board == 1)]
    op_src = [tuple(x) for x in np.argwhere(board == 2)]
    if not my_src and not op_src:
        return 0

    d1 = _queen_distance(board, my_src) if my_src else np.full((N, N), 10**9, dtype=np.int32)
    d2 = _queen_distance(board, op_src) if op_src else np.full((N, N), 10**9, dtype=np.int32)

    score = 0
    empties = np.argwhere(board == 0)
    for r, c in empties:
        a = d1[r, c]
        b = d2[r, c]
        if a < b:
            score += 1
        elif b < a:
            score -= 1
    return score


def _centrality(r: int, c: int) -> float:
    # smaller is better
    return abs(r - CENTER) + abs(c - CENTER)


def _min_chebyshev_to_positions(r: int, c: int, positions: List[Tuple[int, int]]) -> int:
    if not positions:
        return 3  # neutral-ish
    return min(max(abs(r - pr), abs(c - pc)) for pr, pc in positions)


def _move_order_score(board: np.ndarray, move: Move, player: int, opp_positions: List[Tuple[int, int]]) -> float:
    """Fast, no-copy move ordering heuristic."""
    fr, fc, tr, tc, ar, ac = move
    # Prefer moving to center and placing arrows near opponent.
    to_c = _centrality(tr, tc)
    ar_c = _centrality(ar, ac)
    d_opp = _min_chebyshev_to_positions(ar, ac, opp_positions)

    # Encourage arrows close to opponents and decent centrality.
    score = 0.0
    score += -0.35 * to_c
    score += -0.10 * ar_c
    score += -0.55 * d_opp

    # Tiny bonus for longer moves (often increases options).
    score += 0.02 * max(abs(tr - fr), abs(tc - fc))
    return score if player == 1 else -score  # for opponent ordering, flip sign


def _generate_moves(
    board: np.ndarray,
    player: int,
    arrow_cap: Optional[int],
    time_deadline: float,
) -> List[Move]:
    """Generate legal moves. Optionally cap arrow choices per destination to reduce branching."""
    opp = 2 if player == 1 else 1
    opp_positions = [tuple(x) for x in np.argwhere(board == opp)]
    my_positions = np.argwhere(board == player)

    moves: List[Move] = []
    for fr, fc in my_positions:
        if time.perf_counter() > time_deadline:
            break
        dests = _ray_empty_squares(board, int(fr), int(fc), vacated=None)
        for tr, tc in dests:
            if time.perf_counter() > time_deadline:
                break
            arrows = _ray_empty_squares(board, int(tr), int(tc), vacated=(int(fr), int(fc)))

            if arrow_cap is not None and len(arrows) > arrow_cap:
                # Rank arrows by closeness to opponent + centrality, keep top arrow_cap.
                # Always try to include the vacated square if it's a legal arrow target.
                vac = (int(fr), int(fc))
                scored = []
                for (ar, ac) in arrows:
                    d_opp = _min_chebyshev_to_positions(ar, ac, opp_positions)
                    sc = (-d_opp) - 0.05 * _centrality(ar, ac)
                    scored.append((sc, ar, ac))
                scored.sort(reverse=True)
                picked = [(ar, ac) for _, ar, ac in scored[:arrow_cap]]
                if vac in arrows and vac not in picked:
                    picked[-1] = vac
                arrows = picked

            for ar, ac in arrows:
                moves.append((int(fr), int(fc), int(tr), int(tc), int(ar), int(ac)))

    # Order moves for alpha-beta.
    moves.sort(key=lambda mv: _move_order_score(board, mv, player, opp_positions), reverse=True)
    return moves


def _evaluate(board: np.ndarray, eval_cache: Dict[bytes, float]) -> float:
    key = board.tobytes()
    if key in eval_cache:
        return eval_cache[key]

    # If someone has no move, it's effectively terminal (side to move matters in search),
    # but for static eval we still heavily reward positions where opponent is immobile.
    my_can = _has_any_move(board, 1)
    op_can = _has_any_move(board, 2)
    if my_can and not op_can:
        val = 1e6
        eval_cache[key] = val
        return val
    if op_can and not my_can:
        val = -1e6
        eval_cache[key] = val
        return val

    mob = _reachable_count(board, 1) - _reachable_count(board, 2)
    terr = _territory_voronoi(board)

    # Small centrality term: prefer our amazons less centrality distance (more central).
    my_pos = np.argwhere(board == 1)
    op_pos = np.argwhere(board == 2)
    my_cent = sum(_centrality(int(r), int(c)) for r, c in my_pos) if len(my_pos) else 0.0
    op_cent = sum(_centrality(int(r), int(c)) for r, c in op_pos) if len(op_pos) else 0.0
    cent = (op_cent - my_cent)

    val = 1.10 * mob + 1.60 * terr + 0.15 * cent
    eval_cache[key] = val
    return val


def _search(
    board: np.ndarray,
    turn: int,
    depth: int,
    alpha: float,
    beta: float,
    time_deadline: float,
    eval_cache: Dict[bytes, float],
    arrow_cap: Optional[int],
) -> float:
    now = time.perf_counter()
    if now > time_deadline:
        return _evaluate(board, eval_cache)

    # Terminal: no legal move for side to play => they lose.
    if not _has_any_move(board, turn):
        return -1e6 if turn == 1 else 1e6

    if depth <= 0:
        return _evaluate(board, eval_cache)

    moves = _generate_moves(board, turn, arrow_cap=arrow_cap, time_deadline=time_deadline)
    if not moves:
        return -1e6 if turn == 1 else 1e6

    if turn == 1:
        best = -1e18
        for mv in moves:
            if time.perf_counter() > time_deadline:
                break
            b2 = _apply_move(board, mv, 1)
            val = _search(b2, 2, depth - 1, alpha, beta, time_deadline, eval_cache, arrow_cap)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
    else:
        best = 1e18
        for mv in moves:
            if time.perf_counter() > time_deadline:
                break
            b2 = _apply_move(board, mv, 2)
            val = _search(b2, 1, depth - 1, alpha, beta, time_deadline, eval_cache, arrow_cap)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best


def policy(board) -> str:
    """
    Return a legal move string: "from_row,from_col:to_row,to_col:arrow_row,arrow_col"
    """
    # Ensure numpy array
    board = np.asarray(board)
    start = time.perf_counter()
    time_deadline = start + 0.92  # keep margin

    # Fallback: first legal move found (guarantees legality if any move exists).
    fallback_move: Optional[Move] = None

    eval_cache: Dict[bytes, float] = {}

    # Root move generation: slightly higher arrow cap for better tactics.
    root_moves = _generate_moves(board, player=1, arrow_cap=14, time_deadline=time_deadline)
    if root_moves:
        fallback_move = root_moves[0]

    if not root_moves:
        # Environment should not call us here; return a correctly formatted placeholder.
        # (No legal move exists, so any move would be illegal; this is just robustness.)
        return "0,0:0,0:0,0"

    best_move = fallback_move
    best_val = -1e18

    # Depth 2 search (us -> opp)
    depth = 2
    # Limit root branching a bit, but keep enough variety.
    root_limit = 24
    for mv in root_moves[:root_limit]:
        if time.perf_counter() > time_deadline:
            break
        b1 = _apply_move(board, mv, 1)
        # Immediate win if opponent cannot move.
        if not _has_any_move(b1, 2):
            best_move = mv
            best_val = 1e6
            break
        val = _search(b1, 2, depth - 1, -1e18, 1e18, time_deadline, eval_cache, arrow_cap=10)
        if val > best_val:
            best_val = val
            best_move = mv

    # If time remains, deepen to 3 plies with tighter caps.
    if time.perf_counter() < time_deadline - 0.18:
        depth = 3
        root_limit = 12
        for mv in root_moves[:root_limit]:
            if time.perf_counter() > time_deadline:
                break
            b1 = _apply_move(board, mv, 1)
            if not _has_any_move(b1, 2):
                best_move = mv
                best_val = 1e6
                break
            val = _search(b1, 2, depth - 1, -1e18, 1e18, time_deadline, eval_cache, arrow_cap=8)
            if val > best_val:
                best_val = val
                best_move = mv

    fr, fc, tr, tc, ar, ac = best_move if best_move is not None else fallback_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
