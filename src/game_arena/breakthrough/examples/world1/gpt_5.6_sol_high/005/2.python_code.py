
import time


ALL = (1 << 64) - 1
ROW0 = 0xFF
ROW1 = 0xFF << 8
ROW6 = 0xFF << 48
ROW7 = 0xFF << 56

COL0 = sum(1 << (r * 8) for r in range(8))
COL7 = sum(1 << (r * 8 + 7) for r in range(8))
NOT_COL0 = ALL ^ COL0
NOT_COL7 = ALL ^ COL7

MATE = 1_000_000
INF = 1_100_000

EXACT = 1
UPPER = 0
LOWER = 2

CENTER_BONUS = (0, 4, 7, 10, 10, 7, 4, 0)
PROGRESS_BONUS = (0, 4, 11, 23, 43, 78, 150, 300)
PASSED_BONUS = (0, 4, 11, 24, 52, 108, 225, 400)


def _make_pass_masks():
    white_masks = [0] * 64
    black_masks = [0] * 64

    for square in range(64):
        row, col = divmod(square, 8)
        wm = 0
        bm = 0

        for c in range(max(0, col - 1), min(7, col + 1) + 1):
            for r in range(row + 1, 8):
                wm |= 1 << (r * 8 + c)
            for r in range(0, row):
                bm |= 1 << (r * 8 + c)

        white_masks[square] = wm
        black_masks[square] = bm

    return white_masks, black_masks


PASS_WHITE, PASS_BLACK = _make_pass_masks()


def _white_attacks(bits):
    return (
        ((bits & NOT_COL0) << 7)
        | ((bits & NOT_COL7) << 9)
    ) & ALL


def _black_attacks(bits):
    return (
        ((bits & NOT_COL0) >> 9)
        | ((bits & NOT_COL7) >> 7)
    )


def _generate_moves(white, black, side):
    """Moves are encoded as from_square * 64 + to_square."""
    moves = []
    occupied = white | black

    if side == 1:
        own = white
        pieces = white

        while pieces:
            from_bit = pieces & -pieces
            source = from_bit.bit_length() - 1
            pieces ^= from_bit
            col = source & 7

            target = source + 8
            if target < 64 and not (occupied & (1 << target)):
                moves.append((source << 6) | target)

            if col > 0:
                target = source + 7
                if target < 64 and not (own & (1 << target)):
                    moves.append((source << 6) | target)

            if col < 7:
                target = source + 9
                if target < 64 and not (own & (1 << target)):
                    moves.append((source << 6) | target)

    else:
        own = black
        pieces = black

        while pieces:
            from_bit = pieces & -pieces
            source = from_bit.bit_length() - 1
            pieces ^= from_bit
            col = source & 7

            target = source - 8
            if target >= 0 and not (occupied & (1 << target)):
                moves.append((source << 6) | target)

            if col > 0:
                target = source - 9
                if target >= 0 and not (own & (1 << target)):
                    moves.append((source << 6) | target)

            if col < 7:
                target = source - 7
                if target >= 0 and not (own & (1 << target)):
                    moves.append((source << 6) | target)

    return moves


def _apply_move(white, black, side, move):
    source = move >> 6
    target = move & 63
    source_bit = 1 << source
    target_bit = 1 << target

    if side == 1:
        white = (white ^ source_bit) | target_bit
        black &= ~target_bit
    else:
        black = (black ^ source_bit) | target_bit
        white &= ~target_bit

    return white, black


def _has_goal_move(white, black, side):
    occupied = white | black

    if side == 1:
        pieces = white & ROW6
        if not pieces:
            return False

        straight = ((pieces << 8) & ROW7) & (ALL ^ occupied)
        diagonal = (
            ((pieces & NOT_COL0) << 7)
            | ((pieces & NOT_COL7) << 9)
        ) & ROW7 & (ALL ^ white)
        return bool(straight | diagonal)

    pieces = black & ROW1
    if not pieces:
        return False

    straight = (pieces >> 8) & ROW0 & (ALL ^ occupied)
    diagonal = (
        ((pieces & NOT_COL0) >> 9)
        | ((pieces & NOT_COL7) >> 7)
    ) & ROW0 & (ALL ^ black)
    return bool(straight | diagonal)


def _can_win_now(white, black, side):
    if _has_goal_move(white, black, side):
        return True

    if side == 1:
        return black.bit_count() == 1 and bool(_white_attacks(white) & black)

    return white.bit_count() == 1 and bool(_black_attacks(black) & white)


class _SearchTimeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.killers = [[-1, -1] for _ in range(80)]
        self.history = [[0] * 4096 for _ in range(2)]

    def _check_time(self):
        self.nodes += 1
        if (self.nodes & 127) == 0 and time.perf_counter() >= self.deadline:
            raise _SearchTimeout

    @staticmethod
    def _terminal_score(white, black, side, ply):
        white_won = not black or bool(white & ROW7)
        black_won = not white or bool(black & ROW0)

        if white_won:
            return MATE - ply if side == 1 else -MATE + ply
        if black_won:
            return MATE - ply if side == 0 else -MATE + ply
        return None

    @staticmethod
    def _side_position_score(bits, enemy, is_white):
        score = bits.bit_count() * 170
        pieces = bits

        while pieces:
            bit = pieces & -pieces
            square = bit.bit_length() - 1
            pieces ^= bit

            row, col = divmod(square, 8)
            progress = row if is_white else 7 - row

            score += PROGRESS_BONUS[progress]
            score += CENTER_BONUS[col]

            pass_mask = PASS_WHITE[square] if is_white else PASS_BLACK[square]
            if not (enemy & pass_mask):
                score += PASSED_BONUS[progress]

        return score

    def evaluate(self, white, black, side):
        white_score = self._side_position_score(white, black, True)
        black_score = self._side_position_score(black, white, False)

        white_attacks = _white_attacks(white)
        black_attacks = _black_attacks(black)

        # Supported and connected pieces.
        white_score += (white_attacks & white).bit_count() * 18
        black_score += (black_attacks & black).bit_count() * 18

        # Pressure against opposing pieces.
        white_score += (white_attacks & black).bit_count() * 9
        black_score += (black_attacks & white).bit_count() * 9

        # Unsupported attacked pieces are especially vulnerable.
        white_threatened = black_attacks & white
        black_threatened = white_attacks & black

        white_score -= white_threatened.bit_count() * 20
        black_score -= black_threatened.bit_count() * 20

        white_score -= (white_threatened & ~white_attacks).bit_count() * 30
        black_score -= (black_threatened & ~black_attacks).bit_count() * 30

        occupied = white | black
        empty = ALL ^ occupied

        white_mobility = (
            ((white << 8) & ALL & empty).bit_count()
            + (((white & NOT_COL0) << 7) & ALL & (ALL ^ white)).bit_count()
            + (((white & NOT_COL7) << 9) & ALL & (ALL ^ white)).bit_count()
        )
        black_mobility = (
            ((black >> 8) & empty).bit_count()
            + (((black & NOT_COL0) >> 9) & (ALL ^ black)).bit_count()
            + (((black & NOT_COL7) >> 7) & (ALL ^ black)).bit_count()
        )

        white_score += white_mobility * 2
        black_score += black_mobility * 2

        relative = (
            white_score - black_score
            if side == 1
            else black_score - white_score
        )

        # Promotion and final-capture threats dominate positional concerns.
        if _can_win_now(white, black, side):
            return 70_000 + relative
        if _can_win_now(white, black, 1 - side):
            return -52_000 + relative

        return relative

    def _ordered_moves(self, white, black, side, moves, tt_move, ply):
        own = white if side == 1 else black
        enemy = black if side == 1 else white
        enemy_attacks = _black_attacks(black) if side == 1 else _white_attacks(white)
        enemy_count = enemy.bit_count()

        killer1, killer2 = self.killers[ply]
        scored = []

        for move in moves:
            source = move >> 6
            target = move & 63
            source_bit = 1 << source
            target_bit = 1 << target
            row, col = divmod(target, 8)

            capture = bool(enemy & target_bit)
            progress = row if side == 1 else 7 - row

            score = progress * 80 + CENTER_BONUS[col] * 4

            if move == tt_move:
                score += 2_000_000

            if (side == 1 and row == 7) or (side == 0 and row == 0):
                score += 600_000

            if capture:
                victim_progress = (7 - row) if side == 1 else row
                score += 12_000 + victim_progress * 180
                if enemy_count == 1:
                    score += 600_000
            else:
                if move == killer1:
                    score += 8_000
                elif move == killer2:
                    score += 6_000
                score += min(self.history[side][move], 6_000)

            if progress == 6:
                score += 2_500
            elif progress == 5:
                score += 650

            remaining_own = own ^ source_bit
            friendly_support = (
                _white_attacks(remaining_own)
                if side == 1
                else _black_attacks(remaining_own)
            )

            if friendly_support & target_bit:
                score += 220
            if enemy_attacks & target_bit:
                score -= 380
                if friendly_support & target_bit:
                    score += 150

            scored.append((score, move))

        scored.sort(reverse=True)
        return [move for _, move in scored]

    def search(self, white, black, side, depth, alpha, beta, ply):
        self._check_time()

        terminal = self._terminal_score(white, black, side, ply)
        if terminal is not None:
            return terminal

        if depth <= 0:
            return self.evaluate(white, black, side)

        key = (white, black, side)
        alpha_original = alpha
        beta_original = beta
        entry = self.tt.get(key)
        tt_move = -1

        if entry is not None:
            stored_depth, flag, score, tt_move = entry
            if stored_depth >= depth:
                if flag == EXACT:
                    return score
                if flag == LOWER:
                    alpha = max(alpha, score)
                else:
                    beta = min(beta, score)
                if alpha >= beta:
                    return score

        moves = _generate_moves(white, black, side)
        if not moves:
            return -MATE + ply

        moves = self._ordered_moves(
            white, black, side, moves, tt_move, min(ply, 79)
        )

        best_score = -INF
        best_move = moves[0]
        first_move = True

        own_enemy = black if side == 1 else white

        for index, move in enumerate(moves):
            target = move & 63
            target_bit = 1 << target
            capture = bool(own_enemy & target_bit)
            target_row = target >> 3
            progress = target_row if side == 1 else 7 - target_row

            new_white, new_black = _apply_move(white, black, side, move)
            child_depth = depth - 1

            if first_move:
                score = -self.search(
                    new_white,
                    new_black,
                    1 - side,
                    child_depth,
                    -beta,
                    -alpha,
                    ply + 1,
                )
                first_move = False
            else:
                reduction = 0
                if (
                    depth >= 4
                    and index >= 6
                    and not capture
                    and progress < 5
                ):
                    reduction = 1
                    if depth >= 7 and index >= 14:
                        reduction = 2

                reduced_depth = max(0, child_depth - reduction)
                score = -self.search(
                    new_white,
                    new_black,
                    1 - side,
                    reduced_depth,
                    -alpha - 1,
                    -alpha,
                    ply + 1,
                )

                if reduction and score > alpha:
                    score = -self.search(
                        new_white,
                        new_black,
                        1 - side,
                        child_depth,
                        -alpha - 1,
                        -alpha,
                        ply + 1,
                    )

                if alpha < score < beta:
                    score = -self.search(
                        new_white,
                        new_black,
                        1 - side,
                        child_depth,
                        -beta,
                        -alpha,
                        ply + 1,
                    )

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score

            if alpha >= beta:
                if not capture:
                    p = min(ply, 79)
                    if move != self.killers[p][0]:
                        self.killers[p][1] = self.killers[p][0]
                        self.killers[p][0] = move
                    self.history[side][move] = min(
                        20_000,
                        self.history[side][move] + depth * depth,
                    )
                break

        if best_score <= alpha_original:
            flag = UPPER
        elif best_score >= beta_original:
            flag = LOWER
        else:
            flag = EXACT

        old_entry = self.tt.get(key)
        if old_entry is None or depth >= old_entry[0]:
            self.tt[key] = (depth, flag, best_score, best_move)

        return best_score


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.perf_counter()
    deadline = start_time + 0.90

    me_bits = 0
    opp_bits = 0

    for row, col in me:
        me_bits |= 1 << (row * 8 + col)
    for row, col in opp:
        opp_bits |= 1 << (row * 8 + col)

    if color == "w":
        white = me_bits
        black = opp_bits
        side = 1
    else:
        white = opp_bits
        black = me_bits
        side = 0

    legal_moves = _generate_moves(white, black, side)

    # Normal arena calls are made only for nonterminal positions.
    if not legal_moves:
        return ((0, 0), (0, 0))

    enemy = black if side == 1 else white
    enemy_count = enemy.bit_count()

    # Return forced immediate wins without spending search time.
    for move in legal_moves:
        target = move & 63
        target_row = target >> 3
        target_bit = 1 << target

        reaches_goal = (
            (side == 1 and target_row == 7)
            or (side == 0 and target_row == 0)
        )
        captures_last = enemy_count == 1 and bool(enemy & target_bit)

        if reaches_goal or captures_last:
            source = move >> 6
            return (divmod(source, 8), divmod(target, 8))

    engine = _Engine(deadline)

    # Establish a legal, positionally ordered fallback before searching.
    fallback_order = engine._ordered_moves(
        white, black, side, legal_moves, -1, 0
    )
    best_move = fallback_order[0]

    for depth in range(1, 30):
        try:
            score = engine.search(
                white, black, side, depth, -INF, INF, 0
            )
            root_entry = engine.tt.get((white, black, side))
            if root_entry is not None and root_entry[0] >= depth:
                best_move = root_entry[3]

            if abs(score) >= MATE - 1000:
                break

            if time.perf_counter() >= deadline:
                break
        except _SearchTimeout:
            break

    source = best_move >> 6
    target = best_move & 63
    return (divmod(source, 8), divmod(target, 8))
