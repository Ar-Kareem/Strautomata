
def policy(state: list[list[object]], role: str) -> str:
    """
    Policy for multipleknightthrough.
    Board coordinates: (board, file, rank) where board in {a,b,c}, file in {a,b,c,d}, rank in 1..8
    Move format: move(board,from_file,from_rank,to_file,to_rank)
    """
    pieces = {}  # (board, file, rank) -> owner ('white' or 'black')
    
    # Parse the state
    for prop in state:
        if prop[0] == "cell" and len(prop) == 5:
            board, file, rank, owner = prop[1], prop[2], prop[3], prop[4]
            pieces[(board, file, rank)] = owner
    
    # Define forward knight moves based on role
    # Files: a=0, b=1, c=2, d=3
    if role == "white":
        # White moves toward rank 8 (increasing rank)
        deltas = [(1, 2), (2, 1), (-1, 2), (-2, 1)]
        target_rank = 8
    else:
        # Black moves toward rank 1 (decreasing rank)
        deltas = [(1, -2), (2, -1), (-1, -2), (-2, -1)]
        target_rank = 1
    
    candidate_moves = []
    
    for (board, f, r), owner in pieces.items():
        if owner != role:
            continue
            
        f_idx = ord(f) - ord('a')
        r_idx = int(r)
        
        for df, dr in deltas:
            nf_idx = f_idx + df
            nr_idx = r_idx + dr
            
            # Check boundaries: files a-d (0-3), ranks 1-8
            if 0 <= nf_idx < 4 and 1 <= nr_idx <= 8:
                nf = chr(ord('a') + nf_idx)
                nr = str(nr_idx)
                dest = (board, nf, nr)
                
                # Check if destination is occupied by own piece (illegal)
                if dest in pieces and pieces[dest] == role:
                    continue
                
                is_capture = dest in pieces  # Must be opponent if not self
                is_winning = (board == 'b' and nr_idx == target_rank)
                
                # Distance to goal (lower is better)
                if role == "white":
                    dist = 8 - nr_idx
                else:
                    dist = nr_idx - 1
                
                # Priority ranking (lower number = higher priority)
                if is_winning:
                    priority = (0, dist)
                elif board == 'b' and is_capture:
                    priority = (1, dist)
                elif board == 'b':
                    priority = (2, dist)
                elif is_capture:
                    priority = (3, dist)
                else:
                    priority = (4, dist)
                
                move_str = f"move({board},{f},{r},{nf},{nr})"
                candidate_moves.append((priority, move_str))
    
    if candidate_moves:
        candidate_moves.sort()
        return candidate_moves[0][1]
    
    # Fallback (should never reach here if game is legal)
    return "move(a,a,1,b,3)"
