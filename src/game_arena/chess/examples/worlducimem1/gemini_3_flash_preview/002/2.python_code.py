
import random

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    us = to_play[0]
    them = 'b' if us == 'w' else 'w'
    
    piece_vals = {'P': 10, 'N': 30, 'B': 30, 'R': 50, 'Q': 90, 'K': 900}

    def get_legal_moves(board_state, player):
        moves = []
        opp = 'b' if player == 'w' else 'w'
        for sq, p in board_state.items():
            if p[0] != player: continue
            pt = p[1]
            f, r = ord(sq[0]) - 97, int(sq[1]) - 1
            
            if pt == 'P':
                direction = 1 if player == 'w' else -1
                # Push
                target_sq = chr(f + 97) + str(r + direction + 1)
                if 0 <= r + direction <= 7 and target_sq not in board_state:
                    if r + direction in (0, 7):
                        for promo in 'qrbn': moves.append(sq + target_sq + promo)
                    else:
                        moves.append(sq + target_sq)
                        # Double push
                        if (player == 'w' and r == 1) or (player == 'b' and r == 6):
                            ts2 = chr(f + 97) + str(r + 2 * direction + 1)
                            if ts2 not in board_state: moves.append(sq + ts2)
                # Captures
                for df in [-1, 1]:
                    if 0 <= f + df <= 7:
                        ts = chr(f + df + 97) + str(r + direction + 1)
                        if ts in board_state and board_state[ts][0] == opp:
                            if r + direction in (0, 7):
                                for promo in 'qrbn': moves.append(sq + ts + promo)
                            else:
                                moves.append(sq + ts)
            
            elif pt in 'NBRQK':
                vectors = {
                    'N': [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)],
                    'B': [(1,1),(1,-1),(-1,1),(-1,-1)],
                    'R': [(0,1),(0,-1),(1,0),(-1,0)],
                    'Q': [(1,1),(1,-1),(-1,1),(-1,-1),(0,1),(0,-1),(1,0),(-1,0)],
                    'K': [(1,1),(1,-1),(-1,1),(-1,-1),(0,1),(0,-1),(1,0),(-1,0)]
                }[pt]
                limit = 1 if pt in 'NK' else 8
                for dr, df in vectors:
                    for i in range(1, limit + 1):
                        nr, nf = r + dr * i, f + df * i
                        if 0 <= nr <= 7 and 0 <= nf <= 7:
                            ts = chr(nf + 97) + str(nr + 1)
                            if ts not in board_state:
                                moves.append(sq + ts)
                            elif board_state[ts][0] == opp:
                                moves.append(sq + ts)
                                break
                            else: break
                        else: break
        return moves

    def evaluate(board_state):
        score = 0
        for p in board_state.values():
            v = piece_vals.get(p[1], 0)
            score += v if p[0] == us else -v
        return score

    def simulate_move(board_state, move):
        new_board = board_state.copy()
        start, end = move[:2], move[2:4]
        piece = new_board.pop(start)
        if len(move) == 5: # promo
            piece = piece[0] + move[4].upper()
        new_board[end] = piece
        return new_board

    legal_moves = get_legal_moves(pieces, us)
    if not legal_moves: return (None, memory)

    best_move = legal_moves[0]
    best_val = -9999
    
    # 1-depth search with basic response check
    scored_moves = []
    for move in legal_moves:
        st1 = simulate_move(pieces, move)
        # Check if we captured king
        if 'K' not in [p[1] for p in st1.values() if p[0] == them]:
            return (move, memory)
            
        opp_moves = get_legal_moves(st1, them)
        if not opp_moves:
            score = 999
        else:
            # Assume opponent takes our best piece/response
            score = min(evaluate(simulate_move(st1, m)) for m in opp_moves[:20]) # sample for speed
        
        scored_moves.append((score, move))

    scored_moves.sort(key=lambda x: x[0], reverse=True)
    best_score = scored_moves[0][0]
    top_moves = [m for s, m in scored_moves if s == best_score]
    
    return (random.choice(top_moves), memory)
