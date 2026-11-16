
from typing import List, Tuple, Dict, Set

Square = Tuple[int, int]
Move = Tuple[Square, Square]

BOARD_MIN = 0
BOARD_MAX = 7

MAN_VALUE = 100
KING_VALUE = 175
ADVANCE_VALUE = 8
CENTER_VALUE = 4
EDGE_VALUE = 3
MOBILITY_VALUE = 2
CAPTURE_BONUS = 25
PROMOTION_BONUS = 40


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r <= 7 and 0 <= c <= 7


def is_dark(r: int, c: int) -> bool:
    return ((r + c) & 1) == 1


def opp_color(color: str) -> str:
    return 'w' if color == 'b' else 'b'


def man_dirs(color: str):
    # black moves downward to lower rows, white upward to higher rows
    return [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]


def king_dirs():
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]


class State:
    __slots__ = ("my_men", "my_kings", "opp_men", "opp_kings", "color")

    def __init__(self, my_men, my_kings, opp_men, opp_kings, color):
        self.my_men = frozenset(my_men)
        self.my_kings = frozenset(my_kings)
        self.opp_men = frozenset(opp_men)
        self.opp_kings = frozenset(opp_kings)
        self.color = color

    def key(self):
        return (self.my_men, self.my_kings, self.opp_men, self.opp_kings, self.color)


def occupied_map(state: State) -> Dict[Square, int]:
    occ = {}
    for p in state.my_men:
        occ[p] = 1
    for p in state.my_kings:
        occ[p] = 2
    for p in state.opp_men:
        occ[p] = -1
    for p in state.opp_kings:
        occ[p] = -2
    return occ


def crown_row(color: str) -> int:
    return 0 if color == 'b' else 7


def swap_perspective(state: State) -> State:
    return State(state.opp_men, state.opp_kings, state.my_men, state.my_kings, opp_color(state.color))


def piece_dirs(is_king: bool, color: str):
    return king_dirs() if is_king else man_dirs(color)


def generate_simple_moves(state: State) -> List[Move]:
    occ = occupied_map(state)
    moves = []

    for p in state.my_men:
        r, c = p
        for dr, dc in man_dirs(state.color):
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and is_dark(nr, nc) and (nr, nc) not in occ:
                moves.append((p, (nr, nc)))

    for p in state.my_kings:
        r, c = p
        for dr, dc in king_dirs():
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and is_dark(nr, nc) and (nr, nc) not in occ:
                moves.append((p, (nr, nc)))

    return moves


def capture_sequences_from(state: State, start: Square, is_king_piece: bool) -> List[Tuple[Square, List[Square]]]:
    # Returns list of (final_square, captured_squares_sequence)
    occ0 = occupied_map(state)
    my_color = state.color

    results = []

    def dfs(pos: Square, is_king_now: bool, my_men: Set[Square], my_kings: Set[Square],
            opp_men: Set[Square], opp_kings: Set[Square], captured_seq: List[Square]):
        found = False
        r, c = pos
        dirs = king_dirs() if is_king_now else man_dirs(my_color)

        occ = {}
        for x in my_men:
            occ[x] = 1
        for x in my_kings:
            occ[x] = 2
        for x in opp_men:
            occ[x] = -1
        for x in opp_kings:
            occ[x] = -2

        for dr, dc in dirs:
            mr, mc = r + dr, c + dc
            lr, lc = r + 2 * dr, c + 2 * dc
            if not (in_bounds(mr, mc) and in_bounds(lr, lc) and is_dark(lr, lc)):
                continue
            if (mr, mc) not in occ or occ[(mr, mc)] >= 0 or (lr, lc) in occ:
                continue

            found = True

            new_my_men = set(my_men)
            new_my_kings = set(my_kings)
            new_opp_men = set(opp_men)
            new_opp_kings = set(opp_kings)

            if is_king_now:
                new_my_kings.remove(pos)
            else:
                new_my_men.remove(pos)

            if (mr, mc) in new_opp_men:
                new_opp_men.remove((mr, mc))
            else:
                new_opp_kings.remove((mr, mc))

            promoted = False
            if not is_king_now and lr == crown_row(my_color):
                new_my_kings.add((lr, lc))
                promoted = True
            else:
                if is_king_now:
                    new_my_kings.add((lr, lc))
                else:
                    new_my_men.add((lr, lc))

            dfs((lr, lc), is_king_now or promoted, new_my_men, new_my_kings, new_opp_men, new_opp_kings,
                captured_seq + [(mr, mc)])

        if not found and captured_seq:
            results.append((pos, captured_seq))

    my_men = set(state.my_men)
    my_kings = set(state.my_kings)
    opp_men = set(state.opp_men)
    opp_kings = set(state.opp_kings)

    dfs(start, is_king_piece, my_men, my_kings, opp_men, opp_kings, [])
    return results


def generate_capture_moves(state: State) -> List[Move]:
    moves = []
    for p in state.my_men:
        seqs = capture_sequences_from(state, p, False)
        for end_pos, _caps in seqs:
            moves.append((p, end_pos))
    for p in state.my_kings:
        seqs = capture_sequences_from(state, p, True)
        for end_pos, _caps in seqs:
            moves.append((p, end_pos))
    return moves


def has_any_capture(state: State) -> bool:
    for p in state.my_men:
        if capture_sequences_from(state, p, False):
            return True
    for p in state.my_kings:
        if capture_sequences_from(state, p, True):
            return True
    return False


def legal_moves(state: State) -> List[Move]:
    caps = generate_capture_moves(state)
    if caps:
        return caps
    return generate_simple_moves(state)


def apply_move(state: State, move: Move) -> State:
    frm, to = move
    is_king_piece = frm in state.my_kings

    # If capture exists, identify matching capture sequence to final destination.
    if has_any_capture(state):
        seqs = capture_sequences_from(state, frm, is_king_piece)
        chosen = None
        best_score = None
        for end_pos, caps in seqs:
            if end_pos == to:
                score = len(caps)
                if best_score is None or score > best_score:
                    best_score = score
                    chosen = caps
        if chosen is None:
            # Fallback: should not happen if move legal
            chosen = []

        my_men = set(state.my_men)
        my_kings = set(state.my_kings)
        opp_men = set(state.opp_men)
        opp_kings = set(state.opp_kings)

        if is_king_piece:
            my_kings.remove(frm)
        else:
            my_men.remove(frm)

        for cap in chosen:
            if cap in opp_men:
                opp_men.remove(cap)
            elif cap in opp_kings:
                opp_kings.remove(cap)

        promoted = (not is_king_piece and to[0] == crown_row(state.color))
        if is_king_piece or promoted:
            my_kings.add(to)
        else:
            my_men.add(to)

        next_state = State(opp_men, opp_kings, my_men, my_kings, opp_color(state.color))
        return next_state

    # Simple move
    my_men = set(state.my_men)
    my_kings = set(state.my_kings)
    opp_men = set(state.opp_men)
    opp_kings = set(state.opp_kings)

    if is_king_piece:
        my_kings.remove(frm)
        my_kings.add(to)
    else:
        my_men.remove(frm)
        if to[0] == crown_row(state.color):
            my_kings.add(to)
        else:
            my_men.add(to)

    next_state = State(opp_men, opp_kings, my_men, my_kings, opp_color(state.color))
    return next_state


def piece_square_score_man(pos: Square, color: str) -> int:
    r, c = pos
    advance = (7 - r) if color == 'b' else r
    center = 3 - abs(3.5 - c) + 3 - abs(3.5 - r)
    edge = 1 if c in (0, 7) else 0
    return ADVANCE_VALUE * advance + int(CENTER_VALUE * center) + EDGE_VALUE * edge


def piece_square_score_king(pos: Square) -> int:
    r, c = pos
    center = 3 - abs(3.5 - c) + 3 - abs(3.5 - r)
    edge = 1 if c in (0, 7) else 0
    return int(CENTER_VALUE * 1.5 * center) + EDGE_VALUE * edge


def evaluate(state: State) -> int:
    # evaluation from side to move perspective
    score = 0

    score += MAN_VALUE * len(state.my_men)
    score += KING_VALUE * len(state.my_kings)
    score -= MAN_VALUE * len(state.opp_men)
    score -= KING_VALUE * len(state.opp_kings)

    for p in state.my_men:
        score += piece_square_score_man(p, state.color)
    for p in state.my_kings:
        score += piece_square_score_king(p)

    oppc = opp_color(state.color)
    for p in state.opp_men:
        score -= piece_square_score_man(p, oppc)
    for p in state.opp_kings:
        score -= piece_square_score_king(p)

    my_moves = legal_moves(state)
    opp_moves = legal_moves(swap_perspective(state))
    score += MOBILITY_VALUE * (len(my_moves) - len(opp_moves))

    if not my_moves:
        score -= 100000
    if not opp_moves:
        score += 100000

    return score


def move_heuristic(state: State, move: Move) -> int:
    frm, to = move
    score = 0

    is_capture = abs(frm[0] - to[0]) >= 2
    if is_capture:
        seqs = capture_sequences_from(state, frm, frm in state.my_kings)
        maxcaps = 0
        for end_pos, caps in seqs:
            if end_pos == to:
                maxcaps = max(maxcaps, len(caps))
        score += CAPTURE_BONUS * maxcaps

    if frm in state.my_men and to[0] == crown_row(state.color):
        score += PROMOTION_BONUS

    tr, tc = to
    score += int(4 - abs(3.5 - tc)) + int(4 - abs(3.5 - tr))
    return score


TT = {}


def negamax(state: State, depth: int, alpha: int, beta: int) -> int:
    key = (state.key(), depth, alpha, beta)
    if key in TT:
        return TT[key]

    moves = legal_moves(state)
    if depth == 0 or not moves:
        val = evaluate(state)
        TT[key] = val
        return val

    moves.sort(key=lambda m: move_heuristic(state, m), reverse=True)

    best = -10**18
    for mv in moves:
        child = apply_move(state, mv)
        val = -negamax(child, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    TT[key] = best
    return best


def choose_move(state: State) -> Move:
    moves = legal_moves(state)
    if not moves:
        # Should not happen in normal play, but avoid crashing.
        # Return any placeholder legal-looking tuple from own piece to itself if possible.
        if state.my_men:
            p = next(iter(state.my_men))
            return (p, p)
        if state.my_kings:
            p = next(iter(state.my_kings))
            return (p, p)
        return ((0, 1), (0, 1))

    moves.sort(key=lambda m: move_heuristic(state, m), reverse=True)

    piece_count = len(state.my_men) + len(state.my_kings) + len(state.opp_men) + len(state.opp_kings)
    if piece_count >= 20:
        depth = 5
    elif piece_count >= 12:
        depth = 7
    else:
        depth = 9

    best_move = moves[0]
    best_val = -10**18
    alpha = -10**18
    beta = 10**18

    for mv in moves:
        child = apply_move(state, mv)
        val = -negamax(child, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    return best_move


def policy(my_men, my_kings, opp_men, opp_kings, color) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    try:
        state = State(tuple(my_men), tuple(my_kings), tuple(opp_men), tuple(opp_kings), color)
        mv = choose_move(state)

        # Final legality guard
        legals = legal_moves(state)
        if mv in legals:
            return mv
        if legals:
            return legals[0]

        # Emergency fallback: construct some move if possible
        if my_men:
            p = my_men[0]
            occ = set(my_men) | set(my_kings) | set(opp_men) | set(opp_kings)
            for dr, dc in man_dirs(color):
                q = (p[0] + dr, p[1] + dc)
                if in_bounds(*q) and is_dark(*q) and q not in occ:
                    return (p, q)
        if my_kings:
            p = my_kings[0]
            occ = set(my_men) | set(my_kings) | set(opp_men) | set(opp_kings)
            for dr, dc in king_dirs():
                q = (p[0] + dr, p[1] + dc)
                if in_bounds(*q) and is_dark(*q) and q not in occ:
                    return (p, q)

        if my_men:
            p = my_men[0]
            return (p, p)
        if my_kings:
            p = my_kings[0]
            return (p, p)
        return ((0, 1), (0, 1))
    except Exception:
        # Extreme fallback: try to return first obviously legal move found
        occ = set(my_men) | set(my_kings) | set(opp_men) | set(opp_kings)

        # Mandatory capture check
        def emergency_caps():
            res = []
            for p in my_men:
                for dr, dc in man_dirs(color):
                    mr, mc = p[0] + dr, p[1] + dc
                    lr, lc = p[0] + 2 * dr, p[1] + 2 * dc
                    if in_bounds(mr, mc) and in_bounds(lr, lc) and is_dark(lr, lc):
                        if (mr, mc) in set(opp_men) | set(opp_kings) and (lr, lc) not in occ:
                            res.append((p, (lr, lc)))
            for p in my_kings:
                for dr, dc in king_dirs():
                    mr, mc = p[0] + dr, p[1] + dc
                    lr, lc = p[0] + 2 * dr, p[1] + 2 * dc
                    if in_bounds(mr, mc) and in_bounds(lr, lc) and is_dark(lr, lc):
                        if (mr, mc) in set(opp_men) | set(opp_kings) and (lr, lc) not in occ:
                            res.append((p, (lr, lc)))
            return res

        caps = emergency_caps()
        if caps:
            return caps[0]

        for p in my_men:
            for dr, dc in man_dirs(color):
                q = (p[0] + dr, p[1] + dc)
                if in_bounds(*q) and is_dark(*q) and q not in occ:
                    return (p, q)
        for p in my_kings:
            for dr, dc in king_dirs():
                q = (p[0] + dr, p[1] + dc)
                if in_bounds(*q) and is_dark(*q) and q not in occ:
                    return (p, q)

        if my_men:
            return (my_men[0], my_men[0])
        if my_kings:
            return (my_kings[0], my_kings[0])
        return ((0, 1), (0, 1))
