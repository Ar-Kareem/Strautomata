
import re
from collections import defaultdict

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUE = {
    "king": 11,
    "queen": 9,
    "rook": 5,
    "bishop": 3,
    "knight": 3,
    "pawn": 1,
}

def policy(state, role: str) -> str:
    # ---------- Helpers to parse state ----------
    # state contains propositions like ["location", ["cell","a","3"], ["piece","white","knight","1"]]
    # plus control/step/score facts etc.
    pieces = []  # (color, kind, id, file, rank)
    occupied = {}  # (file,rank)->(color,kind,id)
    control = None

    white_score = black_score = None
    for prop in state:
        if not isinstance(prop, list) or len(prop) == 0:
            continue
        if prop[0] == "control" and len(prop) >= 2:
            control = prop[1]
        if prop[0] == "location" and len(prop) == 3:
            cell = prop[1]
            piece_term = prop[2]
            # cell is ["cell","a","3"]
            if isinstance(cell, list) and cell[0] == "cell":
                f = cell[1]
                r = int(cell[2])
            else:
                continue
            # piece_term is ["piece", color, kind, id]
            if isinstance(piece_term, list) and piece_term[0] == "piece":
                color = piece_term[1]
                kind = piece_term[2]
                pid = piece_term[3]
                pieces.append((color, kind, pid, f, r))
                occupied[(f, r)] = (color, kind, pid)

    my_color = role
    opp_color = "black" if my_color == "white" else "white"

    # Determine step (optional)
    # for prop in state: if prop[0]=="step": step=prop[1]

    def in_bounds(f, r):
        return f in FILES and 1 <= r <= 8

    def cell_to_str(f, r):
        return f"cell({f},{r})"

    # ---------- Move generation (legal w.r.t. piece movement + occupancy, not check legality) ----------
    # Skirmish described: same moves as chess except no castling, no en passant, and no queening.
    # We'll ignore check constraints since the game does not end on king capture,
    # and typical implementations often still enforce "can't leave king in check"?
    # But we lack check legality facts; safest is to avoid strict check rules and generate pseudo-legal moves only.
    # Arena legality should still allow those; if legality requires check constraints, pseudo-legal
    # might still be accepted by game engine. Most StanfordGM games allow moves that respect chess rules except check.
    # We'll at least prevent moving into squares occupied by own pieces.

    def my_pieces_by_square():
        d = {}
        for color, kind, pid, f, r in pieces:
            if color == my_color:
                d[(f, r)] = (kind, pid)
        return d

    def king_square(color):
        for c, kind, pid, f, r in pieces:
            if c == color and kind == "king":
                return (f, r)
        return None

    def attackers_of_square(target_f, target_r, by_color):
        # Return set of attackers (not including pins/check). We'll compute by piece type.
        attackers = []
        for c, kind, pid, f, r in pieces:
            if c != by_color:
                continue
            if (f, r) == (target_f, target_r):
                continue
            if can_piece_reach(kind, f, r, target_f, target_r, c, consider_occupancy=True):
                # Need to ensure line-of-sight for sliders.
                # can_piece_reach should handle occupancy for sliding pieces.
                attackers.append((c, kind, pid))
        return attackers

    # We'll implement reachability with occupancy taken into account.
    def can_piece_reach(kind, from_f, from_r, to_f, to_r, color, consider_occupancy=True):
        df = FILES.index(to_f) - FILES.index(from_f)
        dr = to_r - from_r

        def is_empty_or_enemy(tf, tr):
            occ = occupied.get((tf, tr))
            return occ is None or occ[0] != color

        if kind == "pawn":
            # Standard chess: white moves up (increasing rank), black down.
            dir_ = 1 if color == "white" else -1
            start_rank = 2 if color == "white" else 7
            # captures
            if dr == dir_ and abs(df) == 1:
                return True if consider_occupancy else True
            # forward one
            if df == 0 and dr == dir_:
                return True
            # forward two from start
            if df == 0 and dr == 2 * dir_ and from_r == start_rank:
                return True
            return False

        if kind == "knight":
            return (abs(df), abs(dr)) in [(1, 2), (2, 1)]

        if kind in ("bishop", "rook", "queen"):
            # sliders
            if kind == "bishop":
                if abs(df) != abs(dr) or df == 0:
                    return False
                step_f = 1 if df > 0 else -1
                step_r = 1 if dr > 0 else -1
            elif kind == "rook":
                if (df != 0 and dr != 0) or (df == 0 and dr == 0):
                    return False
                if df == 0:
                    step_f = 0
                    step_r = 1 if dr > 0 else -1
                else:
                    step_f = 1 if df > 0 else -1
                    step_r = 0
            else:  # queen
                if df == 0 and dr == 0:
                    return False
                if df == 0:
                    step_f = 0
                    step_r = 1 if dr > 0 else -1
                elif dr == 0:
                    step_f = 1 if df > 0 else -1
                    step_r = 0
                elif abs(df) == abs(dr):
                    step_f = 1 if df > 0 else -1
                    step_r = 1 if dr > 0 else -1
                else:
                    return False

            if not consider_occupancy:
                return True

            cur_f_idx = FILES.index(from_f)
            cur_r = from_r
            while True:
                cur_f_idx += step_f
                cur_r += step_r
                tf = FILES[cur_f_idx]
                tr = cur_r
                if (tf, tr) == (to_f, to_r):
                    return True  # path clear; occupancy at destination handled separately
                if (tf, tr) in occupied:
                    return False

        if kind == "king":
            return max(abs(df), abs(dr)) == 1 and not (df == 0 and dr == 0)

        return False

    def pawn_moves(from_f, from_r, color):
        dir_ = 1 if color == "white" else -1
        start_rank = 2 if color == "white" else 7
        moves = []

        # forward one
        tf, tr = from_f, from_r + dir_
        if in_bounds(tf, tr) and (tf, tr) not in occupied:
            moves.append((tf, tr))
            # forward two
            if from_r == start_rank:
                tf2, tr2 = from_f, from_r + 2 * dir_
                if in_bounds(tf2, tr2) and (tf2, tr2) not in occupied and (tf, tr) not in occupied:
                    moves.append((tf2, tr2))

        # captures
        for df in (-1, 1):
            cf_idx = FILES.index(from_f) + df
            if 0 <= cf_idx < 8:
                tf = FILES[cf_idx]
                tr = from_r + dir_
                if in_bounds(tf, tr) and (tf, tr) in occupied and occupied[(tf, tr)][0] != color:
                    moves.append((tf, tr))
        return moves

    def knight_moves(from_f, from_r, color):
        moves = []
        base_i = FILES.index(from_f)
        for dfi, dri in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
            ni = base_i + dfi
            nr = from_r + dri
            if 0 <= ni < 8 and 1 <= nr <= 8:
                tf = FILES[ni]
                if (tf, nr) not in occupied or occupied[(tf, nr)][0] != color:
                    moves.append((tf, nr))
        return moves

    def king_moves(from_f, from_r, color):
        moves = []
        base_i = FILES.index(from_f)
        for dfi in (-1,0,1):
            for dri in (-1,0,1):
                if dfi == 0 and dri == 0:
                    continue
                ni = base_i + dfi
                nr = from_r + dri
                if 0 <= ni < 8 and 1 <= nr <= 8:
                    tf = FILES[ni]
                    if (tf, nr) not in occupied or occupied[(tf, nr)][0] != color:
                        moves.append((tf, nr))
        return moves

    def slider_moves(from_f, from_r, color, kind):
        moves = []
        base_i = FILES.index(from_f)
        dirs = []
        if kind == "bishop":
            dirs = [(1,1),(1,-1),(-1,1),(-1,-1)]
        elif kind == "rook":
            dirs = [(1,0),(-1,0),(0,1),(0,-1)]
        elif kind == "queen":
            dirs = [(1,1),(1,-1),(-1,1),(-1,-1),(1,0),(-1,0),(0,1),(0,-1)]
        for dfi, dri in dirs:
            ni, nr = base_i + dfi, from_r + dri
            while 0 <= ni < 8 and 1 <= nr <= 8:
                tf = FILES[ni]
                if (tf, nr) in occupied:
                    if occupied[(tf, nr)][0] != color:
                        moves.append((tf, nr))
                    break
                else:
                    moves.append((tf, nr))
                ni += dfi
                nr += dri
        return moves

    def generate_pseudo_legal_moves():
        candidates = []
        for color, kind, pid, f, r in pieces:
            if color != my_color:
                continue
            if kind == "pawn":
                for tf, tr in pawn_moves(f, r, color):
                    candidates.append((kind, pid, f, r, tf, tr))
            elif kind == "knight":
                for tf, tr in knight_moves(f, r, color):
                    candidates.append((kind, pid, f, r, tf, tr))
            elif kind == "king":
                for tf, tr in king_moves(f, r, color):
                    candidates.append((kind, pid, f, r, tf, tr))
            elif kind in ("bishop","rook","queen"):
                for tf, tr in slider_moves(f, r, color, kind):
                    candidates.append((kind, pid, f, r, tf, tr))
        return candidates

    def move_string(kind, pid, from_f, from_r, to_f, to_r):
        return f"move(piece({my_color},{kind},{pid}),{cell_to_str(to_f,to_r)})"

    # ---------- Tactical scoring ----------
    def simulate_capture_if_any(to_f, to_r):
        occ = occupied.get((to_f, to_r))
        if occ and occ[0] == opp_color:
            return occ  # (color,kind,pid)
        return None

    def count_attackers_at(tf, tr, attacker_color):
        # Use pseudo-attack reachability from existing state.
        return len(attackers_of_square(tf, tr, attacker_color))

    moves = generate_pseudo_legal_moves()
    if not moves:
        # Fallback: shouldn't happen often; return a syntactically valid move guess from any king/knight/pawn
        ksq = king_square(my_color)
        if ksq:
            f,r = ksq
            return f"move(piece({my_color},king,1),cell({f},{r}))"
        # else pick first piece in parsing
        if pieces:
            c, k, pid, f, r = pieces[0]
            return f"move(piece({c},{k},{pid}),cell({f},{r}))"
        return "move(piece(white,king,1),cell(e,1))"

    best = None
    best_score = -10**9

    # Precompute potential enemy attackers by square quickly by trying each move destination
    for kind, pid, f, r, tf, tr in moves:
        captured = simulate_capture_if_any(tf, tr)
        is_capture = captured is not None

        # Basic safety: avoid moving into immediate capture by opponent (approx).
        attackers_by_opp = 0
        # if we move there, opponent could capture that square with any piece.
        # We'll count if opponent has reach.
        attackers_by_opp = count_attackers_at(tf, tr, opp_color)

        moving_piece_value = PIECE_VALUE[kind]

        score = 0
        if is_capture:
            cap_kind = captured[1]
            cap_value = PIECE_VALUE[cap_kind]
            score += 100 * cap_value  # primary objective: material gain
            # but penalize if recaptured effectively
            # assume worst-case recapture by one attacker
            score -= 25 * attackers_by_opp * (cap_value / max(1, moving_piece_value))
        else:
            # prefer positions not capturable
            score -= 10 * attackers_by_opp
            # small tempo: central-ish
            central_bonus = 0
            if FILES.index(tf) in (3,4) and tr in (3,4,5,6):
                central_bonus = 2
            score += central_bonus

            # pawn advancement bonus
            if kind == "pawn":
                adv = (tr - 1) if my_color == "white" else (8 - tr)
                score += 0.5 * adv

        # Avoid suicidal moves: if moving piece is valuable and destination attacked
        if moving_piece_value >= 5 and attackers_by_opp > 0 and not is_capture:
            score -= 50

        if score > best_score:
            best_score = score
            best = (kind, pid, f, r, tf, tr)

    if best is None:
        kind, pid, f, r, tf, tr = moves[0]
        return move_string(kind, pid, f, r, tf, tr)

    kind, pid, f, r, tf, tr = best
    return move_string(kind, pid, f, r, tf, tr)
