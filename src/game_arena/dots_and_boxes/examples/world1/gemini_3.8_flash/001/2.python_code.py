
import time
import numpy as np

# ---------------------------------------------------------------------------
# Precomputed lookup tables for 4x4 Dots and Boxes (16 boxes, 40 edges)
# ---------------------------------------------------------------------------
# Horizontal edges: 5 rows x 4 cols = 20 edges (indices 0..19)
#   Index h = r * 4 + c  (r in 0..4, c in 0..3)
# Vertical edges:   4 rows x 5 cols = 20 edges (indices 20..39)
#   Index v = 20 + r * 5 + c  (r in 0..3, c in 0..4)

BOX_EDGES = [None] * 16
BOX_MASKS = [0] * 16
EDGE_BOXES = [[] for _ in range(40)]

for _br in range(4):
    for _bc in range(4):
        _b = _br * 4 + _bc
        _top = _br * 4 + _bc
        _bottom = (_br + 1) * 4 + _bc
        _left = 20 + _br * 5 + _bc
        _right = 20 + _br * 5 + (_bc + 1)
        _edges = (_top, _bottom, _left, _right)
        BOX_EDGES[_b] = _edges
        _mask = (1 << _top) | (1 << _bottom) | (1 << _left) | (1 << _right)
        BOX_MASKS[_b] = _mask
        for _e in _edges:
            EDGE_BOXES[_e].append(_b)


def _edge_to_action(edge_idx: int) -> str:
    """Convert integer edge index (0..39) to 'row,col,dir'."""
    if edge_idx < 20:
        r = edge_idx // 4
        c = edge_idx % 4
        return f"{r},{c},H"
    else:
        idx = edge_idx - 20
        r = idx // 5
        c = idx % 5
        return f"{r},{c},V"


def _count_chain_loss(edges: int, start_edge: int) -> int:
    """Simulate greedy capture rollout to determine conceded boxes on sacrifice."""
    cur_edges = edges | (1 << start_edge)
    lost = 0
    while True:
        found = False
        for b in range(16):
            if (cur_edges & BOX_MASKS[b]).bit_count() == 3:
                missing = BOX_MASKS[b] & ~cur_edges
                cur_edges |= missing
                lost += 1
                found = True
                break
        if not found:
            break
    return lost


def _get_ordered_moves(edges: int, tt_move: int = None):
    """Categorize and order available edges for maximum Alpha-Beta pruning."""
    caps_2 = []
    caps_1 = []
    safe_0 = []
    safe_1 = []
    sacrifices = []

    unplayed = ~edges & 0xFFFFFFFFFF
    while unplayed:
        e = (unplayed & -unplayed).bit_length() - 1
        unplayed &= unplayed - 1

        caps = 0
        creates_three = False
        makes_two = False
        is_perimeter = len(EDGE_BOXES[e]) == 1

        for b in EDGE_BOXES[e]:
            cnt = (edges & BOX_MASKS[b]).bit_count()
            if cnt == 3:
                caps += 1
            elif cnt == 2:
                creates_three = True
            elif cnt == 1:
                makes_two = True

        if caps == 2:
            caps_2.append(e)
        elif caps == 1:
            caps_1.append(e)
        elif not creates_three:
            priority = 0 if is_perimeter else 1
            if not makes_two:
                safe_0.append((priority, e))
            else:
                safe_1.append((priority, e))
        else:
            loss = _count_chain_loss(edges, e)
            sacrifices.append((loss, e))

    safe_0.sort()
    safe_1.sort()
    sacrifices.sort()

    ordered = (
        caps_2
        + caps_1
        + [e for _, e in safe_0]
        + [e for _, e in safe_1]
        + [e for _, e in sacrifices]
    )

    if tt_move is not None and tt_move in ordered:
        ordered.remove(tt_move)
        ordered.insert(0, tt_move)

    return ordered


def _evaluate_state(edges: int, player: int) -> float:
    """Heuristic static evaluation when search depth is exhausted."""
    num_safe = 0
    num_count2 = 0
    unplayed = ~edges & 0xFFFFFFFFFF
    while unplayed:
        e = (unplayed & -unplayed).bit_length() - 1
        unplayed &= unplayed - 1
        if not any((edges & BOX_MASKS[b]).bit_count() == 2 for b in EDGE_BOXES[e]):
            num_safe += 1

    for b in range(16):
        if (edges & BOX_MASKS[b]).bit_count() == 2:
            num_count2 += 1

    # Parity: odd number of safe moves favors the player to move
    parity_advantage = 1.0 if (num_safe % 2 == 1) else -1.0
    val = parity_advantage if player == 0 else -parity_advantage
    val -= 0.1 * num_count2
    return val


def _minimax(
    edges: int,
    player: int,
    depth: int,
    alpha: float,
    beta: float,
    start_time: float,
    time_limit: float,
    tt: dict,
):
    if time.time() - start_time > time_limit:
        raise TimeoutError

    if edges == 0xFFFFFFFFFF:
        return 0, None

    if depth <= 0:
        return _evaluate_state(edges, player), None

    tt_entry = tt.get((edges, player))
    tt_move = None
    if tt_entry is not None:
        tt_d, tt_val, tt_m = tt_entry
        if tt_d >= depth:
            return tt_val, tt_m
        tt_move = tt_m

    moves = _get_ordered_moves(edges, tt_move)
    if not moves:
        return 0, None

    best_move = moves[0]

    if player == 0:
        max_eval = -1000.0
        for m in moves:
            caps = sum(
                1 for b in EDGE_BOXES[m] if (edges & BOX_MASKS[b]).bit_count() == 3
            )
            new_edges = edges | (1 << m)
            if caps > 0:
                # Same player moves again; turn does not consume depth
                val, _ = _minimax(
                    new_edges,
                    0,
                    depth,
                    alpha - caps,
                    beta - caps,
                    start_time,
                    time_limit,
                    tt,
                )
                val += caps
            else:
                val, _ = _minimax(
                    new_edges,
                    1,
                    depth - 1,
                    alpha,
                    beta,
                    start_time,
                    time_limit,
                    tt,
                )

            if val > max_eval:
                max_eval = val
                best_move = m
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        tt[(edges, player)] = (depth, max_eval, best_move)
        return max_eval, best_move
    else:
        min_eval = 1000.0
        for m in moves:
            caps = sum(
                1 for b in EDGE_BOXES[m] if (edges & BOX_MASKS[b]).bit_count() == 3
            )
            new_edges = edges | (1 << m)
            if caps > 0:
                # Opponent continues; turn does not consume depth
                val, _ = _minimax(
                    new_edges,
                    1,
                    depth,
                    alpha + caps,
                    beta + caps,
                    start_time,
                    time_limit,
                    tt,
                )
                val -= caps
            else:
                val, _ = _minimax(
                    new_edges,
                    0,
                    depth - 1,
                    alpha,
                    beta,
                    start_time,
                    time_limit,
                    tt,
                )

            if val < min_eval:
                min_eval = val
                best_move = m
            beta = min(beta, val)
            if beta <= alpha:
                break
        tt[(edges, player)] = (depth, min_eval, best_move)
        return min_eval, best_move


def policy(
    horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray
) -> str:
    """Select the optimal legal move for Dots and Boxes on a 4x4 box grid."""
    start_time = time.time()
    time_limit = 0.82  # Safely within 1.0 second limit

    # Construct the 40-bit edge state representation
    edges = 0
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                edges |= 1 << (r * 4 + c)

    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                edges |= 1 << (20 + r * 5 + c)

    # Pre-order available moves for immediate high-quality fallback
    ordered = _get_ordered_moves(edges)
    if not ordered:
        # Fallback to any empty cell in array bounds
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
        return "0,0,H"

    best_move = ordered[0]
    remaining_edges = 40 - edges.bit_count()
    tt = {}

    # Target search depth: complete endgame solve if remaining <= 16
    target_depth = remaining_edges if remaining_edges <= 16 else 8

    for d in range(1, target_depth + 1):
        try:
            _, m = _minimax(
                edges, 0, d, -1000.0, 1000.0, start_time, time_limit, tt
            )
            if m is not None:
                best_move = m
            if remaining_edges <= 16 and d >= remaining_edges:
                break  # Endgame solved to terminal state
        except TimeoutError:
            break

    action_str = _edge_to_action(best_move)

    # Legality sanity check
    r_str, c_str, d_str = action_str.split(",")
    r, c = int(r_str), int(c_str)
    if d_str == "H" and horizontal[r, c] == 0:
        return action_str
    if d_str == "V" and vertical[r, c] == 0:
        return action_str

    # Safe legal fallback
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    return action_str
