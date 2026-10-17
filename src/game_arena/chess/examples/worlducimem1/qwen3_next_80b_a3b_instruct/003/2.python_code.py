
import numpy as np
from collections import defaultdict

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Define piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'
    
    # Precompute all possible moves for the current player and opponent
    def get_piece_moves(square, piece_code, pieces_dict):
        """Generate all legal moves for a piece at square, ignoring check."""
        file, rank = square[0], square[1]
        file_idx = ord(file) - ord('a')
        rank_idx = int(rank) - 1
        piece_type = piece_code[1]
        moves = []
        
        # Directions for each piece type
        if piece_type == 'P':
            # Pawns move forward, capture diagonally
            direction = 1 if color == 'w' else -1
            # Move one square forward
            new_rank = rank_idx + direction
            if 0 <= new_rank <= 7:
                new_square = file + str(new_rank + 1)
                if new_square not in pieces_dict:  # empty square
                    moves.append(square + new_square)
                    # Move two squares forward from starting rank
                    if (color == 'w' and rank == '2') or (color == 'b' and rank == '7'):
                        new_rank2 = new_rank + direction
                        if 0 <= new_rank2 <= 7:
                            new_square2 = file + str(new_rank2 + 1)
                            if new_square2 not in pieces_dict:
                                moves.append(square + new_square2)
            # Captures
            for df in [-1, 1]:
                new_file_idx = file_idx + df
                if 0 <= new_file_idx <= 7:
                    new_file = chr(ord('a') + new_file_idx)
                    new_rank = rank_idx + direction
                    if 0 <= new_rank <= 7:
                        new_square = new_file + str(new_rank + 1)
                        if new_square in pieces_dict and pieces_dict[new_square][0] == opponent_color:
                            moves.append(square + new_square)
        
        elif piece_type == 'R':
            # Rook: horizontal/vertical
            for df, dr in [(0,1), (0,-1), (1,0), (-1,0)]:
                for step in range(1, 8):
                    new_file_idx = file_idx + df * step
                    new_rank_idx = rank_idx + dr * step
                    if not (0 <= new_file_idx <= 7 and 0 <= new_rank_idx <= 7):
                        break
                    new_square = chr(ord('a') + new_file_idx) + str(new_rank_idx + 1)
                    if new_square in pieces_dict:
                        if pieces_dict[new_square][0] == opponent_color:
                            moves.append(square + new_square)
                        break  # blocked
                    moves.append(square + new_square)
        
        elif piece_type == 'N':
            # Knight: L-shaped
            knight_moves = [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]
            for df, dr in knight_moves:
                new_file_idx = file_idx + df
                new_rank_idx = rank_idx + dr
                if 0 <= new_file_idx <= 7 and 0 <= new_rank_idx <= 7:
                    new_square = chr(ord('a') + new_file_idx) + str(new_rank_idx + 1)
                    if new_square not in pieces_dict or pieces_dict[new_square][0] == opponent_color:
                        moves.append(square + new_square)
        
        elif piece_type == 'B':
            # Bishop: diagonals
            for df, dr in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                for step in range(1, 8):
                    new_file_idx = file_idx + df * step
                    new_rank_idx = rank_idx + dr * step
                    if not (0 <= new_file_idx <= 7 and 0 <= new_rank_idx <= 7):
                        break
                    new_square = chr(ord('a') + new_file_idx) + str(new_rank_idx + 1)
                    if new_square in pieces_dict:
                        if pieces_dict[new_square][0] == opponent_color:
                            moves.append(square + new_square)
                        break  # blocked
                    moves.append(square + new_square)
        
        elif piece_type == 'Q':
            # Queen = Rook + Bishop
            for df, dr in [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                for step in range(1, 8):
                    new_file_idx = file_idx + df * step
                    new_rank_idx = rank_idx + dr * step
                    if not (0 <= new_file_idx <= 7 and 0 <= new_rank_idx <= 7):
                        break
                    new_square = chr(ord('a') + new_file_idx) + str(new_rank_idx + 1)
                    if new_square in pieces_dict:
                        if pieces_dict[new_square][0] == opponent_color:
                            moves.append(square + new_square)
                        break  # blocked
                    moves.append(square + new_square)
        
        elif piece_type == 'K':
            # King: one square in any direction
            for df in [-1,0,1]:
                for dr in [-1,0,1]:
                    if df == 0 and dr == 0:
                        continue
                    new_file_idx = file_idx + df
                    new_rank_idx = rank_idx + dr
                    if 0 <= new_file_idx <= 7 and 0 <= new_rank_idx <= 7:
                        new_square = chr(ord('a') + new_file_idx) + str(new_rank_idx + 1)
                        if new_square not in pieces_dict or pieces_dict[new_square][0] == opponent_color:
                            moves.append(square + new_square)
        
        return moves
    
    # Generate all legal moves for current player
    def get_all_legal_moves(pieces_dict, player_color):
        moves = []
        for square, piece in pieces_dict.items():
            if piece[0] == player_color:
                moves.extend(get_piece_moves(square, piece, pieces_dict))
        return moves

    # The legal moves provided by the arena (we must return one from this list)
    legal_moves = [m for m in get_all_legal_moves(pieces, color) if m in legal_moves]

    # If no legal moves, return empty (but problem guarantees at least one)
    if not legal_moves:
        return 'a2a3', memory  # fallback

    # Evaluate position: utility function
    def evaluate_position(pieces_dict, player_color):
        material_score = 0
        mobility_score = 0
        center_control_score = 0
        king_safety_score = 0
        check_bonus = 0
        central_squares = {'d4', 'd5', 'e4', 'e5'}
        
        # Material
        for square, piece in pieces_dict.items():
            value = piece_values[piece[1]]
            if piece[0] == 'w':
                material_score += value
            else:
                material_score -= value
        
        # Mobility: count pieces' potential moves (approximate)
        for square, piece in pieces_dict.items():
            if piece[0] == player_color:
                moves = len(get_piece_moves(square, piece, pieces_dict))
                mobility_score += moves
        
        # Center control: reward pieces on or attacking central squares
        for square, piece in pieces_dict.items():
            if piece[0] == player_color:
                file_idx = ord(square[0]) - ord('a')
                rank_idx = int(square[1]) - 1
                # One square away from center counts as control
                if abs(file_idx - 3.5) <= 1.5 and abs(rank_idx - 3.5) <= 1.5:
                    center_control_score += 0.1 * piece_values[piece[1]]
        
        # King safety: check if king is exposed (on 1st/8th rank or near opponents)
        king_square = None
        for sq, p in pieces_dict.items():
            if p == player_color + 'K':
                king_square = sq
                break
        if king_square:
            file, rank = king_square[0], king_square[1]
            rank_idx = int(rank)
            # Penalize if king is on edge
            if rank in ['1', '8']:
                king_safety_score -= 1.0
            # Get adjacent squares
            adjacents = []
            for df in [-1,0,1]:
                for dr in [-1,0,1]:
                    if df == 0 and dr == 0:
                        continue
                    new_file = chr(ord(file) + df)
                    new_rank = str(int(rank) + dr)
                    if 'a' <= new_file <= 'h' and '1' <= new_rank <= '8':
                        adjacents.append(new_file + new_rank)
            # Check for enemy pieces nearby
            for adj in adjacents:
                if adj in pieces_dict and pieces_dict[adj][0] == opponent_color:
                    # Penalize each enemy piece adjacent
                    if pieces_dict[adj][1] == 'Q' or pieces_dict[adj][1] == 'R':
                        king_safety_score -= 2.0
                    else:
                        king_safety_score -= 0.5
        
        return material_score + 0.1 * mobility_score + 0.3 * center_control_score + king_safety_score + 100 * check_bonus

    # Check if a move leads to checkmate
    def is_checkmate_after_move(move, pieces_dict):
        # Temporarily apply move
        from_square, to_square = move[:2], move[2:]
        captured = pieces_dict.get(to_square, None)
        moving_piece = pieces_dict[from_square]
        new_pieces = pieces_dict.copy()
        del new_pieces[from_square]
        new_pieces[to_square] = moving_piece
        
        # Check if opponent has any legal move (if none, it's checkmate)
        opponent_moves = get_all_legal_moves(new_pieces, opponent_color)
        
        # Check if opponent king is under attack
        king_square = None
        for sq, p in new_pieces.items():
            if p == opponent_color + 'K':
                king_square = sq
                break
        if king_square is None:
            return False  # opponent king not found? shouldn't happen
        
        # Check if king is attacked
        for sq, p in new_pieces.items():
            if p[0] == player_color:
                for m in get_piece_moves(sq, p, new_pieces):
                    if m[2:] == king_square:
                        # King is in check
                        # Now check if any opponent move gets out of check
                        for om in opponent_moves:
                            # Simulate opponent move
                            om_from, om_to = om[:2], om[2:]
                            temp_pieces = new_pieces.copy()
                            del temp_pieces[om_from]
                            temp_pieces[om_to] = new_pieces[om_from]
                            
                            # Check if opponent king is still in check
                            king_square_after = om_to if om_from == king_square else king_square
                            opponent_attacked = False
                            for ss, pp in temp_pieces.items():
                                if pp[0] == player_color:
                                    for mm in get_piece_moves(ss, pp, temp_pieces):
                                        if mm[2:] == king_square_after:
                                            opponent_attacked = True
                                            break
                                    if opponent_attacked:
                                        break
                            if not opponent_attacked:
                                return False  # found escape
                        return True  # no escape, checkmate
        return False

    # Check if move puts opponent in check
    def is_check_after_move(move, pieces_dict):
        from_square, to_square = move[:2], move[2:]
        captured = pieces_dict.get(to_square, None)
        moving_piece = pieces_dict[from_square]
        new_pieces = pieces_dict.copy()
        del new_pieces[from_square]
        new_pieces[to_square] = moving_piece
        
        # Find opponent king
        king_square = None
        for sq, p in new_pieces.items():
            if p == opponent_color + 'K':
                king_square = sq
                break
        if king_square is None:
            return False
        
        # Check if any of our pieces attack the king
        for sq, p in new_pieces.items():
            if p[0] == color:
                for m in get_piece_moves(sq, p, new_pieces):
                    if m[2:] == king_square:
                        return True
        return False

    # Candidate move ordering: captures, checks, then others
    def order_moves(legal_moves_list):
        checked_moves = []
        captured_moves = []
        others = []
        for move in legal_moves_list:
            from_sq, to_sq = move[:2], move[2:]
            if to_sq in pieces and pieces[to_sq][0] == opponent_color:
                captured_moves.append(move)
            elif is_check_after_move(move, pieces):
                checked_moves.append(move)
            else:
                others.append(move)
        return checked_moves + captured_moves + others

    # Alpha-Beta Search (depth 2)
    def alpha_beta(pieces_current, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return evaluate_position(pieces_current, color)
        
        legal_moves_here = get_all_legal_moves(pieces_current, color if maximizing_player else opponent_color)
        if not legal_moves_here:
            # Check for stalemate or checkmate
            king_square = None
            for sq, p in pieces_current.items():
                if p == (color if maximizing_player else opponent_color) + 'K':
                    king_square = sq
                    break
            if king_square:
                # Check if king is under attack
                attacked = False
                for sq, p in pieces_current.items():
                    if p[0] != (color if maximizing_player else opponent_color):
                        for m in get_piece_moves(sq, p, pieces_current):
                            if m[2:] == king_square:
                                attacked = True
                                break
                        if attacked:
                            break
                if attacked:
                    return -10000 if maximizing_player else 10000  # checkmate
                else:
                    return 0  # stalemate
        
        moves_ordered = order_moves(legal_moves_here)
        
        if maximizing_player:
            max_eval = -float('inf')
            for move in moves_ordered:
                from_sq, to_sq = move[:2], move[2:]
                captured = pieces_current.get(to_sq, None)
                moving_piece = pieces_current[from_sq]
                new_pieces = pieces_current.copy()
                del new_pieces[from_sq]
                new_pieces[to_sq] = moving_piece
                
                # Handle promotion
                if len(move) > 4:
                    promotion_piece = move[4]
                    new_pieces[to_sq] = color + promotion_piece
                
                eval_score = alpha_beta(new_pieces, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves_ordered:
                from_sq, to_sq = move[:2], move[2:]
                captured = pieces_current.get(to_sq, None)
                moving_piece = pieces_current[from_sq]
                new_pieces = pieces_current.copy()
                del new_pieces[from_sq]
                new_pieces[to_sq] = moving_piece
                
                # Handle promotion
                if len(move) > 4:
                    promotion_piece = move[4]
                    new_pieces[to_sq] = opponent_color + promotion_piece
                
                eval_score = alpha_beta(new_pieces, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # alpha cutoff
            return min_eval

    # For speed, if few legal moves or we're in endgame, use minimax
    # Otherwise, if many legal moves, do depth=1 to avoid timeout
    if len(legal_moves) < 10:
        depth = 2
    else:
        depth = 1  # to ensure we don't exceed 1s

    # Use memory for transposition table
    transposition_table = memory.get('tt', {})
    board_key = tuple(sorted(pieces.items()))
    
    if board_key in transposition_table:
        best_move = transposition_table[board_key].get('best_move', legal_moves[0])
        return best_move, memory

    # We'll do minimax for depth=1 for safety (fallback if depth=2 is too slow)
    if depth > 0:
        best_move = legal_moves[0]
        best_score = -float('inf')
        ordered_moves = order_moves(legal_moves)
        
        for move in ordered_moves:
            # Simulate move
            from_sq, to_sq = move[:2], move[2:]
            captured = pieces.get(to_sq, None)
            moving_piece = pieces[from_sq]
            new_pieces = pieces.copy()
            del new_pieces[from_sq]
            new_pieces[to_sq] = moving_piece
            
            # Handle promotion
            if len(move) > 4:
                promotion_piece = move[4]
                new_pieces[to_sq] = color + promotion_piece
            
            # Evaluate after move
            if depth == 1:
                eval_score = evaluate_position(new_pieces, color)
            else:
                # For depth=2, run minimax
                eval_score = alpha_beta(new_pieces, depth-1, -float('inf'), float('inf'), False)
            
            # Check for immediate checkmate
            if is_checkmate_after_move(move, pieces):
                transposition_table[board_key] = {'best_move': move}
                memory['tt'] = transposition_table
                return move, memory
            
            if eval_score > best_score:
                best_score = eval_score
                best_move = move
        
        transposition_table[board_key] = {'best_move': best_move}
        memory['tt'] = transposition_table
        return best_move, memory
    else:
        # Fallback: pick capture or first move
        for move in legal_moves:
            if move[2:] in pieces and pieces[move[2:]][0] == opponent_color:
                return move, memory
        return legal_moves[0], memory
