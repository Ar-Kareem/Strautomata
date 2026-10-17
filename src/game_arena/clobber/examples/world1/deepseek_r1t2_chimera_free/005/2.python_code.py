
def policy(you: list[int], opponent: list[int]) -> str:
    def get_legal_moves(current, other):
        moves = []
        rows = len(current)
        cols = len(current[0])
        for r in range(rows):
            for c in range(cols):
                if current[r][c]:
                    # Check up
                    if r > 0 and other[r-1][c]:
                        moves.append(f"{r},{c},U")
                    # Check right
                    if c < cols - 1 and other[r][c+1]:
                        moves.append(f"{r},{c},R")
                    # Check down
                    if r < rows - 1 and other[r+1][c]:
                        moves.append(f"{r},{c},D")
                    # Check left
                    if c > 0 and other[r][c-1]:
                        moves.append(f"{r},{c},L")
        return moves

    def apply_move(y, o, move_str):
        r_str, c_str, dir = move_str.split(',')
        r = int(r_str)
        c = int(c_str)
        dr, dc = r, c
        if dir == 'U':
            dr = r - 1
        elif dir == 'D':
            dr = r + 1
        elif dir == 'R':
            dc = c + 1
        elif dir == 'L':
            dc = c - 1
        
        new_you = [row.copy() for row in y]
        new_opp = [row.copy() for row in o]
        new_you[r][c] = 0
        new_you[dr][dc] = 1
        new_opp[dr][dc] = 0
        
        return new_you, new_opp

    # Generate current player's legal moves
    my_moves = get_legal_moves(you, opponent)
    
    best_move = None
    min_opp_moves = float('inf')
    max_my_moves = float('-inf')
    
    for move in my_moves:
        new_you, new_opp = apply_move(you, opponent, move)
        opp_next_moves = get_legal_moves(new_opp, new_you)
        num_opp_moves = len(opp_next_moves)
        
        # Win immediately if possible
        if num_opp_moves == 0:
            return move
        
        # Calculate my mobility after move
        my_next_moves = get_legal_moves(new_you, new_opp)
        num_my_moves = len(my_next_moves)
        
        # Update best move
        if num_opp_moves < min_opp_moves or \
           (num_opp_moves == min_opp_moves and num_my_moves > max_my_moves):
            min_opp_moves = num_opp_moves
            max_my_moves = num_my_moves
            best_move = move
    
    return best_move if best_move else my_moves[0]  # Fallback to first move
