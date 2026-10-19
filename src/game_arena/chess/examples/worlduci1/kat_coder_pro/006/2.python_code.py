
import itertools

PIECE_VALUES = {'P': 100, 'N': 300, 'B': 300, 'R': 500, 'Q': 900, 'K': 10000}

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Helper functions
    def square_to_coords(sq: str) -> tuple[int, int]:
        file = ord(sq[0]) - ord('a')
        rank = int(sq[1]) - 1
        return (file, rank)

    def coords_to_square(x: int, y: int) -> str:
        if 0 <= x <= 7 and 0 <= y <= 7:
            return chr(ord('a') + x) + str(y + 1)
        return None

    def get_piece_type(code):
        return code[1] if code else None
    
    def get_color(code):
        return code[0] if code else None

    def get_legal_moves(pieces, color):
        moves = []
        # Get all possible moves for a color (not checking legality)
        # For simplicity, we'll just generate moves for the current position
        # This is a simplified version - a full implementation would need to handle all rules
        for sq, pc in pieces.items():
            if pc[0] == color:
                x, y = square_to_coords(sq)
                pt = pc[1]
                if pt == 'P':
                    # Pawn moves
                    if color == 'w':
                        # Single move
                        if y < 7:
                            target = coords_to_square(x, y + 1)
                            if target not in pieces:
                                if y + 1 == 7: # Promotion
                                    for promo in ['q', 'r', 'b', 'n']:
                                        moves.append(f"{sq}{target}{promo}")
                                else:
                                    moves.append(f"{sq}{target}")
                                # Double move
                                if y == 1 and coords_to_square(x, y + 2) not in pieces:
                                    moves.append(f"{sq}{coords_to_square(x, y + 2)}")
                        # Captures
                        for dx in [-1, 1]:
                            if 0 <= x + dx <= 7 and y < 7:
                                target = coords_to_square(x + dx, y + 1)
                                if target in pieces and pieces[target][0] != color:
                                    if y + 1 == 7: # Promotion
                                        for promo in ['q', 'r', 'b', 'n']:
                                            moves.append(f"{sq}{target}{promo}")
                                    else:
                                        moves.append(f"{sq}{target}")
                    else: # Black
                        if y > 0:
                            target = coords_to_square(x, y - 1)
                            if target not in pieces:
                                if y - 1 == 0: # Promotion
                                    for promo in ['q', 'r', 'b', 'n']:
                                        moves.append(f"{sq}{target}{promo}")
                                else:
                                    moves.append(f"{sq}{target}")
                                if y == 6 and coords_to_square(x, y - 2) not in pieces:
                                    moves.append(f"{sq}{coords_to_square(x, y - 2)}")
                        for dx in [-1, 1]:
                            if 0 <= x + dx <= 7 and y > 0:
                                target = coords_to_square(x + dx, y - 1)
                                if target in pieces and pieces[target][0] != color:
                                    if y - 1 == 0: # Promotion
                                        for promo in ['q', 'r', 'b', 'n']:
                                            moves.append(f"{sq}{target}{promo}")
                                    else:
                                        moves.append(f"{sq}{target}")
                elif pt == 'N':
                    for dx, dy in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
                        if 0 <= x + dx <= 7 and 0 <= y + dy <= 7:
                            target = coords_to_square(x + dx, y + dy)
                            if target not in pieces or pieces[target][0] != color:
                                moves.append(f"{sq}{target}")
                elif pt == 'B':
                    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                        for step in range(1, 8):
                            if 0 <= x + dx * step <= 7 and 0 <= y + dy * step <= 7:
                                target = coords_to_square(x + dx * step, y + dy * step)
                                if target in pieces:
                                    if pieces[target][0] != color:
                                        moves.append(f"{sq}{target}")
                                    break
                                else:
                                    moves.append(f"{sq}{target}")
                elif pt == 'R':
                    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                        for step in range(1, 8):
                            if 0 <= x + dx * step <= 7 and 0 <= y + dy * step <= 7:
                                target = coords_to_square(x + dx * step, y + dy * step)
                                if target in pieces:
                                    if pieces[target][0] != color:
                                        moves.append(f"{sq}{target}")
                                    break
                                else:
                                    moves.append(f"{sq}{target}")
                elif pt == 'Q':
                    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                        for step in range(1, 8):
                            if 0 <= x + dx * step <= 7 and 0 <= y + dy * step <= 7:
                                target = coords_to_square(x + dx * step, y + dy * step)
                                if target in pieces:
                                    if pieces[target][0] != color:
                                        moves.append(f"{sq}{target}")
                                    break
                                else:
                                    moves.append(f"{sq}{target}")
                elif pt == 'K':
                    for dx, dy in itertools.product([-1, 0, 1], repeat=2):
                        if dx == 0 and dy == 0:
                            continue
                        if 0 <= x + dx <= 7 and 0 <= y + dy <= 7:
                            target = coords_to_square(x + dx, y + dy)
                            if target not in pieces or pieces[target][0] != color:
                                moves.append(f"{sq}{target}")
        return moves

    def is_attacked(pieces, square, color):
        # Check if a square is attacked by pieces of the given color
        x, y = square_to_coords(square)
        for sq, pc in pieces.items():
            if pc[0] != color:
                continue
            px, py = square_to_coords(sq)
            pt = pc[1]
            if pt == 'P':
                if color == 'w':
                    if y - py == 1 and abs(x - px) == 1:
                        return True
                else:
                    if py - y == 1 and abs(x - px) == 1:
                        return True
            elif pt == 'N':
                if abs(x - px) == 2 and abs(y - py) == 1:
                    return True
                if abs(x - px) == 1 and abs(y - py) == 2:
                    return True
            elif pt == 'B':
                if abs(x - px) == abs(y - py):
                    # Check if path is clear
                    dx = 1 if x > px else -1
                    dy = 1 if y > py else -1
                    for i in range(1, abs(x - px)):
                        if coords_to_square(px + i * dx, py + i * dy) in pieces:
                            return False
                    return True
            elif pt == 'R':
                if x == px or y == py:
                    # Check if path is clear
                    if x == px:
                        dy = 1 if y > py else -1
                        for i in range(1, abs(y - py)):
                            if coords_to_square(px, py + i * dy) in pieces:
                                return False
                    else:
                        dx = 1 if x > px else -1
                        for i in range(1, abs(x - px)):
                            if coords_to_square(px + i * dx, py) in pieces:
                                return False
                    return True
            elif pt == 'Q':
                if x == px or y == py or abs(x - px) == abs(y - py):
                    # Check if path is clear
                    if x == px:
                        dy = 1 if y > py else -1
                        for i in range(1, abs(y - py)):
                            if coords_to_square(px, py + i * dy) in pieces:
                                return False
                    elif y == py:
                        dx = 1 if x > px else -1
                        for i in range(1, abs(x - px)):
                            if coords_to_square(px + i * dx, py) in pieces:
                                return False
                    else:
                        dx = 1 if x > px else -1
                        dy = 1 if y > py else -1
                        for i in range(1, abs(x - px)):
                            if coords_to_square(px + i * dx, py + i * dy) in pieces:
                                return False
                    return True
            elif pt == 'K':
                if abs(x - px) <= 1 and abs(y - py) <= 1:
                    return True
        return False

    def evaluate_position(pieces, color):
        # Simple evaluation function
        score = 0
        for sq, pc in pieces.items():
            value = PIECE_VALUES[pc[1]]
            if pc[0] == color:
                score += value
            else:
                score -= value
        # Add threat bonuses
        for sq, pc in pieces.items():
            if pc[0] == color:
                if is_attacked(pieces, sq, color):
                    score -= PIECE_VALUES[pc[1]]
            else:
                if is_attacked(pieces, sq, color):
                    score += PIECE_VALUES[pc[1]]
        # King safety
        king_sq = None
        for sq, pc in pieces.items():
            if pc[1] == 'K' and pc[0] == color:
                king_sq = sq
                break
        if king_sq:
            if is_attacked(pieces, king_sq, color):
                score -= 1000
        return score

    def apply_move(pieces, move):
        # Apply a move to the pieces dictionary
        # This is a simplified version
        new_pieces = pieces.copy()
        from_sq = move[:2]
        to_sq = move[2:4]
        new_pieces[to_sq] = new_pieces[from_sq]
        del new_pieces[from_sq]
        # Handle promotion
        if len(move) == 5:
            new_pieces[to_sq] = new_pieces[to_sq][0] + move[4]
        return new_pieces

    # Get legal moves
    color = 'w' if to_play == 'white' else 'b'
    legal_moves = get_legal_moves(pieces, color)

    # Check for mate
    for move in legal_moves:
        new_pieces = apply_move(pieces, move)
        # Simplified check for mate
        # We'll just check if the opponent's king is under attack and has no legal moves
        opp_color = 'b' if color == 'w' else 'w'
        king_sq = None
        for sq, pc in new_pieces.items():
            if pc[1] == 'K' and pc[0] == opp_color:
                king_sq = sq
                break
        if king_sq and is_attacked(new_pieces, king_sq, color):
            # Check if king has any legal moves
            king_moves = get_legal_moves(new_pieces, opp_color)
            safe = False
            for km in king_moves:
                if km[:2] == king_sq:
                    # Check if target square is not attacked
                    if not is_attacked(new_pieces, km[2:4], color):
                        safe = True
                        break
            if not safe:
                return move

    # Evaluate all moves
    best_move = None
    best_score = -100000
    for move in legal_moves:
        new_pieces = apply_move(pieces, move)
        score = evaluate_position(new_pieces, color)
        if score > best_score:
            best_score = score
            best_move = move

    # If we have a best move, return it
    if best_move:
        return best_move

    # Fallback: return the first legal move
    return legal_moves[0] if legal_moves else None
