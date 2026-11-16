
def square_to_pos(square):
    x = ord(square[0]) - ord('a')
    y = int(square[1]) - 1
    return (x, y)

def pos_to_square(pos):
    x, y = pos
    return chr(ord('a') + x) + str(y + 1)

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    color = 'w' if to_play == 'white' else 'b'
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    best_move = None
    best_score = -float('inf')
    
    for square, piece in pieces.items():
        if piece[0] != color:
            continue
        ptype = piece[1]
        pos = square_to_pos(square)
        moves = []
        
        # Knight moves
        if ptype == 'N':
            deltas = [(1,2), (2,1), (-1,2), (-2,1), (1,-2), (2,-1), (-1,-2), (-2,-1)]
            for dx, dy in deltas:
                nx, ny = pos[0] + dx, pos[1] + dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    dest = pos_to_square((nx, ny))
                    if dest not in pieces or pieces[dest][0] != color:
                        moves.append(dest)
        
        # Pawn moves
        elif ptype == 'P':
            direction = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            nx, ny = pos[0], pos[1] + direction
            if 0 <= ny < 8:
                dest = pos_to_square((nx, ny))
                if dest not in pieces:
                    moves.append(dest)
                    if pos[1] == start_rank:
                        ny += direction
                        dest = pos_to_square((nx, ny))
                        if dest not in pieces:
                            moves.append(dest)
                # Captures
                for dx in [-1, 1]:
                    nx_cap = pos[0] + dx
                    if 0 <= nx_cap < 8:
                        dest = pos_to_square((nx_cap, ny))
                        if dest in pieces and pieces[dest][0] != color:
                            moves.append(dest)
            # Promotions (simplified)
            promotion_rank = 7 if color == 'w' else 0
            if pos[1] + direction == promotion_rank:
                for dx in [0, -1, 1]:
                    nx_cap = pos[0] + dx
                    if 0 <= nx_cap < 8:
                        ny_prom = pos[1] + direction
                        dest = pos_to_square((nx_cap, ny_prom))
                        if (dx == 0 and dest not in pieces) or (dx != 0 and dest in pieces and pieces[dest][0] != color):
                            moves.append(f"{dest}q")
        
        # Sliding pieces (R, B, Q)
        elif ptype in ['R', 'B', 'Q']:
            dirs = []
            if ptype == 'R':
                dirs = [(1,0), (-1,0), (0,1), (0,-1)]
            elif ptype == 'B':
                dirs = [(1,1), (-1,1), (1,-1), (-1,-1)]
            else:
                dirs = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1)]
            for dx, dy in dirs:
                nx, ny = pos[0], pos[1]
                while True:
                    nx += dx
                    ny += dy
                    if not (0 <= nx < 8 and 0 <= ny < 8):
                        break
                    dest = pos_to_square((nx, ny))
                    if dest in pieces:
                        if pieces[dest][0] != color:
                            moves.append(dest)
                        break
                    else:
                        moves.append(dest)
        
        # King moves (excluding castling)
        elif ptype == 'K':
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = pos[0] + dx, pos[1] + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        dest = pos_to_square((nx, ny))
                        if dest not in pieces or pieces[dest][0] != color:
                            moves.append(dest)
        
        # Evaluate moves for this piece
        for dest in moves:
            score = 0
            dest_piece = pieces.get(dest[:2], None)  # Handle promotion dest
            if dest_piece and dest_piece[0] != color:
                score += piece_values.get(dest_piece[1], 0) * 10
            # Centrality bonus for knights and bishops
            if ptype in ['N', 'B']:
                center = sum(abs(p - 3.5) for p in (pos[0], pos[1]))
                score += (14 - center) * 0.1
            # Pawn advancement bonus
            if ptype == 'P':
                score += (pos[1] if color == 'w' else 7 - pos[1]) * 0.1
            if score > best_score or (score == best_score and not best_move):
                best_score = score
                best_move = f"{square}{dest}" if len(dest) <= 2 else f"{square}{dest[:2]}{dest[2]}"
    
    # Fallback to first available move if no evaluation done
    if not best_move:
        for square in sorted(pieces.keys()):
            piece = pieces[square]
            if piece[0] == color:
                dests = []
                if piece[1] == 'P':
                    y = int(square[1]) + (1 if color == 'w' else -1)
                    dests.append(f"{square[0]}{y}")
                elif piece[1] == 'K':
                    dests.extend([pos_to_square((x, y)) for x in range(8) for y in range(8)])
                if dests:
                    for dest in dests[:1]:
                        best_move = f"{square}{dest}"
                        break
                if best_move:
                    break
    
    return (best_move, memory)
