
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    def generate_pawn_moves(square, color, pieces):
        file = square[0]
        rank = int(square[1])
        moves = []
        if color == 'w':
            new_rank = rank + 1
            if 1 <= new_rank <= 8:
                dest = f"{file}{new_rank}"
                if dest not in pieces:
                    if new_rank == 8:
                        for promo in ['q', 'r', 'b', 'n']:
                            moves.append(f"{square}{dest}{promo}")
                    else:
                        moves.append(f"{square}{dest}")
                    if rank == 2:
                        two_dest = f"{file}{rank + 2}"
                        if two_dest not in pieces:
                            moves.append(f"{square}{two_dest}")
                for delta in [-1, 1]:
                    dest_file = chr(ord(file) + delta)
                    if 'a' <= dest_file <= 'h':
                        dest = f"{dest_file}{new_rank}"
                        if dest in pieces and pieces[dest][0] != color:
                            if new_rank == 8:
                                for promo in ['q', 'r', 'b', 'n']:
                                    moves.append(f"{square}{dest}{promo}")
                            else:
                                moves.append(f"{square}{dest}")
        else:
            new_rank = rank - 1
            if 1 <= new_rank <= 8:
                dest = f"{file}{new_rank}"
                if dest not in pieces:
                    if new_rank == 1:
                        for promo in ['q', 'r', 'b', 'n']:
                            moves.append(f"{square}{dest}{promo}")
                    else:
                        moves.append(f"{square}{dest}")
                    if rank == 7:
                        two_dest = f"{file}{rank - 2}"
                        if two_dest not in pieces:
                            moves.append(f"{square}{two_dest}")
                for delta in [-1, 1]:
                    dest_file = chr(ord(file) + delta)
                    if 'a' <= dest_file <= 'h':
                        dest = f"{dest_file}{new_rank}"
                        if dest in pieces and pieces[dest][0] != color:
                            if new_rank == 1:
                                for promo in ['q', 'r', 'b', 'n']:
                                    moves.append(f"{square}{dest}{promo}")
                            else:
                                moves.append(f"{square}{dest}")
        return moves

    def generate_knight_moves(square, color, pieces):
        x = ord(square[0]) - ord('a')
        y = int(square[1]) - 1
        deltas = [(2,1), (1,2), (-1,2), (-2,1), (-2,-1), (-1,-2), (1,-2), (2,-1)]
        moves = []
        for dx, dy in deltas:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                dest = f"{chr(nx + ord('a'))}{ny + 1}"
                if dest not in pieces or pieces[dest][0] != color:
                    moves.append(f"{square}{dest}")
        return moves

    def generate_sliding_moves(square, color, pieces, directions):
        x = ord(square[0]) - ord('a')
        y = int(square[1]) - 1
        moves = []
        for dx, dy in directions:
            step = 1
            while True:
                nx = x + dx * step
                ny = y + dy * step
                if not (0 <= nx < 8 and 0 <= ny < 8):
                    break
                dest = f"{chr(nx + ord('a'))}{ny + 1}"
                if dest in pieces:
                    if pieces[dest][0] != color:
                        moves.append(f"{square}{dest}")
                    break
                moves.append(f"{square}{dest}")
                step += 1
        return moves

    def generate_king_moves(square, color, pieces):
        x = ord(square[0]) - ord('a')
        y = int(square[1]) - 1
        deltas = [(1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1), (0,-1), (1,-1)]
        moves = []
        for dx, dy in deltas:
            nx = x + dx
            ny = y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                dest = f"{chr(nx + ord('a'))}{ny + 1}"
                if dest not in pieces or pieces[dest][0] != color:
                    moves.append(f"{square}{dest}")
        return moves

    def evaluate_move(move, pieces, color, piece_values):
        score = 0
        to_sq = move[2:4]
        if to_sq in pieces:
            score += piece_values.get(pieces[to_sq][1], 0)
        if len(move) > 4:
            promo = move[4].upper()
            score += piece_values.get(promo, 0) - 1
        if ord('c') <= ord(to_sq[0]) <= ord('f') and 3 <= int(to_sq[1]) <= 6:
            score += 0.5
        return score

    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    color_code = 'w' if to_play == 'white' else 'b'
    legal_moves = []

    for square, piece in pieces.items():
        if piece[0] != color_code:
            continue
        if piece[1] == 'P':
            legal_moves.extend(generate_pawn_moves(square, color_code, pieces))
        elif piece[1] == 'N':
            legal_moves.extend(generate_knight_moves(square, color_code, pieces))
        elif piece[1] == 'B':
            legal_moves.extend(generate_sliding_moves(square, color_code, pieces, [(1,1), (1,-1), (-1,1), (-1,-1)]))
        elif piece[1] == 'R':
            legal_moves.extend(generate_sliding_moves(square, color_code, pieces, [(1,0), (0,1), (-1,0), (0,-1)]))
        elif piece[1] == 'Q':
            legal_moves.extend(generate_sliding_moves(square, color_code, pieces, [(1,0), (0,1), (-1,0), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]))
        elif piece[1] == 'K':
            legal_moves.extend(generate_king_moves(square, color_code, pieces))

    if not legal_moves:
        return ('', memory)

    best_move, best_score = legal_moves[0], -float('inf')
    for move in legal_moves:
        score = evaluate_move(move, pieces, color_code, piece_values)
        if score > best_score or (score == best_score and len(move) > len(best_move)):
            best_score = score
            best_move = move

    return (best_move, memory)
