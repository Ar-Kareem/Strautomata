
import time

# Column ordering preference (center outward)
COL_ORDER = [3, 2, 4, 1, 5, 0, 6]

def has_won(pos: int) -> bool:
    """Checks if the position contains 4 connected discs in any direction."""
    # Horizontal
    m = pos & (pos >> 7)
    if m & (m >> 14):
        return True
    # Diagonal \ (step 6)
    m = pos & (pos >> 6)
    if m & (m >> 12):
        return True
    # Diagonal / (step 8)
    m = pos & (pos >> 8)
    if m & (m >> 16):
        return True
    # Vertical (step 1)
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True
    return False

def count_threats(pos: int, empty: int) -> int:
    """Counts 3-in-a-row alignments that have an empty 4th cell."""
    threats = 0
    # Horizontal
    m = pos & (pos >> 7)
    threats += bin((m & (pos >> 14) & (empty >> 21)) |
                   (m & (empty >> 14) & (pos >> 21)) |
                   ((pos >> 7) & (empty >> 14) & (pos >> 21) & (pos >> 28))).count('1')
    # Vertical
    m = pos & (pos >> 1)
    threats += bin(m & (pos >> 2) & (empty >> 3)).count('1')
    return threats

def evaluate(pos: int, mask: int) -> int:
    """Static heuristic evaluation from the perspective of the player with discs `pos`."""
    opp_pos = pos ^ mask
    empty = ~mask

    score = 0
    # Center column control (col 3)
    c3_player = bin(pos & (0b111111 << (7 * 3))).count('1')
    c3_opp = bin(opp_pos & (0b111111 << (7 * 3))).count('1')
    score += (c3_player - c3_opp) * 6

    # Adjacent center columns (cols 2 & 4)
    c24_player = bin(pos & ((0b111111 << (7 * 2)) | (0b111111 << (7 * 4)))).count('1')
    c24_opp = bin(opp_pos & ((0b111111 << (7 * 2)) | (0b111111 << (7 * 4)))).count('1')
    score += (c24_player - c24_opp) * 3

    # Alignment threats
    score += count_threats(pos, empty) * 10
    score -= count_threats(opp_pos, empty) * 10

    return score

class SearchTimeout(Exception):
    pass

class Solver:
    def __init__(self, start_time: float, time_limit: float = 0.85):
        self.tt = {}
        self.start_time = start_time
        self.time_limit = time_limit

    def negamax(self, pos: int, mask: int, depth: int, alpha: int, beta: int) -> int:
        if (time.time() - self.start_time) > self.time_limit:
            raise SearchTimeout()

        orig_alpha = alpha
        tt_entry = self.tt.get((pos, mask))
        if tt_entry is not None:
            tt_depth, tt_val, tt_flag, _ = tt_entry
            if tt_depth >= depth:
                if tt_flag == 0:  # EXACT
                    return tt_val
                elif tt_flag == 1:  # LOWERBOUND
                    alpha = max(alpha, tt_val)
                elif tt_flag == 2:  # UPPERBOUND
                    beta = min(beta, tt_val)
                if alpha >= beta:
                    return tt_val

        # Terminal state: draw if all top cells are full
        top_cells_full = True
        for c in range(7):
            if not (mask & (1 << (7 * c + 5))):
                top_cells_full = False
                break
        if top_cells_full:
            return 0

        if depth == 0:
            return evaluate(pos, mask)

        # Move ordering
        moves = []
        tt_move = tt_entry[3] if tt_entry else None
        if tt_move is not None and not (mask & (1 << (7 * tt_move + 5))):
            moves.append(tt_move)
        for c in COL_ORDER:
            if c != tt_move and not (mask & (1 << (7 * c + 5))):
                moves.append(c)

        best_val = -1000000
        best_col = moves[0]

        for col in moves:
            next_mask = mask | (mask + (1 << (7 * col)))
            new_disc = next_mask ^ mask

            # Check if this move wins immediately
            if has_won(pos | new_disc):
                val = 100000 + depth
            else:
                next_pos = pos ^ mask
                val = -self.negamax(next_pos, next_mask, depth - 1, -beta, -alpha)

            if val > best_val:
                best_val = val
                best_col = col

            alpha = max(alpha, val)
            if alpha >= beta:
                break

        # Store into TT
        flag = 0
        if best_val <= orig_alpha:
            flag = 2  # UPPERBOUND
        elif best_val >= beta:
            flag = 1  # LOWERBOUND
        self.tt[(pos, mask)] = (depth, best_val, flag, best_col)

        return best_val

def policy(board: list[list[int]]) -> int:
    start_time = time.time()

    # Convert 6x7 board into bitboards
    pos = 0   # Current player's discs
    mask = 0  # All placed discs
    for c in range(7):
        for r in range(5, -1, -1):
            val = board[r][c]
            if val != 0:
                bit = 1 << (7 * c + (5 - r))
                mask |= bit
                if val == 1:
                    pos |= bit

    # Find playable columns
    playable_cols = [c for c in COL_ORDER if not (mask & (1 << (7 * c + 5)))]
    if not playable_cols:
        return 0
    if len(playable_cols) == 1:
        return playable_cols[0]

    # 1. Immediate Win Check
    for c in playable_cols:
        next_mask = mask | (mask + (1 << (7 * c)))
        if has_won(pos | (next_mask ^ mask)):
            return c

    # 2. Immediate Block Opponent Win Check
    opp_pos = pos ^ mask
    for c in playable_cols:
        next_mask = mask | (mask + (1 << (7 * c)))
        if has_won(opp_pos | (next_mask ^ mask)):
            return c

    # 3. Iterative Deepening Negamax Search
    solver = Solver(start_time=start_time, time_limit=0.82)
    best_move = playable_cols[0]

    for depth in range(1, 42):
        try:
            solver.negamax(pos, mask, depth, -1000000, 1000000)
            entry = solver.tt.get((pos, mask))
            if entry and entry[3] is not None:
                best_move = entry[3]
                # If a guaranteed win is found, stop early
                if entry[1] >= 90000:
                    break
        except SearchTimeout:
            break

    return best_move
