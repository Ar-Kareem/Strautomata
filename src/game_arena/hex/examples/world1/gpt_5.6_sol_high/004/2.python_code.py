
from __future__ import annotations

from collections import deque
import math
import random
import time


SIZE = 11
CELLS = SIZE * SIZE
INF = 10 ** 6

# Hex neighbors:
# (-1, 0), (-1, +1), (0, -1), (0, +1), (+1, -1), (+1, 0)
NEIGHBORS = []
for r in range(SIZE):
    for c in range(SIZE):
        ns = []
        for dr, dc in ((-1, 0), (-1, 1), (0, -1),
                       (0, 1), (1, -1), (1, 0)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                ns.append(nr * SIZE + nc)
        NEIGHBORS.append(tuple(ns))


def _win_from(board: bytearray, player: int, start: int) -> bool:
    """Check whether the component containing start connects player's sides."""
    if board[start] != player:
        return False

    seen = {start}
    stack = [start]

    if player == 1:  # Black: top to bottom
        side_a = start // SIZE == 0
        side_b = start // SIZE == SIZE - 1
    else:  # White: left to right
        side_a = start % SIZE == 0
        side_b = start % SIZE == SIZE - 1

    while stack:
        cell = stack.pop()
        for nxt in NEIGHBORS[cell]:
            if board[nxt] == player and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)

                if player == 1:
                    row = nxt // SIZE
                    if row == 0:
                        side_a = True
                    elif row == SIZE - 1:
                        side_b = True
                else:
                    col = nxt % SIZE
                    if col == 0:
                        side_a = True
                    elif col == SIZE - 1:
                        side_b = True

                if side_a and side_b:
                    return True

    return side_a and side_b


def _has_won(board: bytearray, player: int) -> bool:
    """Full connectivity check."""
    seen = bytearray(CELLS)
    queue = deque()

    if player == 1:
        for c in range(SIZE):
            idx = c
            if board[idx] == player:
                seen[idx] = 1
                queue.append(idx)

        while queue:
            cell = queue.popleft()
            if cell // SIZE == SIZE - 1:
                return True
            for nxt in NEIGHBORS[cell]:
                if board[nxt] == player and not seen[nxt]:
                    seen[nxt] = 1
                    queue.append(nxt)
    else:
        for r in range(SIZE):
            idx = r * SIZE
            if board[idx] == player:
                seen[idx] = 1
                queue.append(idx)

        while queue:
            cell = queue.popleft()
            if cell % SIZE == SIZE - 1:
                return True
            for nxt in NEIGHBORS[cell]:
                if board[nxt] == player and not seen[nxt]:
                    seen[nxt] = 1
                    queue.append(nxt)

    return False


def _connection_distance(board: bytearray, player: int) -> int:
    """
    Minimum number of empty cells needed to connect player's two sides.
    Own stones cost 0, empty cells cost 1, opponent cells are blocked.
    """
    other = 3 - player
    dist = [INF] * CELLS
    queue = deque()

    if player == 1:
        sources = range(SIZE)
    else:
        sources = range(0, CELLS, SIZE)

    for cell in sources:
        if board[cell] == other:
            continue
        cost = 0 if board[cell] == player else 1
        if cost < dist[cell]:
            dist[cell] = cost
            if cost == 0:
                queue.appendleft(cell)
            else:
                queue.append(cell)

    while queue:
        cell = queue.popleft()
        base = dist[cell]

        for nxt in NEIGHBORS[cell]:
            value = board[nxt]
            if value == other:
                continue

            step = 0 if value == player else 1
            nd = base + step
            if nd < dist[nxt]:
                dist[nxt] = nd
                if step == 0:
                    queue.appendleft(nxt)
                else:
                    queue.append(nxt)

    if player == 1:
        result = min(dist[(SIZE - 1) * SIZE + c] for c in range(SIZE))
    else:
        result = min(dist[r * SIZE + SIZE - 1] for r in range(SIZE))

    return result


def _winning_moves(board: bytearray, player: int, empties: list[int]) -> list[int]:
    result = []
    for cell in empties:
        board[cell] = player
        if _win_from(board, player, cell):
            result.append(cell)
        board[cell] = 0
    return result


def _make_priorities(board: bytearray, player: int, empties: list[int]) -> list[float]:
    """
    Score moves by their effect on both shortest connection distances, local
    support, blocking value, and mild central preference.
    """
    other = 3 - player
    base_self = min(_connection_distance(board, player), 20)
    base_other = min(_connection_distance(board, other), 20)

    raw = [-1000.0] * CELLS

    for cell in empties:
        board[cell] = player
        d_self = min(_connection_distance(board, player), 20)
        d_other = min(_connection_distance(board, other), 20)
        board[cell] = 0

        own_adj = 0
        opp_adj = 0
        for nxt in NEIGHBORS[cell]:
            if board[nxt] == player:
                own_adj += 1
            elif board[nxt] == other:
                opp_adj += 1

        r, c = divmod(cell, SIZE)
        center_penalty = abs(r - 5) + abs(c - 5)

        # Improvement in own connection and damage to the opponent dominate.
        score = (
            7.0 * (base_self - d_self)
            + 6.2 * (d_other - base_other)
            - 0.72 * d_self
            + 0.50 * d_other
            + 0.24 * own_adj
            + 0.11 * opp_adj
            - 0.018 * center_penalty
        )

        # Slight encouragement toward the relevant axis without forcing a
        # rigid straight line.
        if player == 1:
            score -= 0.006 * abs(c - 5)
        else:
            score -= 0.006 * abs(r - 5)

        raw[cell] = score

    if not empties:
        return [0.0] * CELLS

    lo = min(raw[cell] for cell in empties)
    hi = max(raw[cell] for cell in empties)
    span = hi - lo

    normalized = [0.0] * CELLS
    if span < 1e-9:
        for cell in empties:
            normalized[cell] = 0.5
    else:
        for cell in empties:
            normalized[cell] = (raw[cell] - lo) / span

    return normalized


def _bridge_saves(board: bytearray, player: int, stones: list[int]) -> set[int]:
    """
    Find the remaining connector of a virtual bridge when the opponent has
    occupied the other connector.
    """
    result = set()
    other = 3 - player
    neighbor_sets = {s: set(NEIGHBORS[s]) for s in stones}

    for i in range(len(stones)):
        a = stones[i]
        na = neighbor_sets[a]
        for j in range(i + 1, len(stones)):
            b = stones[j]

            # Adjacent stones do not form the two-cell virtual bridge pattern.
            if b in na:
                continue

            common = na.intersection(neighbor_sets[b])
            if len(common) != 2:
                continue

            x, y = tuple(common)
            if board[x] == other and board[y] == 0:
                result.add(y)
            elif board[y] == other and board[x] == 0:
                result.add(x)

    return result


class _Node:
    __slots__ = (
        "to_move", "player_just_moved", "move", "parent",
        "children", "untried", "visits", "wins", "amaf", "terminal"
    )

    def __init__(
        self,
        to_move: int,
        player_just_moved: int,
        move: int | None,
        parent: "_Node | None",
        untried: list[int],
        terminal: int = 0,
    ):
        self.to_move = to_move
        self.player_just_moved = player_just_moved
        self.move = move
        self.parent = parent
        self.children: dict[int, _Node] = {}
        self.untried = untried
        self.visits = 0
        self.wins = 0.0
        self.amaf: dict[int, list[float]] = {}
        self.terminal = terminal


def _select_child(node: _Node, priors: list[list[float]]) -> _Node:
    """UCT selection blended with RAVE/AMAF information."""
    log_parent = math.log(node.visits + 1.0)
    best_child = None
    best_score = -1e100

    for move, child in node.children.items():
        n = child.visits
        if n == 0:
            return child

        direct_q = child.wins / n
        amaf_data = node.amaf.get(move)

        if amaf_data is not None and amaf_data[1] > 0:
            rave_wins, rave_n = amaf_data
            rave_q = rave_wins / rave_n
            beta = rave_n / (rave_n + n + (4.0 * rave_n * n / 300.0))
            value = (1.0 - beta) * direct_q + beta * rave_q
        else:
            value = direct_q

        exploration = 0.72 * math.sqrt(log_parent / n)
        progressive_bias = 0.16 * priors[node.to_move][move] / (n + 1.0)
        score = value + exploration + progressive_bias

        if score > best_score:
            best_score = score
            best_child = child

    return best_child


def _rollout(
    board: bytearray,
    to_move: int,
    priors: list[list[float]],
    rng: random.Random,
) -> tuple[int, list[tuple[int, int]]]:
    """
    Biased stochastic rollout. At each turn several random legal moves are
    sampled, then the most promising one is chosen.
    """
    empties = [cell for cell in range(CELLS) if board[cell] == 0]
    sequence: list[tuple[int, int]] = []
    player = to_move

    while empties:
        length = len(empties)
        samples = 5 if length >= 5 else length
        best_pos = 0
        best_score = -1e100

        for _ in range(samples):
            pos = rng.randrange(length)
            cell = empties[pos]

            own_adj = 0
            opp_adj = 0
            for nxt in NEIGHBORS[cell]:
                if board[nxt] == player:
                    own_adj += 1
                elif board[nxt] == 3 - player:
                    opp_adj += 1

            score = (
                1.15 * priors[player][cell]
                + 0.43 * own_adj
                + 0.12 * opp_adj
                + 0.75 * rng.random()
            )

            if score > best_score:
                best_score = score
                best_pos = pos

        cell = empties[best_pos]
        empties[best_pos] = empties[-1]
        empties.pop()

        board[cell] = player
        sequence.append((cell, player))
        player = 3 - player

    winner = 1 if _has_won(board, 1) else 2
    return winner, sequence


def _mcts(
    initial_board: bytearray,
    my_player: int,
    root_moves: list[int],
    priors: list[list[float]],
    rng: random.Random,
    deadline: float,
) -> int:
    root_untried = sorted(
        root_moves,
        key=lambda cell: priors[my_player][cell] + 0.02 * rng.random()
    )
    root = _Node(
        to_move=my_player,
        player_just_moved=3 - my_player,
        move=None,
        parent=None,
        untried=root_untried,
    )

    iterations = 0

    while time.perf_counter() < deadline:
        board = bytearray(initial_board)
        node = root
        path = [root]
        full_sequence: list[tuple[int, int]] = []
        winner = 0

        # Selection.
        while not node.terminal and not node.untried and node.children:
            child = _select_child(node, priors)
            board[child.move] = node.to_move
            full_sequence.append((child.move, node.to_move))
            node = child
            path.append(node)

        if node.terminal:
            winner = node.terminal

        # Expansion.
        elif node.untried:
            move = node.untried.pop()
            player = node.to_move
            board[move] = player
            full_sequence.append((move, player))

            terminal = player if _win_from(board, player, move) else 0
            remaining = [cell for cell in range(CELLS) if board[cell] == 0]
            rng.shuffle(remaining)

            child = _Node(
                to_move=3 - player,
                player_just_moved=player,
                move=move,
                parent=node,
                untried=remaining if not terminal else [],
                terminal=terminal,
            )
            node.children[move] = child
            node = child
            path.append(node)

            if terminal:
                winner = terminal

        # Simulation.
        if winner == 0:
            winner, rollout_sequence = _rollout(
                board, node.to_move, priors, rng
            )
            full_sequence.extend(rollout_sequence)

        # Standard and AMAF/RAVE backpropagation.
        for depth, visited_node in enumerate(path):
            visited_node.visits += 1
            if winner == visited_node.player_just_moved:
                visited_node.wins += 1.0

            current_player = visited_node.to_move
            result = 1.0 if winner == current_player else 0.0

            # Each board cell appears at most once, so no duplicate-action
            # filtering is required.
            for move, player in full_sequence[depth:]:
                if player == current_player:
                    data = visited_node.amaf.get(move)
                    if data is None:
                        visited_node.amaf[move] = [result, 1.0]
                    else:
                        data[0] += result
                        data[1] += 1.0

        iterations += 1

    if not root.children:
        return root_moves[0]

    # Robust-child decision, with win rate and prior as tie breakers.
    best = max(
        root.children.values(),
        key=lambda child: (
            child.visits,
            child.wins / child.visits if child.visits else 0.0,
            priors[my_player][child.move],
        ),
    )
    return best.move


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[int, int]:
    start_time = time.perf_counter()

    my_player = 1 if color == "b" else 2
    opp_player = 3 - my_player

    board = bytearray(CELLS)
    my_stones = []
    opp_stones = []

    for r, c in me:
        if 0 <= r < SIZE and 0 <= c < SIZE:
            idx = r * SIZE + c
            board[idx] = my_player
            my_stones.append(idx)

    for r, c in opp:
        if 0 <= r < SIZE and 0 <= c < SIZE:
            idx = r * SIZE + c
            board[idx] = opp_player
            opp_stones.append(idx)

    empties = [cell for cell in range(CELLS) if board[cell] == 0]

    # Valid game states always have at least one legal move. This defensive
    # branch preserves the function's return type for malformed input.
    if not empties:
        return (0, 0)

    if len(empties) == CELLS:
        return (5, 5)

    # Exact immediate win.
    my_wins = _winning_moves(board, my_player, empties)
    if my_wins:
        move = my_wins[0]
        return divmod(move, SIZE)

    # Compute strategic move priors for both colors.
    my_prior = _make_priorities(board, my_player, empties)
    opp_prior = _make_priorities(board, opp_player, empties)
    priors = [[0.0] * CELLS, [0.0] * CELLS, [0.0] * CELLS]
    priors[my_player] = my_prior
    priors[opp_player] = opp_prior

    # Exact forced block.
    opp_wins = _winning_moves(board, opp_player, empties)
    if opp_wins:
        move = max(opp_wins, key=lambda cell: my_prior[cell])
        return divmod(move, SIZE)

    # Preserve threatened virtual bridges.
    bridge_moves = _bridge_saves(board, my_player, my_stones)

    # Detect mathematically forced double threats in manageable late positions.
    if len(empties) <= 34:
        ordered = sorted(empties, key=lambda x: my_prior[x], reverse=True)

        own_forks = []
        for first in ordered:
            board[first] = my_player
            remaining = [x for x in empties if x != first]
            count = 0
            for second in remaining:
                board[second] = my_player
                if _win_from(board, my_player, second):
                    count += 1
                board[second] = 0
                if count >= 2:
                    own_forks.append(first)
                    break
            board[first] = 0

        if own_forks:
            move = max(own_forks, key=lambda x: my_prior[x])
            return divmod(move, SIZE)

        opponent_forks = []
        opp_ordered = sorted(empties, key=lambda x: opp_prior[x], reverse=True)

        for first in opp_ordered:
            board[first] = opp_player
            remaining = [x for x in empties if x != first]
            count = 0
            for second in remaining:
                board[second] = opp_player
                if _win_from(board, opp_player, second):
                    count += 1
                board[second] = 0
                if count >= 2:
                    opponent_forks.append(first)
                    break
            board[first] = 0

        if opponent_forks:
            move = max(
                opponent_forks,
                key=lambda x: my_prior[x] + 0.4 * opp_prior[x]
            )
            return divmod(move, SIZE)

    # Strategic root ordering, including a large bonus for bridge repair.
    strategic_score = {
        cell: my_prior[cell] + (1.8 if cell in bridge_moves else 0.0)
        for cell in empties
    }
    ranked = sorted(empties, key=lambda x: strategic_score[x], reverse=True)

    # Restrict only the root branching factor. All replies below the root
    # remain legal candidates, while tactical checks above considered every
    # empty cell.
    if len(empties) > 70:
        root_count = 38
    elif len(empties) > 45:
        root_count = 36
    elif len(empties) > 28:
        root_count = 32
    else:
        root_count = len(empties)

    root_moves = ranked[:root_count]

    # Ensure all bridge-defense moves are represented.
    for cell in bridge_moves:
        if cell not in root_moves:
            if len(root_moves) >= root_count and root_moves:
                root_moves[-1] = cell
            else:
                root_moves.append(cell)

    # Deterministic state-dependent RNG seed.
    seed = 1469598103934665603
    for cell in my_stones:
        seed ^= (cell + 1) * 1099511628211
        seed &= (1 << 64) - 1
    for cell in opp_stones:
        seed ^= (cell + 137) * 14029467366897019727
        seed &= (1 << 64) - 1
    seed ^= my_player * 0x9E3779B97F4A7C15
    rng = random.Random(seed)

    deadline = start_time + 0.88
    move = _mcts(
        board,
        my_player,
        root_moves,
        priors,
        rng,
        deadline,
    )

    # Absolute legality safeguard.
    if not (0 <= move < CELLS) or board[move] != 0:
        move = ranked[0] if ranked else empties[0]

    return divmod(move, SIZE)
