
import time
import math
import random
import numpy as np


# Edge numbering:
#   0..19  : horizontal edges, index = row * 4 + col
#   20..39 : vertical edges,   index = 20 + row * 5 + col
NUM_EDGES = 40
FULL_MASK = (1 << NUM_EDGES) - 1

BOX_MASKS = []
EDGE_BOXES = [[] for _ in range(NUM_EDGES)]

for box_row in range(4):
    for box_col in range(4):
        top = box_row * 4 + box_col
        bottom = (box_row + 1) * 4 + box_col
        left = 20 + box_row * 5 + box_col
        right = 20 + box_row * 5 + box_col + 1

        box_index = box_row * 4 + box_col
        box_mask = (
            (1 << top)
            | (1 << bottom)
            | (1 << left)
            | (1 << right)
        )
        BOX_MASKS.append(box_mask)

        EDGE_BOXES[top].append(box_index)
        EDGE_BOXES[bottom].append(box_index)
        EDGE_BOXES[left].append(box_index)
        EDGE_BOXES[right].append(box_index)

EDGE_BOXES = tuple(tuple(x) for x in EDGE_BOXES)
BOX_MASKS = tuple(BOX_MASKS)


class _SearchTimeout(Exception):
    pass


def _edge_to_string(edge: int) -> str:
    if edge < 20:
        row, col = divmod(edge, 4)
        return f"{row},{col},H"
    row, col = divmod(edge - 20, 5)
    return f"{row},{col},V"


def _legal_edges(mask: int):
    empty = FULL_MASK ^ mask
    result = []
    while empty:
        bit = empty & -empty
        result.append(bit.bit_length() - 1)
        empty ^= bit
    return result


def _capture_count(mask: int, edge: int) -> int:
    count = 0
    for box in EDGE_BOXES[edge]:
        if (mask & BOX_MASKS[box]).bit_count() == 3:
            count += 1
    return count


def _risk_count(mask: int, edge: int) -> int:
    """Number of adjacent boxes changed from two sides to three sides."""
    count = 0
    for box in EDGE_BOXES[edge]:
        if (mask & BOX_MASKS[box]).bit_count() == 2:
            count += 1
    return count


def _classify_moves(mask: int):
    captures = []
    safe = []
    risky = []

    empty = FULL_MASK ^ mask
    while empty:
        bit = empty & -empty
        edge = bit.bit_length() - 1
        empty ^= bit

        captured = _capture_count(mask, edge)
        if captured:
            captures.append(edge)
        elif _risk_count(mask, edge) == 0:
            safe.append(edge)
        else:
            risky.append(edge)

    return captures, safe, risky


def _forced_gain_after_opening(mask: int, opening_edge: int) -> int:
    """
    Estimate how many boxes the next player can collect by greedily following
    all immediately available captures after an opening move.
    """
    work = mask | (1 << opening_edge)
    gain = 0

    while work != FULL_MASK:
        best_edge = -1
        best_capture = 0

        empty = FULL_MASK ^ work
        while empty:
            bit = empty & -empty
            edge = bit.bit_length() - 1
            empty ^= bit

            captured = _capture_count(work, edge)
            if captured > best_capture:
                best_capture = captured
                best_edge = edge
                if captured == 2:
                    break

        if best_edge < 0:
            break

        work |= 1 << best_edge
        gain += best_capture

    return gain


def _fallback_move(mask: int) -> int:
    """A fast, deterministic, and always-legal tactical fallback."""
    legal = _legal_edges(mask)
    if not legal:
        return -1

    captures, safe, risky = _classify_moves(mask)

    if captures:
        # Prefer a double capture, then prefer a move that leaves fewer
        # immediate captures available.
        best_edge = captures[0]
        best_key = None

        for edge in captures:
            new_mask = mask | (1 << edge)
            immediate = _capture_count(mask, edge)
            next_captures = 0

            empty = FULL_MASK ^ new_mask
            while empty:
                bit = empty & -empty
                nxt = bit.bit_length() - 1
                empty ^= bit
                if _capture_count(new_mask, nxt):
                    next_captures += 1

            key = (immediate, -next_captures)
            if best_key is None or key > best_key:
                best_key = key
                best_edge = edge

        return best_edge

    if safe:
        best_edge = safe[0]
        best_key = None

        for edge in safe:
            new_mask = mask | (1 << edge)
            _, remaining_safe, _ = _classify_moves(new_mask)
            safe_count = len(remaining_safe)

            two_sided = 0
            for box_mask in BOX_MASKS:
                if (new_mask & box_mask).bit_count() == 2:
                    two_sided += 1

            # With the opponent moving next, an even number of remaining safe
            # moves often gives us the last safe move.
            parity_bonus = 1 if safe_count % 2 == 0 else 0
            boundary_bonus = 1 if len(EDGE_BOXES[edge]) == 1 else 0
            key = (
                parity_bonus,
                safe_count - two_sided,
                boundary_bonus,
                -edge,
            )

            if best_key is None or key > best_key:
                best_key = key
                best_edge = edge

        return best_edge

    # Every move is a sacrifice. Open the smallest apparent chain.
    best_edge = risky[0] if risky else legal[0]
    best_cost = 100

    for edge in risky if risky else legal:
        cost = _forced_gain_after_opening(mask, edge)
        if cost < best_cost:
            best_cost = cost
            best_edge = edge

    return best_edge


def _ordered_exact_moves(mask: int):
    moves = _legal_edges(mask)

    def move_key(edge):
        captured = _capture_count(mask, edge)
        if captured:
            return (0, -captured, edge)

        risk = _risk_count(mask, edge)
        if risk == 0:
            return (1, 0, edge)

        return (2, risk, edge)

    moves.sort(key=move_key)
    return moves


def _exact_best_move(mask: int, deadline: float, fallback: int):
    """
    Exact minimax search.

    Values are measured as the future box differential for the player whose
    turn it is. A capture retains the turn; a non-capture negates the value
    because the opponent moves next.
    """
    transposition = {}
    nodes = [0]

    # TT flags
    EXACT = 0
    LOWER = 1
    UPPER = 2

    def search(state: int, alpha: int, beta: int) -> int:
        nodes[0] += 1
        if (nodes[0] & 255) == 0 and time.perf_counter() >= deadline:
            raise _SearchTimeout

        if state == FULL_MASK:
            return 0

        original_alpha = alpha
        original_beta = beta

        entry = transposition.get(state)
        if entry is not None:
            value, flag = entry
            if flag == EXACT:
                return value
            if flag == LOWER:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value

        best = -100

        for edge in _ordered_exact_moves(state):
            captured = _capture_count(state, edge)
            new_state = state | (1 << edge)

            if captured:
                value = captured + search(
                    new_state,
                    alpha - captured,
                    beta - captured,
                )
            else:
                value = -search(new_state, -beta, -alpha)

            if value > best:
                best = value
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        if best <= original_alpha:
            flag = UPPER
        elif best >= original_beta:
            flag = LOWER
        else:
            flag = EXACT

        transposition[state] = (best, flag)
        return best

    best_move = fallback
    best_value = -100
    alpha = -17
    completed_any = False

    for edge in _ordered_exact_moves(mask):
        if time.perf_counter() >= deadline:
            raise _SearchTimeout

        captured = _capture_count(mask, edge)
        new_mask = mask | (1 << edge)

        if captured:
            value = captured + search(
                new_mask,
                alpha - captured,
                17 - captured,
            )
        else:
            value = -search(new_mask, -17, -alpha)

        completed_any = True
        if value > best_value:
            best_value = value
            best_move = edge

        if value > alpha:
            alpha = value

    return best_move if completed_any else fallback


class _MCTSNode:
    __slots__ = (
        "mask",
        "player",
        "visits",
        "total",
        "untried",
        "children",
    )

    def __init__(self, mask: int, player: int):
        self.mask = mask
        self.player = player
        self.visits = 0
        self.total = 0.0
        self.untried = None
        self.children = []


def _strategic_tree_moves(mask: int):
    captures, safe, risky = _classify_moves(mask)

    if captures:
        # Captures are normally best. Risky moves are retained because they
        # include hard-hearted handouts and double-cross possibilities.
        return captures + risky

    if safe:
        # Giving away a box while a safe move exists is generally dominated.
        return safe

    return risky


def _rollout(mask: int, player: int, rng: random.Random) -> int:
    result = 0

    while mask != FULL_MASK:
        captures, safe, risky = _classify_moves(mask)

        if captures:
            best_capture = max(_capture_count(mask, edge) for edge in captures)
            candidates = [
                edge for edge in captures
                if _capture_count(mask, edge) == best_capture
            ]
            edge = candidates[rng.randrange(len(candidates))]
        elif safe:
            # Mostly use a random safe move to preserve rollout diversity,
            # with a mild preference for moves touching fewer two-sided boxes.
            if len(safe) <= 3 or rng.random() < 0.35:
                best_score = None
                candidates = []

                for candidate in safe:
                    new_mask = mask | (1 << candidate)
                    two_sided = sum(
                        1 for box_mask in BOX_MASKS
                        if (new_mask & box_mask).bit_count() == 2
                    )
                    score = -two_sided

                    if best_score is None or score > best_score:
                        best_score = score
                        candidates = [candidate]
                    elif score == best_score:
                        candidates.append(candidate)

                edge = candidates[rng.randrange(len(candidates))]
            else:
                edge = safe[rng.randrange(len(safe))]
        else:
            # Open the smallest estimated chain. Sampling a subset keeps
            # rollouts fast when many equivalent sacrifices remain.
            candidates = risky
            if len(candidates) > 8:
                candidates = rng.sample(candidates, 8)

            edge = candidates[0]
            best_cost = 100
            for candidate in candidates:
                cost = _forced_gain_after_opening(mask, candidate)
                if cost < best_cost:
                    best_cost = cost
                    edge = candidate

        captured = _capture_count(mask, edge)
        mask |= 1 << edge

        if captured:
            result += player * captured
        else:
            player = -player

    return result


def _mcts_best_move(
    mask: int,
    deadline: float,
    fallback: int,
    seed: int,
) -> int:
    rng = random.Random(seed)
    root = _MCTSNode(mask, 1)

    while time.perf_counter() < deadline:
        node = root
        path = [root]
        current_mask = mask
        current_player = 1
        accrued = 0

        # Selection and expansion.
        while current_mask != FULL_MASK:
            if node.untried is None:
                node.untried = _strategic_tree_moves(current_mask)
                rng.shuffle(node.untried)

            if node.untried:
                edge = node.untried.pop()
                captured = _capture_count(current_mask, edge)
                current_mask |= 1 << edge

                if captured:
                    accrued += current_player * captured
                    next_player = current_player
                else:
                    next_player = -current_player

                child = _MCTSNode(current_mask, next_player)
                node.children.append((edge, child))
                node = child
                current_player = next_player
                path.append(node)
                break

            if not node.children:
                break

            log_parent = math.log(node.visits + 1.0)
            best_child = None
            best_score = -1e100

            for edge, child in node.children:
                if child.visits == 0:
                    score = 1e50
                else:
                    mean = child.total / child.visits
                    score = (
                        current_player * mean
                        + 1.20 * math.sqrt(log_parent / child.visits)
                    )

                if score > best_score:
                    best_score = score
                    best_child = (edge, child)

            edge, child = best_child
            captured = _capture_count(current_mask, edge)
            current_mask |= 1 << edge

            if captured:
                accrued += current_player * captured
            else:
                current_player = -current_player

            node = child
            path.append(node)

        result = accrued + _rollout(current_mask, current_player, rng)

        for visited in path:
            visited.visits += 1
            visited.total += result

    if not root.children:
        return fallback

    best_move = fallback
    best_key = None

    for edge, child in root.children:
        if child.visits == 0:
            continue

        mean = child.total / child.visits
        key = (mean, child.visits)

        if best_key is None or key > best_key:
            best_key = key
            best_move = edge

    return best_move


def policy(
    horizontal: np.ndarray,
    vertical: np.ndarray,
    capture: np.ndarray,
) -> str:
    start = time.perf_counter()

    # Build the standard 40-edge occupancy mask. The unused fifth column of
    # horizontal and fifth row of vertical are intentionally ignored.
    mask = 0

    for row in range(5):
        for col in range(4):
            if int(horizontal[row, col]) != 0:
                mask |= 1 << (row * 4 + col)

    for row in range(4):
        for col in range(5):
            if int(vertical[row, col]) != 0:
                mask |= 1 << (20 + row * 5 + col)

    legal = _legal_edges(mask)

    # A policy should not normally be called after the game has ended. This
    # defensive branch attempts to return an array-empty entry if it is.
    if not legal:
        for row in range(5):
            for col in range(5):
                if int(horizontal[row, col]) == 0:
                    return f"{row},{col},H"
                if int(vertical[row, col]) == 0:
                    return f"{row},{col},V"
        return "0,0,H"

    if len(legal) == 1:
        return _edge_to_string(legal[0])

    fallback = _fallback_move(mask)
    chosen = fallback

    try:
        captures, safe, risky = _classify_moves(mask)
        no_safe_move = len(safe) == 0
        empty_count = len(legal)

        # Exact search is most effective once the board is small or has
        # entered the forced-chain phase.
        if empty_count <= 21 or no_safe_move:
            try:
                chosen = _exact_best_move(
                    mask,
                    start + 0.90,
                    fallback,
                )
            except _SearchTimeout:
                chosen = fallback
        else:
            capture_seed = 0
            for row in range(4):
                for col in range(4):
                    value = int(capture[row, col])
                    if value > 0:
                        capture_seed ^= 1 << (row * 4 + col)
                    elif value < 0:
                        capture_seed ^= 1 << (16 + row * 4 + col)

            chosen = _mcts_best_move(
                mask,
                start + 0.90,
                fallback,
                mask ^ capture_seed ^ 0x9E3779B9,
            )

    except Exception:
        chosen = fallback

    # Final legality guard.
    if chosen < 0 or chosen >= NUM_EDGES or (mask & (1 << chosen)):
        chosen = legal[0]

    return _edge_to_string(chosen)
