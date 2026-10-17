
import time
import numpy as np

# 5 rows x 6 columns
ROWS = 5
COLS = 6
TOTAL_CELLS = 30

# Precompute neighbor adjacencies
# ADJ[sq] = list of (nbr_sq, dir_char, r, c)
ADJ = [[] for _ in range(TOTAL_CELLS)]
DIRS = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]

for r in range(ROWS):
    for c in range(COLS):
        sq = r * COLS + c
        for dr, dc, d_char in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                n_sq = nr * COLS + nc
                ADJ[sq].append((n_sq, d_char, r, c))


def get_moves(mover_bits: int, opp_bits: int):
    """Generate all legal moves for the mover.
    Returns list of tuples: (from_sq, to_sq, move_str)
    """
    moves = []
    # Iterate through all squares where mover has a piece
    b = mover_bits
    while b:
        lsb = b & -b
        sq = (lsb.bit_length() - 1)
        b ^= lsb

        for n_sq, d_char, r, c in ADJ[sq]:
            if (opp_bits >> n_sq) & 1:
                moves.append((sq, n_sq, f"{r},{c},{d_char}"))
    return moves


def evaluate(mover_bits: int, opp_bits: int) -> float:
    """Heuristic static evaluation when search depth is exhausted."""
    # Count pieces
    mover_count = bin(mover_bits).count('1')
    opp_count = bin(opp_bits).count('1')

    # Count active pieces and connections
    mover_active = 0
    opp_active = 0
    total_edges = 0

    b = mover_bits
    while b:
        lsb = b & -b
        sq = lsb.bit_length() - 1
        b ^= lsb
        edges = 0
        for n_sq, _, _, _ in ADJ[sq]:
            if (opp_bits >> n_sq) & 1:
                edges += 1
        if edges > 0:
            mover_active += 1
            total_edges += edges

    b = opp_bits
    while b:
        lsb = b & -b
        sq = lsb.bit_length() - 1
        b ^= lsb
        edges = 0
        for n_sq, _, _, _ in ADJ[sq]:
            if (mover_bits >> n_sq) & 1:
                edges += 1
        if edges > 0:
            opp_active += 1

    # Evaluation balance:
    # 1. Having more active pieces means more potential options down the line.
    # 2. Having fewer dead pieces (mover_count - mover_active) is preferable.
    score = 15.0 * (mover_active - opp_active) + 5.0 * (mover_count - opp_count)
    return score


class SearchTimeout(Exception):
    pass


class ClobberAI:
    def __init__(self, time_limit=0.88):
        self.time_limit = time_limit
        self.start_time = 0.0
        self.tt = {}  # Transposition table: (mover_bits, opp_bits) -> (depth, score, flag, best_move)
        # Flags: 0 = EXACT, 1 = LOWERBOUND (alpha), 2 = UPPERBOUND (beta)

    def search(self, you_bits: int, opp_bits: int) -> str:
        self.start_time = time.time()
        legal_moves = get_moves(you_bits, opp_bits)
        if not legal_moves:
            return "0,0,U"  # Fallback (should not happen if game is not already over)
        if len(legal_moves) == 1:
            return legal_moves[0][2]

        best_move_str = legal_moves[0][2]

        # Iterative Deepening
        depth = 1
        while depth <= 25:
            try:
                score, move_tuple = self.negamax(you_bits, opp_bits, depth, -1000000.0, 1000000.0, True)
                if move_tuple is not None:
                    best_move_str = move_tuple[2]
                # If a forced win or loss is found, we can stop
                if abs(score) >= 90000:
                    break
            except SearchTimeout:
                break
            depth += 1

        return best_move_str

    def negamax(self, mover_bits: int, opp_bits: int, depth: int, alpha: float, beta: float, is_root: bool):
        if (time.time() - self.start_time) > self.time_limit:
            raise SearchTimeout()

        orig_alpha = alpha
        state_key = (mover_bits, opp_bits)

        # Transposition table lookup
        tt_entry = self.tt.get(state_key)
        pv_move = None
        if tt_entry is not None:
            tt_depth, tt_score, tt_flag, tt_move = tt_entry
            pv_move = tt_move
            if not is_root and tt_depth >= depth:
                if tt_flag == 0:  # EXACT
                    return tt_score, tt_move
                elif tt_flag == 1:  # LOWERBOUND
                    alpha = max(alpha, tt_score)
                elif tt_flag == 2:  # UPPERBOUND
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score, tt_move

        moves = get_moves(mover_bits, opp_bits)
        # Normal play convention: no legal moves means current player loses immediately
        if not moves:
            return -100000.0 - depth, None

        if depth <= 0:
            return evaluate(mover_bits, opp_bits), None

        # Move ordering: prioritize PV move from TT, then moves capturing high-degree opponent pieces
        def move_priority(m):
            if pv_move and m[0] == pv_move[0] and m[1] == pv_move[1]:
                return 1000
            # Capturing pieces adjacent to multiple friendly pieces is tactically critical
            to_sq = m[1]
            adj_friendly = sum(1 for n, _, _, _ in ADJ[to_sq] if (mover_bits >> n) & 1)
            return adj_friendly

        moves.sort(key=move_priority, reverse=True)

        best_score = -1000000.0
        best_move = moves[0]

        for m in moves:
            from_sq, to_sq, _ = m
            # Make move
            next_mover = (mover_bits ^ (1 << from_sq)) | (1 << to_sq)
            next_opp = opp_bits ^ (1 << to_sq)

            # Negamax step (roles invert)
            score, _ = self.negamax(next_opp, next_mover, depth - 1, -beta, -alpha, False)
            score = -score

            if score > best_score:
                best_score = score
                best_move = m

            alpha = max(alpha, score)
            if alpha >= beta:
                break

        # Record into transposition table
        tt_flag = 0
        if best_score <= orig_alpha:
            tt_flag = 2  # UPPERBOUND
        elif best_score >= beta:
            tt_flag = 1  # LOWERBOUND
        self.tt[state_key] = (depth, best_score, tt_flag, best_move)

        return best_score, best_move


def policy(you: list[int], opponent: list[int]) -> str:
    """Entry point for the Clobber competition policy."""
    # Robust conversion to flat 1D boolean array / bits
    you_arr = np.asarray(you).flatten()
    opp_arr = np.asarray(opponent).flatten()

    you_bits = 0
    opp_bits = 0
    for i in range(TOTAL_CELLS):
        if you_arr[i]:
            you_bits |= (1 << i)
        if opp_arr[i]:
            opp_bits |= (1 << i)

    ai = ClobberAI(time_limit=0.88)
    return ai.search(you_bits, opp_bits)
