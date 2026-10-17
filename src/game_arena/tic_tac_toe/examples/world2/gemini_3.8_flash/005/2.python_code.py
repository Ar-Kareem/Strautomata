
import time

WINNING_MASKS = [
    0x000F, 0x00F0, 0x0F00, 0xF000,  # Rows
    0x1111, 0x2222, 0x4444, 0x8888,  # Columns
    0x8421, 0x1248                   # Diagonals
]

# Move preference ordering: center squares and corners have more line intersections
MOVE_ORDER = [5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14]

def is_win(bb: int) -> bool:
    for mask in WINNING_MASKS:
        if (bb & mask) == mask:
            return True
    return False

def evaluate(bb_me: int, bb_opp: int) -> int:
    score = 0
    for mask in WINNING_MASKS:
        m = bb_me & mask
        o = bb_opp & mask
        if o == 0 and m != 0:
            count = m.bit_count()
            if count == 3:
                score += 100
            elif count == 2:
                score += 10
            elif count == 1:
                score += 1
        elif m == 0 and o != 0:
            count = o.bit_count()
            if count == 3:
                score -= 100
            elif count == 2:
                score -= 10
            elif count == 1:
                score -= 1
    return score

def policy(board: list[list[int]]) -> tuple[int, int]:
    start_time = time.time()
    time_limit = 0.80

    bb_me = 0
    bb_opp = 0
    legal_moves = []

    for r in range(4):
        for c in range(4):
            idx = r * 4 + c
            val = board[r][c]
            if val == 1:
                bb_me |= (1 << idx)
            elif val == -1:
                bb_opp |= (1 << idx)
            else:
                legal_moves.append(idx)

    if not legal_moves:
        return (0, 0)
    if len(legal_moves) == 1:
        idx = legal_moves[0]
        return (idx // 4, idx % 4)

    # 1. Immediate winning move
    for idx in legal_moves:
        if is_win(bb_me | (1 << idx)):
            return (idx // 4, idx % 4)

    # 2. Block immediate opponent win
    for idx in legal_moves:
        if is_win(bb_opp | (1 << idx)):
            return (idx // 4, idx % 4)

    # Sort legal moves according to preferred strategic positions
    ordered_legal = [m for m in MOVE_ORDER if m in legal_moves]

    best_move = ordered_legal[0]
    tt = {}

    def negamax(me: int, opp: int, depth: int, alpha: int, beta: int) -> int:
        if time.time() - start_time > time_limit:
            raise TimeoutError

        state_key = (me, opp)
        if state_key in tt:
            cached_depth, cached_val = tt[state_key]
            if cached_depth >= depth:
                return cached_val

        if is_win(opp):
            return -10000 - depth

        occupied = me | opp
        if occupied == 0xFFFF:
            return 0

        if depth == 0:
            return evaluate(me, opp)

        moves = [m for m in MOVE_ORDER if not (occupied & (1 << m))]
        if not moves:
            return 0

        val = -100000
        for move in moves:
            next_me = me | (1 << move)
            score = -negamax(opp, next_me, depth - 1, -beta, -alpha)
            if score > val:
                val = score
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        tt[state_key] = (depth, val)
        return val

    # Iterative deepening
    max_depth = len(legal_moves)
    for depth in range(1, max_depth + 1):
        try:
            current_best_move = best_move
            best_val = -100000
            alpha = -100000
            beta = 100000

            for move in ordered_legal:
                next_me = bb_me | (1 << move)
                if is_win(next_me):
                    return (move // 4, move % 4)
                val = -negamax(bb_opp, next_me, depth - 1, -beta, -alpha)
                if val > best_val:
                    best_val = val
                    current_best_move = move
                if val > alpha:
                    alpha = val

            best_move = current_best_move
            if best_val >= 9000:
                break
        except TimeoutError:
            break

    return (best_move // 4, best_move % 4)
