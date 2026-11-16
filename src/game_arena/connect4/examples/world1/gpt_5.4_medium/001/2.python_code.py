
import time

ROWS = 6
COLS = 7
ORDER = (3, 2, 4, 1, 5, 0, 6)
WIN_BASE = 1_000_000

BOTTOM_MASK = [1 << (c * 7) for c in range(COLS)]
COLUMN_MASK = [((1 << ROWS) - 1) << (c * 7) for c in range(COLS)]
TOP_MASK = [1 << (c * 7 + (ROWS - 1)) for c in range(COLS)]
FULL_MASK = sum(COLUMN_MASK)

COL_WEIGHT = (3, 4, 5, 7, 5, 4, 3)
LINE_SCORE = (0, 1, 8, 60, 0)


def _cell_bit(col: int, row_from_bottom: int) -> int:
    return 1 << (col * 7 + row_from_bottom)


WIN_MASKS = []

# Horizontal
for rb in range(ROWS):
    for c in range(COLS - 3):
        m = 0
        for i in range(4):
            m |= _cell_bit(c + i, rb)
        WIN_MASKS.append(m)

# Vertical
for c in range(COLS):
    for rb in range(ROWS - 3):
        m = 0
        for i in range(4):
            m |= _cell_bit(c, rb + i)
        WIN_MASKS.append(m)

# Diagonal up-right
for c in range(COLS - 3):
    for rb in range(ROWS - 3):
        m = 0
        for i in range(4):
            m |= _cell_bit(c + i, rb + i)
        WIN_MASKS.append(m)

# Diagonal down-right
for c in range(COLS - 3):
    for rb in range(3, ROWS):
        m = 0
        for i in range(4):
            m |= _cell_bit(c + i, rb - i)
        WIN_MASKS.append(m)


def has_won(pos: int) -> bool:
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True
    m = pos & (pos >> 7)
    if m & (m >> 14):
        return True
    m = pos & (pos >> 6)
    if m & (m >> 12):
        return True
    m = pos & (pos >> 8)
    if m & (m >> 16):
        return True
    return False


def play_bit(mask: int, col: int) -> int:
    return (mask + BOTTOM_MASK[col]) & COLUMN_MASK[col]


def legal_moves(mask: int, preferred: int | None = None) -> list[int]:
    moves = []
    if preferred is not None and not (mask & TOP_MASK[preferred]):
        moves.append(preferred)
    for c in ORDER:
        if c != preferred and not (mask & TOP_MASK[c]):
            moves.append(c)
    return moves


def winning_moves(player: int, opp: int) -> list[int]:
    mask = player | opp
    wins = []
    for c in ORDER:
        if not (mask & TOP_MASK[c]):
            mv = play_bit(mask, c)
            if has_won(player | mv):
                wins.append(c)
    return wins


class _Timeout(Exception):
    pass


class Solver:
    def __init__(self, deadline: float):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}

    def _check_time(self) -> None:
        self.nodes += 1
        if (self.nodes & 1023) == 0 and time.perf_counter() >= self.deadline:
            raise _Timeout

    def evaluate(self, cur: int, opp: int) -> int:
        score = 0

        # Positional / center preference
        for c in range(COLS):
            cm = COLUMN_MASK[c]
            score += COL_WEIGHT[c] * ((cur & cm).bit_count() - (opp & cm).bit_count())

        # Open lines
        for line in WIN_MASKS:
            ccount = (line & cur).bit_count()
            if ccount:
                if line & opp:
                    continue
                score += LINE_SCORE[ccount]
            else:
                ocount = (line & opp).bit_count()
                if ocount:
                    score -= LINE_SCORE[ocount]

        return score

    def opponent_can_win_next(self, cur_after_move: int, opp: int) -> bool:
        mask = cur_after_move | opp
        for c in ORDER:
            if not (mask & TOP_MASK[c]):
                mv = play_bit(mask, c)
                if has_won(opp | mv):
                    return True
        return False

    def non_losing_moves(self, cur: int, opp: int, preferred: int | None = None) -> list[int]:
        mask = cur | opp
        moves = legal_moves(mask, preferred)
        safe = []
        for c in moves:
            mv = play_bit(mask, c)
            new_cur = cur | mv
            if not self.opponent_can_win_next(new_cur, opp):
                safe.append(c)
        return safe if safe else moves

    def negamax(self, cur: int, opp: int, depth: int, alpha: int, beta: int) -> int:
        self._check_time()

        if has_won(opp):
            return -WIN_BASE - depth

        mask = cur | opp
        if mask == FULL_MASK:
            return 0

        key = (cur, opp, depth)
        orig_alpha = alpha
        orig_beta = beta

        tt_move = None
        entry = self.tt.get(key)
        if entry is not None:
            flag, val, best_move = entry
            tt_move = best_move
            if flag == 0:
                return val
            elif flag == 1:  # lower bound
                alpha = max(alpha, val)
            else:  # upper bound
                beta = min(beta, val)
            if alpha >= beta:
                return val

        moves = legal_moves(mask, tt_move)

        # Immediate win check
        for c in moves:
            mv = play_bit(mask, c)
            if has_won(cur | mv):
                val = WIN_BASE + depth
                self.tt[key] = (0, val, c)
                return val

        if depth == 0:
            val = self.evaluate(cur, opp)
            self.tt[key] = (0, val, None)
            return val

        moves = self.non_losing_moves(cur, opp, tt_move)

        best = -10**9
        best_move = moves[0]

        for c in moves:
            mv = play_bit(mask, c)
            score = -self.negamax(opp, cur | mv, depth - 1, -beta, -alpha)
            if score > best:
                best = score
                best_move = c
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        if best <= orig_alpha:
            flag = -1  # upper bound
        elif best >= orig_beta:
            flag = 1   # lower bound
        else:
            flag = 0   # exact

        self.tt[key] = (flag, best, best_move)
        return best

    def choose_move(self, cur: int, opp: int) -> int:
        mask = cur | opp
        legal = legal_moves(mask)
        if not legal:
            return 0
        if len(legal) == 1:
            return legal[0]

        # Immediate win
        my_wins = winning_moves(cur, opp)
        if my_wins:
            return my_wins[0]

        # Immediate block
        opp_wins = winning_moves(opp, cur)
        if len(opp_wins) >= 2:
            # Usually losing, but must still return a legal move.
            return opp_wins[0]
        if len(opp_wins) == 1:
            return opp_wins[0]

        root_moves = self.non_losing_moves(cur, opp)
        if len(root_moves) == 1:
            return root_moves[0]

        best_move = root_moves[0]
        preferred = best_move
        empties = 42 - mask.bit_count()

        depth = 1
        try:
            while depth <= empties:
                alpha = -10**9
                beta = 10**9
                best_score = -10**9
                current_best = best_move

                ordered = []
                if preferred in root_moves:
                    ordered.append(preferred)
                for c in ORDER:
                    if c in root_moves and c not in ordered:
                        ordered.append(c)
                for c in root_moves:
                    if c not in ordered:
                        ordered.append(c)

                for c in ordered:
                    mv = play_bit(mask, c)
                    score = -self.negamax(opp, cur | mv, depth - 1, -beta, -alpha)
                    if score > best_score:
                        best_score = score
                        current_best = c
                    if score > alpha:
                        alpha = score

                best_move = current_best
                preferred = best_move
                depth += 1

        except _Timeout:
            pass

        return best_move


def policy(board: list[list[int]]) -> int:
    cur = 0
    opp = 0

    for r in range(ROWS):
        for c in range(COLS):
            v = board[r][c]
            if v == 0:
                continue
            bit = 1 << (c * 7 + (ROWS - 1 - r))
            if v == 1:
                cur |= bit
            elif v == -1:
                opp |= bit

    mask = cur | opp
    legal = legal_moves(mask)
    if not legal:
        return 0

    deadline = time.perf_counter() + 0.92
    solver = Solver(deadline)
    move = solver.choose_move(cur, opp)

    # Final legality guard
    if 0 <= move < COLS and not (mask & TOP_MASK[move]):
        return move
    for c in ORDER:
        if not (mask & TOP_MASK[c]):
            return c
    return legal[0]
