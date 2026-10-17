
#!/usr/bin/env python3
from typing import List, Tuple, Set, Dict, Optional
import math

# Type aliases
Coord = Tuple[int, int]
Move = Tuple[Coord, Coord]

# Heuristic weights
WEIGHT_KING = 120
WEIGHT_MAN = 80
WEIGHT_ADVANCE = 8
WEIGHT_CENTER = 2
PENALTY_EXPOSE = 150

def policy(my_men: List[Coord], my_kings: List[Coord], opp_men: List[Coord], opp_kings: List[Coord], color: str) -> Tuple[Coord, Coord]:
    """
    Return the chosen move as ((from_row, from_col), (to_row, to_col))
    """

    # Helper utility functions
    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8

    # Forward direction for men: black moves downward (decreasing rows), white upward (increasing rows)
    forward_dir = -1 if color == 'b' else 1
    opp_color = 'w' if color == 'b' else 'b'
    opp_forward_dir = -forward_dir

    # Build board sets for occupancy checks
    def make_board(my_men_set, my_kings_set, opp_men_set, opp_kings_set):
        return {
            'my_men': set(my_men_set),
            'my_kings': set(my_kings_set),
            'opp_men': set(opp_men_set),
            'opp_kings': set(opp_kings_set),
        }

    start_board = make_board(my_men, my_kings, opp_men, opp_kings)

    # Determine directions for moves and captures
    def man_directions(forward):
        # men move/capture forward diagonals only (common English/American rules)
        return [(forward, -1), (forward, 1)]

    king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    # Generate all capture sequences (multi-jumps) for a single piece
    def generate_jumps_for_piece(pos: Coord, is_king: bool, board: Dict) -> List[Tuple[Coord, List[Coord]]]:
        """
        Return list of tuples: (final_landing_coord, list_of_captured_coords)
        Each sequence starts from pos and captures captured_coords in order, landing at final_landing_coord.
        """
        results: List[Tuple[Coord, List[Coord]]] = []

        start_r, start_c = pos

        # sets for quick membership
        opp_all = board['opp_men'] | board['opp_kings']
        occupied = board['my_men'] | board['my_kings'] | board['opp_men'] | board['opp_kings']

        # Choose allowed directions for the piece (men only forward)
        dirs = king_directions if is_king else man_directions(forward_dir)

        # DFS
        def dfs(r, c, captured: List[Coord], occ_set: Set[Coord], opp_remaining: Set[Coord]):
            found_any = False
            local_dirs = king_directions if is_king else man_directions(forward_dir)
            for dr, dc in local_dirs:
                mid_r, mid_c = r + dr, c + dc
                landing_r, landing_c = r + 2*dr, c + 2*dc
                if not (in_bounds(mid_r, mid_c) and in_bounds(landing_r, landing_c)):
                    continue
                mid = (mid_r, mid_c)
                land = (landing_r, landing_c)
                # must capture opponent piece at mid and landing empty
                if mid in opp_remaining and land not in occ_set:
                    # perform capture
                    found_any = True
                    # update sets
                    occ_set.add(land)
                    occ_set.discard(mid)
                    new_opp_remaining = set(opp_remaining)
                    new_opp_remaining.discard(mid)
                    dfs(landing_r, landing_c, captured + [mid], occ_set, new_opp_remaining)
                    # backtrack
                    occ_set.discard(land)
                    occ_set.add(mid)
            if not found_any:
                # No further captures possible from current location: record final landing and captured list
                results.append(((r, c), captured))

        # initial occupancy: remove starting position since piece will move
        occ_copy = set(occupied)
        occ_copy.discard(pos)
        dfs(start_r, start_c, [], occ_copy, set(opp_all))
        return results

    # Generate simple (non-capturing) moves for a piece
    def generate_simple_moves_for_piece(pos: Coord, is_king: bool, board: Dict) -> List[Coord]:
        moves = []
        r, c = pos
        dirs = king_directions if is_king else man_directions(forward_dir)
        occupied = board['my_men'] | board['my_kings'] | board['opp_men'] | board['opp_kings']
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and (nr, nc) not in occupied:
                moves.append((nr, nc))
        return moves

    # Generate all legal moves for the current side
    def generate_all_moves(board: Dict):
        all_captures: List[Tuple[Coord, Coord, List[Coord]]] = []  # (from, landing, captured_list)
        # men captures
        for m in board['my_men']:
            jumps = generate_jumps_for_piece(m, False, board)
            for landing, captured in jumps:
                if captured:
                    all_captures.append((m, landing, captured))
        # kings captures
        for k in board['my_kings']:
            jumps = generate_jumps_for_piece(k, True, board)
            for landing, captured in jumps:
                if captured:
                    all_captures.append((k, landing, captured))
        if all_captures:
            return all_captures, True  # there are captures

        # otherwise generate simple moves
        all_moves: List[Tuple[Coord, Coord]] = []
        for m in board['my_men']:
            for to in generate_simple_moves_for_piece(m, False, board):
                all_moves.append((m, to))
        for k in board['my_kings']:
            for to in generate_simple_moves_for_piece(k, True, board):
                all_moves.append((k, to))
        return all_moves, False

    # Apply a move to a board and return new board
    def apply_move(board: Dict, from_sq: Coord, to_sq: Coord, captured_list: Optional[List[Coord]] = None, promote_if_needed: bool = True) -> Dict:
        new_board = {
            'my_men': set(board['my_men']),
            'my_kings': set(board['my_kings']),
            'opp_men': set(board['opp_men']),
            'opp_kings': set(board['opp_kings']),
        }
        # Determine if moving a king or man
        is_king = from_sq in new_board['my_kings']
        if is_king:
            new_board['my_kings'].discard(from_sq)
        else:
            new_board['my_men'].discard(from_sq)

        # Remove captured pieces
        if captured_list:
            for cap in captured_list:
                if cap in new_board['opp_men']:
                    new_board['opp_men'].discard(cap)
                if cap in new_board['opp_kings']:
                    new_board['opp_kings'].discard(cap)

        # Place moved piece; handle promotion
        landing_row, landing_col = to_sq
        promote_row = 7 if color == 'w' else 0
        if (not is_king) and promote_if_needed and landing_row == promote_row:
            # promote
            new_board['my_kings'].add(to_sq)
        else:
            if is_king:
                new_board['my_kings'].add(to_sq)
            else:
                new_board['my_men'].add(to_sq)
        return new_board

    # Evaluate a board from our perspective (higher is better)
    def evaluate_board(board: Dict) -> float:
        my_men_count = len(board['my_men'])
        my_kings_count = len(board['my_kings'])
        opp_men_count = len(board['opp_men'])
        opp_kings_count = len(board['opp_kings'])

        score = WEIGHT_KING * (my_kings_count - opp_kings_count) + WEIGHT_MAN * (my_men_count - opp_men_count)

        # Advancement: men closer to promotion are better
        for (r, c) in board['my_men']:
            # for white, higher r is better; for black, lower r is better
            if color == 'w':
                adv = r / 7.0
            else:
                adv = (7 - r) / 7.0
            score += WEIGHT_ADVANCE * adv

            # center control
            center_dist = math.hypot(r - 3.5, c - 3.5)
            score += WEIGHT_CENTER * max(0, (3.5 - center_dist) / 3.5)

        for (r, c) in board['opp_men']:
            if opp_color == 'w':
                adv = r / 7.0
            else:
                adv = (7 - r) / 7.0
            score -= WEIGHT_ADVANCE * adv
            center_dist = math.hypot(r - 3.5, c - 3.5)
            score -= WEIGHT_CENTER * max(0, (3.5 - center_dist) / 3.5)

        # Penalize if opponent has immediate captures (we're exposed)
        # Generate opponent moves on this board (swap roles)
        opp_board = {
            'my_men': set(board['opp_men']),
            'my_kings': set(board['opp_kings']),
            'opp_men': set(board['my_men']),
            'opp_kings': set(board['my_kings']),
        }
        opp_moves, opp_has_captures = generate_all_moves(opp_board)
        if opp_has_captures:
            # magnitude proportional to max captures available to opponent
            max_caps = 0
            for item in opp_moves:
                # item is (from, landing, captured_list)
                _, _, caps = item
                if len(caps) > max_caps:
                    max_caps = len(caps)
            score -= PENALTY_EXPOSE * max_caps

        return score

    # MAIN selection logic:
    # 1) generate all moves; if captures exist, restrict to captures and pick best by (captures_count, evaluation)
    # 2) else evaluate simple moves by evaluation after move, also penalize moves that allow immediate opponent capture

    # Generate our moves
    all_moves, has_captures = generate_all_moves(start_board)

    best_move: Optional[Move] = None
    best_score = -1e9

    if has_captures:
        # all_moves contains tuples (from, landing, captured_list)
        # First maximize number of captures
        max_capture_num = max(len(caps) for (_, _, caps) in all_moves)
        candidate_moves = [m for m in all_moves if len(m[2]) == max_capture_num]

        # Evaluate each candidate by simulation and heuristic
        for frm, landing, caps in candidate_moves:
            new_board = apply_move(start_board, frm, landing, caps, promote_if_needed=True)
            # after move, it's opponent's turn; penalize if opponent has good captures
            val = evaluate_board(new_board)
            # prefer capturing kings slightly
            captured_kings = sum(1 for cap in caps if cap in start_board['opp_kings'])
            val += 15 * captured_kings
            # prefer longer captures (already same length)
            if val > best_score:
                best_score = val
                best_move = (frm, landing)
    else:
        # Non-capturing moves: all_moves is list of (from, to)
        if not all_moves:
            # No legal moves -> but must return something legal. Return a dummy invalid? Better to return any piece staying (illegal).
            # Instead, try to return any occupant move even if blocked: try to pass (not allowed). We'll try to return first piece to same square (fallback).
            # However problem states you are always player to move; there should always be at least one legal move in most positions. We'll defensively handle.
            # Return a simple no-op from first man to itself (will probably be invalid). But to be safer, try to find any simple move by scanning one-step empties ignoring occupancy.
            fallback_from = (my_men[0] if my_men else (my_kings[0] if my_kings else (0,1)))
            fallback_to = fallback_from
            return (fallback_from, fallback_to)

        for frm, to in all_moves:
            new_board = apply_move(start_board, frm, to, captured_list=None, promote_if_needed=True)
            val = evaluate_board(new_board)

            # Additionally penalize moves that move into a square where opponent immediately captures the moved piece
            # Simulate opponent captures; if opponent has any capture that captures the moved landing square, penalize
            opp_b = {
                'my_men': set(new_board['opp_men']),
                'my_kings': set(new_board['opp_kings']),
                'opp_men': set(new_board['my_men']),
                'opp_kings': set(new_board['my_kings']),
            }
            opp_moves2, opp_has_captures2 = generate_all_moves(opp_b)
            if opp_has_captures2:
                # check if any opponent capture list contains the landing square as captured piece
                landing_captured = False
                for item in opp_moves2:
                    # item (from, landing, captured_list)
                    _, _, caps = item
                    if to in caps:
                        landing_captured = True
                        break
                if landing_captured:
                    val -= PENALTY_EXPOSE

            # Slight preference to promote
            landing_row, _ = to
            promote_row = 7 if color == 'w' else 0
            if landing_row == promote_row and frm not in start_board['my_kings']:
                val += 50

            if val > best_score:
                best_score = val
                best_move = (frm, to)

    # As a final safeguard, if best_move is None (shouldn't happen), pick any legal move
    if best_move is None:
        if has_captures:
            frm, landing, caps = all_moves[0]
            best_move = (frm, landing)
        else:
            frm, to = all_moves[0]
            best_move = (frm, to)

    return best_move
