
import itertools

def get_legal_moves(me, opp, color):
    delta = 1 if color == 'w' else -1
    my_pieces = set(me)
    opp_pieces = set(opp)
    moves = []
    for r, c in my_pieces:
        # Straight forward
        nr, nc = r + delta, c
        if 0 <= nr <= 7 and 0 <= nc <= 7 and (nr, nc) not in my_pieces and (nr, nc) not in opp_pieces:
            moves.append(((r, c), (nr, nc)))
        # Diagonal captures or empty
        for dc in [-1, 1]:
            nr, nc = r + delta, c + dc
            if 0 <= nr <= 7 and 0 <= nc <= 7 and (nr, nc) not in my_pieces:
                moves.append(((r, c), (nr, nc)))
    return moves

def policy(me, opp, color):
    moves = get_legal_moves(me, opp, color)
    if not moves:
        # This should never happen in a valid game state, but return dummy if needed
        raise ValueError("No legal moves available")
    # Score moves: 100 for captures, 10 for others
    opp_set = set(opp)
    scored_moves = []
    for move in moves:
        _, to_pos = move
        score = 100 if to_pos in opp_set else 10
        scored_moves.append((score, move))
    # Sort descending by score and pick the top one
    scored_moves.sort(reverse=True, key=lambda x: x[0])
    return scored_moves[0][1]
