
from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple, Optional

BoardCoord = Tuple[int, int]
Move = Tuple[BoardCoord, BoardCoord]

DARK = {(r, c) for r in range(8) for c in range(8) if (r + c) % 2 == 1}

def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8

def _is_dark(r: int, c: int) -> bool:
    return (r + c) % 2 == 1

def _color_dirs(color: str) -> Tuple[int, int]:
    # black moves downward (decreasing row), white moves upward (increasing row)
    if color == 'b':
        return (-1, 1)  # forward step row deltas for men: -1
    else:
        return (1, -1)

def _forward_step_delta(color: str) -> int:
    return -1 if color == 'b' else 1

def _opponent(color: str) -> str:
    return 'w' if color == 'b' else 'b'

def _king_delta_dirs(color: str) -> List[int]:
    # kings move both directions
    return [-1, 1]

def _man_dirs(color: str) -> List[int]:
    return [_forward_step_delta(color)]

def _encode_state(my_men, my_kings, opp_men, opp_kings, color: str):
    # Create sets for fast checks
    my = set(my_men) | set(my_kings)
    opp = set(opp_men) | set(opp_kings)
    kings = set(my_kings)
    opp_kings = set(opp_kings)
    return (tuple(sorted(my)), tuple(sorted(kings)), tuple(sorted(opp)), tuple(sorted(opp_kings)), color)

def _is_king(pos, my_kings_set):
    return pos in my_kings_set

def _make_piece_sets(my_men, my_kings, opp_men, opp_kings):
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    return my_men_set, my_kings_set, opp_men_set, opp_kings_set

def _occupied(my_men_set, my_kings_set, opp_men_set, opp_kings_set, pos: BoardCoord) -> bool:
    return pos in my_men_set or pos in my_kings_set or pos in opp_men_set or pos in opp_kings_set

def _at_piece_type(pos: BoardCoord, my_men_set, my_kings_set, opp_men_set, opp_kings_set):
    if pos in my_kings_set:
        return 'my_king'
    if pos in my_men_set:
        return 'my_man'
    if pos in opp_kings_set:
        return 'opp_king'
    if pos in opp_men_set:
        return 'opp_man'
    return None

def _promote_if_needed(pos: BoardCoord, color: str) -> Optional[bool]:
    r, _ = pos
    if color == 'b' and r == 0:
        return True
    if color == 'w' and r == 7:
        return True
    return None

def _generate_capture_sequences_from(
    start: BoardCoord,
    is_king: bool,
    color: str,
    my_men_set: set,
    my_kings_set: set,
    opp_men_set: set,
    opp_kings_set: set
) -> List[Tuple[List[BoardCoord], List[BoardCoord]]]:
    """
    Returns list of capture sequences:
      (path_positions, captured_positions)
    path_positions includes start and final landing squares.
    """
    sequences = []

    # Copy mutable sets for simulation
    # We'll explore using recursion on local state
    def rec(cur_pos: BoardCoord, local_my_men, local_my_kings, local_opp_men, local_opp_kings,
            path: List[BoardCoord], captured: List[BoardCoord], became_king: bool):
        # Determine directions
        r, c = cur_pos
        dirs = _king_delta_dirs(color) if (is_king or became_king) else _man_dirs(color)
        any_capture = False

        for dr in dirs:
            mid = (r + dr, c + (-1 if dr == 1 else 1))  # not used; wrong formula
        # We'll compute diagonals properly:
        # dr is row delta for the landing step. Captured is one step, landing is two steps.
        for dr in dirs:
            for dc in (-1, 1):
                mid = (r + dr, c + dc)
                land = (r + 2 * dr, c + 2 * dc)
                if not _in_bounds(land[0], land[1]) or not _is_dark(land[0], land[1]):
                    continue
                if mid in local_opp_men or mid in local_opp_kings:
                    if land not in local_my_men and land not in local_my_kings and land not in local_opp_men and land not in local_opp_kings:
                        any_capture = True
                        # perform capture
                        nm_men = set(local_my_men)
                        nm_kings = set(local_my_kings)
                        no_men = set(local_opp_men)
                        no_kings = set(local_opp_kings)

                        # move piece
                        if cur_pos in nm_kings:
                            nm_kings.remove(cur_pos)
                            moved_kind_is_king = True
                        else:
                            nm_men.remove(cur_pos)
                            moved_kind_is_king = False

                        # remove captured
                        if mid in no_kings:
                            no_kings.remove(mid)
                        else:
                            no_men.remove(mid)

                        # land and possibly promote
                        land_promotes = False
                        # Determine whether piece is king after this landing
                        # If it was king already, it remains king; if man reaches last row, becomes king.
                        if moved_kind_is_king or is_king or became_king:
                            became = True
                        else:
                            # promotion check for men
                            if _promote_if_needed(land, color):
                                became = True
                                land_promotes = True
                            else:
                                became = False

                        if became:
                            nm_kings.add(land)
                        else:
                            nm_men.add(land)

                        new_became_king = became  # once king, always
                        rec(
                            land, nm_men, nm_kings, no_men, no_kings,
                            path + [land], captured + [mid],
                            became_king=new_became_king
                        )

        if not any_capture:
            if len(captured) > 0:
                sequences.append((path, captured))

    # Initialize local sets
    loc_my_men = set(my_men_set)
    loc_my_kings = set(my_kings_set)
    loc_opp_men = set(opp_men_set)
    loc_opp_kings = set(opp_kings_set)

    rec(start, loc_my_men, loc_my_kings, loc_opp_men, loc_opp_kings, [start], [], became_king=False)
    return sequences

def _generate_moves_for_color(
    my_men, my_kings, opp_men, opp_kings, color: str
) -> List[Tuple[Move, Tuple[BoardCoord, ...]]]:
    """
    Returns list of actions:
      [ ( (from,to), captured_tuple ) ]
    captured_tuple empty for quiet move.
    Note: If multiple-jump exists, 'to' is the final landing square and captured is all captured.
    """
    my_men_set, my_kings_set, opp_men_set, opp_kings_set = _make_piece_sets(my_men, my_kings, opp_men, opp_kings)

    capture_actions: List[Tuple[Move, Tuple[BoardCoord, ...]]] = []
    quiet_actions: List[Tuple[Move, Tuple[BoardCoord, ...]]] = []

    # First find all capture sequences from any piece; mandatory captures handled outside.
    for pos in list(my_men_set | my_kings_set):
        piece_type = _at_piece_type(pos, my_men_set, my_kings_set, opp_men_set, opp_kings_set)
        if piece_type is None:
            continue
        is_king = piece_type == 'my_king'

        seqs = _generate_capture_sequences_from(
            pos, is_king, color,
            my_men_set, my_kings_set, opp_men_set, opp_kings_set
        )
        for path, captured in seqs:
            from_sq = path[0]
            to_sq = path[-1]
            capture_actions.append(((from_sq, to_sq), tuple(captured)))

    if capture_actions:
        # Captures are mandatory; also prefer longest captures? We'll leave scoring to search,
        # but it's safe to include all capture actions.
        return capture_actions

    # Otherwise generate quiet moves (men forward, kings both)
    for pos in (my_men_set | my_kings_set):
        r, c = pos
        is_king = pos in my_kings_set
        dirs = _king_delta_dirs(color) if is_king else _man_dirs(color)

        for dr in dirs:
            for dc in (-1, 1):
                nr, nc = r + dr, c + dc
                if not _in_bounds(nr, nc) or not _is_dark(nr, nc):
                    continue
                if nr in range(8) and nc in range(8):
                    if (nr, nc) not in my_men_set and (nr, nc) not in my_kings_set and (nr, nc) not in opp_men_set and (nr, nc) not in opp_kings_set:
                        quiet_actions.append((((r, c), (nr, nc)), tuple()))
    return quiet_actions

def _apply_move(
    my_men, my_kings, opp_men, opp_kings, color: str,
    move: Move, captured: Tuple[BoardCoord, ...]
):
    # Returns new (my_men, my_kings, opp_men, opp_kings, next_color)
    my_men_set, my_kings_set, opp_men_set, opp_kings_set = _make_piece_sets(my_men, my_kings, opp_men, opp_kings)
    (fr, fc), (tr, tc) = move
    piece_is_king = (fr, fc) in my_kings_set

    # move piece
    if (fr, fc) in my_kings_set:
        my_kings_set.remove((fr, fc))
    else:
        my_men_set.remove((fr, fc))

    # capture removal
    for cap in captured:
        if cap in opp_kings_set:
            opp_kings_set.remove(cap)
        elif cap in opp_men_set:
            opp_men_set.remove(cap)
        else:
            # should not happen if move is legal
            pass

    # place moved piece, with promotion if needed
    land = (tr, tc)
    promoted = False
    if piece_is_king:
        promoted = True
    else:
        if _promote_if_needed(land, color):
            promoted = True
    if promoted:
        my_kings_set.add(land)
    else:
        my_men_set.add(land)

    # Next player's perspective: swap sides
    next_color = _opponent(color)
    # Now the "my" sets are previous opponent sets
    new_my_men = list(opp_men_set)
    new_my_kings = list(opp_kings_set)
    new_opp_men = list(my_men_set)
    new_opp_kings = list(my_kings_set)
    return new_my_men, new_my_kings, new_opp_men, new_opp_kings, next_color

def _evaluate(my_men, my_kings, opp_men, opp_kings, color: str) -> int:
    # material
    val_man = 100
    val_king = 175
    score = 0

    # positional: advancement towards promotion
    my_men_adv = 0
    my_king_adv = 0
    opp_men_adv = 0
    opp_king_adv = 0

    if color == 'b':
        # black promotes at row 0, so advancement is (7-r)
        my_men_adv = sum(7 - r for r, _ in my_men)
        my_king_adv = sum(7 - r for r, _ in my_kings)
        opp_men_adv = sum(r for r, _ in opp_men)  # opponent is white relative; but from our eval we just want relative
        opp_king_adv = sum(r for r, _ in opp_kings)
    else:
        # white promotes at row 7, so advancement is r
        my_men_adv = sum(r for r, _ in my_men)
        my_king_adv = sum(r for r, _ in my_kings)
        opp_men_adv = sum(7 - r for r, _ in opp_men)
        opp_king_adv = sum(7 - r for r, _ in opp_kings)

    # centralization bonus
    def center_bonus(pos_list):
        return sum(3.5 - abs(c - 3.5) for _, c in pos_list)

    score += len(my_men) * val_man
    score += len(my_kings) * val_king
    score -= len(opp_men) * val_man
    score -= len(opp_kings) * val_king

    score += int(0.8 * my_men_adv + 0.6 * my_king_adv)
    score -= int(0.7 * opp_men_adv + 0.5 * opp_king_adv)

    score += int(2.0 * center_bonus(my_men) + 3.0 * center_bonus(my_kings))
    score -= int(2.0 * center_bonus(opp_men) + 3.0 * center_bonus(opp_kings))

    return score

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Depth adapts slightly to branching
    legal = _generate_moves_for_color(my_men, my_kings, opp_men, opp_kings, color)
    # Must return a legal move; if no legal moves, this should not happen in arena,
    # but we guard by returning a dummy (still legal when there is at least one).
    if not legal:
        # fallback: return first piece to some forward diag if available
        # (should be unreachable for legal states)
        for fr in my_men + my_kings:
            r, c = fr
            for dr in (-1, 1):
                for dc in (-1, 1):
                    tr, tc = r + dr, c + dc
                    if _in_bounds(tr, tc) and _is_dark(tr, tc):
                        return (fr, (tr, tc))
        return ((0, 0), (0, 0))

    # Quick tactical: if capture moves exist, bias towards captures that take most pieces,
    # and towards king-making.
    capture_moves = [a for a in legal if len(a[1]) > 0]
    if capture_moves:
        # If multiple, pick among top by (len(captured), immediate promotion)
        best_action = None
        best_key = None
        my_kings_set = set(my_kings)
        for (move, captured) in capture_moves:
            (fr, fc), (tr, tc) = move
            became_king = ((fr, fc) in my_kings_set) or bool(_promote_if_needed((tr, tc), color))
            key = (len(captured), int(became_king))
            if best_key is None or key > best_key:
                best_key = key
                best_action = (move, captured)
        return best_action[0]

    # Otherwise do minimax for quiet play
    # Depth choice: more depth when fewer moves
    branching = max(1, len(legal))
    depth = 3 if branching <= 8 else 2
    # Add 1 ply in late game with fewer pieces
    if (len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings)) <= 10:
        depth = max(depth, 4 - (branching > 10))

    @lru_cache(maxsize=50_000)
    def negamax(state_key, d, alpha, beta):
        # state_key: (my_men_t, my_kings_t, opp_men_t, opp_kings_t, color)
        my_men_t, my_kings_t, opp_men_t, opp_kings_t, st_color = state_key
        my_men_l = list(my_men_t)
        my_kings_l = list(my_kings_t)
        opp_men_l = list(opp_men_t)
        opp_kings_l = list(opp_kings_t)

        moves = _generate_moves_for_color(my_men_l, my_kings_l, opp_men_l, opp_kings_l, st_color)
        if d == 0 or not moves:
            return _evaluate(my_men_l, my_kings_l, opp_men_l, opp_kings_l, st_color)

        best = -10**9
        # Move ordering: captures first (already none here in top-level quiet, but deeper may have captures)
        def move_order(m):
            (mv, cap) = m
            return (len(cap), )  # fewer not needed; just maximize

        moves_sorted = sorted(moves, key=move_order, reverse=True)

        for mv, cap in moves_sorted:
            nmy_men, nmy_kings, nopp_men, nopp_kings, ncolor = _apply_move(
                my_men_l, my_kings_l, opp_men_l, opp_kings_l, st_color, mv, cap
            )
            nkey = (tuple(sorted(nmy_men)), tuple(sorted(nmy_kings)),
                    tuple(sorted(nopp_men)), tuple(sorted(nopp_kings)), ncolor)
            val = -negamax(nkey, d - 1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    state0 = (tuple(sorted(my_men)), tuple(sorted(my_kings)), tuple(sorted(opp_men)), tuple(sorted(opp_kings)), color)

    best_move = legal[0][0]
    best_score = -10**9
    # Root move ordering by simple heuristic: prefer advancing and centralization
    my_kings_set = set(my_kings)

    def root_order(action):
        mv, cap = action
        (fr, fc), (tr, tc) = mv
        became_king = ((fr, fc) in my_kings_set) or bool(_promote_if_needed((tr, tc), color))
        adv = (7 - tr) if color == 'b' else tr
        cent = 3.5 - abs(tc - 3.5)
        return (int(became_king), len(cap), adv, cent)

    legal_sorted = sorted(legal, key=root_order, reverse=True)

    alpha = -10**9
    beta = 10**9
    for mv, cap in legal_sorted:
        nmy_men, nmy_kings, nopp_men, nopp_kings, ncolor = _apply_move(
            my_men, my_kings, opp_men, opp_kings, color, mv, cap
        )
        nkey = (tuple(sorted(nmy_men)), tuple(sorted(nmy_kings)),
                tuple(sorted(nopp_men)), tuple(sorted(nopp_kings)), ncolor)
        score = -negamax(nkey, depth - 1, -beta, -alpha)
        if score > best_score:
            best_score = score
            best_move = mv
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best_move
