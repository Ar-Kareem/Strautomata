
import random

WIN_SCORE = 10**7
FULL_MASK = 0xFFFF

# Precomputed masks for all winning lines (4 rows, 4 columns, 2 diagonals)
LINE_MASKS = []
# rows
for r in range(4):
    LINE_MASKS.append(0b1111 << (r * 4))
# columns
for c in range(4):
    mask = (1 << c) | (1 << (c + 4)) | (1 << (c + 8)) | (1 << (c + 12))
    LINE_MASKS.append(mask)
# main diagonal
LINE_MASKS.append((1 << 0) | (1 << 5) | (1 << 10) | (1 << 15))
# anti diagonal
LINE_MASKS.append((1 << 3) | (1 << 6) | (1 << 9) | (1 << 12))

# Static move ordering: cells with higher strategic value first
STATIC_ORDER = [
    5, 6, 9, 10,          # center four
    0, 3, 12, 15,         # corners
    1, 2, 4, 7, 8, 11, 13, 14  # edges
]

def is_win(bits: int) -> bool:
    """Return True if the given bitboard contains a winning line."""
    for mask in LINE_MASKS:
        if (bits & mask) == mask:
            return True
    return False

def evaluate(our_bits: int, opp_bits: int) -> int:
    """
    Heuristic evaluation from our perspective.
    For each line, if only one player has pieces, add (count^3) for us
    or subtract for opponent. Dead lines (both players) contribute 0.
    """
    score = 0
    for mask in LINE_MASKS:
        our_cnt = (our_bits & mask).bit_count()
        opp_cnt = (opp_bits & mask).bit_count()
        if our_cnt == 0 and opp_cnt == 0:
            continue
        if our_cnt > 0 and opp_cnt > 0:
            continue
        if our_cnt > 0:
            score += our_cnt * our_cnt * our_cnt
        else:
            score -= opp_cnt * opp_cnt * opp_cnt
    return score

def get_ordered_moves(empty_bits: int) -> list[int]:
    """Return list of empty cell indices in static order."""
    moves = []
    for idx in STATIC_ORDER:
        if empty_bits & (1 << idx):
            moves.append(idx)
    return moves

def minimax(our_bits: int, opp_bits: int, depth: int,
            alpha: int, beta: int, player: int, ply: int) -> int:
    """
    Alpha-beta minimax search.
    player: 1 (our turn, max), -1 (opponent turn, min).
    ply: distance from the root (used to adjust win scores).
    """
    # Terminal checks
    if is_win(our_bits):
        return WIN_SCORE - ply          # prefer earlier wins
    if is_win(opp_bits):
        return -WIN_SCORE + ply         # delay losses
    empty_bits = FULL_MASK ^ (our_bits | opp_bits)
    if empty_bits == 0:
        return 0

    if depth == 0:
        return evaluate(our_bits, opp_bits)

    ordered_moves = get_ordered_moves(empty_bits)
    if player == 1:          # maximizing player (us)
        value = -2 * WIN_SCORE
        for idx in ordered_moves:
            new_our = our_bits | (1 << idx)
            child_score = minimax(new_our, opp_bits, depth - 1,
                                  alpha, beta, -1, ply + 1)
            if child_score > value:
                value = child_score
            if value > alpha:
                alpha = value
            if value >= beta:
                break
        return value
    else:                    # minimizing player (opponent)
        value = 2 * WIN_SCORE
        for idx in ordered_moves:
            new_opp = opp_bits | (1 << idx)
            child_score = minimax(our_bits, new_opp, depth - 1,
                                  alpha, beta, 1, ply + 1)
            if child_score < value:
                value = child_score
            if value < beta:
                beta = value
            if value <= alpha:
                break
        return value

def policy(board: list[list[int]]) -> tuple[int, int]:
    """Return (row, col) for the next move."""
    # Convert board to bitboards
    our_bits = 0
    opp_bits = 0
    for r in range(4):
        for c in range(4):
            val = board[r][c]
            idx = r * 4 + c
            if val == 1:
                our_bits |= 1 << idx
            elif val == -1:
                opp_bits |= 1 << idx

    empty_bits = FULL_MASK ^ (our_bits | opp_bits)
    empty_count = empty_bits.bit_count()

    # Depth selection
    if empty_count <= 8:
        depth = empty_count          # full search
    elif empty_count <= 12:
        depth = 6
    else:
        depth = 5

    # Immediate winning move
    for idx in STATIC_ORDER:
        if empty_bits & (1 << idx):
            new_our = our_bits | (1 << idx)
            if is_win(new_our):
                return divmod(idx, 4)

    # Immediate blocking move (opponent would win next turn)
    for idx in STATIC_ORDER:
        if empty_bits & (1 << idx):
            new_opp = opp_bits | (1 << idx)
            if is_win(new_opp):
                return divmod(idx, 4)

    # Root search
    best_score = -2 * WIN_SCORE
    best_moves = []
    alpha = -2 * WIN_SCORE
    beta = 2 * WIN_SCORE

    ordered_moves = get_ordered_moves(empty_bits)
    for idx in ordered_moves:
        new_our = our_bits | (1 << idx)
        score = minimax(new_our, opp_bits, depth - 1,
                        alpha, beta, -1, ply=1)
        if score > best_score:
            best_score = score
            best_moves = [idx]
        elif score == best_score:
            best_moves.append(idx)
        if score > alpha:
            alpha = score

    # Fallback and random tie-breaking
    if not best_moves:
        # Should never happen, but pick first empty cell
        for idx in range(16):
            if empty_bits & (1 << idx):
                best_moves.append(idx)
                break
    idx = random.choice(best_moves)
    return divmod(idx, 4)
