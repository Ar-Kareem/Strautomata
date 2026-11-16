
import time

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Checkers AI Policy using Iterative Deepening Minimax with Alpha-Beta Pruning.
    """
    
    # --- Constants & Setup ---
    EMPTY = 0
    # Map board values to logic: 1/2 for our pieces, 3/4 for opponent
    MY_MAN = 1
    MY_KING = 2
    OPP_MAN = 3
    OPP_KING = 4
    
    BOARD_SIZE = 8
    
    # Initialize Board
    # 0 = Empty
    # 1 = My Man, 2 = My King
    # 3 = Opp Man, 4 = Opp King
    board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    
    for r, c in my_men:
        board[r][c] = MY_MAN
    for r, c in my_kings:
        board[r][c] = MY_KING
    for r, c in opp_men:
        board[r][c] = OPP_MAN
    for r, c in opp_kings:
        board[r][c] = OPP_KING
        
    # Directions
    # If color is 'w', 'my' pieces move UP (+1 row).
    # If color is 'b', 'my' pieces move DOWN (-1 row).
    forward = 1 if color == 'w' else -1
    
    # Evaluation Weights
    KING_VAL = 200
    MAN_VAL = 100
    CENTER_BONUS = 5
    ADVANCE_BONUS = 2
    BACK_RANK_BONUS = 5
    
    start_time = time.time()
    TIME_LIMIT = 0.95  # Safety buffer for 1s limit
    
    # --- Helper Functions ---
    
    def is_on_board(r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def deep_copy_board(b):
        return [row[:] for row in b]

    def get_piece_legal_moves(b, r, c, p_type, is_mine):
        """
        Generates jumps and slides for a single piece. 
        Note: This is a low-level helper. Global rule requires checking jumps first.
        """
        moves_jumps = [] # list of (next_r, next_c, captured_r, captured_c)
        moves_slides = [] # list of (next_r, next_c)
        
        # Determine movement directions
        # Men move forward diagonal. Kings move all diagonals.
        if p_type == MY_KING or p_type == OPP_KING:
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            # Man
            direction = forward if is_mine else -forward
            dirs = [(direction, -1), (direction, 1)]
            
        for dr, dc in dirs:
            # Check Slide
            nr, nc = r + dr, c + dc
            if is_on_board(nr, nc):
                if b[nr][nc] == EMPTY:
                    moves_slides.append((nr, nc))
                else:
                    # Check Jump
                    # Must be opponent piece
                    cell = b[nr][nc]
                    is_opp_piece = (cell in (OPP_MAN, OPP_KING)) if is_mine else (cell in (MY_MAN, MY_KING))
                    
                    if is_opp_piece:
                        nnr, nnc = nr + dr, nc + dc
                        if is_on_board(nnr, nnc) and b[nnr][nnc] == EMPTY:
                            moves_jumps.append((nnr, nnc, nr, nc))
                            
        return moves_slides, moves_jumps

    def get_all_valid_moves(b, is_my_turn):
        """
        Returns list of legal moves. Each move is ((start_r, start_c), (end_r, end_c), resulting_board).
        Enforces mandatory captures. 
        Simulates multi-jumps to return the final board state.
        The returned move tuple is the FIRST step of the sequence (required by API).
        """
        pieces = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                cell = b[r][c]
                if is_my_turn:
                    if cell == MY_MAN or cell == MY_KING:
                        pieces.append((r, c))
                else:
                    if cell == OPP_MAN or cell == OPP_KING:
                        pieces.append((r, c))
        
        # 1. Check for possible jumps (captures) from ANY piece
        all_jumps = []
        
        for r, c in pieces:
            p_type = b[r][c]
            _, jumps = get_piece_legal_moves(b, r, c, p_type, is_my_turn)
            if jumps:
                # If jumps exist for this piece, we must explore capture chains
                # We do DFS to find all terminal states of jumping
                find_capture_chains(b, r, c, r, c, p_type, is_my_turn, [], all_jumps)
        
        if all_jumps:
            # If any jumps exist, only jumps are allowed
            return all_jumps
        
        # 2. If no jumps, return slides
        all_slides = []
        for r, c in pieces:
            p_type = b[r][c]
            slides, _ = get_piece_legal_moves(b, r, c, p_type, is_my_turn)
            for nr, nc in slides:
                # Generate new board
                new_b = deep_copy_board(b)
                move_piece(new_b, r, c, nr, nc, p_type, is_my_turn)
                # First step is same as slide
                all_slides.append( ((r,c), (nr,nc), new_b) )
                
        return all_slides

    def find_capture_chains(b, start_r, start_c, current_r, current_c, p_type, is_my_turn, path, results):
        """
        Recursive DFS to find all full capture chains.
        path: list of steps taken so far in this chain
        results: list to append final valid moves to
        """
        _, jumps = get_piece_legal_moves(b, current_r, current_c, p_type, is_my_turn)
        
        if not jumps:
            # No more jumps, chain ends.
            # However, we only care if we actually made a jump (captured something).
            # Helper is called initially with no path. Logic outside checks if jumps exist.
            if len(path) > 0:
                # The move is defined by the FIRST step: path[0] -> ((r,c), (nr,nc))
                # The board state is the current 'b'
                # Note: path contains successive (nr, nc) coordinates.
                # First step was start -> path[0]
                first_step_dest = path[0]
                results.append( ((start_r, start_c), first_step_dest, b) )
            return

        for nr, nc, cap_r, cap_c in jumps:
            # Execute jump on a copy
            nb = deep_copy_board(b)
            # Remove captured piece
            nb[cap_r][cap_c] = EMPTY
            # Move jumper
            promoted = move_piece(nb, current_r, current_c, nr, nc, p_type, is_my_turn)
            
            # If promoted, turn ends immediately rules (standard US/UK checkers).
            if promoted:
                first_step_dest = path[0] if path else (nr, nc)
                results.append( ((start_r, start_c), first_step_dest, nb) )
            else:
                # Continue chain
                new_path = path + [(nr, nc)]
                # The piece type remains same unless promoted (handled above)
                find_capture_chains(nb, start_r, start_c, nr, nc, p_type, is_my_turn, new_path, results)

    def move_piece(b, r, c, nr, nc, p_type, is_mine):
        """Moves piece, handles promotion. Returns True if promoted."""
        b[nr][nc] = p_type
        b[r][c] = EMPTY
        
        promoted = False
        # Promotion Logic
        # White moves to row 7. Black moves to row 0. (Index based on 0..7)
        if p_type == MY_MAN or p_type == OPP_MAN:
            promotion_row = 7 if (is_mine and forward == 1) or (not is_mine and forward == -1) else 0
            # If forward=1 (White), targets 7. If forward=-1 (Black), targets 0.
            # My pieces: if White(1) -> 7. If Black(-1) -> 0.
            # Opp pieces: if I am White(1), Opp is Black(-1) -> Opp targets 0.
            #             if I am Black(-1), Opp is White(1) -> Opp targets 7.
            
            target = 7 if ((is_mine and forward == 1) or (not is_mine and forward == -1)) else 0
            if nr == target:
                b[nr][nc] = MY_KING if is_mine else OPP_KING
                promoted = True
        return promoted

    def evaluate(b):
        score = 0
        my_count = 0
        opp_count = 0
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                cell = b[r][c]
                if cell == EMPTY: continue
                
                val = 0
                is_mine = (cell == MY_MAN or cell == MY_KING)
                
                # Material
                if cell == MY_MAN or cell == OPP_MAN:
                    val = MAN_VAL
                else: 
                    val = KING_VAL
                
                # Position
                # Center control (generic)
                if 2 <= r <= 5 and 2 <= c <= 5:
                    val += CENTER_BONUS
                
                # Advancement / Back Rank
                if cell == MY_MAN:
                    # Encourage moving forward
                    # If moving UP (0->7), row is progress.
                    advancement = r if forward == 1 else (7 - r)
                    val += advancement * ADVANCE_BONUS
                    
                    # Back rank defense (row 0 for White, row 7 for Black)
                    home_row = 0 if forward == 1 else 7
                    if r == home_row:
                        val += BACK_RANK_BONUS
                        
                elif cell == OPP_MAN:
                    # Opponent moves opposite direction
                    opp_forward = -forward
                    # If opp moves DOWN (7->0), progress is (7-r).
                    opp_advancement = (7 - r) if opp_forward == -1 else r
                    val += opp_advancement * ADVANCE_BONUS

                if is_mine:
                    score += val
                    my_count += 1
                else:
                    score -= val
                    opp_count += 1
                    
        # Simple endgame heuristic: if winning, push boundaries, if losing, create chaos?
        # For now, just raw score
        return score

    # --- Minimax ---
    
    def minimax(b, depth, alpha, beta, maximizing_player):
        # Time check
        if time.time() - start_time > TIME_LIMIT:
             raise TimeoutError
             
        if depth == 0:
            return evaluate(b)
            
        moves = get_all_valid_moves(b, maximizing_player)
        
        if not moves:
            # No moves available = Loss
            return -100000 + depth if maximizing_player else 100000 - depth

        if maximizing_player:
            max_eval = -float('inf')
            for _, _, next_board in moves:
                eval_val = minimax(next_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for _, _, next_board in moves:
                eval_val = minimax(next_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Execution ---
    
    # Generate initial moves
    possible_moves = get_all_valid_moves(board, True)
    
    if not possible_moves:
        return ((0,0), (0,0)) # Should theoretically be game over before this call

    # Default move (random or first)
    best_move_coords = possible_moves[0][0], possible_moves[0][1]
    
    # Iterative Deepening
    max_depth = 1
    
    try:
        while True:
            if time.time() - start_time > TIME_LIMIT:
                break
                
            current_best_val = -float('inf')
            current_best_move = None
            
            # Root level move ordering or search
            for start, end, next_board in possible_moves:
                val = minimax(next_board, max_depth - 1, -float('inf'), float('inf'), False)
                
                if val > current_best_val:
                    current_best_val = val
                    current_best_move = (start, end)
            
            if current_best_move:
                best_move_coords = current_best_move
            
            max_depth += 1
            if max_depth > 12: # Depth limit safety
                break
                
    except TimeoutError:
        pass # Return best move found so far

    return best_move_coords
