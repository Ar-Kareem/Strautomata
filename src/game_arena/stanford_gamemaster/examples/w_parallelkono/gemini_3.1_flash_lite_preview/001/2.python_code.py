
import random

def policy(state: list[list[object]], role: str) -> str:
    # Build board representation
    # The state inputs contain cells like ["cell", "a"|"b", row, col, color]
    # We mainly care about the "cell" facts
    board = {}
    for fact in state:
        if fact[0] == "cell":
            # fact format: ["cell", board_id, row, col, content]
            # Since both 'a' and 'b' boards exist, we track them separately
            board[(fact[1], int(fact[2]), int(fact[3]))] = fact[4]

    legal_actions = []

    # Logic to find possible moves/jumps based on known Kono patterns
    # A piece can move 1 step (up, down, left, right) if the target is blank
    # A piece can jump to capture if:
    # 1. Own piece exists at current pos
    # 2. Same-color piece exists at adjacent pos
    # 3. Destination is empty
    
    # Simple search for moves
    for (b_id, r, c), color in board.items():
        if color == role:
            # Directions
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 4 and 1 <= nc <= 4:
                    target = board.get((b_id, nr, nc))
                    if target == "blank":
                        legal_actions.append(f"move({b_id},{r},{c},{nr},{nc})")
                    elif target == role:
                        # Attempt jump
                        jr, jc = nr + dr, nc + dc
                        if 1 <= jr <= 4 and 1 <= jc <= 4:
                            if board.get((b_id, jr, jc)) == "blank":
                                legal_actions.append(f"jump({b_id},{r},{c},{nr},{nc},{jr},{jc})")

    if not legal_actions:
        return "tick"
    
    # Prioritize jumps over moves
    jumps = [a for a in legal_actions if a.startswith("jump")]
    if jumps:
        return random.choice(jumps)
        
    return random.choice(legal_actions)
