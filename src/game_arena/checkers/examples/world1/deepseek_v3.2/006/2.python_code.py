
import time
import numpy as np
from typing import List, Tuple, Optional, Set, Dict

def policy(my_men: List[Tuple[int, int]],
           my_kings: List[Tuple[int, int]],
           opp_men: List[Tuple[int, int]],
           opp_kings: List[Tuple[int, int]],
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    
    # Constants
    PLAYER = color
    OPPONENT = 'b' if PLAYER == 'w' else 'w'
    MAX_DEPTH = 6
    TIME_LIMIT = 0.95  # seconds

    # Material weights
    MAN_VALUE = 10
    KING_VALUE = 30
    PROMOTION_BONUS = 5
    CENTER_BONUS = 1
    MOBILITY_WEIGHT = 0.1
    DEFENSE_BONUS = 0.5
    BACK_RANK_SAFETY = 2

    # Dark squares only
    DARK_SQUARES = {(r, c) for r in range(8) for c in range(8) if (r + c) % 2 == 1}

    def is_dark(sq):
        return sq in DARK_SQUARES

    def on_board(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_all_my_pieces():
        return set(my_men + my_kings)

    def get_all_opp_pieces():
        return set(opp_men + opp_kings)

    def get_moves_from(sq, is_king, player_color):
        """Return normal moves (non-captures) from a square."""
        r, c = sq
        moves = []
        if is_king:
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            if player_color == 'b':
                dirs = [(-1, -1), (-1, 1)]  # black moves down
            else:
                dirs = [(1, -1), (1, 1)]     # white moves up
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if on_board(nr, nc) and is_dark((nr, nc)) and (nr, nc) not in get_all_my_pieces() | get_all_opp_pieces():
                moves.append((nr, nc))
        return moves

    def get_captures_from(sq, is_king, player_color, board_men, board_kings):
        """Return all possible capture sequences starting from sq."""
        all_sequences = []
        r, c = sq
        my_pieces = board_men | board_kings
        opp_pieces = (set(opp_men) | set(opp_kings)) if player_color == PLAYER else (set(my_men) | set(my_kings))

        def dfs(current_sq, captured_set, path, is_king_flag):
            cr, cc = current_sq
            found = False
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king_flag else (
                [(-1, -1), (-1, 1)] if player_color == 'b' else [(1, -1), (1, 1)]
            )
            for dr, dc in dirs:
                jump_r, jump_c = cr + dr, cc + dc
                land_r, land_c = cr + 2*dr, cc + 2*dc
                if not on_board(land_r, land_c) or not is_dark((land_r, land_c)):
                    continue
                if (jump_r, jump_c) in opp_pieces and (land_r, land_c) not in my_pieces | opp_pieces and (jump_r, jump_c) not in captured_set:
                    # valid capture
                    new_captured = captured_set | {(jump_r, jump_c)}
                    new_path = path + [(land_r, land_c)]
                    # king promotion
                    new_king = is_king_flag or (player_color == 'b' and land_r == 0) or (player_color == 'w' and land_r == 7)
                    found = True
                    dfs((land_r, land_c), new_captured, new_path, new_king)
            if not found and path:
                all_sequences.append((path[:], captured_set, is_king_flag))
        
        dfs(sq, set(), [], is_king)
        return all_sequences

    def generate_all_moves(board_men, board_kings, player_color):
        """Return list of (from_sq, to_sq, captured_set, promoted) for all possible moves."""
        my_pieces = set(board_men) | set(board_kings)
        moves = []
        # Check captures first
        for piece in my_pieces:
            is_king = piece in board_kings
            captures = get_captures_from(piece, is_king, player_color, set(board_men), set(board_kings))
            for path, captured_set, promoted in captures:
                moves.append((piece, path[0], captured_set, promoted))
                # If multiple jumps, we only need the first step for move generation; the rest will be handled in search
                # Here we add only the first jump, because the rule says return only one move, but we must consider full sequence in evaluation.
                # For simplicity, we just take first jump.
        if moves:  # captures mandatory
            # Only return first jump of each sequence
            return moves
        # Normal moves
        for piece in my_pieces:
            is_king = piece in board_kings
            normal_moves = get_moves_from(piece, is_king, player_color)
            for nm in normal_moves:
                promoted = (player_color == 'b' and nm[0] == 0) or (player_color == 'w' and nm[0] == 7)
                moves.append((piece, nm, set(), promoted))
        return moves

    def apply_move(men, kings, move, player_color):
        """Return new men and kings after move."""
        from_sq, to_sq, captured_set, promoted = move
        new_men = list(men)
        new_kings = list(kings)
        # Remove captured pieces
        for cap in captured_set:
            if cap in new_men:
                new_men.remove(cap)
            if cap in new_kings:
                new_kings.remove(cap)
        # Move piece
        if from_sq in new_men:
            new_men.remove(from_sq)
        else:
            new_kings.remove(from_sq)
        if promoted:
            new_kings.append(to_sq)
        else:
            new_men.append(to_sq)
        return new_men, new_kings

    def evaluate(men1, kings1, men2, kings2, player_color):
        """Heuristic evaluation."""
        score = 0
        # Material
        score += len(men1) * MAN_VALUE
        score += len(kings1) * KING_VALUE
        score -= len(men2) * MAN_VALUE
        score -= len(kings2) * KING_VALUE
        
        # Promotion bonus
        for m in men1:
            if player_color == 'b' and m[0] == 1:
                score += PROMOTION_BONUS  # about to promote
            if player_color == 'w' and m[0] == 6:
                score += PROMOTION_BONUS
        
        # Center control
        center_squares = {(3, 3), (3, 4), (4, 3), (4, 4)}
        for piece in men1 + kings1:
            if piece in center_squares:
                score += CENTER_BONUS
        for piece in men2 + kings2:
            if piece in center_squares:
                score -= CENTER_BONUS
        
        # King safety
        back_rank = 0 if player_color == 'b' else 7
        for k in kings1:
            if k[0] == back_rank:
                score += BACK_RANK_SAFETY
        
        # Mobility estimate (simplified)
        my_moves = generate_all_moves(men1, kings1, player_color)
        opp_moves = generate_all_moves(men2, kings2, 'b' if player_color == 'w' else 'w')
        score += len(my_moves) * MOBILITY_WEIGHT
        score -= len(opp_moves) * MOBILITY_WEIGHT
        
        return score

    def alphabeta(men1, kings1, men2, kings2, depth, alpha, beta, maximizing, player_color, start_time):
        if time.time() - start_time > TIME_LIMIT:
            raise TimeoutError
        if depth == 0:
            return evaluate(men1, kings1, men2, kings2, PLAYER if maximizing else OPPONENT)
        
        moves = generate_all_moves(men1 if maximizing else men2,
                                   kings1 if maximizing else kings2,
                                   player_color if maximizing else ('b' if player_color == 'w' else 'w'))
        if not moves:
            # no moves -> loss
            return -1000 if maximizing else 1000
        
        if maximizing:
            value = -float('inf')
            for move in moves:
                new_men, new_kings = apply_move(men1, kings1, move, player_color)
                # Switch sides
                value = max(value, alphabeta(new_men, new_kings, men2, kings2, depth-1, alpha, beta, False, player_color, start_time))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for move in moves:
                new_men, new_kings = apply_move(men2, kings2, move, 'b' if player_color == 'w' else 'w')
                value = min(value, alphabeta(men1, kings1, new_men, new_kings, depth-1, alpha, beta, True, player_color, start_time))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    # Main iterative deepening
    best_move = None
    start_time = time.time()
    try:
        for depth in range(1, MAX_DEPTH+1):
            moves = generate_all_moves(my_men, my_kings, PLAYER)
            if not moves:
                # must return a legal move, so return any (but there are none)
                # fallback: pick first piece and move forward if possible (shouldn't happen)
                for piece in get_all_my_pieces():
                    r, c = piece
                    nr = r - 1 if PLAYER == 'b' else r + 1
                    for nc in (c-1, c+1):
                        if on_board(nr, nc) and is_dark((nr, nc)) and (nr, nc) not in get_all_my_pieces() | get_all_opp_pieces():
                            return (piece, (nr, nc))
                # emergency fallback
                return ((0, 1), (1, 0)) if (0,1) in get_all_my_pieces() else ((7, 6), (6, 7))
            current_best = None
            best_val = -float('inf')
            for move in moves:
                new_men, new_kings = apply_move(my_men, my_kings, move, PLAYER)
                val = alphabeta(new_men, new_kings, opp_men, opp_kings, depth-1, -float('inf'), float('inf'), False, PLAYER, start_time)
                if val > best_val:
                    best_val = val
                    current_best = move
            best_move = current_best
    except TimeoutError:
        pass
    
    if best_move is None:
        # fallback: first legal move
        moves = generate_all_moves(my_men, my_kings, PLAYER)
        best_move = moves[0] if moves else None
    
    if best_move is None:
        # ultimate fallback
        for piece in get_all_my_pieces():
            r, c = piece
            nr = r - 1 if PLAYER == 'b' else r + 1
            for nc in (c-1, c+1):
                if on_board(nr, nc) and is_dark((nr, nc)) and (nr, nc) not in get_all_my_pieces() | get_all_opp_pieces():
                    return (piece, (nr, nc))
        return ((0, 1), (1, 0))
    
    from_sq, to_sq, _, _ = best_move
    return (from_sq, to_sq)
