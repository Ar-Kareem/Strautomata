
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

Move = Tuple[int, int]  # (from_idx, to_idx)


ROW0_MASK = sum(1 << i for i in range(0, 8))
ROW7_MASK = sum(1 << i for i in range(56, 64))

MATE = 10**9
INF = 10**18


class Timeout(Exception):
    pass


def idx_to_rc(idx: int) -> Tuple[int, int]:
    return idx // 8, idx % 8


def rc_to_idx(r: int, c: int) -> int:
    return r * 8 + c


def iter_bits(bb: int):
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        yield idx
        bb ^= lsb


@dataclass(frozen=True)
class TTEntry:
    depth: int
    score: int
    best: Optional[Move]


class BreakthroughAI:
    def __init__(self, time_limit_s: float = 0.95):
        self.time_limit_s = time_limit_s
        self.start = 0.0
        self.tt: Dict[Tuple[int, int, str], TTEntry] = {}

    def time_up(self) -> bool:
        return (time.perf_counter() - self.start) >= self.time_limit_s

    def terminal_score(self, w_bb: int, b_bb: int, to_move: str, ply: int) -> Optional[int]:
        # Win conditions (regardless of side to move)
        if w_bb == 0:
            # black has captured all white
            return (MATE - ply) if to_move == "b" else -(MATE - ply)
        if b_bb == 0:
            return (MATE - ply) if to_move == "w" else -(MATE - ply)

        w_win = (w_bb & ROW7_MASK) != 0
        b_win = (b_bb & ROW0_MASK) != 0
        if w_win:
            return (MATE - ply) if to_move == "w" else -(MATE - ply)
        if b_win:
            return (MATE - ply) if to_move == "b" else -(MATE - ply)

        return None

    def gen_moves(self, w_bb: int, b_bb: int, to_move: str) -> List[Tuple[Move, bool]]:
        """Return list of ((from_idx,to_idx), is_capture)."""
        occ = w_bb | b_bb
        moves: List[Tuple[Move, bool]] = []

        if to_move == "w":
            own = w_bb
            opp = b_bb
            dir_row = 1
        else:
            own = b_bb
            opp = w_bb
            dir_row = -1

        for fr in iter_bits(own):
            r, c = idx_to_rc(fr)
            nr = r + dir_row
            if nr < 0 or nr > 7:
                continue

            # forward
            to = fr + (8 * dir_row)
            if (occ >> to) & 1 == 0:
                moves.append(((fr, to), False))

            # diag left
            if c > 0:
                to = fr + (8 * dir_row) - 1
                if ((own >> to) & 1) == 0:
                    if ((opp >> to) & 1) == 1:
                        moves.append(((fr, to), True))
                    elif ((occ >> to) & 1) == 0:
                        moves.append(((fr, to), False))

            # diag right
            if c < 7:
                to = fr + (8 * dir_row) + 1
                if ((own >> to) & 1) == 0:
                    if ((opp >> to) & 1) == 1:
                        moves.append(((fr, to), True))
                    elif ((occ >> to) & 1) == 0:
                        moves.append(((fr, to), False))

        return moves

    def apply_move(self, w_bb: int, b_bb: int, to_move: str, mv: Move) -> Tuple[int, int]:
        fr, to = mv
        fr_bit = 1 << fr
        to_bit = 1 << to
        if to_move == "w":
            w_bb ^= fr_bit
            # capture if needed
            if (b_bb & to_bit) != 0:
                b_bb ^= to_bit
            w_bb |= to_bit
        else:
            b_bb ^= fr_bit
            if (w_bb & to_bit) != 0:
                w_bb ^= to_bit
            b_bb |= to_bit
        return w_bb, b_bb

    def can_win_next(self, w_bb: int, b_bb: int, color: str) -> bool:
        occ = w_bb | b_bb
        if color == "w":
            own, opp, dir_row, goal_row = w_bb, b_bb, 1, 7
        else:
            own, opp, dir_row, goal_row = b_bb, w_bb, -1, 0

        for fr in iter_bits(own):
            r, c = idx_to_rc(fr)
            nr = r + dir_row
            if nr != goal_row:
                continue
            # forward into goal
            to = fr + 8 * dir_row
            if 0 <= to < 64 and ((occ >> to) & 1) == 0:
                return True
            # diag into goal (empty or capture)
            if c > 0:
                to = fr + 8 * dir_row - 1
                if 0 <= to < 64 and (((own >> to) & 1) == 0) and ((((opp >> to) & 1) == 1) or (((occ >> to) & 1) == 0)):
                    return True
            if c < 7:
                to = fr + 8 * dir_row + 1
                if 0 <= to < 64 and (((own >> to) & 1) == 0) and ((((opp >> to) & 1) == 1) or (((occ >> to) & 1) == 0)):
                    return True
        return False

    def passed_pawn_bonus(self, own_bb: int, opp_bb: int, color: str) -> int:
        # Passed pawn heuristic: no opponent pawn in the forward cone (same/adjacent files) ahead.
        bonus = 0
        for idx in iter_bits(own_bb):
            r, c = idx_to_rc(idx)
            files = (c - 1, c, c + 1)
            ok = True
            if color == "w":
                rows = range(r + 1, 8)
            else:
                rows = range(r - 1, -1, -1)
            for rr in rows:
                for ff in files:
                    if 0 <= ff <= 7:
                        j = rc_to_idx(rr, ff)
                        if (opp_bb >> j) & 1:
                            ok = False
                            break
                if not ok:
                    break
            if ok:
                # Bigger bonus if more advanced
                adv = r if color == "w" else (7 - r)
                bonus += 18 + 2 * adv
        return bonus

    def eval(self, w_bb: int, b_bb: int, to_move: str) -> int:
        # Score from perspective of side to move (positive good for to_move).
        my_bb = w_bb if to_move == "w" else b_bb
        op_bb = b_bb if to_move == "w" else w_bb

        my_count = my_bb.bit_count()
        op_count = op_bb.bit_count()

        material = 120 * (my_count - op_count)

        # Advancement
        adv = 0
        for idx in iter_bits(my_bb):
            r, _ = idx_to_rc(idx)
            adv += r if to_move == "w" else (7 - r)
        for idx in iter_bits(op_bb):
            r, _ = idx_to_rc(idx)
            adv -= r if to_move == "b" else (7 - r)  # opponent advancement reduces my score
        advancement = 10 * adv

        # Mobility
        mob = len(self.gen_moves(w_bb, b_bb, to_move))
        mobility = 3 * mob

        # Passed pawns
        if to_move == "w":
            passed = self.passed_pawn_bonus(w_bb, b_bb, "w") - self.passed_pawn_bonus(b_bb, w_bb, "b")
        else:
            passed = self.passed_pawn_bonus(b_bb, w_bb, "b") - self.passed_pawn_bonus(w_bb, b_bb, "w")

        # Immediate threats (1-move win)
        my_threat = 600 if self.can_win_next(w_bb, b_bb, to_move) else 0
        op_threat = 700 if self.can_win_next(w_bb, b_bb, "b" if to_move == "w" else "w") else 0

        return material + advancement + mobility + passed + my_threat - op_threat

    def move_order_key(self, w_bb: int, b_bb: int, to_move: str, mv: Move, is_cap: bool) -> int:
        fr, to = mv
        tr, tc = idx_to_rc(to)
        # Winning move?
        if to_move == "w" and tr == 7:
            return 10_000_000
        if to_move == "b" and tr == 0:
            return 10_000_000

        score = 0
        if is_cap:
            score += 500_000

        # Prefer advancing
        score += (tr if to_move == "w" else (7 - tr)) * 10_000

        # Prefer central files
        score -= int(abs(tc - 3.5) * 1000)

        # Slight preference for diagonal moves (often create threats / avoid blocks)
        fr_r, fr_c = idx_to_rc(fr)
        if fr_c != tc:
            score += 500

        return score

    def negamax(self, w_bb: int, b_bb: int, to_move: str, depth: int, alpha: int, beta: int, ply: int) -> Tuple[int, Optional[Move]]:
        if self.time_up():
            raise Timeout()

        term = self.terminal_score(w_bb, b_bb, to_move, ply)
        if term is not None:
            return term, None
        if depth <= 0:
            return self.eval(w_bb, b_bb, to_move), None

        key = (w_bb, b_bb, to_move)
        ent = self.tt.get(key)
        if ent is not None and ent.depth >= depth:
            return ent.score, ent.best

        moves = self.gen_moves(w_bb, b_bb, to_move)
        if not moves:
            # In standard Breakthrough this is effectively a loss (no moves).
            # Return a very negative score (from side to move).
            return -(MATE - ply), None

        # Order moves
        moves.sort(key=lambda x: self.move_order_key(w_bb, b_bb, to_move, x[0], x[1]), reverse=True)

        best_move: Optional[Move] = None
        best_score = -INF

        next_to_move = "b" if to_move == "w" else "w"

        for (mv, _) in moves:
            w2, b2 = self.apply_move(w_bb, b_bb, to_move, mv)
            score, _ = self.negamax(w2, b2, next_to_move, depth - 1, -beta, -alpha, ply + 1)
            score = -score

            if score > best_score:
                best_score = score
                best_move = mv
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                break

        self.tt[key] = TTEntry(depth=depth, score=int(best_score), best=best_move)
        return int(best_score), best_move

    def choose(self, w_bb: int, b_bb: int, to_move: str) -> Move:
        self.start = time.perf_counter()
        self.tt.clear()

        # Always have a legal fallback
        root_moves = self.gen_moves(w_bb, b_bb, to_move)
        if not root_moves:
            # Should not happen in arena; but avoid crashing.
            # Return a dummy (still illegal) would be disqualifying; raise instead.
            # (If this happens, game state is already terminal / invalid for move.)
            raise RuntimeError("No legal moves available.")

        root_moves.sort(key=lambda x: self.move_order_key(w_bb, b_bb, to_move, x[0], x[1]), reverse=True)
        fallback = root_moves[0][0]

        best = fallback
        best_score = -INF

        # Iterative deepening
        for depth in range(1, 8):  # usually reaches 4-6 within limit
            try:
                score, mv = self.negamax(w_bb, b_bb, to_move, depth, -INF, INF, 0)
                if mv is not None:
                    best = mv
                    best_score = score
            except Timeout:
                break

        return best


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Build bitboards as absolute colors (white/black), not "me/opp"
    w_bb = 0
    b_bb = 0

    if color not in ("w", "b"):
        color = "w"

    if color == "w":
        for r, c in me:
            if 0 <= r <= 7 and 0 <= c <= 7:
                w_bb |= 1 << rc_to_idx(r, c)
        for r, c in opp:
            if 0 <= r <= 7 and 0 <= c <= 7:
                b_bb |= 1 << rc_to_idx(r, c)
    else:
        for r, c in me:
            if 0 <= r <= 7 and 0 <= c <= 7:
                b_bb |= 1 << rc_to_idx(r, c)
        for r, c in opp:
            if 0 <= r <= 7 and 0 <= c <= 7:
                w_bb |= 1 << rc_to_idx(r, c)

    ai = BreakthroughAI(time_limit_s=0.95)

    try:
        fr, to = ai.choose(w_bb, b_bb, color)
    except Exception:
        # Absolute last-resort fallback: generate a move directly and return the first legal one.
        # (Should be legal if any exists.)
        occ = w_bb | b_bb
        own = w_bb if color == "w" else b_bb
        opp_bb = b_bb if color == "w" else w_bb
        dir_row = 1 if color == "w" else -1
        found = None
        for fr in iter_bits(own):
            r, c = idx_to_rc(fr)
            nr = r + dir_row
            if 0 <= nr <= 7:
                # forward
                to = fr + 8 * dir_row
                if 0 <= to < 64 and ((occ >> to) & 1) == 0:
                    found = (fr, to)
                    break
                # diag left
                if c > 0:
                    to = fr + 8 * dir_row - 1
                    if 0 <= to < 64 and ((own >> to) & 1) == 0 and ((((opp_bb >> to) & 1) == 1) or (((occ >> to) & 1) == 0)):
                        found = (fr, to)
                        break
                # diag right
                if c < 7:
                    to = fr + 8 * dir_row + 1
                    if 0 <= to < 64 and ((own >> to) & 1) == 0 and ((((opp_bb >> to) & 1) == 1) or (((occ >> to) & 1) == 0)):
                        found = (fr, to)
                        break
        if found is None:
            # If truly no moves, we cannot produce a legal move; raise to signal invalid state.
            raise RuntimeError("No legal move found in fallback.")
        fr, to = found

    return idx_to_rc(fr), idx_to_rc(to)
