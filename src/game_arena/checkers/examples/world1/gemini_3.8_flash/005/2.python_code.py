
import time
from typing import List, Tuple, Set, Optional

Square = Tuple[int, int]
Move = Tuple[Square, Square]

# Direction vectors
KING_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
WHITE_MAN_DIRS = [(1, -1), (1, 1)]
BLACK_MAN_DIRS = [(-1, -1), (-1, 1)]


class SearchTimeout(Exception):
    pass


def get_moves_for_piece(
    pos: Square,
    is_king: bool,
    color: str,
    my_pieces: Set[Square],
    opp_pieces: Set[Square],
    all_pieces: Set[Square],
    only_captures: bool = False
) -> Tuple[List[Tuple[Move, Square, bool]], List[Move]]:
    """
    Returns (captures, non_captures).
    captures format: [(((from_r, from_c), (to_r, to_c)), captured_sq, becomes_king), ...]
    non_captures format: [((from_r, from_c), (to_r, to_c)), ...]
    """
    r, c = pos
    dirs = KING_DIRS if is_king else (WHITE_MAN_DIRS if color == 'w' else BLACK_MAN_DIRS)
    promo_row = 7 if color == 'w' else 0

    captures = []
    non_captures = []

    for dr, dc in dirs:
        mid_r, mid_c = r + dr, c + dc
        mid = (mid_r, mid_c)
        if mid in opp_pieces:
            land_r, land_c = r + 2 * dr, c + 2 * dc
            if 0 <= land_r < 8 and 0 <= land_c < 8:
                land = (land_r, land_c)
                if land not in all_pieces:
                    promoted = (not is_king) and (land_r == promo_row)
                    captures.append(((pos, land), mid, promoted))
        elif not only_captures:
            if 0 <= mid_r < 8 and 0 <= mid_c < 8 and mid not in all_pieces:
                non_captures.append((pos, mid))

    return captures, non_captures


def generate_all_moves(
    w_men: Set[Square],
    w_kings: Set[Square],
    b_men: Set[Square],
    b_kings: Set[Square],
    active_color: str,
    continuation_piece: Optional[Tuple[Square, bool]] = None
) -> Tuple[List[Tuple[Move, Square, bool]], List[Move], bool]:
    """
    Generates legal moves for active_color.
    If continuation_piece is provided: (pos, is_king), only captures from that piece are legal.
    Returns (capture_moves, quiet_moves, is_capture_mandatory).
    """
    if active_color == 'w':
        my_men, my_kings = w_men, w_kings
        opp_men, opp_kings = b_men, b_kings
    else:
        my_men, my_kings = b_men, b_kings
        opp_men, opp_kings = w_men, w_kings

    my_pieces = my_men | my_kings
    opp_pieces = opp_men | opp_kings
    all_pieces = my_pieces | opp_pieces

    all_captures = []
    all_quiets = []

    if continuation_piece is not None:
        pos, is_king = continuation_piece
        caps, _ = get_moves_for_piece(pos, is_king, active_color, my_pieces, opp_pieces, all_pieces, only_captures=True)
        return caps, [], True

    # Check for any captures across all pieces
    for pos in my_men:
        caps, quiets = get_moves_for_piece(pos, False, active_color, my_pieces, opp_pieces, all_pieces)
        all_captures.extend(caps)
        if not caps:
            all_quiets.extend(quiets)

    for pos in my_kings:
        caps, quiets = get_moves_for_piece(pos, True, active_color, my_pieces, opp_pieces, all_pieces)
        all_captures.extend(caps)
        if not caps:
            all_quiets.extend(quiets)

    if all_captures:
        return all_captures, [], True
    return [], all_quiets, False


def evaluate(w_men: Set[Square], w_kings: Set[Square], b_men: Set[Square], b_kings: Set[Square], my_color: str) -> int:
    score = 0

    # Material values
    score += len(w_men) * 100 + len(w_kings) * 180
    score -= len(b_men) * 100 + len(b_kings) * 180

    # Positional evaluation for White
    for r, c in w_men:
        score += r * 4  # Advance bonus
        if r == 0:
            score += 15  # Back rank defense
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 6   # Center control
        if c == 0 or c == 7:
            score -= 5   # Edge penalty

    for r, c in w_kings:
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 10  # King center control

    # Positional evaluation for Black
    for r, c in b_men:
        score -= (7 - r) * 4  # Advance bonus
        if r == 7:
            score -= 15       # Back rank defense
        if 2 <= r <= 5 and 2 <= c <= 5:
            score -= 6        # Center control
        if c == 0 or c == 7:
            score += 5        # Edge penalty

    for r, c in b_kings:
        if 2 <= r <= 5 and 2 <= c <= 5:
            score -= 10       # King center control

    return score if my_color == 'w' else -score


def alpha_beta(
    w_men: Set[Square],
    w_kings: Set[Square],
    b_men: Set[Square],
    b_kings: Set[Square],
    depth: int,
    alpha: float,
    beta: float,
    active_color: str,
    my_color: str,
    start_time: float,
    time_limit: float,
    continuation_piece: Optional[Tuple[Square, bool]] = None
) -> Tuple[float, Optional[Move]]:
    if time.time() - start_time > time_limit:
        raise SearchTimeout()

    caps, quiets, is_cap = generate_all_moves(w_men, w_kings, b_men, b_kings, active_color, continuation_piece)

    if continuation_piece is not None and not caps:
        # Multi-jump sequence ended for this player, switch turn
        next_color = 'b' if active_color == 'w' else 'w'
        return alpha_beta(w_men, w_kings, b_men, b_kings, depth - 1, alpha, beta, next_color, my_color, start_time, time_limit, None)

    if not caps and not quiets:
        # No legal moves: active player loses
        loss_val = -90000 - depth if active_color == my_color else 90000 + depth
        return loss_val, None

    if depth <= 0 and not is_cap:
        return evaluate(w_men, w_kings, b_men, b_kings, my_color), None

    is_maximizing = (active_color == my_color)
    best_move = None

    if is_maximizing:
        max_eval = -float('inf')
        if is_cap:
            for move, mid, promoted in caps:
                src, dst = move
                nw_m, nw_k = set(w_men), set(w_kings)
                nb_m, nb_k = set(b_men), set(b_kings)

                if active_color == 'w':
                    if src in nw_m:
                        nw_m.remove(src)
                        if promoted:
                            nw_k.add(dst)
                        else:
                            nw_m.add(dst)
                    else:
                        nw_k.remove(src)
                        nw_k.add(dst)

                    if mid in nb_m:
                        nb_m.remove(mid)
                    else:
                        nb_k.discard(mid)

                    is_dst_king = (dst in nw_k)
                else:
                    if src in nb_m:
                        nb_m.remove(src)
                        if promoted:
                            nb_k.add(dst)
                        else:
                            nb_m.add(dst)
                    else:
                        nb_k.remove(src)
                        nb_k.add(dst)

                    if mid in nw_m:
                        nw_m.remove(mid)
                    else:
                        nw_k.discard(mid)

                    is_dst_king = (dst in nb_k)

                # English draughts rule: if crowned on jump, turn ends immediately
                if promoted:
                    next_color = 'b' if active_color == 'w' else 'w'
                    eval_val, _ = alpha_beta(nw_m, nw_k, nb_m, nb_k, depth - 1, alpha, beta, next_color, my_color, start_time, time_limit, None)
                else:
                    eval_val, _ = alpha_beta(nw_m, nw_k, nb_m, nb_k, depth, alpha, beta, active_color, my_color, start_time, time_limit, (dst, is_dst_king))

                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            for move in quiets:
                src, dst = move
                nw_m, nw_k = set(w_men), set(w_kings)
                nb_m, nb_k = set(b_men), set(b_kings)

                next_color = 'b' if active_color == 'w' else 'w'
                if active_color == 'w':
                    if src in nw_m:
                        nw_m.remove(src)
                        if dst[0] == 7:
                            nw_k.add(dst)
                        else:
                            nw_m.add(dst)
                    else:
                        nw_k.remove(src)
                        nw_k.add(dst)
                else:
                    if src in nb_m:
                        nb_m.remove(src)
                        if dst[0] == 0:
                            nb_k.add(dst)
                        else:
                            nb_m.add(dst)
                    else:
                        nb_k.remove(src)
                        nb_k.add(dst)

                eval_val, _ = alpha_beta(nw_m, nw_k, nb_m, nb_k, depth - 1, alpha, beta, next_color, my_color, start_time, time_limit, None)
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval, best_move
    else:
        min_eval = float('inf')
        if is_cap:
            for move, mid, promoted in caps:
                src, dst = move
                nw_m, nw_k = set(w_men), set(w_kings)
                nb_m, nb_k = set(b_men), set(b_kings)

                if active_color == 'w':
                    if src in nw_m:
                        nw_m.remove(src)
                        if promoted:
                            nw_k.add(dst)
                        else:
                            nw_m.add(dst)
                    else:
                        nw_k.remove(src)
                        nw_k.add(dst)

                    if mid in nb_m:
                        nb_m.remove(mid)
                    else:
                        nb_k.discard(mid)

                    is_dst_king = (dst in nw_k)
                else:
                    if src in nb_m:
                        nb_m.remove(src)
                        if promoted:
                            nb_k.add(dst)
                        else:
                            nb_m.add(dst)
                    else:
                        nb_k.remove(src)
                        nb_k.add(dst)

                    if mid in nw_m:
                        nw_m.remove(mid)
                    else:
                        nw_k.discard(mid)

                    is_dst_king = (dst in nb_k)

                if promoted:
                    next_color = 'b' if active_color == 'w' else 'w'
                    eval_val, _ = alpha_beta(nw_m, nw_k, nb_m, nb_k, depth - 1, alpha, beta, next_color, my_color, start_time, time_limit, None)
                else:
                    eval_val, _ = alpha_beta(nw_m, nw_k, nb_m, nb_k, depth, alpha, beta, active_color, my_color, start_time, time_limit, (dst, is_dst_king))

                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = move
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval, best_move
        else:
            for move in quiets:
                src, dst = move
                nw_m, nw_k = set(w_men), set(w_kings)
                nb_m, nb_k = set(b_men), set(b_kings)

                next_color = 'b' if active_color == 'w' else 'w'
                if active_color == 'w':
                    if src in nw_m:
                        nw_m.remove(src)
                        if dst[0] == 7:
                            nw_k.add(dst)
                        else:
                            nw_m.add(dst)
                    else:
                        nw_k.remove(src)
                        nw_k.add(dst)
                else:
                    if src in nb_m:
                        nb_m.remove(src)
                        if dst[0] == 0:
                            nb_k.add(dst)
                        else:
                            nb_m.add(dst)
                    else:
                        nb_k.remove(src)
                        nb_k.add(dst)

                eval_val, _ = alpha_beta(nw_m, nw_k, nb_m, nb_k, depth - 1, alpha, beta, next_color, my_color, start_time, time_limit, None)
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = move
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval, best_move


def policy(my_men: List[Square], my_kings: List[Square], opp_men: List[Square], opp_kings: List[Square], color: str) -> Tuple[Square, Square]:
    start_time = time.time()
    time_limit = 0.82  # Safely within 1.0 second limit

    if color == 'w':
        w_men = set(my_men)
        w_kings = set(my_kings)
        b_men = set(opp_men)
        b_kings = set(opp_kings)
    else:
        b_men = set(my_men)
        b_kings = set(my_kings)
        w_men = set(opp_men)
        w_kings = set(opp_kings)

    caps, quiets, _ = generate_all_moves(w_men, w_kings, b_men, b_kings, color)
    legal_moves = [m[0] for m in caps] if caps else quiets

    if not legal_moves:
        return ((0, 0), (0, 0))

    if len(legal_moves) == 1:
        return legal_moves[0]

    best_move = legal_moves[0]

    # Iterative deepening
    for depth in range(1, 30):
        try:
            score, move = alpha_beta(
                w_men, w_kings, b_men, b_kings,
                depth=depth,
                alpha=-float('inf'),
                beta=float('inf'),
                active_color=color,
                my_color=color,
                start_time=start_time,
                time_limit=time_limit
            )
            if move is not None:
                best_move = move
            if score >= 90000 or score <= -90000:
                break
        except SearchTimeout:
            break

    return best_move
