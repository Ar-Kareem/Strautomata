import random

def policy(state: list[list[object]], role: str) -> str:
    # Identify positions of pieces
    pieces = []
    board = {}
    for fact in state:
        if fact[0] == 'location':
            _, c, r, color = fact
            board[(int(c), int(r))] = color
            if color == role:
                pieces.append((int(c), int(r)))
    
    # Helper to handle barrel board wrapping
    def wrap(val):
        return (val - 1) % 8 + 1

    legal_actions = []
    
    # Simple logic to find moves and jumps
    # Since we aren't given legal actions, we simulate basic checkers moves
    # Red moves typically toward lower row numbers, Black toward higher
    directions = [(1, 1), (-1, 1), (1, -1), (-1, -1)]
    
    for c, r in pieces:
        for dc, dr in directions:
            target_c, target_r = wrap(c + dc), wrap(r + dr)
            # Check for a move
            if (target_c, target_r) not in board:
                legal_actions.append(f"move({c},{r},{target_c},{target_r})")
            # Check for a jump
            else:
                if board[(target_c, target_r)] != role:
                    jump_c, jump_r = wrap(c + 2*dc), wrap(r + 2*dr)
                    if (jump_c, jump_r) not in board:
                        legal_actions.append(f"jump({c},{r},{target_c},{target_r},{jump_c},{jump_r})")

    # If no moves/jumps are available, we must return noop
    if not legal_actions:
        return "noop"
    
    # Prioritize jumps over moves
    jumps = [a for a in legal_actions if a.startswith("jump")]
    if jumps:
        return random.choice(jumps)
        
    return random.choice(legal_actions)
