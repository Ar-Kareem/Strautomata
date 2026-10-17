
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    
    # Determine movement direction
    forward = 1 if color == 'w' else -1  # White moves to higher rows, Black to lower rows
    home_row = 7 if color == 'b' else 0  # Black home row is 7, White home row is 0
    
    # Helper function to check if a position is valid
    def is_valid(row, col):
        return 0 <= row < 8 and 0 <= col < 8
    
    # Evaluate move quality (higher is better)
    def evaluate_move(move):
        _, to_pos = move
        to_row, to_col = to_pos
        
        # Win condition
        if to_row == home_row:
            return float('inf')
        
        # Capture moves are valuable
        if to_pos in opp_set:
            return 100
        
        # Forward move is valuable
        if (to_pos[0] - move[0][0]) == forward:
            return 10
        
        return 1
    
    # Collect all legal moves
    legal_moves = []
    
    for piece in me:
        r, c = piece
        
        # Forward move (straight)
        next_r = r + forward
        if is_valid(next_r, c):
            if (next_r, c) not in occupied:
                legal_moves.append(((r, c), (next_r, c)))
        
        # Diagonal moves (left and right)
        for dc in (-1, 1):
            next_c = c + dc
            if is_valid(next_r, next_c):
                target = (next_r, next_c)
                if target not in me_set:  # Can't move onto own piece
                    legal_moves.append(((r, c), target))
    
    # Sort moves by evaluation
    legal_moves.sort(key=evaluate_move, reverse=True)
    
    # Return the best move
    return legal_moves[0]
