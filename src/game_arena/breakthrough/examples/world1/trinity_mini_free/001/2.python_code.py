
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Define movement directions based on color
    if color == 'w':  # White moves upward (increasing row)
        forward_dir = (1, 0)
        diagonals = [(1, 1), (1, -1)]
    else:  # Black moves downward (decreasing row)
        forward_dir = (-1, 0)
        diagonals = [(-1, 1), (-1, -1)]
    
    # Generate all possible moves
    possible_moves = []
    for piece in me:
        r, c = piece
        for direction in [forward_dir] + diagonals:
            dr, dc = direction
            to_r = r + dr
            to_c = c + dc
            if 0 <= to_r < 8 and 0 <= to_c < 8:  # Check board boundaries
                if (to_r, to_c) in opp:  # Capture opportunity
                    possible_moves.append((piece, (to_r, to_c)))
                elif (to_r, to_c) not in me and (to_r, to_c) not in opp:  # Empty square
                    possible_moves.append((piece, (to_r, to_c)))
    
    # Check for winning moves (reach opponent's home row)
    for piece, to in possible_moves:
        if (color == 'w' and to[0] == 7) or (color == 'b' and to[0] == 0):
            return (piece, to)
    
    # Check for captures
    for piece, to in possible_moves:
        if (to[0], to[1]) in opp:
            return (piece, to)
    
    # Check for safe moves (not under threat)
    def is_under_threat(r, c, me, opp):
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) in opp:
                return True
        return False
    
    for piece, to in possible_moves:
        if not is_under_threat(to[0], to[1], me, opp):
            return (piece, to)
    
    # Default to first available move if no threats or captures
    return possible_moves[0][0], possible_moves[0][1]
