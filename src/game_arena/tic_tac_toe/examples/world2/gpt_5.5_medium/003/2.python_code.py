
import time

# 4x4 Tic Tac Toe policy
# Board values:
#   0  = empty
#   1  = us
#  -1  = opponent

N = 4
WIN_SCORE = 100000
INF = 10 ** 9

# Winning lines for 4-in-a-row on a 4x4 board.
_LINES = (
    (0, 1, 2, 3),
    (4, 5, 6, 7),
    (8, 9, 10, 11),
    (12, 13, 14, 15),
    (0, 4, 8, 12),
    (1, 5, 9, 13),
    (2, 6, 10, 14),
    (3, 7, 11, 15),
    (0, 5, 10, 15),
    (3, 6, 9, 12),
)

_CELL_LINES = [[] for _ in range(16)]
for line in _LINES:
    for idx in line:
        _CELL_LINES[idx].append(line)
_CELL_LINES = tuple(tuple(x) for x in _CELL_LINES)

# Center cells are strongest on a 4x4 board.
_POSITION_SCORE = (
    4, 5, 5, 4,
    5, 8, 8, 5,
    5, 8, 8, 5,
    4, 5, 5, 4,
)

_PREFERRED = (5, 10, 6, 9, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14)

# Transposition table.
# key: (position_tuple, player_to_move, depth)
# value: (score, flag)
_EXACT, _LOWER, _UPPER = 0, 1, 2
_TT = {}

_deadline = 0.0
_nodes = 0


class _Timeout(Exception):
    pass


def _to_tuple(board):
    """Convert board to a flat immutable tuple."""
    out = []
    for r in range(4):
        for c in range(4):
            try:
                v = board[r][c]
            except Exception:
                v = 0
            if v == 1:
                out.append(1)
            elif v == -1:
                out.append(-1)
            else:
                out.append(0)
    return tuple(out)


def _first_legal(pos):
    for i, v in enumerate(pos):
        if v == 0:
            return divmod(i, 4)
    # Should never be needed in a valid game state.
    return (0, 0)


def _winner(pos):
    for line in _LINES:
        s = pos[line[0]] + pos[line[1]] + pos[line[2]] + pos[line[3]]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def _would_win(pos, idx, player):
    """True if player wins immediately by playing idx."""
    if pos[idx] != 0:
        return False
    for line in _CELL_LINES[idx]:
        ok = True
        for j in line:
            if j != idx and pos[j] != player:
                ok = False
                break
        if ok:
            return True
    return False


def _winning_moves(pos, player):
    return [i for i, v in enumerate(pos) if v == 0 and _would_win(pos, i, player)]


def _play(pos, idx, player):
    return pos[:idx] + (player,) + pos[idx + 1:]


def _check_time():
    global _nodes
    _nodes += 1
    # Checking every 1024 nodes keeps the overhead low.
    if (_nodes & 1023) == 0 and time.perf_counter() > _deadline:
        raise _Timeout()


def _evaluate(pos):
    """Static evaluation from our perspective, where we are player 1."""
    win = _winner(pos)
    if win == 1:
        return WIN_SCORE + pos.count(0)
    if win == -1:
        return -WIN_SCORE - pos.count(0)

    score = 0

    # Positional control.
    for i, v in enumerate(pos):
        if v == 1:
            score += _POSITION_SCORE[i]
        elif v == -1:
            score -= _POSITION_SCORE[i]

    # Line potential.
    # Open 3-in-a-row is highly important because it creates an immediate threat.
    line_score = (0, 4, 35, 900, WIN_SCORE)
    for line in _LINES:
        ours = 0
        theirs = 0
        for j in line:
            if pos[j] == 1:
                ours += 1
            elif pos[j] == -1:
                theirs += 1

        if ours and theirs:
            continue
        if ours:
            score += line_score[ours]
        elif theirs:
            # Defend slightly more urgently than we attack.
            score -= line_score[theirs] + (120 if theirs == 3 else 0)

    # Count direct threats/forks.
    our_threats = 0
    opp_threats = 0
    for i, v in enumerate(pos):
        if v == 0:
            if _would_win(pos, i, 1):
                our_threats += 1
            if _would_win(pos, i, -1):
                opp_threats += 1

    score += 6500 * our_threats
    score -= 7500 * opp_threats

    return score


def _move_order_score(pos, idx, player):
    """Score a move for ordering only, from player-to-move perspective."""
    score = _POSITION_SCORE[idx]

    if _would_win(pos, idx, player):
        score += 1000000

    # Blocking an opponent immediate win is also urgent.
    if _would_win(pos, idx, -player):
        score += 500000

    for line in _CELL_LINES[idx]:
        own = 1
        opp = 0
        for j in line:
            if j == idx:
                continue
            if pos[j] == player:
                own += 1
            elif pos[j] == -player:
                opp += 1

        if opp == 0:
            if own == 2:
                score += 30
            elif own == 3:
                score += 1200
            elif own == 4:
                score += 100000
        else:
            # Mixed line: value mainly comes from blocking.
            if opp == 3:
                score += 200000
            elif opp == 2:
                score += 250
            elif opp == 1:
                score += 10

    return score


def _ordered_moves(pos, player):
    moves = [i for i, v in enumerate(pos) if v == 0]
    moves.sort(key=lambda m: _move_order_score(pos, m, player), reverse=True)
    return moves


def _search(pos, player, depth, alpha, beta):
    """
    Alpha-beta minimax.
    Returns value from our perspective:
      higher is better for player 1,
      lower is better for player -1.
    """
    _check_time()

    win = _winner(pos)
    if win == 1:
        return WIN_SCORE + pos.count(0)
    if win == -1:
        return -WIN_SCORE - pos.count(0)

    empties = pos.count(0)
    if empties == 0:
        return 0
    if depth <= 0:
        return _evaluate(pos)

    key = (pos, player, depth)
    entry = _TT.get(key)
    if entry is not None:
        val, flag = entry
        if flag == _EXACT:
            return val
        if flag == _LOWER:
            alpha = max(alpha, val)
        elif flag == _UPPER:
            beta = min(beta, val)
        if alpha >= beta:
            return val

    original_alpha = alpha
    original_beta = beta

    if player == 1:
        best = -INF
        for m in _ordered_moves(pos, player):
            val = _search(_play(pos, m, player), -player, depth - 1, alpha, beta)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    else:
        best = INF
        for m in _ordered_moves(pos, player):
            val = _search(_play(pos, m, player), -player, depth - 1, alpha, beta)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break

    if best <= original_alpha:
        flag = _UPPER
    elif best >= original_beta:
        flag = _LOWER
    else:
        flag = _EXACT

    _TT[key] = (best, flag)
    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _deadline, _nodes, _TT

    pos = _to_tuple(board)
    legal = [i for i, v in enumerate(pos) if v == 0]
    if not legal:
        return (0, 0)

    fallback = _first_legal(pos)

    try:
        # Keep memory bounded across many arena games.
        if len(_TT) > 500000:
            _TT.clear()

        # Opening book: take a center if the board is nearly empty.
        total_marks = 16 - len(legal)
        our_marks = sum(1 for v in pos if v == 1)

        if total_marks == 0 or (our_marks == 0 and total_marks <= 1):
            for m in _PREFERRED:
                if pos[m] == 0:
                    return divmod(m, 4)

        # 1. Win immediately if possible.
        wins = _winning_moves(pos, 1)
        if wins:
            wins.sort(key=lambda m: _move_order_score(pos, m, 1), reverse=True)
            return divmod(wins[0], 4)

        # 2. Block opponent's immediate win.
        opp_wins = _winning_moves(pos, -1)
        if opp_wins:
            opp_wins.sort(key=lambda m: _move_order_score(pos, m, 1), reverse=True)
            return divmod(opp_wins[0], 4)

        # 3. Iterative-deepening minimax with a time limit.
        _deadline = time.perf_counter() + 0.85
        _nodes = 0

        ordered = _ordered_moves(pos, 1)
        best_move = ordered[0]
        best_score = -INF

        max_depth = len(legal)

        for depth in range(1, max_depth + 1):
            local_best = best_move
            local_score = -INF

            moves = list(ordered)
            if best_move in moves:
                moves.remove(best_move)
                moves.insert(0, best_move)

            alpha = -INF
            beta = INF

            for m in moves:
                child = _play(pos, m, 1)
                val = _search(child, -1, depth - 1, alpha, beta)

                if val > local_score:
                    local_score = val
                    local_best = m

                if val > alpha:
                    alpha = val

            # Completed this depth successfully.
            best_move = local_best
            best_score = local_score

            # If we found a forced win, no need to search deeper.
            if best_score >= WIN_SCORE:
                break

        if pos[best_move] == 0:
            return divmod(best_move, 4)

    except Exception:
        # Never fail to return a legal move.
        pass

    return fallback
