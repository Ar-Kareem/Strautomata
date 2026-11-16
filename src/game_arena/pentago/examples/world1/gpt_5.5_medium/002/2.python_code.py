
# Pentago policy: tactical 2-ply minimax with robust legal fallback.
# Required API:
#     def policy(you, opponent) -> str

import time

N = 6
WIN_SCORE = 100000000
INF = 1000000000

# Positional weights. Quadrant centers and central influence are useful in Pentago.
_POS_GRID = [
    [3, 4, 4, 4, 4, 3],
    [4, 8, 5, 5, 8, 4],
    [4, 5, 7, 7, 5, 4],
    [4, 5, 7, 7, 5, 4],
    [4, 8, 5, 5, 8, 4],
    [3, 4, 4, 4, 4, 3],
]
POSVAL = [_POS_GRID[r][c] for r in range(6) for c in range(6)]

# Line pattern weights for static evaluation.
# Terminal 5-in-a-row is handled separately.
OWN_LINE_W = [0, 2, 25, 250, 3500, 0]
OPP_LINE_W = [0, 3, 35, 325, 4300, 0]


def _idx(r, c):
    return r * 6 + c


def _make_lines():
    lines = []
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))
    for dr, dc in directions:
        for r in range(6):
            for c in range(6):
                rr = r + 4 * dr
                cc = c + 4 * dc
                if 0 <= rr < 6 and 0 <= cc < 6:
                    lines.append(tuple(_idx(r + k * dr, c + k * dc) for k in range(5)))
    return tuple(lines)


LINES = _make_lines()


def _make_rotations():
    # ROT_PAIRS[q][d] where d=0 is L, d=1 is R.
    rotations = []
    for q in range(4):
        tr = (q // 2) * 3
        tc = (q % 2) * 3

        left_pairs = []
        right_pairs = []

        for i in range(3):
            for j in range(3):
                src = _idx(tr + i, tc + j)

                # Left / anticlockwise: new local position is (2-j, i)
                dst_l = _idx(tr + (2 - j), tc + i)
                left_pairs.append((dst_l, src))

                # Right / clockwise: new local position is (j, 2-i)
                dst_r = _idx(tr + j, tc + (2 - i))
                right_pairs.append((dst_r, src))

        rotations.append((tuple(left_pairs), tuple(right_pairs)))
    return tuple(rotations)


ROT_PAIRS = _make_rotations()


def _make_rot_order():
    # For each placement cell, try rotating its own quadrant first for better move ordering,
    # then the other quadrants.
    orders = []
    for pos in range(36):
        r, c = divmod(pos, 6)
        own_q = (r // 3) * 2 + (c // 3)
        qs = [own_q] + [q for q in range(4) if q != own_q]
        opts = []
        for q in qs:
            opts.append((q, 0, "L"))
            opts.append((q, 1, "R"))
        orders.append(tuple(opts))
    return tuple(orders)


ROT_ORDER_FOR_POS = _make_rot_order()


def _move_string(pos, q, dchar):
    r, c = divmod(pos, 6)
    return f"{r + 1},{c + 1},{q},{dchar}"


def _apply_move(board, pos, player, q, d):
    # Place, then rotate quadrant q in direction d.
    temp = board.copy()
    temp[pos] = player

    out = temp.copy()
    for dst, src in ROT_PAIRS[q][d]:
        out[dst] = temp[src]
    return out


def _win_flags(board):
    you_win = False
    opp_win = False

    for a, b, c, d, e in LINES:
        s = board[a] + board[b] + board[c] + board[d] + board[e]
        if s == 5:
            you_win = True
        elif s == -5:
            opp_win = True

        if you_win and opp_win:
            break

    return you_win, opp_win


def _static_eval(board):
    score = 0

    # Positional component.
    for i, v in enumerate(board):
        if v == 1:
            score += POSVAL[i]
        elif v == -1:
            score -= POSVAL[i]

    # Line potential component.
    for line in LINES:
        own = 0
        opp = 0
        for i in line:
            v = board[i]
            if v == 1:
                own += 1
            elif v == -1:
                opp += 1

        if own and opp:
            continue
        if own:
            score += OWN_LINE_W[own]
        elif opp:
            score -= OPP_LINE_W[opp]

    return score


def _ordered_empties(board):
    empties = [i for i, v in enumerate(board) if v == 0]
    empties.sort(key=lambda p: POSVAL[p], reverse=True)
    return empties


def _opponent_min_value(board_after_us, alpha, deadline):
    # Opponent is represented as -1 and chooses the reply minimizing our score.
    empties = _ordered_empties(board_after_us)
    if not empties:
        return 0

    worst = INF
    checked = 0

    for pos in empties:
        for q, d, _dchar in ROT_ORDER_FOR_POS[pos]:
            b2 = _apply_move(board_after_us, pos, -1, q, d)
            you_win, opp_win = _win_flags(b2)

            if opp_win and not you_win:
                return -WIN_SCORE
            elif you_win and not opp_win:
                val = WIN_SCORE
            elif you_win and opp_win:
                val = 0
            elif 0 not in b2:
                val = 0
            else:
                val = _static_eval(b2)

            if val < worst:
                worst = val
                if worst <= alpha:
                    return worst

            checked += 1
            if (checked & 31) == 0 and time.perf_counter() > deadline:
                if worst == INF:
                    return _static_eval(board_after_us)
                return worst

    if worst == INF:
        return _static_eval(board_after_us)
    return worst


def _choose_move(board, fallback):
    start = time.perf_counter()
    deadline = start + 0.90

    empties = _ordered_empties(board)
    if not empties:
        return fallback

    best_move = fallback
    best_score = -INF

    # Search every legal placement + rotation.
    for pos in empties:
        if time.perf_counter() > deadline:
            break

        for q, d, dchar in ROT_ORDER_FOR_POS[pos]:
            move_str = _move_string(pos, q, dchar)
            b1 = _apply_move(board, pos, 1, q, d)
            you_win, opp_win = _win_flags(b1)

            # Pure immediate win: take it instantly.
            if you_win and not opp_win:
                return move_str

            # Draw by simultaneous five-in-a-row.
            if you_win and opp_win:
                score = 0

            # Never voluntarily rotate the opponent into a sole win unless unavoidable.
            elif opp_win and not you_win:
                score = -WIN_SCORE + _static_eval(b1) // 1000

            # Board full after our move: draw.
            elif 0 not in b1:
                score = 0

            else:
                score = _opponent_min_value(b1, best_score, deadline)

            if score > best_score:
                best_score = score
                best_move = move_str

            if time.perf_counter() > deadline:
                break

    return best_move


def policy(you, opponent) -> str:
    fallback = None

    try:
        board = []
        first_empty = None

        for r in range(6):
            for c in range(6):
                y = int(you[r][c])
                o = int(opponent[r][c])

                if y:
                    board.append(1)
                elif o:
                    board.append(-1)
                else:
                    pos = r * 6 + c
                    board.append(0)
                    if first_empty is None:
                        first_empty = pos

        # The caller promises at least one empty cell, but keep a fallback anyway.
        if first_empty is None:
            return "1,1,0,L"

        fallback = _move_string(first_empty, 0, "L")
        return _choose_move(board, fallback)

    except Exception:
        # Last-resort legal fallback for valid inputs.
        if fallback is not None:
            return fallback

        try:
            for r in range(6):
                for c in range(6):
                    if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                        return f"{r + 1},{c + 1},0,L"
        except Exception:
            pass

        # This should never be reached for valid non-full boards.
        return "1,1,0,L"
