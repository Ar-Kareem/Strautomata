
from __future__ import annotations

from typing import List, Tuple, Dict, Set

Square = Tuple[int, int]
Move = Tuple[Square, Square]


def policy(my_men, my_kings, opp_men, opp_kings, color) -> Move:
    my_men = [tuple(x) for x in my_men]
    my_kings = [tuple(x) for x in my_kings]
    opp_men = [tuple(x) for x in opp_men]
    opp_kings = [tuple(x) for x in opp_kings]

    state = State(
        black_men=set(my_men) if color == 'b' else set(opp_men),
        black_kings=set(my_kings) if color == 'b' else set(opp_kings),
        white_men=set(opp_men) if color == 'b' else set(my_men),
        white_kings=set(opp_kings) if color == 'b' else set(my_kings),
        turn=color,
    )

    legal = generate_legal_sequences(state)
    if not legal:
        # Should not happen in valid arena states, but return something safe-looking.
        # Fallback to any owned piece square to itself is not legal, so instead synthesize
        # from available pieces to a nearby diagonal if possible.
        pieces = list(my_men) + list(my_kings)
        if pieces:
            fr = pieces[0]
            for dr in (-1, 1):
                for dc in (-1, 1):
                    to = (fr[0] + dr, fr[1] + dc)
                    if in_bounds(*to):
                        return (fr, to)
            return (fr, fr)
        return ((0, 1), (1, 0))

    # Iterative preference by branching factor / tactical urgency
    if any(len(seq) > 2 for seq in legal):
        depth = 8
    elif len(legal) <= 6:
        depth = 7
    elif len(legal) <= 12:
        depth = 6
    else:
        depth = 5

    best_seq = choose_best_move(state, depth)
    if not best_seq:
        best_seq = legal[0]

    return (best_seq[0], best_seq[1])


class State:
    __slots__ = ("black_men", "black_kings", "white_men", "white_kings", "turn")

    def __init__(
        self,
        black_men: Set[Square],
        black_kings: Set[Square],
        white_men: Set[Square],
        white_kings: Set[Square],
        turn: str,
    ):
        self.black_men = black_men
        self.black_kings = black_kings
        self.white_men = white_men
        self.white_kings = white_kings
        self.turn = turn

    def clone(self) -> "State":
        return State(
            set(self.black_men),
            set(self.black_kings),
            set(self.white_men),
            set(self.white_kings),
            self.turn,
        )


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def playable(r: int, c: int) -> bool:
    return (r + c) % 2 == 1


def side_sets(state: State, side: str):
    if side == 'b':
        return state.black_men, state.black_kings, state.white_men, state.white_kings
    else:
        return state.white_men, state.white_kings, state.black_men, state.black_kings


def occupied_map(state: State) -> Dict[Square, Tuple[str, str]]:
    occ = {}
    for p in state.black_men:
        occ[p] = ('b', 'm')
    for p in state.black_kings:
        occ[p] = ('b', 'k')
    for p in state.white_men:
        occ[p] = ('w', 'm')
    for p in state.white_kings:
        occ[p] = ('w', 'k')
    return occ


def man_dirs(color: str):
    return [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]


def king_dirs():
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def promotion_row(color: str) -> int:
    return 0 if color == 'b' else 7


def generate_legal_sequences(state: State) -> List[List[Square]]:
    side = state.turn
    men, kings, opp_men, opp_kings = side_sets(state, side)

    captures = []
    for p in men:
        captures.extend(generate_captures_for_piece(state, p, False, side))
    for p in kings:
        captures.extend(generate_captures_for_piece(state, p, True, side))

    if captures:
        return captures

    moves = []
    occ = occupied_map(state)
    for p in men:
        for dr, dc in man_dirs(side):
            nr, nc = p[0] + dr, p[1] + dc
            if in_bounds(nr, nc) and playable(nr, nc) and (nr, nc) not in occ:
                moves.append([p, (nr, nc)])
    for p in kings:
        for dr, dc in king_dirs():
            nr, nc = p[0] + dr, p[1] + dc
            if in_bounds(nr, nc) and playable(nr, nc) and (nr, nc) not in occ:
                moves.append([p, (nr, nc)])
    return moves


def generate_captures_for_piece(state: State, start: Square, is_king: bool, side: str) -> List[List[Square]]:
    occ = occupied_map(state)
    results = []

    def dfs(pos: Square, piece_is_king: bool, occ_local: Dict[Square, Tuple[str, str]], path: List[Square]):
        dirs = king_dirs() if piece_is_king else man_dirs(side)
        found = False
        for dr, dc in dirs:
            mr, mc = pos[0] + dr, pos[1] + dc
            lr, lc = pos[0] + 2 * dr, pos[1] + 2 * dc
            if not (in_bounds(mr, mc) and in_bounds(lr, lc) and playable(lr, lc)):
                continue
            if (mr, mc) not in occ_local:
                continue
            mid_side, _ = occ_local[(mr, mc)]
            if mid_side == side:
                continue
            if (lr, lc) in occ_local:
                continue

            found = True
            new_occ = dict(occ_local)
            if pos in new_occ:
                del new_occ[pos]
            del new_occ[(mr, mc)]

            promoted = piece_is_king or (lr == promotion_row(side))
            new_occ[(lr, lc)] = (side, 'k' if promoted else 'm')

            dfs((lr, lc), promoted, new_occ, path + [(lr, lc)])

        if not found and len(path) > 1:
            results.append(path)

    dfs(start, is_king, occ, [start])
    return results


def apply_sequence(state: State, seq: List[Square]) -> State:
    new_state = state.clone()
    side = state.turn

    men, kings, opp_men, opp_kings = side_sets(new_state, side)
    start = seq[0]
    end = seq[-1]

    if start in men:
        men.remove(start)
        is_king = False
    else:
        kings.remove(start)
        is_king = True

    cur = start
    for nxt in seq[1:]:
        if abs(nxt[0] - cur[0]) == 2:
            mr, mc = (cur[0] + nxt[0]) // 2, (cur[1] + nxt[1]) // 2
            if (mr, mc) in opp_men:
                opp_men.remove((mr, mc))
            elif (mr, mc) in opp_kings:
                opp_kings.remove((mr, mc))
        cur = nxt

    if not is_king and end[0] == promotion_row(side):
        is_king = True

    if is_king:
        kings.add(end)
    else:
        men.add(end)

    new_state.turn = 'w' if side == 'b' else 'b'
    return new_state


def choose_best_move(state: State, depth: int) -> List[Square] | None:
    legal = generate_legal_sequences(state)
    if not legal:
        return None

    maximizing_side = state.turn
    alpha = -10**18
    beta = 10**18
    best_score = -10**18
    best_seq = legal[0]

    legal = order_moves(state, legal)

    for seq in legal:
        child = apply_sequence(state, seq)
        score = minimax(child, depth - 1, alpha, beta, False, maximizing_side)
        if score > best_score:
            best_score = score
            best_seq = seq
        alpha = max(alpha, best_score)

    return best_seq


def minimax(state: State, depth: int, alpha: float, beta: float, maximizing: bool, root_side: str) -> float:
    legal = generate_legal_sequences(state)
    if depth <= 0 or not legal:
        return evaluate(state, root_side, legal)

    legal = order_moves(state, legal)

    if maximizing:
        value = -10**18
        for seq in legal:
            child = apply_sequence(state, seq)
            value = max(value, minimax(child, depth - 1, alpha, beta, False, root_side))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 10**18
        for seq in legal:
            child = apply_sequence(state, seq)
            value = min(value, minimax(child, depth - 1, alpha, beta, True, root_side))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def order_moves(state: State, moves: List[List[Square]]) -> List[List[Square]]:
    caps = [m for m in moves if abs(m[1][0] - m[0][0]) == 2]
    if caps:
        return sorted(moves, key=capture_order_key, reverse=True)
    return sorted(moves, key=lambda m: quiet_order_key(state, m), reverse=True)


def capture_order_key(seq: List[Square]):
    length = len(seq) - 1
    end = seq[-1]
    promo = 1 if (end[0] == 0 or end[0] == 7) else 0
    return (length, promo, center_bonus(end))


def quiet_order_key(state: State, seq: List[Square]):
    start, end = seq[0], seq[1]
    side = state.turn
    men, kings, _, _ = side_sets(state, side)
    is_king = start in kings
    promo = 0
    if not is_king and end[0] == promotion_row(side):
        promo = 50
    return promo + center_bonus(end) + advancement_bonus(side, end, is_king)


def center_bonus(p: Square) -> float:
    r, c = p
    return 3.5 - abs(r - 3.5) + 3.5 - abs(c - 3.5)


def advancement_bonus(side: str, p: Square, is_king: bool) -> float:
    if is_king:
        return 0.0
    return (7 - p[0]) if side == 'b' else p[0]


def evaluate(state: State, root_side: str, legal_now: List[List[Square]] | None = None) -> float:
    if legal_now is None:
        legal_now = generate_legal_sequences(state)

    bm, bk = len(state.black_men), len(state.black_kings)
    wm, wk = len(state.white_men), len(state.white_kings)

    # Terminal
    if bm + bk == 0:
        return -100000 if root_side == 'b' else 100000
    if wm + wk == 0:
        return 100000 if root_side == 'b' else -100000
    if not legal_now:
        return -90000 if state.turn == root_side else 90000

    score_black = 0.0
    score_white = 0.0

    score_black += 100 * bm + 175 * bk
    score_white += 100 * wm + 175 * wk

    for p in state.black_men:
        score_black += (7 - p[0]) * 6
        score_black += center_bonus(p) * 2
        score_black += safety_bonus(state, p, 'b', False)
    for p in state.white_men:
        score_white += p[0] * 6
        score_white += center_bonus(p) * 2
        score_white += safety_bonus(state, p, 'w', False)
    for p in state.black_kings:
        score_black += center_bonus(p) * 4 + safety_bonus(state, p, 'b', True)
    for p in state.white_kings:
        score_white += center_bonus(p) * 4 + safety_bonus(state, p, 'w', True)

    # Mobility
    turn_save = state.turn
    state.turn = 'b'
    black_moves = generate_legal_sequences(state)
    state.turn = 'w'
    white_moves = generate_legal_sequences(state)
    state.turn = turn_save

    score_black += len(black_moves) * 2
    score_white += len(white_moves) * 2

    # Capture pressure
    black_caps = sum(1 for m in black_moves if abs(m[1][0] - m[0][0]) == 2)
    white_caps = sum(1 for m in white_moves if abs(m[1][0] - m[0][0]) == 2)
    score_black += black_caps * 8
    score_white += white_caps * 8

    result = score_black - score_white
    return result if root_side == 'b' else -result


def safety_bonus(state: State, p: Square, side: str, is_king: bool) -> float:
    r, c = p
    bonus = 0.0

    if c == 0 or c == 7:
        bonus += 4.0
    if r == 0 or r == 7:
        bonus += 2.0

    # Light local support heuristic
    friends = 0
    enemies = 0
    occ = occupied_map(state)
    for dr in (-1, 1):
        for dc in (-1, 1):
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and (nr, nc) in occ:
                s, _ = occ[(nr, nc)]
                if s == side:
                    friends += 1
                else:
                    enemies += 1
    bonus += friends * 1.5
    bonus -= enemies * 1.0

    # Vulnerability approximation: if an enemy adjacent could jump us
    if is_vulnerable(state, p, side):
        bonus -= 8.0

    return bonus


def is_vulnerable(state: State, p: Square, side: str) -> bool:
    occ = occupied_map(state)
    enemy = 'w' if side == 'b' else 'b'
    r, c = p

    for dr, dc in king_dirs():
        ar, ac = r + dr, c + dc
        br, bc = r - dr, c - dc
        if not (in_bounds(ar, ac) and in_bounds(br, bc) and playable(br, bc)):
            continue
        if (ar, ac) in occ and (br, bc) not in occ:
            s, kind = occ[(ar, ac)]
            if s != enemy:
                continue
            if kind == 'k':
                return True
            # Enemy man can only capture forward relative to enemy
            if enemy == 'b':
                if br == ar - 2:
                    return True
            else:
                if br == ar + 2:
                    return True
    return False
