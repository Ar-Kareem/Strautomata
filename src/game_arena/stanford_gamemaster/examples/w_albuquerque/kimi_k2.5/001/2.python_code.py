
def policy(state: list[list[object]], role: str) -> str:
    # Parse state into board dictionary: (r,c) -> content
    board = {}
    for prop in state:
        if prop[0] == "cell" and len(prop) == 4:
            r, c, content = int(prop[1]), int(prop[2]), prop[3]
            board[(r, c)] = content
    
    opponent = "black" if role == "red" else "red"
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    candidates = []  # list of (action_str, new_board_dict)
    
    # Generate all legal moves
    for (r, c), content in board.items():
        if content == role:
            for dr, dc in directions:
                # Simple move
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 5 and 1 <= nc <= 5 and board.get((nr, nc)) == "blank":
                    new_board = board.copy()
                    new_board[(r, c)] = "blank"
                    new_board[(nr, nc)] = role
                    action = f"move({r},{c},{nr},{nc})"
                    candidates.append((action, new_board))
                
                # Jump capture
                mr, mc = r + dr, c + dc  # midpoint (opponent location)
                er, ec = r + 2*dr, c + 2*dc  # landing spot
                if (1 <= mr <= 5 and 1 <= mc <= 5 and 
                    1 <= er <= 5 and 1 <= ec <= 5):
                    if board.get((mr, mc)) == opponent and board.get((er, ec)) == "blank":
                        new_board = board.copy()
                        new_board[(r, c)] = "blank"
                        new_board[(mr, mc)] = "blank"  # capture
                        new_board[(er, ec)] = role
                        action = f"jump({r},{c},{mr},{mc},{er},{ec})"
                        candidates.append((action, new_board))
    
    # If no candidates found (should not happen in legal play), return a dummy
    if not candidates:
        return "move(3,3,3,3)"
    
    # Separate jumps (captures) from regular moves
    jumps = [(a, b) for a, b in candidates if a.startswith("jump")]
    moves = [(a, b) for a, b in candidates if a.startswith("move")]
    
    # Prioritize captures if available
    actions_to_consider = jumps if jumps else moves
    
    def evaluate(b):
        """Evaluate board state from perspective of role"""
        my_count = 0
        opp_count = 0
        my_threats = 0  # pieces that can be captured by opponent
        opp_threats = 0  # opponent pieces we can capture
        advancement = 0
        
        for (r, c), piece in b.items():
            if piece == role:
                my_count += 1
                # Advancement: red wants low rows (1), black wants high rows (5)
                if role == "red":
                    advancement += (5 - r)
                else:
                    advancement += (r - 1)
                
                # Check if this piece is under threat
                threatened = False
                for dr, dc in directions:
                    # Opponent would be at (r-dr, c-dc), land at (r+dr, c+dc)
                    opp_r, opp_c = r - dr, c - dc
                    land_r, land_c = r + dr, c + dc
                    if (1 <= opp_r <= 5 and 1 <= opp_c <= 5 and 
                        1 <= land_r <= 5 and 1 <= land_c <= 5):
                        if b.get((opp_r, opp_c)) == opponent and b.get((land_r, land_c)) == "blank":
                            threatened = True
                            break
                if threatened:
                    my_threats += 1
                    
            elif piece == opponent:
                opp_count += 1
                # Check if opponent piece is threatened by us
                threatened = False
                for dr, dc in directions:
                    my_r, my_c = r - dr, c - dc
                    land_r, land_c = r + dr, c + dc
                    if (1 <= my_r <= 5 and 1 <= my_c <= 5 and 
                        1 <= land_r <= 5 and 1 <= land_c <= 5):
                        if b.get((my_r, my_c)) == role and b.get((land_r, land_c)) == "blank":
                            threatened = True
                            break
                if threatened:
                    opp_threats += 1
        
        # Score: material is dominant (1000 per piece), then threats (50), then advancement (10)
        score = (my_count - opp_count) * 1000
        score += (opp_threats - my_threats) * 50
        score += advancement * 10
        return score
    
    best_action = None
    best_score = -float('inf')
    
    for action, new_board in actions_to_consider:
        score = evaluate(new_board)
        if score > best_score:
            best_score = score
            best_action = action
    
    return best_action
