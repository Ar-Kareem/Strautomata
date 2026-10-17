
def policy(pieces: dict, to_play: str, legal_moves: list) -> str:
    # Define the value of each piece type.
    value_map = {'K': float('inf'), 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}
    
    # Check for checkmate moves first.
    for move in legal_moves:
        if move.endswith('#'):
            return move
    
    # Check for captures.
    capture_candidates = []
    for move in legal_moves:
        if 'x' not in move:
            continue
        try:
            target_square = move.split('x', 1)[1]
        except IndexError:
            continue  # invalid move format
        if target_square not in pieces:
            continue
        captured_piece = pieces[target_square]
        if captured_piece[0] == ('w' if to_play == 'black' else 'b'):
            continue  # cannot capture own pieces
        captured_type = captured_piece[1]
        captured_val = value_map.get(captured_type, 0)
        if captured_val == 0:
            continue
        # Determine the attacker's type.
        attacker_part = move.split('x')[0]
        attacker_type = attacker_part[0] if len(attacker_part) == 1 else 'P'
        attacker_val = value_map.get(attacker_type, 0)
        net_gain = captured_val - attacker_val
        capture_candidates.append((net_gain, captured_val, attacker_val, move))
    
    if capture_candidates:
        # Sort by highest captured value, then lowest attacker value.
        capture_candidates.sort(key=lambda x: (-x[1], x[2]))
        best_candidates = [cm for cm in capture_candidates if cm[1] == capture_candidates[0][1]]
        # Among these, choose the one with the lowest attacker value (smallest loss).
        best_net = max(c[0] for c in best_candidates)
        best_net_moves = [cm for cm in best_candidates if cm[0] == best_net]
        return best_net_moves[0][3]
    
    # Check if there's any check move (ending with '+'), though not required by problem statement
    # but can be a good heuristic. Here, we simply return the first move.
    return legal_moves[0]
