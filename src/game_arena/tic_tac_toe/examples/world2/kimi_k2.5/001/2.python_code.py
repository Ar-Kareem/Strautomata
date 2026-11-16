
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to bitboards: bit i corresponds to row i//4, col i%4
    my_bits = 0
    opp_bits = 0
    for r in range(4):
        for c in range(4):
            idx = r * 4 + c
            if board[r][c] == 1:
                my_bits |= (1 << idx)
            elif board[r][c] == -1:
                opp_bits |= (1 << idx)
    
    # Precomputed winning masks for 4x4 grid
    WIN_MASKS = [
        0x000F, 0x00F0, 0x0F00, 0xF000,  # Rows
        0x1111, 0x2222, 0x4444, 0x8888,  # Cols
        0x1248, 0x8421                   # Diagonals (anti, main)
    ]
    
    def is_win(bits: int) -> bool:
        for mask in WIN_MASKS:
            if bits & mask == mask:
                return True
        return False
    
    # Identify empty cells
    filled = my_bits | opp_bits
    empty_mask = (~filled) & 0xFFFF
    
    moves = []
    e = empty_mask
    while e:
        lsb = e & -e
        moves.append(lsb)
        e ^= lsb
    
    # Immediate win check
    for move in moves:
        if is_win(my_bits | move):
            idx = (move.bit_length() - 1)
            return (idx // 4, idx % 4)
    
    # Separate blocking moves from others for move ordering
    block_moves = []
    other_moves = []
    for move in moves:
        if is_win(opp_bits | move):
            block_moves.append(move)
        else:
            other_moves.append(move)
    ordered_moves = block_moves + other_moves
    
    # Transposition table for this decision
    cache = {}
    
    def minimax(my_b: int, opp_b: int, alpha: int, beta: int, depth: int) -> int:
        # Terminal state checks
        if is_win(my_b):
            return 10 - depth
        if is_win(opp_b):
            return depth - 10
        if (my_b | opp_b) == 0xFFFF:
            return 0
        
        # Memoization
        key = (my_b, opp_b)
        if key in cache:
            return cache[key]
        
        my_count = my_b.bit_count()
        opp_count = opp_b.bit_count()
        
        if my_count == opp_count:  # AI's turn (Maximizing)
            max_eval = -1000
            empty = (~(my_b | opp_b)) & 0xFFFF
            while empty:
                lsb = empty & -empty
                empty ^= lsb
                new_my = my_b | lsb
                # Immediate win check for pruning
                if is_win(new_my):
                    return 9 - depth
                score = minimax(new_my, opp_b, alpha, beta, depth + 1)
                if score > max_eval:
                    max_eval = score
                if max_eval > alpha:
                    alpha = max_eval
                if beta <= alpha:
                    break
            cache[key] = max_eval
            return max_eval
        else:  # Opponent's turn (Minimizing)
            min_eval = 1000
            empty = (~(my_b | opp_b)) & 0xFFFF
            while empty:
                lsb = empty & -empty
                empty ^= lsb
                new_opp = opp_b | lsb
                # Immediate loss check (opponent win)
                if is_win(new_opp):
                    return depth - 9
                score = minimax(my_b, new_opp, alpha, beta, depth + 1)
                if score < min_eval:
                    min_eval = score
                if min_eval < beta:
                    beta = min_eval
                if beta <= alpha:
                    break
            cache[key] = min_eval
            return min_eval
    
    best_score = -1000
    best_move = ordered_moves[0] if ordered_moves else moves[0]
    
    for move in ordered_moves:
        new_my = my_bits | move
        score = minimax(new_my, opp_bits, -1000, 1000, 0)
        if score > best_score:
            best_score = score
            best_move = move
    
    idx = (best_move.bit_length() - 1)
    return (idx // 4, idx % 4)
