
from time import perf_counter

# 3x3x3 Tic Tac Toe policy
# Board values:
#   1  = our mark
#  -1  = opponent mark
#   0  = empty


N = 3
CELLS = list(range(27))


def _idx(i, j, k):
    return i * 9 + j * 3 + k


def _coord(idx):
    return (idx // 9, (idx // 3) % 3, idx % 3)


def _generate_lines():
    lines = []

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            lines.append(tuple(_idx(i, j, k) for i in range(3)))
    for i in range(3):
        for k in range(3):
            lines.append(tuple(_idx(i, j, k) for j in range(3)))
    for i in range(3):
        for j in range(3):
            lines.append(tuple(_idx(i, j, k) for k in range(3)))

    # Face diagonals in i-j planes, for each k
    for k in range(3):
        lines.append(tuple(_idx(t, t, k) for t in range(3)))
        lines.append(tuple(_idx(t, 2 - t, k) for t in range(3)))

    # Face diagonals in i-k planes, for each j
    for j in range(3):
        lines.append(tuple(_idx(t, j, t) for t in range(3)))
        lines.append(tuple(_idx(t, j, 2 - t) for t in range(3)))

    # Face diagonals in j-k planes, for each i
    for i in range(3):
        lines.append(tuple(_idx(i, t, t) for t in range(3)))
        lines.append(tuple(_idx(i, t, 2 - t) for t in range(3)))

    # Space diagonals
    lines.append(tuple(_idx(t, t, t) for t in range(3)))
    lines.append(tuple(_idx(t, t, 2 - t) for t in range(3)))
    lines.append(tuple(_idx(t, 2 - t, t) for t in range(3)))
    lines.append(tuple(_idx(t, 2 - t, 2 - t) for t in range(3)))

    # Remove duplicates defensively
    return list(dict.fromkeys(lines))


LINES = _generate_lines()

LINES_BY_CELL = [[] for _ in range(27)]
for line in LINES:
    for c in line:
        LINES_BY_CELL[c].append(line)


# Positional weights:
# center is strongest, corners are strong, face centers/edges moderate.
POS_WEIGHT = [0] * 27
for idx in CELLS:
    i, j, k = _coord(idx)
    dist = abs(i - 1) + abs(j - 1) + abs(k - 1)
    # Also reward number of winning lines through a cell.
    POS_WEIGHT[idx] = 2 * len(LINES_BY_CELL[idx]) - dist

CENTER = _idx(1, 1, 1)


def _flatten(board):
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))


def _winner(flat):
    for a, b, c in LINES:
        s = flat[a] + flat[b] + flat[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _is_win_after(flat_list, move, player):
    for line in LINES_BY_CELL[move]:
        ok = True
        for c in line:
            if flat_list[c] != player:
                ok = False
                break
        if ok:
            return True
    return False


def _immediate_winning_moves(flat, player):
    arr = list(flat)
    wins = []
    for m, v in enumerate(arr):
        if v == 0:
            arr[m] = player
            if _is_win_after(arr, m, player):
                wins.append(m)
            arr[m] = 0
    return wins


def _count_immediate_wins_after_move(flat, move, player):
    arr = list(flat)
    arr[move] = player
    cnt = 0
    for m, v in enumerate(arr):
        if v == 0:
            arr[m] = player
            if _is_win_after(arr, m, player):
                cnt += 1
            arr[m] = 0
    return cnt


def _static_eval(flat):
    w = _winner(flat)
    if w == 1:
        return 1000000
    if w == -1:
        return -1000000

    score = 0

    # Positional control
    for i, v in enumerate(flat):
        if v == 1:
            score += POS_WEIGHT[i]
        elif v == -1:
            score -= POS_WEIGHT[i]

    # Line potential
    for line in LINES:
        vals = [flat[c] for c in line]
        ours = vals.count(1)
        opps = vals.count(-1)

        if ours and opps:
            continue

        if ours == 2:
            score += 120
        elif ours == 1:
            score += 8
        elif ours == 0 and opps == 0:
            score += 1

        if opps == 2:
            score -= 150
        elif opps == 1:
            score -= 9

    return score


def _ordered_moves(flat, player):
    empties = [i for i, v in enumerate(flat) if v == 0]

    def key(m):
        arr = list(flat)

        # Very high priority for direct wins
        arr[m] = player
        win = _is_win_after(arr, m, player)
        arr[m] = 0
        if win:
            return 10_000 + POS_WEIGHT[m]

        # High priority for blocking opponent direct wins
        arr[m] = -player
        opp_win_if_they_played = _is_win_after(arr, m, -player)
        arr[m] = 0

        fork_bonus = 0
        try:
            fw = _count_immediate_wins_after_move(flat, m, player)
            if fw >= 2:
                fork_bonus += 500 + 100 * fw
        except Exception:
            pass

        return (4000 if opp_win_if_they_played else 0) + fork_bonus + POS_WEIGHT[m]

    empties.sort(key=key, reverse=True)
    return empties


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    start = perf_counter()
    TIME_LIMIT = 0.92

    try:
        flat = _flatten(board)
        empties = [i for i, v in enumerate(flat) if v == 0]

        if not empties:
            return (0, 0, 0)

        # Opening: center is extremely strong in 3D.
        if flat[CENTER] == 0:
            return _coord(CENTER)

        # 1. Win immediately if possible.
        wins = _immediate_winning_moves(flat, 1)
        if wins:
            wins.sort(key=lambda m: POS_WEIGHT[m], reverse=True)
            return _coord(wins[0])

        # 2. Block opponent immediate win.
        blocks = _immediate_winning_moves(flat, -1)
        if blocks:
            blocks.sort(key=lambda m: POS_WEIGHT[m], reverse=True)
            return _coord(blocks[0])

        # 3. Create a fork if available.
        best_fork = None
        best_fork_score = -1
        for m in empties:
            fw = _count_immediate_wins_after_move(flat, m, 1)
            if fw >= 2:
                sc = fw * 100 + POS_WEIGHT[m]
                if sc > best_fork_score:
                    best_fork_score = sc
                    best_fork = m
        if best_fork is not None:
            return _coord(best_fork)

        # 4. If opponent has a fork threat, try to block the strongest one.
        opp_forks = []
        for m in empties:
            fw = _count_immediate_wins_after_move(flat, m, -1)
            if fw >= 2:
                opp_forks.append((fw, POS_WEIGHT[m], m))
        if opp_forks:
            opp_forks.sort(reverse=True)
            return _coord(opp_forks[0][2])

        # 5. Iterative deepening alpha-beta search.
        trans = {}

        def terminal_score(pos, depth_remaining):
            w = _winner(pos)
            if w == 1:
                return 100000 + depth_remaining
            if w == -1:
                return -100000 - depth_remaining
            if all(v != 0 for v in pos):
                return 0
            return None

        def alphabeta(pos, depth, alpha, beta, player):
            if perf_counter() - start > TIME_LIMIT:
                raise TimeoutError

            t = terminal_score(pos, depth)
            if t is not None:
                return t

            if depth == 0:
                return _static_eval(pos)

            key = (pos, depth, player)
            if key in trans:
                return trans[key]

            moves = _ordered_moves(pos, player)

            if player == 1:
                value = -10**9
                arr = list(pos)
                for m in moves:
                    arr[m] = 1
                    child = tuple(arr)
                    arr[m] = 0
                    score = alphabeta(child, depth - 1, alpha, beta, -1)
                    if score > value:
                        value = score
                    if value > alpha:
                        alpha = value
                    if alpha >= beta:
                        break
            else:
                value = 10**9
                arr = list(pos)
                for m in moves:
                    arr[m] = -1
                    child = tuple(arr)
                    arr[m] = 0
                    score = alphabeta(child, depth - 1, alpha, beta, 1)
                    if score < value:
                        value = score
                    if value < beta:
                        beta = value
                    if alpha >= beta:
                        break

            trans[key] = value
            return value

        ordered = _ordered_moves(flat, 1)
        best_move = ordered[0]
        best_score = -10**9

        # Dynamic maximum depth.
        n_empty = len(empties)
        if n_empty <= 8:
            max_depth = n_empty
        elif n_empty <= 12:
            max_depth = 8
        elif n_empty <= 17:
            max_depth = 6
        else:
            max_depth = 4

        for depth in range(1, max_depth + 1):
            if perf_counter() - start > TIME_LIMIT:
                break

            current_best = best_move
            current_score = -10**9

            for m in ordered:
                if perf_counter() - start > TIME_LIMIT:
                    raise TimeoutError

                arr = list(flat)
                arr[m] = 1
                child = tuple(arr)

                score = alphabeta(child, depth - 1, -10**9, 10**9, -1)

                # Slight preference for central/versatile cells on ties.
                score += POS_WEIGHT[m] * 0.01

                if score > current_score:
                    current_score = score
                    current_best = m

            best_move = current_best
            best_score = current_score

            # Certain win found.
            if best_score > 90000:
                break

        return _coord(best_move)

    except Exception:
        # Absolute safety fallback: always return a legal move if one exists.
        try:
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if board[i][j][k] == 0:
                            return (i, j, k)
        except Exception:
            pass

        # Should only happen on a terminal/full board or malformed input.
        return (0, 0, 0)
