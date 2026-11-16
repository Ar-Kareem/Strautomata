

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Define board geometry and helper functions for move generation and evaluation
    # No external libraries used. Pure Python and fast enough within 1 second.
    
    # Directions for sliding pieces
    DIRS = {
        'R': [(1,0), (-1,0), (0,1), (0,-1)],
        'B': [(1,1), (1,-1), (-1,1), (-1,-1)],
        'Q': [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)],
        'N': [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)],
        'K': [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)],
        'P': []  # handled separately
    }

    # Piece values (centipawns)
    VAL = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

    # Piece-square tables (simple, optimistic for center and advancement)
    # Rows 0..7, columns 0..7 (index 0=a1 for white, but we will orient by color)
    # We'll define from white perspective. We mirror for black.
    PST = {
        'P': [
            0, 0, 0, 0, 0, 0, 0, 0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5, 5, 10, 25, 25, 10, 5, 5,
            0, 0, 0, 20, 20, 0, 0, 0,
            5, -5, -10, 0, 0, -10, -5, 5,
            5, 10, 10, -20, -20, 10, 10, 5,
            0, 0, 0, 0, 0, 0, 0, 0
        ],
        'N': [
            -50, -40, -30, -30, -30, -30, -40, -50,
            -40, -20, 0, 0, 0, 0, -20, -40,
            -30, 0, 10, 15, 15, 10, 0, -30,
            -30, 5, 15, 20, 20, 15, 5, -30,
            -30, 0, 15, 20, 20, 15, 0, -30,
            -30, 5, 10, 15, 15, 10, 5, -30,
            -40, -20, 0, 5, 5, 0, -20, -40,
            -50, -40, -30, -30, -30, -30, -40, -50
        ],
        'B': [
            -20, -10, -10, -10, -10, -10, -10, -20,
            -10, 0, 0, 0, 0, 0, 0, -10,
            -10, 0, 5, 10, 10, 5, 0, -10,
            -10, 5, 5, 10, 10, 5, 5, -10,
            -10, 0, 10, 10, 10, 10, 0, -10,
            -10, 10, 10, 10, 10, 10, 10, -10,
            -10, 5, 0, 0, 0, 0, 5, -10,
            -20, -10, -10, -10, -10, -10, -10, -20
        ],
        'R': [
            0, 0, 0, 0, 0, 0, 0, 0,
            5, 10, 10, 10, 10, 10, 10, 5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            0, 0, 0, 5, 5, 0, 0, 0
        ],
        'Q': [
            -20, -10, -10, -5, -5, -10, -10, -20,
            -10, 0, 0, 0, 0, 0, 0, -10,
            -10, 0, 5, 5, 5, 5, 0, -10,
            -5, 0, 5, 5, 5, 5, 0, -5,
            0, 0, 5, 5, 5, 5, 0, -5,
            -10, 5, 5, 5, 5, 5, 0, -10,
            -10, 0, 5, 0, 0, 0, 0, -10,
            -20, -10, -10, -5, -5, -10, -10, -20
        ],
        'K': [
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -20, -30, -30, -40, -40, -30, -30, -20,
            -10, -20, -20, -20, -20, -20, -20, -10,
            20, 20, 0, 0, 0, 0, 20, 20,
            20, 30, 10, 0, 0, 10, 30, 20
        ]
    }

    # File/Rank to index
    FILES = {'a':0,'b':1,'c':2,'d':3,'e':4,'f':5,'g':6,'h':7}
    RANKS = {'1':0,'2':1,'3':2,'4':3,'5':4,'6':5,'7':6,'8':7}
    INV_FILES = ['a','b','c','d','e','f','g','h']
    INV_RANKS = ['1','2','3','4','5','6','7','8']

    def sq_to_idx(sq):
        f = FILES[sq[0]]
        r = RANKS[sq[1]]
        return r, f

    def idx_to_sq(r, f):
        if 0 <= r <= 7 and 0 <= f <= 7:
            return INV_FILES[f] + INV_RANKS[r]
        return None

    def inside(r, f):
        return 0 <= r < 8 and 0 <= f < 8

    def color_of(piece):
        return piece[0]  # 'w' or 'b'

    def type_of(piece):
        return piece[1]  # 'K','Q','R','B','N','P'

    def setup_pieces_map(pieces):
        # Build occupancy map and piece lists
        occ = {}  # (r,c) -> piece
        white = []
        black = []
        for sq, p in pieces.items():
            r, c = sq_to_idx(sq)
            occ[(r,c)] = p
            if p[0] == 'w':
                white.append(((r,c), p[1]))
            else:
                black.append(((r,c), p[1]))
        return occ, white, black

    def get_king_pos(occ, color):
        for (r,c), p in occ.items():
            if p == color + 'K':
                return (r,c)
        return None

    def is_square_attacked(occ, square, by_color):
        r, c = square
        # Pawns
        if by_color == 'w':
            # white pawns attack up-left (-1, +1) and up-right (+1, +1) relative to white? Actually from white perspective they move up (r+1). But attacks are diagonal.
            # Easier: squares attacked by white pawn at (rp, cp): (rp+1, cp+1) and (rp+1, cp-1)
            # So to check if (r,c) is attacked by any white pawn, we see if there's a white pawn at (r-1, c-1) or (r-1, c+1)
            for dc in (-1, 1):
                pr, pc = r-1, c+dc
                if inside(pr, pc) and occ.get((pr, pc)) == 'wP':
                    return True
        else:  # black
            # black pawns attack down-left and down-right
            for dc in (-1, 1):
                pr, pc = r+1, c+dc
                if inside(pr, pc) and occ.get((pr, pc)) == 'bP':
                    return True

        # Knights
        for dr, dc in DIRS['N']:
            nr, nc = r+dr, c+dc
            if inside(nr, nc):
                p = occ.get((nr, nc))
                if p and p[0] == by_color and p[1] == 'N':
                    return True

        # Kings
        for dr, dc in DIRS['K']:
            nr, nc = r+dr, c+dc
            if inside(nr, nc):
                p = occ.get((nr, nc))
                if p and p[0] == by_color and p[1] == 'K':
                    return True

        # Sliding pieces
        for dr, dc in DIRS['R']:
            nr, nc = r+dr, c+dc
            while inside(nr, nc):
                p = occ.get((nr, nc))
                if p:
                    if p[0] == by_color and p[1] in ('R', 'Q'):
                        return True
                    break
                nr += dr
                nc += dc
        for dr, dc in DIRS['B']:
            nr, nc = r+dr, c+dc
            while inside(nr, nc):
                p = occ.get((nr, nc))
                if p:
                    if p[0] == by_color and p[1] in ('B', 'Q'):
                        return True
                    break
                nr += dr
                nc += dc
        return False

    def in_check(occ, color):
        king = get_king_pos(occ, color)
        if not king:
            return False
        opp = 'w' if color == 'b' else 'b'
        return is_square_attacked(occ, king, opp)

    def gen_moves(occ, color, legal_only=True):
        # Generate moves (from_sq, to_sq, promotion or None)
        moves = []
        opp = 'w' if color == 'b' else 'b'

        # Determine en passant target from memory? We don't track it exactly.
        # We'll ignore en passant for simplicity (rare impact for quick engine).
        # Castling: We'll check if king and rook haven't moved by inspecting initial squares. But we don't have move history.
        # We'll assume if king is on its start square and rook is on its start square and path clear, allow castling.
        # But we cannot track rook moves or king moves across calls.
        # Solution: allow castling if king is on e1/e8 and rook is on a1/h1/a8/h8 and path clear and not in check and squares not attacked.
        # This is a reasonable approximation.

        for (r, c), p in list(occ.items()):
            if p[0] != color:
                continue
            t = p[1]

            if t == 'P':
                # Pawn moves
                if color == 'w':
                    dir_r = 1
                    start_r = 1
                    promotion_r = 7
                    enemy_color = 'b'
                else:
                    dir_r = -1
                    start_r = 6
                    promotion_r = 0
                    enemy_color = 'w'

                # One step
                nr = r + dir_r
                if inside(nr, c) and (nr, c) not in occ:
                    if nr == promotion_r:
                        for prom in ['q', 'r', 'b', 'n']:
                            moves.append(((r,c), (nr,c), prom))
                    else:
                        moves.append(((r,c), (nr,c), None))
                    # Two step from start
                    if r == start_r:
                        nr2 = r + 2*dir_r
                        if inside(nr2, c) and (nr2, c) not in occ:
                            moves.append(((r,c), (nr2, c), None))
                # Captures
                for dc in (-1, 1):
                    nc = c + dc
                    nr = r + dir_r
                    if inside(nr, nc):
                        target = occ.get((nr, nc))
                        if target and target[0] == enemy_color:
                            if nr == promotion_r:
                                for prom in ['q', 'r', 'b', 'n']:
                                    moves.append(((r,c), (nr, nc), prom))
                            else:
                                moves.append(((r,c), (nr, nc), None))
                        # En passant: we skip for simplicity (rare)
            elif t in ('R','B','N','K','Q'):
                for dr, dc in DIRS[t]:
                    nr, nc = r+dr, c+dc
                    if t == 'N' or t == 'K':
                        if inside(nr, nc):
                            target = occ.get((nr, nc))
                            if not target or target[0] != color:
                                moves.append(((r,c), (nr, nc), None))
                    else:
                        while inside(nr, nc):
                            target = occ.get((nr, nc))
                            if target:
                                if target[0] != color:
                                    moves.append(((r,c), (nr, nc), None))
                                break
                            else:
                                moves.append(((r,c), (nr, nc), None))
                            nr += dr
                            nc += dc

        # Castling (approximate): Only for king on start squares if empty path and not in check and squares not attacked
        if color == 'w':
            ksq = (0,4)
            if occ.get(ksq) == 'wK' and not in_check(occ, 'w'):
                # Kingside: rook on h1 (0,7)
                if occ.get((0,7)) == 'wR' and (0,5) not in occ and (0,6) not in occ and not is_square_attacked(occ, (0,5), 'b') and not is_square_attacked(occ, (0,6), 'b'):
                    moves.append((ksq, (0,6), None))
                # Queenside: rook on a1 (0,0)
                if occ.get((0,0)) == 'wR' and (0,1) not in occ and (0,2) not in occ and (0,3) not in occ and not is_square_attacked(occ, (0,3), 'b') and not is_square_attacked(occ, (0,2), 'b'):
                    moves.append((ksq, (0,2), None))
        else:
            ksq = (7,4)
            if occ.get(ksq) == 'bK' and not in_check(occ, 'b'):
                # Kingside: rook on h8 (7,7)
                if occ.get((7,7)) == 'bR' and (7,5) not in occ and (7,6) not in occ and not is_square_attacked(occ, (7,5), 'w') and not is_square_attacked(occ, (7,6), 'w'):
                    moves.append((ksq, (7,6), None))
                # Queenside: rook on a8 (7,0)
                if occ.get((7,0)) == 'bR' and (7,1) not in occ and (7,2) not in occ and (7,3) not in occ and not is_square_attacked(occ, (7,3), 'w') and not is_square_attacked(occ, (7,2), 'w'):
                    moves.append((ksq, (7,2), None))

        if not legal_only:
            return moves

        # Filter legal moves: cannot leave king in check
        legal = []
        for m in moves:
            from_sq, to_sq, prom = m
            # Simulate move
            p = occ.get(from_sq)
            captured = occ.get(to_sq)
            new_occ = occ.copy()
            if prom:
                new_p = color + prom.upper()
            else:
                new_p = p
            del new_occ[from_sq]
            new_occ[to_sq] = new_p

            # Handle castling rook move (approximate)
            if p[1] == 'K' and abs(to_sq[1] - from_sq[1]) == 2:
                if color == 'w':
                    if to_sq[1] == 6:  # O-O
                        del new_occ[(0,7)]
                        new_occ[(0,5)] = 'wR'
                    else:  # O-O-O
                        del new_occ[(0,0)]
                        new_occ[(0,3)] = 'wR'
                else:
                    if to_sq[1] == 6:
                        del new_occ[(7,7)]
                        new_occ[(7,5)] = 'bR'
                    else:
                        del new_occ[(7,0)]
                        new_occ[(7,3)] = 'bR'

            if not in_check(new_occ, color):
                legal.append(m)
        return legal

    def move_to_str(m):
        from_sq = m[0]
        to_sq = m[1]
        prom = m[2]
        s = INV_FILES[from_sq[1]] + INV_RANKS[from_sq[0]] + INV_FILES[to_sq[1]] + INV_RANKS[to_sq[0]]
        if prom:
            s += prom
        return s

    def evaluate(occ, color):
        # Material + PST
        score = 0
        for (r,c), p in occ.items():
            base = p[1]
            val = VAL[base]
            pst_val = PST[base][r*8 + c] if base != 'P' else PST['P'][r*8 + c]
            # Mirror PST for black
            if p[0] == 'b':
                # Mirror row: 7-r
                if base == 'P':
                    pst_val = PST['P'][(7-r)*8 + c]
                elif base == 'N':
                    pst_val = PST['N'][(7-r)*8 + c]
                elif base == 'B':
                    pst_val = PST['B'][(7-r)*8 + c]
                elif base == 'R':
                    pst_val = PST['R'][(7-r)*8 + c]
                elif base == 'Q':
                    pst_val = PST['Q'][(7-r)*8 + c]
                elif base == 'K':
                    pst_val = PST['K'][(7-r)*8 + c]
                val = -val
                pst_val = -pst_val
            score += val + pst_val
        # Encourage checkmate
        opp = 'w' if color == 'b' else 'b'
        legal_next = gen_moves(occ, color, True)
        if not legal_next:
            # No legal moves: stalemate or checkmate
            if in_check(occ, color):
                # We are checkmated (very bad)
                return -99999
            else:
                return 0  # stalemate neutral
        # Opponent's material and mobility next (heuristic)
        # We'll add small mobility component
        opp_moves = gen_moves(occ, opp, True)
        score += 2 * (len(legal_next) - len(opp_moves))
        return score

    def alpha_beta(occ, color, depth, alpha, beta, maximizing_player, orig_color, quiescence=False):
        # Terminal conditions
        moves = gen_moves(occ, color, True)
        if depth <= 0 or not moves:
            if not moves:
                if in_check(occ, color):
                    # Checkmate
                    return (-100000 + (5 - depth)) if color == orig_color else (100000 - (5 - depth))
                else:
                    # Stalemate
                    return 0
            # Quiescence search: include captures only
            if not quiescence:
                cap_moves = [m for m in moves if occ.get(m[1])]
                if cap_moves:
                    return alpha_beta(occ, color, 0, alpha, beta, maximizing_player, orig_color, quiescence=True)
            return evaluate(occ, orig_color)

        # Order moves: captures first, promotions first, checks later (heuristic)
        def move_score(m):
            s = 0
            target = occ.get(m[1])
            if target:
                s += VAL[target[1]] - VAL[m[0][1]]  # capture value - own piece value (rough)
            if m[2]:  # promotion
                s += 800
            # Try to detect if move gives check (quick check)
            # Simulate move
            p = occ.get(m[0])
            new_occ = occ.copy()
            new_p = p if not m[2] else (color + m[2].upper())
            del new_occ[m[0]]
            new_occ[m[1]] = new_p
            if in_check(new_occ, 'w' if color == 'b' else 'b'):
                s += 50
            return s

        moves.sort(key=move_score, reverse=True)

        if maximizing_player:
            best = -999999
            for m in moves:
                # Simulate
                p = occ.get(m[0])
                captured = occ.get(m[1])
                new_occ = occ.copy()
                new_p = p if not m[2] else (color + m[2].upper())
                del new_occ[m[0]]
                new_occ[m[1]] = new_p
                # Castling handling for exact state
                if p[1] == 'K' and abs(m[1][1] - m[0][1]) == 2:
                    if color == 'w':
                        if m[1][1] == 6:
                            del new_occ[(0,7)]
                            new_occ[(0,5)] = 'wR'
                        else:
                            del new_occ[(0,0)]
                            new_occ[(0,3)] = 'wR'
                    else:
                        if m[1][1] == 6:
                            del new_occ[(7,7)]
                            new_occ[(7,5)] = 'bR'
                        else:
                            del new_occ[(7,0)]
                            new_occ[(7,3)] = 'bR'
                next_color = 'w' if color == 'b' else 'b'
                val = alpha_beta(new_occ, next_color, depth-1, alpha, beta, False, orig_color, quiescence)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break  # beta cutoff
            return best
        else:
            best = 999999
            for m in moves:
                p = occ.get(m[0])
                captured = occ.get(m[1])
                new_occ = occ.copy()
                new_p = p if not m[2] else (color + m[2].upper())
                del new_occ[m[0]]
                new_occ[m[1]] = new_p
                if p[1] == 'K' and abs(m[1][1] - m[0][1]) == 2:
                    if color == 'w':
                        if m[1][1] == 6:
                            del new_occ[(0,7)]
                            new_occ[(0,5)] = 'wR'
                        else:
                            del new_occ[(0,0)]
                            new_occ[(0,3)] = 'wR'
                    else:
                        if m[1][1] == 6:
                            del new_occ[(7,7)]
                            new_occ[(7,5)] = 'bR'
                        else:
                            del new_occ[(7,0)]
                            new_occ[(7,3)] = 'bR'
                next_color = 'w' if color == 'b' else 'b'
                val = alpha_beta(new_occ, next_color, depth-1, alpha, beta, True, orig_color, quiescence)
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break
            return best

    def choose_move(pieces, to_play):
        occ, white, black = setup_pieces_map(pieces)
        color = to_play[0]  # 'w' or 'b'
        legal_moves = gen_moves(occ, color, True)
        if not legal_moves:
            # No move? Shouldn't happen if legal, but pick something if forced
            return "0000"

        # If checkmate in one exists, return it
        # Quick scan
        for m in legal_moves:
            p = occ.get(m[0])
            new_occ = occ.copy()
            new_p = p if not m[2] else (color + m[2].upper())
            del new_occ[m[0]]
            new_occ[m[1]] = new_p
            if p[1] == 'K' and abs(m[1][1] - m[0][1]) == 2:
                if color == 'w':
                    if m[1][1] == 6:
                        del new_occ[(0,7)]
                        new_occ[(0,5)] = 'wR'
                    else:
                        del new_occ[(0,0)]
                        new_occ[(0,3)] = 'wR'
                else:
                    if m[1][1] == 6:
                        del new_occ[(7,7)]
                        new_occ[(7,5)] = 'bR'
                    else:
                        del new_occ[(7,0)]
                        new_occ[(7,3)] = 'bR'
            opp = 'w' if color == 'b' else 'b'
            if not gen_moves(new_occ, opp, True) and in_check(new_occ, opp):
                return move_to_str(m)

        # Search with alpha-beta
        best_move = legal_moves[0]
        best_val = -999999 if color == 'w' else 999999
        orig_color = color
        maximizing = (color == 'w')

        # Time-aware: limit to 0.9 seconds if possible
        start_time = None
        try:
            import time
            start_time = time.time()
        except:
            start_time = None

        # Iterative deepening 2 to 3
        for depth in [2, 3]:
            current_best = None
            current_val = -999999 if maximizing else 999999
            # Order moves by heuristic for root
            def root_score(m):
                s = 0
                target = occ.get(m[1])
                if target:
                    s += VAL[target[1]]
                if m[2]:
                    s += 800
                # Check detection
                p = occ.get(m[0])
                new_occ = occ.copy()
                new_p = p if not m[2] else (color + m[2].upper())
                del new_occ[m[0]]
                new_occ[m[1]] = new_p
                if in_check(new_occ, 'w' if color == 'b' else 'b'):
                    s += 50
                return s

            sorted_moves = sorted(legal_moves, key=root_score, reverse=True)

            for m in sorted_moves:
                # Time check
                if start_time and (time.time() - start_time) > 0.85:
                    break

                # Simulate move
                p = occ.get(m[0])
                new_occ = occ.copy()
                new_p = p if not m[2] else (color + m[2].upper())
                del new_occ[m[0]]
                new_occ[m[1]] = new_p
                if p[1] == 'K' and abs(m[1][1] - m[0][1]) == 2:
                    if color == 'w':
                        if m[1][1] == 6:
                            del new_occ[(0,7)]
                            new_occ[(0,5)] = 'wR'
                        else:
                            del new_occ[(0,0)]
                            new_occ[(0,3)] = 'wR'
                    else:
                        if m[1][1] == 6:
                            del new_occ[(7,7)]
                            new_occ[(7,5)] = 'bR'
                        else:
                            del new_occ[(7,0)]
                            new_occ[(7,3)] = 'bR'
                next_color = 'w' if color == 'b' else 'b'
                val = alpha_beta(new_occ, next_color, depth-1, -999999, 999999, not maximizing, orig_color, False)
                if maximizing:
                    if val > current_val:
                        current_val = val
                        current_best = m
                else:
                    if val < current_val:
                        current_val = val
                        current_best = m
            if current_best:
                best_move = current_best
                best_val = current_val
            # If time low, stop
            if start_time and (time.time() - start_time) > 0.9:
                break

        return move_to_str(best_move)

    # Main execution
    action = choose_move(pieces, to_play)
    return action, memory

