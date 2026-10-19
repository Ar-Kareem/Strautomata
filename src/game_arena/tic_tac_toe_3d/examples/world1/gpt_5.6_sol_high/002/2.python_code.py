
import time
from typing import Optional


# ---------------------------------------------------------------------------
# Board geometry
# ---------------------------------------------------------------------------

FULL_MASK = (1 << 27) - 1
CENTER = 13
WIN_SCORE = 100_000
MAX_STATIC = 5_000

EXACT = 0
LOWER = 1
UPPER = 2


def _cell_index(i: int, j: int, k: int) -> int:
    return (i * 3 + j) * 3 + k


def _coordinates(index: int) -> tuple[int, int, int]:
    return index // 9, (index // 3) % 3, index % 3


def _make_lines() -> tuple[int, ...]:
    lines: set[int] = set()

    for i in range(3):
        for j in range(3):
            for k in range(3):
                for di in (-1, 0, 1):
                    for dj in (-1, 0, 1):
                        for dk in (-1, 0, 1):
                            if di == 0 and dj == 0 and dk == 0:
                                continue

                            # Keep one orientation for each direction.
                            direction = (di, dj, dk)
                            first_nonzero = next(x for x in direction if x != 0)
                            if first_nonzero < 0:
                                continue

                            ei = i + 2 * di
                            ej = j + 2 * dj
                            ek = k + 2 * dk
                            if not (0 <= ei < 3 and
                                    0 <= ej < 3 and
                                    0 <= ek < 3):
                                continue

                            mask = 0
                            for t in range(3):
                                index = _cell_index(
                                    i + t * di,
                                    j + t * dj,
                                    k + t * dk,
                                )
                                mask |= 1 << index
                            lines.add(mask)

    return tuple(sorted(lines))


LINES = _make_lines()

_cell_lines_list: list[list[int]] = [[] for _ in range(27)]
for _line in LINES:
    for _index in range(27):
        if _line & (1 << _index):
            _cell_lines_list[_index].append(_line)

CELL_LINES = tuple(tuple(x) for x in _cell_lines_list)
CELL_WEIGHT = tuple(len(CELL_LINES[i]) for i in range(27))


# ---------------------------------------------------------------------------
# Persistent search information
# ---------------------------------------------------------------------------

# Entry: depth, extension budget, value, bound type, best move bit
_TT: dict[int, tuple[int, int, int, int, int]] = {}
_HISTORY = [0] * 27
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


# ---------------------------------------------------------------------------
# Tactical bitboard operations
# ---------------------------------------------------------------------------

def _threats(player: int, opponent: int) -> int:
    """Empty cells on which player can win immediately."""
    result = 0
    occupied = player | opponent

    for line in LINES:
        if line & opponent:
            continue
        if (line & player).bit_count() == 2:
            result |= line & ~occupied

    return result


def _created_threats(player: int, opponent: int, move: int) -> int:
    """
    Immediate winning cells created by placing move.

    At normal search nodes player has no pre-existing immediate threat, so
    only lines through move need examination.
    """
    index = move.bit_length() - 1
    new_player = player | move
    occupied = new_player | opponent
    result = 0

    for line in CELL_LINES[index]:
        if line & opponent:
            continue
        if (line & new_player).bit_count() == 2:
            result |= line & ~occupied

    return result


def _store_tt(
    key: int,
    depth: int,
    extensions: int,
    value: int,
    flag: int,
    best_move: int,
) -> None:
    old = _TT.get(key)
    if old is None:
        _TT[key] = (depth, extensions, value, flag, best_move)
        return

    old_depth, old_ext, _, old_flag, _ = old
    if (depth > old_depth or
            (depth == old_depth and extensions >= old_ext) or
            (flag == EXACT and old_flag != EXACT)):
        _TT[key] = (depth, extensions, value, flag, best_move)


# ---------------------------------------------------------------------------
# Evaluation and ordering
# ---------------------------------------------------------------------------

def _static_evaluation(player: int, opponent: int) -> int:
    """Evaluation from the side-to-move player's perspective."""
    score = 0
    line_value = (0, 2, 13, 90)

    for line in LINES:
        p_count = (line & player).bit_count()
        o_count = (line & opponent).bit_count()

        if o_count == 0:
            score += line_value[p_count]
        if p_count == 0:
            score -= line_value[o_count]

    p_bits = player
    while p_bits:
        bit = p_bits & -p_bits
        score += CELL_WEIGHT[bit.bit_length() - 1]
        p_bits ^= bit

    o_bits = opponent
    while o_bits:
        bit = o_bits & -o_bits
        score -= CELL_WEIGHT[bit.bit_length() - 1]
        o_bits ^= bit

    empty = FULL_MASK & ~(player | opponent)
    player_single_threat_moves = 0
    opponent_single_threat_moves = 0
    opponent_fork_moves = 0

    bits = empty
    while bits:
        move = bits & -bits
        bits ^= move

        p_created = _created_threats(player, opponent, move).bit_count()
        o_created = _created_threats(opponent, player, move).bit_count()

        if p_created == 1:
            player_single_threat_moves += 1
        if o_created == 1:
            opponent_single_threat_moves += 1
        elif o_created >= 2:
            opponent_fork_moves += 1

    score += 7 * (
        player_single_threat_moves - opponent_single_threat_moves
    )
    score -= 55 * opponent_fork_moves
    score += 3  # Small initiative bonus for the side to move.

    if score > MAX_STATIC:
        return MAX_STATIC
    if score < -MAX_STATIC:
        return -MAX_STATIC
    return score


def _ordered_moves(
    player: int,
    opponent: int,
    empty: int,
    tt_move: int,
) -> list[tuple[int, int, int, int]]:
    """
    Return tuples of:
        ordering score, move bit, created own threats, blocked fork strength
    """
    result: list[tuple[int, int, int, int]] = []
    bits = empty

    while bits:
        move = bits & -bits
        bits ^= move
        index = move.bit_length() - 1

        own_count = _created_threats(
            player, opponent, move
        ).bit_count()
        opponent_count = _created_threats(
            opponent, player, move
        ).bit_count()

        order_score = (
            own_count * 3200
            + opponent_count * 220
            + (2200 if opponent_count >= 2 else 0)
            + CELL_WEIGHT[index] * 24
            + _HISTORY[index]
        )

        if move == tt_move:
            order_score += 1_000_000

        result.append((order_score, move, own_count, opponent_count))

    result.sort(reverse=True)
    return result


def _fallback_move(player: int, opponent: int, empty: int) -> int:
    """Fast deterministic legal move used before and after search."""
    best_move = empty & -empty
    best_score = -10**9

    bits = empty
    while bits:
        move = bits & -bits
        bits ^= move
        index = move.bit_length() - 1

        own_count = _created_threats(
            player, opponent, move
        ).bit_count()
        opponent_count = _created_threats(
            opponent, player, move
        ).bit_count()

        score = (
            own_count * 5000
            + opponent_count * 500
            + (3000 if opponent_count >= 2 else 0)
            + CELL_WEIGHT[index] * 30
            - index
        )

        if score > best_score:
            best_score = score
            best_move = move

    return best_move


# ---------------------------------------------------------------------------
# Negamax search
# ---------------------------------------------------------------------------

def _search(
    player: int,
    opponent: int,
    depth: int,
    alpha: int,
    beta: int,
    extensions: int,
) -> int:
    global _NODES

    _NODES += 1
    if (_NODES & 511) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout

    key = player | (opponent << 27)
    entry = _TT.get(key)
    tt_move = 0

    if entry is not None:
        entry_depth, entry_ext, entry_value, entry_flag, tt_move = entry
        sufficient = (
            entry_depth > depth
            or (entry_depth == depth and entry_ext >= extensions)
        )

        if sufficient:
            if entry_flag == EXACT:
                return entry_value
            if entry_flag == LOWER:
                if entry_value > alpha:
                    alpha = entry_value
            else:
                if entry_value < beta:
                    beta = entry_value

            if alpha >= beta:
                return entry_value

    window_alpha = alpha
    window_beta = beta

    own_wins = _threats(player, opponent)
    if own_wins:
        return WIN_SCORE

    opponent_wins = _threats(opponent, player)
    opponent_win_count = opponent_wins.bit_count()

    if opponent_win_count >= 2:
        return -WIN_SCORE

    empty = FULL_MASK & ~(player | opponent)
    if empty == 0:
        return 0

    # A single enemy threat makes the blocking move compulsory.
    if opponent_win_count == 1:
        move = opponent_wins & -opponent_wins

        if depth > 0:
            value = -_search(
                opponent,
                player | move,
                depth - 1,
                -beta,
                -alpha,
                extensions,
            )
        elif extensions > 0:
            value = -_search(
                opponent,
                player | move,
                0,
                -beta,
                -alpha,
                extensions - 1,
            )
        else:
            value = -_static_evaluation(opponent, player | move)

        if value <= window_alpha:
            flag = UPPER
        elif value >= window_beta:
            flag = LOWER
        else:
            flag = EXACT

        _store_tt(key, depth, extensions, value, flag, move)
        return value

    moves = _ordered_moves(player, opponent, empty, tt_move)

    # A move making two distinct threats is a proven forced win.
    for _, move, own_count, _ in moves:
        if own_count >= 2:
            _store_tt(key, 99, 99, WIN_SCORE, EXACT, move)
            return WIN_SCORE

    if depth <= 0:
        value = _static_evaluation(player, opponent)
        _store_tt(key, 0, extensions, value, EXACT, 0)
        return value

    best_value = -WIN_SCORE
    best_move = moves[0][1]
    first_move = True

    for _, move, _, _ in moves:
        if first_move:
            value = -_search(
                opponent,
                player | move,
                depth - 1,
                -beta,
                -alpha,
                extensions,
            )
            first_move = False
        else:
            # Principal variation search.
            value = -_search(
                opponent,
                player | move,
                depth - 1,
                -alpha - 1,
                -alpha,
                extensions,
            )

            if alpha < value < beta:
                value = -_search(
                    opponent,
                    player | move,
                    depth - 1,
                    -beta,
                    -alpha,
                    extensions,
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            index = move.bit_length() - 1
            _HISTORY[index] += depth * depth
            break

    if best_value <= window_alpha:
        flag = UPPER
    elif best_value >= window_beta:
        flag = LOWER
    else:
        flag = EXACT

    _store_tt(
        key,
        depth,
        extensions,
        best_value,
        flag,
        best_move,
    )
    return best_value


# ---------------------------------------------------------------------------
# Required API
# ---------------------------------------------------------------------------

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global _DEADLINE, _NODES

    start = time.perf_counter()
    _DEADLINE = start + 0.90
    _NODES = 0

    player = 0
    opponent = 0

    for i in range(3):
        for j in range(3):
            for k in range(3):
                value = board[i][j][k]
                bit = 1 << _cell_index(i, j, k)
                if value == 1:
                    player |= bit
                elif value == -1:
                    opponent |= bit

    empty = FULL_MASK & ~(player | opponent)

    # A full board should never be passed to a move policy.
    if empty == 0:
        return 0, 0, 0

    # Prevent unbounded persistent-cache growth across many arena games.
    if len(_TT) > 350_000:
        _TT.clear()

    # Always establish a legal answer before doing any expensive work.
    chosen = _fallback_move(player, opponent, empty)

    # Immediate win.
    wins = _threats(player, opponent)
    if wins:
        chosen = wins & -wins
        return _coordinates(chosen.bit_length() - 1)

    # Mandatory block, or best practical block in an already lost position.
    enemy_wins = _threats(opponent, player)
    enemy_win_count = enemy_wins.bit_count()

    if enemy_win_count == 1:
        chosen = enemy_wins & -enemy_wins
        return _coordinates(chosen.bit_length() - 1)

    if enemy_win_count >= 2:
        candidates = enemy_wins & empty
        chosen = _fallback_move(player, opponent, candidates)
        return _coordinates(chosen.bit_length() - 1)

    occupied_count = (player | opponent).bit_count()

    # Symmetric opening choices avoid spending most of the budget proving
    # equivalent early-game positions.
    if occupied_count == 0:
        return 1, 1, 1

    if occupied_count == 1:
        center_bit = 1 << CENTER
        if empty & center_bit:
            return 1, 1, 1

    # Direct fork: two distinct threats guarantee a win.
    best_fork = 0
    best_fork_score = -1
    bits = empty
    while bits:
        move = bits & -bits
        bits ^= move
        threat_count = _created_threats(
            player, opponent, move
        ).bit_count()

        if threat_count >= 2:
            index = move.bit_length() - 1
            fork_score = threat_count * 100 + CELL_WEIGHT[index]
            if fork_score > best_fork_score:
                best_fork_score = fork_score
                best_fork = move

    if best_fork:
        return _coordinates(best_fork.bit_length() - 1)

    # Iterative deepening preserves the last fully searched legal move.
    root_key = player | (opponent << 27)
    remaining = empty.bit_count()

    try:
        for depth in range(1, remaining + 1):
            if time.perf_counter() >= _DEADLINE:
                break

            value = _search(
                player,
                opponent,
                depth,
                -WIN_SCORE,
                WIN_SCORE,
                6,
            )

            root_entry = _TT.get(root_key)
            if root_entry is not None:
                candidate = root_entry[4]
                if candidate and (candidate & empty):
                    chosen = candidate

            # These values are tactical proofs rather than heuristic scores.
            if value == WIN_SCORE or value == -WIN_SCORE:
                break

    except _SearchTimeout:
        pass

    # Final validation guarantees that a stale cache entry cannot leak an
    # occupied move.
    if chosen == 0 or not (chosen & empty):
        chosen = empty & -empty

    return _coordinates(chosen.bit_length() - 1)
