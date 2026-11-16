
import time

# Column ordering from center outward for optimal alpha-beta cutoffs
COL_ORDER = [3, 2, 4, 1, 5, 0, 6]
BOTTOM_MASKS = [1 << (7 * c) for c in range(7)]
COL_MASKS = [0b111111 << (7 * c) for c in range(7)]
TOP_MASKS = [1 << (7 * c + 5) for c in range(7)]

WIN_SCORE = 100000
LOSS_SCORE = -100000


def is_win(b: int) -> bool:
    # Horizontal
    m = b & (b >> 7)
    if m & (m >> 14):
        return True
    # Diagonal \
    m = b & (b >> 6)
    if m & (m >> 12):
        return True
    # Vertical
    m = b & (b >> 1)
    if m & (m >> 2):
        return True
    # Diagonal /
    m = b & (b >> 8)
    if m & (m >> 16):
        return True
    return False


def count_bits(n: int) -> int:
    return bin(n).count("1")


def evaluate(p_board: int, o_board: int, mask: int) -> int:
    score = 0
    # Center column control
    p_center = count_bits(p_board & COL_MASKS[3])
    o_center = count_bits(o_board & COL_MASKS[3])
    score += (p_center - o_center) * 35

    # Flanking center columns (2 and 4)
    p_inner = count_bits(p_board & (COL_MASKS[2] | COL_MASKS[4]))
    o_inner = count_bits(o_board & (COL_MASKS[2] | COL_MASKS[4]))
    score += (p_inner - o_inner) * 15

    # Count open pairs and triples for both players
    for shift in (1, 6, 7, 8):
        # Pairs
        p_pairs = p_board & (p_board >> shift)
        o_pairs = o_board & (o_board >> shift)
        score += (count_bits(p_pairs) - count_bits(o_pairs)) * 10

        # Triples
        p_triples = p_pairs & (p_board >> (2 * shift))
        o_triples = o_pairs & (o_board >> (2 * shift))
        score += (count_bits(p_triples) - count_bits(o_triples)) * 40

    return score


def get_legal_moves(mask: int) -> list[int]:
    return [col for col in COL_ORDER if (mask & TOP_MASKS[col]) == 0]


def policy(board: list[list[int]]) -> int:
    start_time = time.time()
    time_limit = 0.82  # Target safe execution within 1.0 second

    # Encode board into bitboards
    # Row 5 is bottom (index 0 in column bits), Row 0 is top (index 5)
    p1 = 0
    p2 = 0
    for c in range(7):
        for r in range(5, -1, -1):
            cell = board[r][c]
            bit = 7 * c + (5 - r)
            if cell == 1:
                p1 |= 1 << bit
            elif cell == -1:
                p2 |= 1 << bit

    mask = p1 | p2
    legal_moves = get_legal_moves(mask)

    if not legal_moves:
        return 3

    if len(legal_moves) == 1:
        return legal_moves[0]

    # Immediate winning move or block check
    for col in legal_moves:
        move_bit = (mask + BOTTOM_MASKS[col]) & COL_MASKS[col]
        if is_win(p1 | move_bit):
            return col

    blocks = []
    for col in legal_moves:
        move_bit = (mask + BOTTOM_MASKS[col]) & COL_MASKS[col]
        if is_win(p2 | move_bit):
            blocks.append(col)

    if len(blocks) == 1:
        return blocks[0]

    transposition_table = {}

    def negamax(p_curr: int, p_opp: int, current_mask: int, depth: int, alpha: int, beta: int) -> int:
        if time.time() - start_time > time_limit:
            raise TimeoutError

        tt_key = (p_curr, current_mask)
        if tt_key in transposition_table:
            tt_depth, tt_score, tt_flag = transposition_table[tt_key]
            if tt_depth >= depth:
                if tt_flag == 0:
                    return tt_score
                elif tt_flag == 1:
                    alpha = max(alpha, tt_score)
                elif tt_flag == 2:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score

        moves = [c for c in COL_ORDER if (current_mask & TOP_MASKS[c]) == 0]
        if not moves:
            return 0

        # Check for immediate wins in current position
        for c in moves:
            m_bit = (current_mask + BOTTOM_MASKS[c]) & COL_MASKS[c]
            if is_win(p_curr | m_bit):
                return WIN_SCORE - (100 - depth)

        if depth <= 0:
            return evaluate(p_curr, p_opp, current_mask)

        original_alpha = alpha
        best_val = -float("inf")

        for c in moves:
            m_bit = (current_mask + BOTTOM_MASKS[c]) & COL_MASKS[c]
            next_p_curr = p_opp
            next_p_opp = p_curr | m_bit
            next_mask = current_mask | m_bit

            val = -negamax(next_p_curr, next_p_opp, next_mask, depth - 1, -beta, -alpha)

            if val > best_val:
                best_val = val
            alpha = max(alpha, val)
            if alpha >= beta:
                break

        # Store transposition
        if best_val <= original_alpha:
            flag = 2  # Upper bound
        elif best_val >= beta:
            flag = 1  # Lower bound
        else:
            flag = 0  # Exact
        transposition_table[tt_key] = (depth, best_val, flag)

        return best_val

    best_move = legal_moves[0]
    depth = 1

    # Iterative deepening
    while depth <= 20:
        current_best = None
        current_max = -float("inf")
        try:
            moves = [c for c in COL_ORDER if (mask & TOP_MASKS[c]) == 0]
            for c in moves:
                m_bit = (mask + BOTTOM_MASKS[c]) & COL_MASKS[c]
                val = -negamax(p2, p1 | m_bit, mask | m_bit, depth - 1, -WIN_SCORE * 2, -current_max)
                if val > current_max:
                    current_max = val
                    current_best = c
                if time.time() - start_time > time_limit:
                    raise TimeoutError

            if current_best is not None:
                best_move = current_best

            if current_max >= WIN_SCORE - 200:
                break

            depth += 1
        except TimeoutError:
            break

    return best_move
