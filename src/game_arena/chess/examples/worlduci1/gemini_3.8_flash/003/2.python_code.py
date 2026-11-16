
def policy(pieces: dict[str, str], to_play: str, *args, **kwargs) -> str:
    color_char = 'w' if to_play.lower().startswith('w') else 'b'
    enemy_char = 'b' if color_char == 'w' else 'w'

    # Retrieve legal moves if passed as an argument or keyword
    legal_moves = None
    if args:
        legal_moves = args[0]
    elif 'legal_moves' in kwargs:
        legal_moves = kwargs['legal_moves']

    # Coordinate helpers
    def sq_to_cr(sq: str):
        return ord(sq[0]) - 97, ord(sq[1]) - 49

    def cr_to_sq(c: int, r: int):
        return chr(c + 97) + str(r + 1)

    def in_bounds(c: int, r: int):
        return 0 <= c < 8 and 0 <= r < 8

    # Check if a square is attacked by a given color
    def is_square_attacked(board: dict[str, str], sq: str, by_color: str) -> bool:
        c, r = sq_to_cr(sq)
        
        # Pawn attacks
        pawn_p = by_color + 'P'
        pr = r - 1 if by_color == 'w' else r + 1
        for pc in (c - 1, c + 1):
            if in_bounds(pc, pr) and board.get(cr_to_sq(pc, pr)) == pawn_p:
                return True

        # Knight attacks
        knight_p = by_color + 'N'
        for dc, dr in ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)):
            nc, nr = c + dc, r + dr
            if in_bounds(nc, nr) and board.get(cr_to_sq(nc, nr)) == knight_p:
                return True

        # King attacks
        king_p = by_color + 'K'
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == 0 and dr == 0:
                    continue
                kc, kr = c + dc, r + dr
                if in_bounds(kc, kr) and board.get(cr_to_sq(kc, kr)) == king_p:
                    return True

        # Orthogonal sliders (Rook, Queen)
        rq_pieces = (by_color + 'R', by_color + 'Q')
        for dc, dr in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nc, nr = c + dc, r + dr
            while in_bounds(nc, nr):
                p = board.get(cr_to_sq(nc, nr))
                if p:
                    if p in rq_pieces:
                        return True
                    break
                nc += dc
                nr += dr

        # Diagonal sliders (Bishop, Queen)
        bq_pieces = (by_color + 'B', by_color + 'Q')
        for dc, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            nc, nr = c + dc, r + dr
            while in_bounds(nc, nr):
                p = board.get(cr_to_sq(nc, nr))
                if p:
                    if p in bq_pieces:
                        return True
                    break
                nc += dc
                nr += dr

        return False

    def find_king(board: dict[str, str], col: str):
        target = col + 'K'
        for sq, p in board.items():
            if p == target:
                return sq
        return None

    def in_check(board: dict[str, str], col: str) -> bool:
        ksq = find_king(board, col)
        if not ksq:
            return True
        enemy = 'b' if col == 'w' else 'w'
        return is_square_attacked(board, ksq, enemy)

    # Apply move on a board copy
    def apply_move(board: dict[str, str], move: str) -> dict[str, str]:
        nb = board.copy()
        src, dst = move[:2], move[2:4]
        piece = nb.pop(src, None)
        if not piece:
            return nb

        # Handle promotion
        if len(move) == 5:
            nb[dst] = piece[0] + move[4].upper()
        else:
            nb[dst] = piece

        # Handle castling king move
        if piece[1] == 'K':
            if src == 'e1' and dst == 'g1':
                nb['f1'] = nb.pop('h1', 'wR')
            elif src == 'e1' and dst == 'c1':
                nb['d1'] = nb.pop('a1', 'wR')
            elif src == 'e8' and dst == 'g8':
                nb['f8'] = nb.pop('h8', 'bR')
            elif src == 'e8' and dst == 'c8':
                nb['d8'] = nb.pop('a8', 'bR')

        # Handle en passant pawn capture
        if piece[1] == 'P' and src[0] != dst[0] and dst not in board:
            cap_sq = dst[0] + src[1]
            nb.pop(cap_sq, None)

        return nb

    # Move generator in case legal_moves is not passed
    def generate_legal_moves(board: dict[str, str], col: str) -> list[str]:
        moves = []
        enemy = 'b' if col == 'w' else 'w'
        pawn_dir = 1 if col == 'w' else -1
        start_rank = 1 if col == 'w' else 6
        promo_rank = 7 if col == 'w' else 0

        for sq, piece in list(board.items()):
            if piece[0] != col:
                continue
            ptype = piece[1]
            c, r = sq_to_cr(sq)

            if ptype == 'P':
                # Advance 1
                nr = r + pawn_dir
                if in_bounds(c, nr) and cr_to_sq(c, nr) not in board:
                    dst = cr_to_sq(c, nr)
                    if nr == promo_rank:
                        for promo in ('q', 'r', 'b', 'n'):
                            moves.append(sq + dst + promo)
                    else:
                        moves.append(sq + dst)
                        # Advance 2
                        nr2 = r + 2 * pawn_dir
                        if r == start_rank and in_bounds(c, nr2) and cr_to_sq(c, nr2) not in board:
                            moves.append(sq + cr_to_sq(c, nr2))

                # Diagonal captures
                for dc in (-1, 1):
                    nc = c + dc
                    if in_bounds(nc, nr):
                        dst = cr_to_sq(nc, nr)
                        target = board.get(dst)
                        if target and target[0] == enemy:
                            if nr == promo_rank:
                                for promo in ('q', 'r', 'b', 'n'):
                                    moves.append(sq + dst + promo)
                            else:
                                moves.append(sq + dst)

            elif ptype == 'N':
                for dc, dr in ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)):
                    nc, nr = c + dc, r + dr
                    if in_bounds(nc, nr):
                        dst = cr_to_sq(nc, nr)
                        target = board.get(dst)
                        if not target or target[0] == enemy:
                            moves.append(sq + dst)

            elif ptype in ('B', 'R', 'Q'):
                dirs = []
                if ptype in ('B', 'Q'):
                    dirs.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
                if ptype in ('R', 'Q'):
                    dirs.extend([(0, 1), (0, -1), (1, 0), (-1, 0)])

                for dc, dr in dirs:
                    nc, nr = c + dc, r + dr
                    while in_bounds(nc, nr):
                        dst = cr_to_sq(nc, nr)
                        target = board.get(dst)
                        if not target:
                            moves.append(sq + dst)
                        elif target[0] == enemy:
                            moves.append(sq + dst)
                            break
                        else:
                            break
                        nc += dc
                        nr += dr

            elif ptype == 'K':
                for dc in (-1, 0, 1):
                    for dr in (-1, 0, 1):
                        if dc == 0 and dr == 0:
                            continue
                        nc, nr = c + dc, r + dr
                        if in_bounds(nc, nr):
                            dst = cr_to_sq(nc, nr)
                            target = board.get(dst)
                            if not target or target[0] == enemy:
                                moves.append(sq + dst)

                # Castling checks
                if col == 'w' and sq == 'e1' and not in_check(board, 'w'):
                    if board.get('h1') == 'wR' and 'f1' not in board and 'g1' not in board:
                        if not is_square_attacked(board, 'f1', 'b') and not is_square_attacked(board, 'g1', 'b'):
                            moves.append('e1g1')
                    if board.get('a1') == 'wR' and 'd1' not in board and 'c1' not in board and 'b1' not in board:
                        if not is_square_attacked(board, 'd1', 'b') and not is_square_attacked(board, 'c1', 'b'):
                            moves.append('e1c1')
                elif col == 'b' and sq == 'e8' and not in_check(board, 'b'):
                    if board.get('h8') == 'bR' and 'f8' not in board and 'g8' not in board:
                        if not is_square_attacked(board, 'f8', 'w') and not is_square_attacked(board, 'g8', 'w'):
                            moves.append('e8g8')
                    if board.get('a8') == 'bR' and 'd8' not in board and 'c8' not in board and 'b8' not in board:
                        if not is_square_attacked(board, 'd8', 'w') and not is_square_attacked(board, 'c8', 'w'):
                            moves.append('e8c8')

        # Filter strictly illegal moves leaving own king in check
        legal = []
        for m in moves:
            nb = apply_move(board, m)
            if not in_check(nb, col):
                legal.append(m)
        return legal

    # Ensure we have valid candidate moves
    if legal_moves is None:
        legal_moves = generate_legal_moves(pieces, color_char)
    else:
        # Sanitize against any spurious non-moves
        legal_moves = [m for m in legal_moves if isinstance(m, str) and len(m) >= 4]

    if not legal_moves:
        return 'e2e4'

    # Piece values
    P_VAL = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

    # Center and positional tables
    CENTER_BONUS = {
        'd4': 25, 'e4': 25, 'd5': 25, 'e5': 25,
        'c4': 12, 'f4': 12, 'c5': 12, 'f5': 12,
        'd3': 10, 'e3': 10, 'd6': 10, 'e6': 10
    }

    def evaluate_board(b: dict[str, str]) -> float:
        score = 0.0
        for sq, piece in b.items():
            val = P_VAL.get(piece[1], 0)
            bonus = CENTER_BONUS.get(sq, 0) if piece[1] in ('N', 'P', 'B') else 0

            # Pawn advancement bonus
            if piece[1] == 'P':
                _, r = sq_to_cr(sq)
                adv = r if piece[0] == 'w' else (7 - r)
                bonus += adv * 5

            total_val = val + bonus
            if piece[0] == color_char:
                score += total_val
            else:
                score -= total_val
        return score

    # 2-Ply Minimax search
    best_move = legal_moves[0]
    best_score = -1e9

    for m in legal_moves:
        b1 = apply_move(pieces, m)

        # Check if own move leaves us in check (if moves came externally unverified)
        if in_check(b1, color_char):
            continue

        opp_in_check = in_check(b1, enemy_char)
        opp_moves = generate_legal_moves(b1, enemy_char)

        if not opp_moves:
            if opp_in_check:
                # Immediate checkmate!
                return m
            else:
                # Stalemate
                move_score = 0.0
        else:
            # Minimax opponent response: opponent minimizes our score
            worst_score = 1e9

            # Prioritize opponent captures for quick tactical pruning
            sorted_opp_moves = sorted(
                opp_moves,
                key=lambda om: P_VAL.get(b1.get(om[2:4], '  ')[1], 0),
                reverse=True
            )

            # Check up to 16 best candidate replies to stay fast & sharp
            for om in sorted_opp_moves[:16]:
                b2 = apply_move(b1, om)
                if in_check(b2, enemy_char):
                    continue
                score2 = evaluate_board(b2)
                if score2 < worst_score:
                    worst_score = score2
            
            move_score = worst_score if worst_score < 1e8 else evaluate_board(b1)

        # Small bonus for checking the opponent
        if opp_in_check:
            move_score += 35

        # Promotion bonus
        if len(m) == 5 and m[4].lower() == 'q':
            move_score += 800

        if move_score > best_score:
            best_score = move_score
            best_move = m

    return best_move
