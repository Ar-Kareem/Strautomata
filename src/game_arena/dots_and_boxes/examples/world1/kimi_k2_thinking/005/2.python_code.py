
import numpy as np
import sys
import time

sys.setrecursionlimit(10000)

# ----------------------------------------------------------------------
#  Constants and pre‑computed tables
# ----------------------------------------------------------------------
ALL_EDGES = (1 << 40) - 1          # 40 drawn edges → game finished
INF = 10 ** 9
transposition = {}                  # cleared before every move

# Box masks and adjacency tables
BOX_MASKS = [0] * 16                # 4×4 boxes
EDGE_TO_BOXES = [[] for _ in range(40)]   # which boxes an edge belongs to
EDGE_TO_MOVE = []                   # (row, col, dir) for each edge index

# Build box masks (four edges per box)
for r in range(4):
    for c in range(4):
        idx = r * 4 + c
        top = r * 4 + c
        bottom = (r + 1) * 4 + c
        left = 20 + r * 5 + c
        right = 20 + r * 5 + (c + 1)
        BOX_MASKS[idx] = (1 << top) | (1 << bottom) | (1 << left) | (1 << right)

# Build edge‑to‑boxes mapping (each edge touches at most two boxes)
# Horizontal edges (i=0..4, j=0..3)
for i in range(5):
    for j in range(4):
        eidx = i * 4 + j
        if i > 0:
            EDGE_TO_BOXES[eidx].append((i - 1) * 4 + j)   # top edge of box (i‑1,j)
        if i < 4:
            EDGE_TO_BOXES[eidx].append(i * 4 + j)          # bottom edge of box (i,j)

# Vertical edges (i=0..3, j=0..4)
for i in range(4):
    for j in range(5):
        eidx = 20 + i * 5 + j
        if j > 0:
            EDGE_TO_BOXES[eidx].append(i * 4 + (j - 1))   # left edge of box (i,j‑1)
        if j < 4:
            EDGE_TO_BOXES[eidx].append(i * 4 + j)          # right edge of box (i,j)

# Quick conversion from edge index to move string components
for eidx in range(40):
    if eidx < 20:                     # horizontal
        row = eidx // 4
        col = eidx % 4
        EDGE_TO_MOVE.append((row, col, 'H'))
    else:                              # vertical
        tmp = eidx - 20
        row = tmp // 5
        col = tmp % 5
        EDGE_TO_MOVE.append((row, col, 'V'))

# ----------------------------------------------------------------------
#  Helper functions using the bit‑board representation
# ----------------------------------------------------------------------
def boxes_with_three_sides(edges: int) -> int:
    """Return a 16‑bit mask of free boxes that currently have exactly three sides drawn."""
    mask = 0
    for b in range(16):
        m = BOX_MASKS[b]
        if (edges & m).bit_count() == 3:
            mask |= (1 << b)
    return mask

def evaluate(state, player) -> int:
    """Heuristic evaluation from the perspective of the maximizing player (player=1)."""
    edges, our_boxes, opp_boxes = state
    our_cnt = our_boxes.bit_count()
    opp_cnt = opp_boxes.bit_count()
    diff = (our_cnt - opp_cnt) * 10                # scale to dominate

    # bonus for boxes that are one move away from being captured
    three_mask = boxes_with_three_sides(edges)
    free_mask = (~(our_boxes | opp_boxes)) & ((1 << 16) - 1)
    potential = (three_mask & free_mask).bit_count()
    return diff + potential * player

def apply_move(state, move, player):
    """Return (new_state, same_player) after playing *move*."""
    edges, our_boxes, opp_boxes = state
    r, c, d = move
    if d == 'H':
        eidx = r * 4 + c
    else:
        eidx = 20 + r * 5 + c

    new_edges = edges | (1 << eidx)
    captured_mask = 0

    for b in EDGE_TO_BOXES[eidx]:
        # skip boxes already captured
        if (our_boxes >> b) & 1 or (opp_boxes >> b) & 1:
            continue
        m = BOX_MASKS[b]
        if (new_edges & m) == m:          # box becomes complete
            captured_mask |= (1 << b)

    if player == 1:
        new_our = our_boxes | captured_mask
        new_opp = opp_boxes
    else:
        new_our = our_boxes
        new_opp = opp_boxes | captured_mask

    same_player = captured_mask != 0
    return (new_edges, new_our, new_opp), same_player

def move_info(state, move, player):
    """Return (captured_mask, new_threats) for a prospective move."""
    edges, our_boxes, opp_boxes = state
    r, c, d = move
    eidx = r * 4 + c if d == 'H' else 20 + r * 5 + c

    captured_mask = 0
    new_threats = 0
    for b in EDGE_TO_BOXES[eidx]:
        if (our_boxes >> b) & 1 or (opp_boxes >> b) & 1:
            continue
        m = BOX_MASKS[b]
        old_bits = (edges & m).bit_count()
        new_bits = ((edges | (1 << eidx)) & m).bit_count()
        if new_bits == 4 and old_bits == 3:
            captured_mask |= (1 << b)
        elif new_bits == 3 and old_bits == 2:
            new_threats += 1
    return captured_mask, new_threats

def order_moves(state, player):
    """Return a list of legal moves ordered by the policy: captures → safe → dangerous."""
    edges, our_boxes, opp_boxes = state
    moves = []
    for eidx in range(40):
        if (edges >> eidx) & 1:
            continue
        mv = EDGE_TO_MOVE[eidx]
        captured_mask, new_threats = move_info(state, mv, player)
        captured_cnt = captured_mask.bit_count()

        if captured_cnt > 0:                     # capture move
            key = (0, -captured_cnt, new_threats)
        elif new_threats == 0:                    # safe move
            key = (1, 0, 0)
        else:                                     # dangerous move
            key = (2, new_threats, 0)
        moves.append((key, mv))
    moves.sort(key=lambda x: x[0])
    return [m for _, m in moves]

def get_legal_moves(state):
    edges, _, _ = state
    moves = []
    for eidx in range(40):
        if (edges >> eidx) & 1:
            continue
        moves.append(EDGE_TO_MOVE[eidx])
    return moves

# ----------------------------------------------------------------------
#  Minimax search with α‑β pruning and iterative deepening
# ----------------------------------------------------------------------
def search_eval(state, player, depth, alpha, beta):
    """Pure evaluation (no move) – returns a score for the *maximising* player."""
    edges, _, _ = state
    if edges == ALL_EDGES:
        return evaluate(state, player)
    if depth == 0:
        return evaluate(state, player)

    key = (edges, state[1], state[2], player)
    if key in transposition:
        stored_depth, stored_eval, _ = transposition[key]
        if stored_depth >= depth:
            return stored_eval

    moves = order_moves(state, player)
    if not moves:
        return evaluate(state, player)

    best_move = None
    if player == 1:                                   # maximising player
        best_val = -INF
        for mv in moves:
            nstate, same = apply_move(state, mv, player)
            nxt = player if same else -player
            val = search_eval(nstate, nxt, depth - 1, alpha, beta)
            if val > best_val:
                best_val = val
                best_move = mv
            alpha = max(alpha, best_val)
            if beta <= alpha:
                break
        transposition[key] = (depth, best_val, best_move)
        return best_val
    else:                                             # minimising player
        best_val = INF
        for mv in moves:
            nstate, same = apply_move(state, mv, player)
            nxt = player if same else -player
            val = search_eval(nstate, nxt, depth - 1, alpha, beta)
            if val < best_val:
                best_val = val
                best_move = mv
            beta = min(beta, best_val)
            if beta <= alpha:
                break
        transposition[key] = (depth, best_val, best_move)
        return best_val

# ----------------------------------------------------------------------
#  Policy interface required by the competition
# ----------------------------------------------------------------------
def policy(horizontal: np.ndarray,
           vertical: np.ndarray,
           capture: np.ndarray) -> str:
    """
    Return a legal move as the string "row,col,dir" (dir is 'H' or 'V').
    The function first converts the three 5×5 numpy arrays into a compact
    bit‑board representation and then runs an iterative‑deepening α‑β search.
    If the search does not finish in time a fast fallback (most‑captures /
    safest‑move) is used, guaranteeing a legal answer.
    """
    # ---- encode the current position ---------------------------------
    edges = 0
    for i in range(5):
        for j in range(4):
            if horizontal[i, j] != 0:
                edges |= 1 << (i * 4 + j)

    for i in range(4):
        for j in range(5):
            if vertical[i, j] != 0:
                edges |= 1 << (20 + i * 5 + j)

    our_boxes = 0
    opp_boxes = 0
    for i in range(4):
        for j in range(4):
            v = capture[i, j]
            if v == 1:
                our_boxes |= 1 << (i * 4 + j)
            elif v == -1:
                opp_boxes |= 1 << (i * 4 + j)

    state = (edges, our_boxes, opp_boxes)

    # ---- fast fallback (always legal) --------------------------------
    legal_moves = get_legal_moves(state)
    if not legal_moves:                    # should never happen
        return "0,0,H"

    # a quick heuristic ranking in case we run out of time
    scored = []
    for mv in legal_moves:
        captured, threats = move_info(state, mv, 1)   # we are player 1
        scored.append((-captured.bit_count(), threats, mv))
    scored.sort(key=lambda x: (x[0], x[1]))
    best_move_fallback = scored[0][2]

    # ---- iterative deepening search ----------------------------------
    transposition.clear()
    start = time.perf_counter()
    best_move = best_move_fallback
    for depth in range(1, 20):            # high upper bound – time stops us
        _ = search_eval(state, 1, depth, -INF, INF)
        # retrieve the move that the search stored for the root
        key = (edges, our_boxes, opp_boxes, 1)
        if key in transposition:
            _, _, mv = transposition[key]
            if mv is not None:
                best_move = mv
        if time.perf_counter() - start > 0.9:
            break

    row, col, d = best_move
    return f"{row},{col},{d}"
