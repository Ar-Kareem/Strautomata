
def policy(state: list[list[object]], role: str) -> str:
    # Parse state
    cells = {}
    for fact in state:
        if fact[0] == "cell":
            row, col, color = int(fact[1]), int(fact[2]), fact[3]
            cells[(row, col)] = color
    
    # Determine piece color and opponent
    my_color = role
    opp_color = "black" if role == "red" else "red"
    
    # Find my pieces
    my_pieces = [(r, c) for (r, c), color in cells.items() if color == my_color]
    
    if not my_pieces:
        return "kerchunk"
    
    # Helper: check if position is valid
    def is_valid(r, c):
        return 1 <= r <= 4 and 1 <= c <= 4
    
    # Helper: get cell color
    def get_color(r, c):
        return cells.get((r, c), "blank")
    
    # Helper: determine forward direction
    def forward_direction():
        return 1 if my_color == "red" else -1
    
    # Generate all legal moves
    all_moves = []
    
    for pr, pc in my_pieces:
        fwd = forward_direction()
        
        # Try jumps (capture moves) - prioritize these
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                mr1, mc1 = pr + dr, pc + dc
                if not is_valid(mr1, mc1):
                    continue
                
                # Check if there's a same-color piece to jump over
                if get_color(mr1, mc1) != my_color:
                    continue
                
                # Try jumping over it
                mr2, mc2 = mr1 + dr, mc1 + dc
                if not is_valid(mr2, mc2):
                    continue
                
                # Landing spot must be empty or opponent piece
                landing_color = get_color(mr2, mc2)
                if landing_color == my_color:
                    continue
                
                # Check if we're capturing
                if landing_color == opp_color:
                    move_str = f"jump({pr},{pc},{mr1},{mc1},{mr2},{mc2})"
                    all_moves.append((move_str, 2, mr2))  # Priority 2, row bonus
                elif landing_color == "blank":
                    move_str = f"jump({pr},{pc},{mr1},{mc1},{mr2},{mc2})"
                    all_moves.append((move_str, 1, mr2))  # Priority 1, no capture
        
        # Try regular moves (one step)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                mr, mc = pr + dr, pc + dc
                if not is_valid(mr, mc):
                    continue
                
                target_color = get_color(mr, mc)
                
                # Can only move to empty cells
                if target_color != "blank":
                    continue
                
                move_str = f"move({pr},{pc},{mr},{mc})"
                # Bonus for moving forward
                forward_bonus = 1 if (my_color == "red" and mr > pr) or (my_color == "black" and mr < pr) else 0
                all_moves.append((move_str, forward_bonus, mr))
    
    # Sort by priority (descending), then by row position
    all_moves.sort(key=lambda x: (-x[1], -x[2] if my_color == "red" else x[2]))
    
    if all_moves:
        return all_moves[0][0]
    
    # Fallback
    return "kerchunk"
