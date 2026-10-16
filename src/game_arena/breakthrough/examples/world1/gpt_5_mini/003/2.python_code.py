
import math
import time
from typing import List, Tuple

# Type aliases
Pos = Tuple[int, int]
Move = Tuple[Pos, Pos]

# Global time guard (very small budget within 1s limit). Not strictly necessary
# but keeps us safe for depth-limited search.
_TIME_LIMIT = 0.9  # seconds
_start_time = None


def policy(me: List[Pos], opp: List[Pos], color: str) -> Move:
    """
    Return a move ((r_from, c_from), (r_to, c_to)) for the current player.
    me: list of my piece positions (row, col)
    opp: list of opponent piece positions
    color: 'b' or 'w' (b moves downwards: -1 rows; w moves upwards: +1 rows)
    """

    global _start_time
    _start_time = time.time()

    # Convert to sets for fast lookup
    me_set = set(me)
    opp_set = set(opp)

    # Helper values
    dr = 1 if color == 'w' else -1
    my_goal_row = 7 if color == 'w' else 0
    opp_goal_row = 0 if color == 'w' else 7  # opponent's home row

    # Generate all legal moves for given side
    def generate_moves_for(side_me: set, side_opp: set, side_color: str):
        moves = []
        d = 1 if side_color == 'w' else -1
        for (r, c) in side_me:
            nr = r + d
            if not (0 <= nr <= 7):
                continue
            # forward
            if (nr, c) not in side_me and (nr, c) not in side_opp:
                is_capture = False
                reaches_goal = (nr == (7 if side_color == 'w' else 0))
                moves.append(((r, c), (nr, c), is_capture, reaches_goal))
            # diagonal left
            nc = c - 1
            if 0 <= nc <= 7:
                if (nr, nc) in side_opp:
                    is_capture = True
                    reaches_goal = (nr == (7 if side_color == 'w' else 0))
                    moves.append(((r, c), (nr, nc), is_capture, reaches_goal))
                elif (nr, nc) not in side_me and (nr, nc) not in side_opp:
                    # diagonal non-capture allowed on empty square
                    is_capture = False
                    reaches_goal = (nr == (7 if side_color == 'w' else 0))
                    moves.append(((r, c), (nr, nc), is_capture, reaches_goal))
            # diagonal right
            nc = c + 1
            if 0 <= nc <= 7:
                if (nr, nc) in side_opp:
                    is_capture = True
                    reaches_goal = (nr == (7 if side_color == 'w' else 0))
                    moves.append(((r, c), (nr, nc), is_capture, reaches_goal))
                elif (nr, nc) not in side_me and (nr, nc) not in side_opp:
                    is_capture = False
                    reaches_goal = (nr == (7 if side_color == 'w' else 0))
                    moves.append(((r, c), (nr, nc), is_capture, reaches_goal))
        return moves

    # Apply a move for a given side, return new (side_me, side_opp) sets
    def apply_move(side_me: set, side_opp: set, move: Tuple[Pos, Pos]):
        frm, to = move
        new_me = set(side_me)
        new_opp = set(side_opp)
        # remove from origin and put to destination
        if frm in new_me:
            new_me.remove(frm)
        # capture if opponent occupies to
        if to in new_opp:
            new_opp.remove(to)
        new_me.add(to)
        return new_me, new_opp

    # Check terminal states
    def check_win(root_color: str, my_set: set, opp_set: set):
        # returns +inf if root wins, -inf if root loses, None if not terminal
        # root wins if any of root pieces reaches opponent home row or opponent has no pieces
        # root loses if any opponent piece reaches root home row or root has no pieces
        # find root/opp home rows
        root_goal = 7 if root_color == 'w' else 0
        opp_goal = 0 if root_color == 'w' else 7
        # If root has no pieces -> loss
        if len(my_set) == 0:
            return -math.inf
        # If opponent has no pieces -> win
        if len(opp_set) == 0:
            return math.inf
        # If any of my pieces reached opponent home row -> win
        for (r, c) in my_set:
            if r == root_goal:
                return math.inf
        # If any opponent pieces reached my home row -> loss
        for (r, c) in opp_set:
            if r == opp_goal:
                return -math.inf
        return None

    # Heuristic evaluation for non-terminal positions from root player's perspective
    def heuristic(root_color: str, my_set: set, opp_set: set):
        # Material
        my_count = len(my_set)
        opp_count = len(opp_set)
        mat = 1000 * (my_count - opp_count)

        # Advancement: sum of distances toward goal
        def advancement_sum(s: set, col: str):
            if col == 'w':
                # white advances to row 7: use row value
                return sum(r for (r, c) in s)
            else:
                # black advances to row 0: use (7 - row) or (7 - r)? Want higher if closer to 0
                # For consistency, distance-to-opponent-home: for black target row 0 -> (7 - r)
                return sum(7 - r for (r, c) in s)

        adv_my = advancement_sum(my_set, root_color)
        adv_opp = advancement_sum(opp_set, 'b' if root_color == 'w' else 'w')
        adv = 10 * (adv_my - adv_opp)

        # Mobility: number of legal moves
        my_moves = len(generate_moves_for(my_set, opp_set, root_color))
        opp_color = 'b' if root_color == 'w' else 'w'
        opp_moves = len(generate_moves_for(opp_set, my_set, opp_color))
        mob = 5 * (my_moves - opp_moves)

        # Center control: pieces in columns 3 and 4 are slightly better
        center_my = sum(1 for (r, c) in my_set if 2 <= c <= 5)
        center_opp = sum(1 for (r, c) in opp_set if 2 <= c <= 5)
        center = 3 * (center_my - center_opp)

        score = mat + adv + mob + center
        return score

    # Root color
    root_color = color

    # Quick immediate-check: if there's any immediate winning move, play it.
    root_moves = generate_moves_for(me_set, opp_set, color)
    # Sort moves to examine winning captures/promotions first
    # Each move tuple: (from, to, is_capture, reaches_goal)
    for frm, to, is_cap, reaches_goal in root_moves:
        if reaches_goal:
            return (frm, to)
        # capture that captures last opponent piece -> win
        if is_cap and len(opp_set) == 1:
            return (frm, to)

    # If no immediate terminal move, prepare search
    # Minimax with alpha-beta.
    MAX_DEPTH = 3  # depth 3 is a balance of strength and time

    # Time check
    def time_exceeded():
        return (time.time() - _start_time) > _TIME_LIMIT

    # Minimax: returns (score, best_move) where best_move is from the perspective of the current player to move.
    # But score is always measured relative to root player (positive better for root).
    def minimax(my_set: set, opp_set: set, to_move_color: str, depth: int, alpha: float, beta: float):
        # my_set and opp_set are sets where my_set are the root player's pieces and opp_set are the root opponent's pieces.
        # But the side to move may be root_color or opponent color.
        # Determine which piece sets correspond to the moving side.
        # If to_move_color == root_color -> moving side is root (we will generate moves for my_set)
        # else -> generate moves for opp_set, but when applying moves we must update opp_set.
        # First check terminal
        terminal = check_win(root_color, my_set, opp_set)
        if terminal is not None:
            return (terminal, None)
        if depth == 0 or time_exceeded():
            return (heuristic(root_color, my_set, opp_set), None)

        moving_is_root = (to_move_color == root_color)
        side_me = my_set if moving_is_root else opp_set
        side_opp = opp_set if moving_is_root else my_set
        moves = generate_moves_for(side_me, side_opp, to_move_color)

        if not moves:
            # No legal moves for side to move -> opponent wins? We'll evaluate as a very bad outcome for the side to move.
            # If side to move is root, this is a loss; if it's opponent, it's a win for root.
            if moving_is_root:
                return (-math.inf, None)
            else:
                return (math.inf, None)

        # Order moves: promotions and captures first
        moves.sort(key=lambda m: (not m[3], not m[2]))  # prioritize reaches_goal True, then captures True

        best_move = None
        if moving_is_root:
            # Maximizer
            value = -math.inf
            for frm, to, is_cap, reaches_goal in moves:
                # apply move
                if moving_is_root:
                    new_my, new_opp = apply_move(my_set, opp_set, (frm, to))
                else:
                    new_opp, new_my = apply_move(opp_set, my_set, (frm, to))
                    # swap names back
                # If move is immediate win for root (reaches goal or removes last opp), short-circuit
                if reaches_goal:
                    return (math.inf, (frm, to))
                if is_cap and len(opp_set) == 1:
                    return (math.inf, (frm, to))

                # Recurse with switched player
                next_color = 'b' if to_move_color == 'w' else 'w'
                sc, _ = minimax(new_my, new_opp, next_color, depth - 1, alpha, beta)
                if sc is None:
                    sc = heuristic(root_color, new_my, new_opp)
                if sc > value:
                    value = sc
                    best_move = (frm, to)
                alpha = max(alpha, value)
                if alpha >= beta or time_exceeded():
                    break
            return (value, best_move)
        else:
            # Minimizer (opponent trying to minimize root's score)
            value = math.inf
            for frm, to, is_cap, reaches_goal in moves:
                if moving_is_root:
                    new_my, new_opp = apply_move(my_set, opp_set, (frm, to))
                else:
                    new_opp, new_my = apply_move(opp_set, my_set, (frm, to))
                # If opponent move reaches root home row -> immediate loss for root
                if reaches_goal:
                    return (-math.inf, (frm, to))
                if is_cap and len(my_set) == 1:
                    # opponent captured last root piece
                    return (-math.inf, (frm, to))

                next_color = 'b' if to_move_color == 'w' else 'w'
                sc, _ = minimax(new_my, new_opp, next_color, depth - 1, alpha, beta)
                if sc is None:
                    sc = heuristic(root_color, new_my, new_opp)
                if sc < value:
                    value = sc
                    best_move = (frm, to)
                beta = min(beta, value)
                if alpha >= beta or time_exceeded():
                    break
            return (value, best_move)

    # Use minimax to pick best move
    score, best = minimax(me_set, opp_set, color, MAX_DEPTH, -math.inf, math.inf)
    if best is not None:
        return best

    # If minimax failed (e.g., time ran out), fall back to a safe greedy selection:
    # Prefer captures, promotions, then forward, then diagonal moves.
    if root_moves:
        # sort by (is_capture desc, reaches_goal desc, forward first)
        def move_priority(m):
            frm, to, is_cap, reaches_goal = m
            frm_r, frm_c = frm
            to_r, to_c = to
            forward = (to_c == frm_c)
            return (-int(is_cap), -int(reaches_goal), -int(forward))
        root_moves.sort(key=move_priority)
        frm, to, _, _ = root_moves[0]
        return (frm, to)

    # As an absolute fallback (should rarely happen), try to find any legal move by brute force scanning pieces:
    pieces = list(me_set)
    d = 1 if color == 'w' else -1
    for (r, c) in pieces:
        nr = r + d
        if 0 <= nr <= 7:
            # forward
            if (nr, c) not in me_set and (nr, c) not in opp_set:
                return ((r, c), (nr, c))
            # diagonals
            for nc in (c - 1, c + 1):
                if 0 <= nc <= 7:
                    if (nr, nc) not in me_set:
                        # may capture or move into empty
                        return ((r, c), (nr, nc))

    # If still nothing, return a deterministic dummy (shouldn't happen in legal states)
    # Return first piece stays in place (illegal), but contest rules require legal moves; we tried best.
    # To avoid returning an illegal move, attempt any board cell forward for piece 0.
    if pieces:
        r, c = pieces[0]
        nr = max(0, min(7, r + (1 if color == 'w' else -1)))
        if (nr, c) not in me_set and (nr, c) not in opp_set:
            return ((r, c), (nr, c))
    # Last resort: return first legal coordinate pair (should never be used)
    return ((me[0][0], me[0][1]), (me[0][0], me[0][1]))  # fallback (likely illegal)
