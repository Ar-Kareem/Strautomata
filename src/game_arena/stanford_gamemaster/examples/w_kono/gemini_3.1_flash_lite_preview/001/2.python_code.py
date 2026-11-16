
def policy(state: list[list[object]], role: str) -> str:
    board = {}
    for fact in state:
        if fact[0] == 'cell':
            board[(int(fact[1]), int(fact[2]))] = fact[3]

    def get_legal_moves():
        moves = []
        # Directions for neighbors
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for (r, c), content in board.items():
            if content == role:
                # Check simple moves
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 4 and 1 <= nc <= 4 and board.get((nr, nc)) == 'blank':
                        moves.append(f"move({r},{c},{nr},{nc})")
                
                # Check jumps
                for dr, dc in directions:
                    mid_r, mid_c = r + dr, c + dc
                    end_r, end_c = r + 2 * dr, c + 2 * dc
                    if 1 <= end_r <= 4 and 1 <= end_c <= 4:
                        if board.get((mid_r, mid_c)) == role and board.get((end_r, end_c)) != role and board.get((end_r, end_c)) != 'blank':
                            moves.append(f"jump({r},{c},{mid_r},{mid_c},{end_r},{end_c})")
        return moves

    legal_moves = get_legal_moves()
    
    # Prioritize jumps
    jumps = [m for m in legal_moves if m.startswith('jump')]
    if jumps:
        return jumps[0]
    
    # Otherwise return a move or kerchunk
    if legal_moves:
        return legal_moves[0]
    
    return "kerchunk"
