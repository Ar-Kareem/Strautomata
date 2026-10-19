
import time

class SearchTimeout(Exception):
    """Raised when the search exceeds allocated time."""
    pass

def is_win(b: int) -> bool:
    """Check if bitboard b contains four-in-a-row."""
    # Horizontal (+7)
    m = b & (b >> 7)
    if m & (m >> 14):
        return True
    # Vertical (+1)
    m = b & (b >> 1)
    if m & (m >> 2):
        return True
    # Diagonal \ (down-right, +6)
    m = b & (b >> 6)
    if m & (m >> 12):
        return True
    # Diagonal / (up-right, +8)
    m = b & (b >> 8)
    if m & (m >> 16):
        return True
    return False

def evaluate(p1: int, p2: int) -> int:
    """Heuristic evaluation from the perspective of p1."""
    # Column weights: Center column (col 3) is strongest, followed by 2,4 and 1,5
    c3 = ((p1 >> 21) & 63).bit_count() - ((p2 >> 21) & 63).bit_count()
    c24 = (((p1 >> 14) & 63).bit_count() + ((p1 >> 28) & 63).bit_count() -
           ((p2 >> 14) & 63).bit_count() - ((p2 >> 28) & 63).bit_count())
    c15 = (((p1 >> 7) & 63).bit_count() + ((p1 >> 35) & 63).bit_count() -
           ((p2 >> 7) & 63).bit_count() - ((p2 >> 35) & 63).bit_count())
    
    score = c3 * 6 + c24 * 3 + c15 * 1

    # Alignment pairs
    h = (p1 & (p1 >> 7)).bit_count() - (p2 & (p2 >> 7)).bit_count()
    v = (p1 & (p1 >> 1)).bit_count() - (p2 & (p2 >> 1)).bit_count()
    d1 = (p1 & (p1 >> 6)).bit_count() - (p2 & (p2 >> 6)).bit_count()
    d2 = (p1 & (p1 >> 8)).bit_count() - (p2 & (p2 >> 8)).bit_count()

    score += (h + v + d1 + d2) * 2
    return score

def policy(board: list[list[int]]) -> int:
    """
    Given a 6x7 Connect 4 board, return the best column index (0-6) to drop a disc.
    1 represents our disc, -1 opponent's disc, 0 empty cell.
    """
    start_time = time.perf_counter()
    time_limit = 0.85  # Conservative safety margin within the 1-second constraint

    # Convert board representation to bitboards and column heights
    p1 = 0
    p2 = 0
    heights = [-1] * 7
    for c in range(7):
        for r in range(6):
            val = board[r][c]
            if val == 1:
                p1 |= 1 << (c * 7 + (5 - r))
            elif val == -1:
                p2 |= 1 << (c * 7 + (5 - r))
        for r in range(5, -1, -1):
            if board[r][c] == 0:
                heights[c] = r
                break

    legal_moves = [c for c in range(7) if heights[c] != -1]
    if not legal_moves:
        return 0
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Immediate win check
    for c in legal_moves:
        bit = 1 << (c * 7 + (5 - heights[c]))
        if is_win(p1 | bit):
            return c

    # Immediate block check
    block_col = None
    for c in legal_moves:
        bit = 1 << (c * 7 + (5 - heights[c]))
        if is_win(p2 | bit):
            block_col = c
            break

    # Transposition table
    tt = {}
    EXACT = 0
    LOWERBOUND = 1
    UPPERBOUND = 2

    node_count = 0

    def negamax(p_curr: int, p_opp: int, current_heights: list[int], depth: int, alpha: int, beta: int) -> int:
        nonlocal node_count
        node_count += 1
        if (node_count & 1023) == 0:
            if time.perf_counter() - start_time > time_limit:
                raise SearchTimeout()

        orig_alpha = alpha
        key = (p_curr, p_opp)
        tt_move = None

        if key in tt:
            tt_depth, tt_flag, tt_score, tt_move = tt[key]
            if tt_depth >= depth:
                if tt_flag == EXACT:
                    return tt_score
                elif tt_flag == LOWERBOUND:
                    alpha = max(alpha, tt_score)
                elif tt_flag == UPPERBOUND:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score

        moves = [3, 2, 4, 1, 5, 0, 6]
        if tt_move is not None:
            moves = [tt_move] + [m for m in moves if m != tt_move]

        best_score = -200000
        best_move = None
        has_moves = False

        for col in moves:
            row = current_heights[col]
            if row == -1:
                continue
            has_moves = True
            bit = 1 << (col * 7 + (5 - row))
            new_p_curr = p_curr | bit

            if is_win(new_p_curr):
                score = 10000 + depth
            else:
                if depth == 1:
                    score = -evaluate(p_opp, new_p_curr)
                else:
                    current_heights[col] = row - 1
                    score = -negamax(p_opp, new_p_curr, current_heights, depth - 1, -beta, -alpha)
                    current_heights[col] = row

            if score > best_score:
                best_score = score
                best_move = col
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        if not has_moves:
            return 0  # Draw

        flag = EXACT
        if best_score <= orig_alpha:
            flag = UPPERBOUND
        elif best_score >= beta:
            flag = LOWERBOUND

        if len(tt) < 400000:
            tt[key] = (depth, flag, best_score, best_move)

        return best_score

    # Fallback to block or center-most available move
    best_move = block_col if block_col is not None else (3 if heights[3] != -1 else legal_moves[0])

    # Iterative Deepening
    for max_depth in range(1, 43):
        try:
            moves = [3, 2, 4, 1, 5, 0, 6]
            key = (p1, p2)
            if key in tt:
                tt_move = tt[key][3]
                if tt_move is not None:
                    moves = [tt_move] + [m for m in moves if m != tt_move]

            best_depth_move = None
            best_depth_score = -200000
            alpha = -200000
            beta = 200000

            for col in moves:
                row = heights[col]
                if row == -1:
                    continue
                bit = 1 << (col * 7 + (5 - row))
                new_p1 = p1 | bit

                if is_win(new_p1):
                    return col

                if max_depth == 1:
                    score = -evaluate(p2, new_p1)
                else:
                    heights[col] = row - 1
                    score = -negamax(p2, new_p1, heights, max_depth - 1, -beta, -alpha)
                    heights[col] = row

                if score > best_depth_score:
                    best_depth_score = score
                    best_depth_move = col
                if score > alpha:
                    alpha = score

            if best_depth_move is not None:
                best_move = best_depth_move

            # Stop deepening if a forced win is found
            if best_depth_score >= 9000:
                break

        except SearchTimeout:
            break

    return best_move
