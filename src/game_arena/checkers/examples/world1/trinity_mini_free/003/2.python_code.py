
def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Check for captures
    captures = []
    for piece in my_men + my_kings:
        r, c = piece
        if color == 'b':
            directions = [(-2, -2), (-2, 2)]
        else:
            directions = [(2, -2), (2, 2)]
        for dx, dy in directions:
            adj = (r + dx, c + dy)
            if 0 <= adj[0] < 8 and 0 <= adj[1] < 8:
                if adj in opp_men or adj in opp_kings:
                    jump = (r + 2*dx, c + 2*dy)
                    if 0 <= jump[0] < 8 and 0 <= jump[1] < 8:
                        if jump not in my_men and jump not in my_kings:
                            if (jump[0] + jump[1]) % 2 == 0:  # Dark square
                                captures.append((piece, jump))
    
    # Prefer king captures if available
    king_captures = [cap for cap in captures if cap[1][0] == 7 if color == 'b' or cap[1][0] == 0 if color == 'w']
    if king_captures:
        return king_captures[0]
    
    # If no king captures, use man captures
    man_captures = [cap for cap in captures if cap[1][0] != 7 if color == 'b' or cap[1][0] != 0 if color == 'w']
    if man_captures:
        return man_captures[0]
    
    # If no captures, move a piece to a safe square
    moves = []
    for piece in my_men + my_kings:
        r, c = piece
        if color == 'b':
            directions = [(-1, -1), (-1, 1)]
        else:
            directions = [(1, -1), (1, 1)]
        for dx, dy in directions:
            adj = (r + dx, c + dy)
            if 0 <= adj[0] < 8 and 0 <= adj[1] < 8:
                if adj not in my_men and adj not in my_kings:
                    if (adj[0] + adj[1]) % 2 == 0:  # Dark square
                        moves.append((piece, adj))
    
    # Return the first valid move
    if moves:
        return moves[0]
    
    # Fallback: return any legal move (should not happen in valid game state)
    return ((0, 0), (0, 1))
