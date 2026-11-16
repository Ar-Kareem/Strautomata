
from typing import List, Tuple, Optional

# Backgammon policy:
# Return format: "<ORDER>:<FROM1>,<FROM2>"
# ORDER in {"H","L"} indicates whether the first move uses the higher or lower die.
# FROM tokens are "A0".."A23", "B", or "P".

def policy(state: dict) -> str:
    my_pts = list(state["my_pts"])
    opp_pts = list(state["opp_pts"])
    my_bar = int(state["my_bar"])
    my_off = int(state["my_off"])
    dice = list(state["dice"])

    # No dice => pass
    if len(dice) == 0:
        return "H:P,P"

    # Normalize to two dice if one die only.
    if len(dice) == 1:
        d = dice[0]
        move_infos = legal_first_moves(my_pts, opp_pts, my_bar, my_off, d)
        if not move_infos:
            return "H:P,P"
        best = None
        best_score = None
        for info in move_infos:
            pts2, opp2, bar2, off2 = apply_move(my_pts, opp_pts, my_bar, my_off, d, info[0])
            score = evaluate_position(pts2, opp2, bar2, off2)
            if best is None or score > best_score:
                best = info
                best_score = score
        tok = from_token(best[0])
        return f"H:{tok},P"

    d1, d2 = dice[0], dice[1]
    hi = max(d1, d2)
    lo = min(d1, d2)

    # Enumerate both orders (H then L) and (L then H)
    seq_H = enumerate_sequences(my_pts, opp_pts, my_bar, my_off, hi, lo, order_char="H")
    seq_L = enumerate_sequences(my_pts, opp_pts, my_bar, my_off, lo, hi, order_char="L")

    allseq = seq_H + seq_L

    # Apply mandatory-use rules.
    # Prefer sequences using 2 moves if any exist.
    two_move = [s for s in allseq if s["used"] == 2]
    if two_move:
        candidates = two_move
    else:
        # If only one die can be played, must play the higher die when possible.
        any_hi_single = any(s["used"] == 1 and s["used_dice"] == {hi} for s in allseq)
        if any_hi_single:
            candidates = [s for s in allseq if s["used"] == 1 and s["used_dice"] == {hi}]
        else:
            one_move = [s for s in allseq if s["used"] == 1]
            if one_move:
                candidates = one_move
            else:
                return "H:P,P"

    # Choose by heuristic evaluation.
    best = None
    best_score = None
    for s in candidates:
        score = evaluate_sequence(s, hi, lo)
        if best is None or score > best_score:
            best = s
            best_score = score

    return best["move_str"]


def from_token(src: Optional[int]) -> str:
    if src is None:
        return "P"
    if src == -1:
        return "B"
    return f"A{src}"


def all_in_home(my_pts: List[int], my_bar: int) -> bool:
    if my_bar > 0:
        return False
    # Home board is points 0..5 for player moving 23 -> 0
    return sum(my_pts[6:]) == 0


def highest_occupied_point(my_pts: List[int]) -> int:
    for i in range(23, -1, -1):
        if my_pts[i] > 0:
            return i
    return -1


def legal_first_moves(my_pts: List[int], opp_pts: List[int], my_bar: int, my_off: int, die: int) -> List[Tuple[Optional[int], dict]]:
    """
    Returns list of legal single-move sources for this die.
    Source encoding:
      -1 => Bar
      0..23 => point
    """
    moves = []

    # Must enter from bar first.
    if my_bar > 0:
        dest = 24 - die  # entering from bar to opponent's home side viewed in absolute indexing
        if 0 <= dest <= 23 and opp_pts[dest] < 2:
            moves.append((-1, {"hit": opp_pts[dest] == 1, "dest": dest, "bearoff": False}))
        return moves

    can_bear = all_in_home(my_pts, my_bar)

    for src in range(24):
        if my_pts[src] <= 0:
            continue
        dest = src - die
        if dest >= 0:
            if opp_pts[dest] < 2:
                moves.append((src, {"hit": opp_pts[dest] == 1, "dest": dest, "bearoff": False}))
        else:
            if can_bear:
                # Exact bear off always legal
                if dest == -1:
                    moves.append((src, {"hit": False, "dest": None, "bearoff": True}))
                else:
                    # Oversized bear-off allowed only from highest occupied point
                    hp = highest_occupied_point(my_pts)
                    if src == hp:
                        moves.append((src, {"hit": False, "dest": None, "bearoff": True}))
    return moves


def apply_move(my_pts: List[int], opp_pts: List[int], my_bar: int, my_off: int, die: int, src: int):
    pts = my_pts[:]
    opp = opp_pts[:]
    bar = my_bar
    off = my_off

    if src == -1:
        dest = 24 - die
        bar -= 1
        if opp[dest] == 1:
            opp[dest] = 0
            # Opponent checker goes to their bar; for evaluation we approximate via opp_bar-like effect
            # Since opp_bar is not propagated in evaluation except indirectly, we track by impossible extra field outside.
            # Here we just leave board correct.
        pts[dest] += 1
        return pts, opp, bar, off

    pts[src] -= 1
    dest = src - die
    if dest >= 0:
        if opp[dest] == 1:
            opp[dest] = 0
        pts[dest] += 1
    else:
        off += 1
    return pts, opp, bar, off


def blot_count(pts: List[int]) -> int:
    return sum(1 for x in pts if x == 1)


def made_points_count(pts: List[int]) -> int:
    return sum(1 for x in pts if x >= 2)


def home_made_points_count(pts: List[int]) -> int:
    return sum(1 for i in range(6) if pts[i] >= 2)


def anchor_points_count(pts: List[int]) -> int:
    # Advanced anchors in opp home board from our perspective are high indices 18..23
    return sum(1 for i in range(18, 24) if pts[i] >= 2)


def pip_count(pts: List[int], bar: int, off: int) -> int:
    # Approximate pip count for us moving toward 0:
    # checker on point i needs i+1 pips to bear off
    # checker on bar needs 25 pips (entry plus path)
    total = bar * 25
    for i, n in enumerate(pts):
        total += n * (i + 1)
    return total


def direct_shots_on_point(point: int, opp_pts: List[int], opp_bar: int = 0) -> int:
    # Approximate count of opposing blots/checkers that can hit this point in one roll by a single die.
    # Opponent moves from low to high indices.
    shots = 0
    # Opponent from board
    for j, n in enumerate(opp_pts):
        if n <= 0:
            continue
        dist = point - j
        if 1 <= dist <= 6:
            shots += n
    # Opponent from bar enters at die-1, so can only hit high points 0..5? Not relevant for our blots usually.
    # Ignored for simplicity.
    return shots


def exposed_blot_penalty(my_pts: List[int], opp_pts: List[int]) -> float:
    pen = 0.0
    for i, n in enumerate(my_pts):
        if n == 1:
            shots = direct_shots_on_point(i, opp_pts)
            # More dangerous if farther from home / in outer board
            zone = 1.0
            if i >= 18:
                zone = 0.7
            elif 6 <= i <= 17:
                zone = 1.2
            pen += zone * min(shots, 8)
    return pen


def stack_penalty(my_pts: List[int]) -> float:
    pen = 0.0
    for i, n in enumerate(my_pts):
        if n > 2:
            pen += (n - 2) * 0.6
        if n > 5:
            pen += (n - 5) * 0.8
    return pen


def evaluate_position(my_pts: List[int], opp_pts: List[int], my_bar: int, my_off: int) -> float:
    score = 0.0
    score += my_off * 14.0
    score -= my_bar * 22.0
    score -= pip_count(my_pts, my_bar, my_off) * 0.18
    score += made_points_count(my_pts) * 4.0
    score += home_made_points_count(my_pts) * 3.0
    score += anchor_points_count(my_pts) * 2.0
    score -= blot_count(my_pts) * 2.6
    score -= exposed_blot_penalty(my_pts, opp_pts) * 1.7
    score -= stack_penalty(my_pts) * 1.2

    # Small bonus for prime-like consecutive made points
    consec = 0
    best_consec = 0
    for i in range(24):
        if my_pts[i] >= 2:
            consec += 1
            best_consec = max(best_consec, consec)
        else:
            consec = 0
    score += best_consec * 2.5

    return score


def enumerate_sequences(my_pts: List[int], opp_pts: List[int], my_bar: int, my_off: int,
                        first_die: int, second_die: int, order_char: str):
    result = []

    first_moves = legal_first_moves(my_pts, opp_pts, my_bar, my_off, first_die)
    if not first_moves:
        # Try second die only? This sequence represents using none in this order.
        result.append({
            "used": 0,
            "used_dice": set(),
            "move_str": f"{order_char}:P,P",
            "score_pos": evaluate_position(my_pts, opp_pts, my_bar, my_off),
            "hits": 0,
            "made_delta": 0,
            "bar_left": my_bar,
            "off": my_off,
        })
        return result

    base_made = made_points_count(my_pts)

    for src1, meta1 in first_moves:
        pts1, opp1, bar1, off1 = apply_move(my_pts, opp_pts, my_bar, my_off, first_die, src1)
        second_moves = legal_first_moves(pts1, opp1, bar1, off1, second_die)

        if second_moves:
            for src2, meta2 in second_moves:
                pts2, opp2, bar2, off2 = apply_move(pts1, opp1, bar1, off1, second_die, src2)
                move_str = f"{order_char}:{from_token(src1)},{from_token(src2)}"
                result.append({
                    "used": 2,
                    "used_dice": {first_die, second_die},
                    "move_str": move_str,
                    "score_pos": evaluate_position(pts2, opp2, bar2, off2),
                    "hits": int(meta1["hit"]) + int(meta2["hit"]),
                    "made_delta": made_points_count(pts2) - base_made,
                    "bar_left": bar2,
                    "off": off2,
                })
        else:
            move_str = f"{order_char}:{from_token(src1)},P"
            result.append({
                "used": 1,
                "used_dice": {first_die},
                "move_str": move_str,
                "score_pos": evaluate_position(pts1, opp1, bar1, off1),
                "hits": int(meta1["hit"]),
                "made_delta": made_points_count(pts1) - base_made,
                "bar_left": bar1,
                "off": off1,
            })

    return result


def evaluate_sequence(seq: dict, hi: int, lo: int) -> float:
    score = seq["score_pos"]
    score += seq["used"] * 100.0
    score += seq["hits"] * 18.0
    score += seq["made_delta"] * 10.0
    score -= seq["bar_left"] * 30.0
    score += seq["off"] * 8.0

    # Tiny tiebreak preference for H ordering if equivalent and both-dice used.
    if seq["used"] == 2 and seq["move_str"].startswith("H:"):
        score += 0.05
    return score
