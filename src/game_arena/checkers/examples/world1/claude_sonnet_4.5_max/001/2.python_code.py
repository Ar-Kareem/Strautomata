
def policy(my_men, my_kings, opp_men, opp_kings, color):
    """
    Advanced checkers policy with minimax search and smart evaluation.
    """
    
    class GameState:
        def __init__(self, my_men, my_kings, opp_men, opp_kings, color):
            self.my_men = set(my_men)
            self.my_kings = set(my_kings)
            self.opp_men = set(opp_men)
            self.opp_kings = set(opp_kings)
            self.color = color
            self.my_pieces = self.my_men | self.my_kings
            self.opp_pieces = self.opp_men | self.opp_kings
            self.all_pieces = self.my_pieces | self.opp_pieces
        
        def get_legal_moves(self):
            """Returns list of (from_pos, to_pos, captured_set) tuples"""
            # Jumps are mandatory
            jumps = []
            for pos in self.my_men:
                jumps.extend(self._find_jump_sequences(pos, pos, False, set()))
            for pos in self.my_kings:
                jumps.extend(self._find_jump_sequences(pos, pos, True, set()))
            
            if jumps:
                return jumps
            
            # No jumps, return simple moves
            moves = []
            for pos in self.my_men:
                moves.extend(self._simple_moves_from(pos, False))
            for pos in self.my_kings:
                moves.extend(self._simple_moves_from(pos, True))
            
            return moves
        
        def _find_jump_sequences(self, start_pos, curr_pos, is_king, captured):
            """Recursively find all jump sequences from current position"""
            r, c = curr_pos
            sequences = []
            
            for dr, dc in self._directions(is_king):
                mid_r, mid_c = r + dr, c + dc  # Jumped piece
                land_r, land_c = r + 2*dr, c + 2*dc  # Landing square
                
                if not (0 <= land_r < 8 and 0 <= land_c < 8):
                    continue
                
                # Must jump over opponent piece not yet captured
                if (mid_r, mid_c) not in self.opp_pieces or (mid_r, mid_c) in captured:
                    continue
                
                # Landing must be empty (except for our start position)
                if (land_r, land_c) in self.all_pieces and (land_r, land_c) != start_pos:
                    continue
                
                # This is a valid jump
                new_captured = captured | {(mid_r, mid_c)}
                
                # Check if we become a king
                becomes_king = is_king or (
                    (self.color == 'b' and land_r == 0) or 
                    (self.color == 'w' and land_r == 7)
                )
                
                # Try to find further jumps
                further_jumps = self._find_jump_sequences(
                    start_pos, (land_r, land_c), becomes_king, new_captured
                )
                
                if further_jumps:
                    sequences.extend(further_jumps)
                else:
                    # No further jumps, this is a complete sequence
                    sequences.append((start_pos, (land_r, land_c), new_captured))
            
            return sequences
        
        def _simple_moves_from(self, pos, is_king):
            """Get simple (non-jump) moves from position"""
            r, c = pos
            moves = []
            
            for dr, dc in self._directions(is_king):
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in self.all_pieces:
                    moves.append((pos, (nr, nc), set()))
            
            return moves
        
        def _directions(self, is_king):
            """Get movement directions for piece type"""
            if is_king:
                return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            elif self.color == 'b':  # Black moves down
                return [(-1, -1), (-1, 1)]
            else:  # White moves up
                return [(1, -1), (1, 1)]
        
        def apply_move(self, move):
            """Apply move and return new game state from opponent's perspective"""
            from_pos, to_pos, captured = move
            
            # Create new piece sets
            new_my_men = self.my_men.copy()
            new_my_kings = self.my_kings.copy()
            new_opp_men = self.opp_men - captured
            new_opp_kings = self.opp_kings - captured
            
            # Move the piece
            was_king = from_pos in self.my_kings
            if was_king:
                new_my_kings.remove(from_pos)
                new_my_kings.add(to_pos)
            else:
                new_my_men.remove(from_pos)
                # Check promotion
                if (self.color == 'b' and to_pos[0] == 0) or (self.color == 'w' and to_pos[0] == 7):
                    new_my_kings.add(to_pos)
                else:
                    new_my_men.add(to_pos)
            
            # Return state from opponent's perspective
            opp_color = 'w' if self.color == 'b' else 'b'
            return GameState(
                list(new_opp_men), list(new_opp_kings),
                list(new_my_men), list(new_my_kings),
                opp_color
            )
        
        def evaluate(self):
            """Evaluate position (positive is good for current player)"""
            score = 0
            
            # Material advantage
            score += len(self.my_men) * 100
            score += len(self.my_kings) * 150
            score -= len(self.opp_men) * 100
            score -= len(self.opp_kings) * 150
            
            # Positional factors
            for r, c in self.my_men:
                # Reward advancement toward promotion
                if self.color == 'b':
                    score += (7 - r) * 5
                else:
                    score += r * 5
                
                # Center control bonus
                if 2 <= c <= 5:
                    score += 3
                
                # Edge penalty
                if c == 0 or c == 7:
                    score -= 2
            
            for r, c in self.my_kings:
                # Kings prefer center
                center_distance = abs(r - 3.5) + abs(c - 3.5)
                score += (7 - center_distance) * 2
            
            # Penalty for opponent's advancement
            for r, c in self.opp_men:
                if self.color == 'b':
                    score -= r * 3  # Opponent is white, advancing up
                else:
                    score -= (7 - r) * 3  # Opponent is black, advancing down
            
            return score
    
    def alpha_beta(state, depth, alpha, beta, maximizing_player):
        """Minimax with alpha-beta pruning"""
        if depth == 0:
            return state.evaluate(), None
        
        moves = state.get_legal_moves()
        
        if not moves:
            # No legal moves = game over
            return (-999999 if maximizing_player else 999999), None
        
        best_move = None
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in moves:
                new_state = state.apply_move(move)
                eval_score, _ = alpha_beta(new_state, depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                new_state = state.apply_move(move)
                eval_score, _ = alpha_beta(new_state, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return min_eval, best_move
    
    # Initialize game state
    state = GameState(my_men, my_kings, opp_men, opp_kings, color)
    
    # Perform search
    search_depth = 5  # Can be tuned based on performance
    _, best_move = alpha_beta(state, search_depth, float('-inf'), float('inf'), True)
    
    if best_move:
        return (best_move[0], best_move[1])
    
    # Fallback: return any legal move
    moves = state.get_legal_moves()
    if moves:
        return (moves[0][0], moves[0][1])
    
    # Emergency fallback (shouldn't reach here)
    if state.my_pieces:
        pos = list(state.my_pieces)[0]
        return (pos, pos)
    
    return ((0, 0), (0, 0))
