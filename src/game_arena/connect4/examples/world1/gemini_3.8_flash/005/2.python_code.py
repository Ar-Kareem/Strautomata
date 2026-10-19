
import time

# Column exploration preference: center columns offer the greatest strategic value
ORDER = [3, 2, 4, 1, 5, 0, 6]

# Precompute cell weights based on 4-in-a-row line participation and center control
CELL_4_COUNTS = [[0] * 7 for _ in range(6)]

for r in range(6):
    for c in range(4):
        for i in range(4):
            CELL_4_COUNTS[r][c + i] += 1

for c in range(7):
    for r in range(3):
        for i in range(4):
            CELL_4_COUNTS[r + i][c] += 1

for r in range(3):
    for c in range(4):
        for i in range(4):
            CELL_4_COUNTS[r + i][c + i] += 1

for r in range(3, 6):
    for c in range(4):
        for i in range(4):
            CELL_4_COUNTS[r - i][c + i] += 1

BIT_WEIGHT = [0] * 49
for c in range(7):
    for h in range(6):
        center_bonus = 4 if c == 3 else (2 if c in (2, 4) else 0)
        BIT_WEIGHT[7 * c + h] = CELL_4_COUNTS[h][c] + center_bonus

EXACT = 0
LOWERBOUND = 1
UPPERBOUND = 2


def check_win(bb: int) -> bool:
    """Checks if bitboard contains 4 connected discs in any direction."""
    # Horizontal
    m = bb & (bb >> 7)
    if m & (m >> 14):
        return True
    # Vertical
    m = bb & (bb >> 1)
    if m & (m >> 2):
        return True
    # Diagonal \
    m = bb & (bb >> 6)
    if m & (m >> 12):
        return True
    # Diagonal /
    m = bb & (bb >> 8)
    if m & (m >> 16):
        return True
    return False


class SearchTimeout(Exception):
    pass


def policy(board: list[list[int]]) -> int:
    start_time = time.time()
    deadline = start_time + 0.85

    # Legal moves verification
    legal_moves = [c for c in ORDER if board[0][c] == 0]
    if not legal_moves:
        return 3

    # Build bitboards and height tracker from input grid
    my_bb = 0
    opp_bb = 0
    height = [0] * 7

    for c in range(7):
        h = 0
        for r in range(5, -1, -1):
            val = board[r][c]
            if val == 1:
                my_bb |= 1 << (7 * c + h)
                h += 1
            elif val == -1:
                opp_bb |= 1 << (7 * c + h)
                h += 1
            else:
                break
        height[c] = h

    # 1. Immediate Win: play it immediately if available
    for c in legal_moves:
        bit = 1 << (7 * c + height[c])
        if check_win(my_bb | bit):
            return c

    # 2. Immediate Block: if opponent can win next move, prioritize blocking
    opp_threats = []
    for c in legal_moves:
        bit = 1 << (7 * c + height[c])
        if check_win(opp_bb | bit):
            opp_threats.append(c)

    if len(opp_threats) == 1:
        return opp_threats[0]

    # Calculate initial static score from perspective of player 1
    eval_score = 0
    for c in range(7):
        for h in range(height[c]):
            bit_idx = 7 * c + h
            if (my_bb >> bit_idx) & 1:
                eval_score += BIT_WEIGHT[bit_idx]
            elif (opp_bb >> bit_idx) & 1:
                eval_score -= BIT_WEIGHT[bit_idx]

    tt = {}
    nodes = 0

    def negamax(my, opp, depth, alpha, beta, ply, current_eval):
        nonlocal nodes
        nodes += 1
        if (nodes & 511) == 0 and time.time() > deadline:
            raise SearchTimeout()

        # Immediate winning moves for current player
        for c in ORDER:
            if height[c] < 6:
                b = 1 << (7 * c + height[c])
                if check_win(my | b):
                    return 100000 - ply, c

        avail = [c for c in ORDER if height[c] < 6]
        if not avail:
            return 0, None

        # Check opponent threats
        threats = []
        for c in avail:
            b = 1 << (7 * c + height[c])
            if check_win(opp | b):
                threats.append(c)

        if len(threats) > 1:
            return -(100000 - (ply + 1)), avail[0]

        if depth <= 0:
            return current_eval, None

        key = (my, opp)
        tt_entry = tt.get(key)
        tt_move = None
        if tt_entry is not None:
            tt_depth, tt_flag, tt_score, tt_move = tt_entry
            if tt_depth >= depth:
                if tt_flag == EXACT:
                    return tt_score, tt_move
                elif tt_flag == LOWERBOUND:
                    if tt_score >= beta:
                        return tt_score, tt_move
                    if tt_score > alpha:
                        alpha = tt_score
                elif tt_flag == UPPERBOUND:
                    if tt_score <= alpha:
                        return tt_score, tt_move
                    if tt_score < beta:
                        beta = tt_score
                if alpha >= beta:
                    return tt_score, tt_move

        if len(threats) == 1:
            moves_to_search = threats
        else:
            if tt_move is not None and height[tt_move] < 6:
                moves_to_search = [tt_move] + [c for c in avail if c != tt_move]
            else:
                moves_to_search = avail

        best_score = -1000000
        best_col = moves_to_search[0]
        orig_alpha = alpha

        for c in moves_to_search:
            h = height[c]
            b = 1 << (7 * c + h)
            height[c] = h + 1

            score, _ = negamax(
                opp,
                my | b,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
                -(current_eval + BIT_WEIGHT[7 * c + h]),
            )
            score = -score

            height[c] = h

            if score > best_score:
                best_score = score
                best_col = c

            if score > alpha:
                alpha = score
                if alpha >= beta:
                    break

        if best_score <= orig_alpha:
            flag = UPPERBOUND
        elif best_score >= beta:
            flag = LOWERBOUND
        else:
            flag = EXACT
        tt[key] = (depth, flag, best_score, best_col)

        return best_score, best_col

    best_move = legal_moves[0]

    # Iterative deepening
    for depth in range(1, 43):
        try:
            score, move = negamax(
                my_bb, opp_bb, depth, -1000000, 1000000, 0, eval_score
            )
            if move is not None and board[0][move] == 0:
                best_move = move
            if score >= 90000 or score <= -90000:
                break
        except SearchTimeout:
            break

    return best_move if board[0][best_move] == 0 else legal_moves[0]
