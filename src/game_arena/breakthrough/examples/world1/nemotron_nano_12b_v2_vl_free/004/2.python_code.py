
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    moves = []
    for (r, c) in me:
        if color == 'w':
            new_r = r + 1
        else:
            new_r = r - 1
        
        if 0 <= new_r < 8:
            target = (new_r, c)
            if target not in me and target not in opp:
                moves.append(((r, c), target))
        
        for dc in [-1, 1]:
            if color == 'w':
                new_r_diag = r + 1
            else:
                new_r_diag = r - 1
            new_c = c + dc
            if 0 <= new_r_diag < 8 and 0 <= new_c < 8:
                target = (new_r_diag, new_c)
                if target in opp:
                    moves.append(((r, c), target))
    
    promote_row = 7 if color == 'w' else 0
    
    for move in moves:
        _, to_pos = move
        if to_pos[0] == promote_row:
            return move
    
    capture_moves = [m for m in moves if m[1] in opp]
    non_capture_moves = [m for m in moves if m[1] not in opp]
    
    if capture_moves:
        if color == 'w':
            sorted_captures = sorted(capture_moves, key=lambda m: m[1][0], reverse=True)
        else:
            sorted_captures = sorted(capture_moves, key=lambda m: m[1][0])
        return sorted_captures[0]
    
    if color == 'w':
        non_capture_moves.sort(key=lambda m: m[1][0], reverse=True)
    else:
        non_capture_moves.sort(key=lambda m: m[1][0])
    
    return non_capture_moves[0] if non_capture_moves else moves[0]
