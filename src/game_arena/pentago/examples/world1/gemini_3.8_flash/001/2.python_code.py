
import time

# --- Board and Game Constants ---
# Cell index: r * 6 + c (r in 0..5, c in 0..5)
QUAD_CELLS = []
for q in range(4):
    ro = 0 if q in (0, 1) else 3
    co = 0 if q in (0, 2) else 3
    cells = []
    for dr in range(3):
        for dc in range(3):
            cells.append((ro + dr) * 6 + (co + dc))
    QUAD_CELLS.append(cells)

QUAD_MASKS = [sum(1 << idx for idx in QUAD_CELLS[q]) for q in range(4)]
OUTSIDE_MASKS = [((1 << 36) - 1) ^ m for m in QUAD_MASKS]

# Precompute rotation lookup tables: ROT_LUT[quad][dir][9-bit-pattern] -> 36-bit mask
ROT_LUT = {q: {'L': [0] * 512, 'R': [0] * 512} for q in range(4)}
for q in range(4):
    for d in ('L', 'R'):
        for val in range(512):
            out_mask = 0
            for k in range(9):
                if (val >> k) & 1:
                    dr = k // 3
                    dc = k % 3
                    if d == 'R':
                        dr_new = dc
                        dc_new = 2 - dr
                    else:
                        dr_new = 2 - dc
                        dc_new = dr
                    k_new = dr_new * 3 + dc_new
                    out_mask |= 1 << QUAD_CELLS[q][k_new]
            ROT_LUT[q][d][val] = out_mask

# 32 winning lines of length 5
WIN_MASKS = []
# Horizontals (12)
for r in range(6):
    for c in range(2):
        WIN_MASKS.append(sum(1 << (r * 6 + c + i) for i in range(5)))
# Verticals (12)
for c in range(6):
    for r in range(2):
        WIN_MASKS.append(sum(1 << ((r + i) * 6 + c) for i in range(5)))
# Main diagonals (4)
for r, c in [(0, 0), (1, 1), (0, 1), (1, 0)]:
    WIN_MASKS.append(sum(1 << ((r + i) * 6 + (c + i)) for i in range(5)))
# Anti-diagonals (4)
for r, c in [(0, 4), (0, 5), (1, 5), (1, 4)]:
    WIN_MASKS.append(sum(1 << ((r + i) * 6 + (c - i)) for i in range(5)))

# Permanent center cells of the four 3x3 quadrants (indices 7, 10, 25, 28)
CENTER_CELLS = [QUAD_CELLS[q][4] for q in range(4)]
CENTER_MASK = sum(1 << idx for idx in CENTER_CELLS)


def extract_quad(bits: int, q: int) -> int:
    c = QUAD_CELLS[q]
    return (
        ((bits >> c[0]) & 1)
        | (((bits >> c[1]) & 1) << 1)
        | (((bits >> c[2]) & 1) << 2)
        | (((bits >> c[3]) & 1) << 3)
        | (((bits >> c[4]) & 1) << 4)
        | (((bits >> c[5]) & 1) << 5)
        | (((bits >> c[6]) & 1) << 6)
        | (((bits >> c[7]) & 1) << 7)
        | (((bits >> c[8]) & 1) << 8)
    )


def rotate(bits: int, q: int, d: str) -> int:
    val = extract_quad(bits, q)
    return (bits & OUTSIDE_MASKS[q]) | ROT_LUT[q][d][val]


def check_win(bits: int) -> bool:
    for m in WIN_MASKS:
        if (bits & m) == m:
            return True
    return False


def move_to_str(idx: int, q: int, d: str) -> str:
    r = (idx // 6) + 1
    c = (idx % 6) + 1
    return f"{r},{c},{q},{d}"


def count_opponent_wins(b_my: int, b_opp: int) -> int:
    """Returns number of winning moves available to opponent."""
    if b_opp.bit_count() < 4:
        return 0
    occ = b_my | b_opp
    empty_bits = ((1 << 36) - 1) ^ occ
    opp_wins = 0
    for oc in range(36):
        if (empty_bits >> oc) & 1:
            placed_opp = b_opp | (1 << oc)
            for q in range(4):
                for d in ('L', 'R'):
                    n_opp = rotate(placed_opp, q, d)
                    if check_win(n_opp):
                        n_my = rotate(b_my, q, d)
                        if not check_win(n_my):
                            opp_wins += 1
                            if opp_wins >= 5:
                                return opp_wins
    return opp_wins


def evaluate_board(b_my: int, b_opp: int) -> int:
    """Heuristic static evaluation for player."""
    score = 0

    # Center anchors (permanent cells)
    my_centers = (b_my & CENTER_MASK).bit_count()
    opp_centers = (b_opp & CENTER_MASK).bit_count()
    score += (my_centers - opp_centers) * 60

    # Line potentials
    for m in WIN_MASKS:
        m_my = (b_my & m).bit_count()
        m_opp = (b_opp & m).bit_count()
        if m_my > 0 and m_opp == 0:
            if m_my == 4:
                score += 800
            elif m_my == 3:
                score += 90
            elif m_my == 2:
                score += 15
            elif m_my == 1:
                score += 2
        elif m_opp > 0 and m_my == 0:
            if m_opp == 4:
                score -= 750
            elif m_opp == 3:
                score -= 80
            elif m_opp == 2:
                score -= 12
            elif m_opp == 1:
                score -= 2

    return score


def policy(you, opponent) -> str:
    start_time = time.perf_counter()

    # Convert 6x6 arrays to 36-bit integers
    my_bits = 0
    opp_bits = 0
    for r in range(6):
        for c in range(6):
            idx = r * 6 + c
            if you[r][c]:
                my_bits |= 1 << idx
            elif opponent[r][c]:
                opp_bits |= 1 << idx

    empty_mask = ((1 << 36) - 1) ^ (my_bits | opp_bits)
    empty_cells = [i for i in range(36) if (empty_mask >> i) & 1]

    # Guaranteed fallback move
    fallback_move = move_to_str(empty_cells[0], 0, 'R')

    # Prioritize center/inner empty cells for better move ordering
    order_pref = {7: 10, 10: 10, 25: 10, 28: 10}
    empty_cells.sort(key=lambda idx: order_pref.get(idx, 0), reverse=True)

    # 1. Immediate Win Check
    draw_candidate = None
    all_moves = []

    for cell in empty_cells:
        placed_my = my_bits | (1 << cell)
        for q in range(4):
            for d in ('L', 'R'):
                n_my = rotate(placed_my, q, d)
                n_opp = rotate(opp_bits, q, d)
                my_w = check_win(n_my)
                opp_w = check_win(n_opp)
                if my_w and not opp_w:
                    return move_to_str(cell, q, d)
                if my_w and opp_w and draw_candidate is None:
                    draw_candidate = move_to_str(cell, q, d)
                all_moves.append((cell, q, d, n_my, n_opp))

    # 2. Filter moves safe from opponent immediate win
    safe_moves = []
    risky_moves = []

    for cell, q, d, n_my, n_opp in all_moves:
        if time.perf_counter() - start_time > 0.85:
            break

        opp_win_count = count_opponent_wins(n_my, n_opp)
        if opp_win_count == 0:
            safe_moves.append((cell, q, d, n_my, n_opp))
        else:
            risky_moves.append((opp_win_count, cell, q, d, n_my, n_opp))

    # If no completely safe moves exist, choose the move minimizing opponent win paths
    if not safe_moves:
        if draw_candidate is not None:
            return draw_candidate
        if risky_moves:
            risky_moves.sort(key=lambda item: item[0])
            best_risky = risky_moves[0]
            return move_to_str(best_risky[1], best_risky[2], best_risky[3])
        return fallback_move

    # 3. Evaluate Safe Moves
    best_score = -float('inf')
    best_move = move_to_str(safe_moves[0][0], safe_moves[0][1], safe_moves[0][2])

    # Rank safe moves by base heuristic score
    scored_safe = []
    for cell, q, d, n_my, n_opp in safe_moves:
        s = evaluate_board(n_my, n_opp)
        scored_safe.append((s, cell, q, d, n_my, n_opp))

    scored_safe.sort(key=lambda x: x[0], reverse=True)

    # For top candidates, test if they create winning forks on our next turn
    for s, cell, q, d, n_my, n_opp in scored_safe[:16]:
        if time.perf_counter() - start_time > 0.90:
            break

        # Check win threats we create for next turn
        threats = 0
        if n_my.bit_count() >= 4:
            occ2 = n_my | n_opp
            empty2 = ((1 << 36) - 1) ^ occ2
            for c2 in range(36):
                if (empty2 >> c2) & 1:
                    pl2 = n_my | (1 << c2)
                    for q2 in range(4):
                        for d2 in ('L', 'R'):
                            if check_win(rotate(pl2, q2, d2)):
                                threats += 1
                                break
                        if threats >= 2:
                            break
                if threats >= 2:
                    break

        total_score = s + (threats * 1500)
        if total_score > best_score:
            best_score = total_score
            best_move = move_to_str(cell, q, d)

    return best_move
