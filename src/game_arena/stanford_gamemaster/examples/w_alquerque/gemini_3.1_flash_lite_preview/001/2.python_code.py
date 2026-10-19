
def policy(state: list[list[object]], role: str) -> str:
    board = {}
    for fact in state:
        if fact[0] == "cell":
            board[(int(fact[1]), int(fact[2]))] = fact[3]
    
    opponent = "black" if role == "red" else "red"
    
    # Possible directions: orthagonal and diagonal
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    # Check for Jumps first (Priority)
    for r in range(1, 6):
        for c in range(1, 6):
            if board.get((r, c)) == role:
                for dr, dc in directions:
                    mid_r, mid_c = r + dr, c + dc
                    end_r, end_c = r + 2 * dr, c + 2 * dc
                    if 1 <= end_r <= 5 and 1 <= end_c <= 5:
                        if board.get((mid_r, mid_c)) == opponent and board.get((end_r, end_c)) == "blank":
                            return f"jump({r},{c},{mid_r},{mid_c},{end_r},{end_c})"
    
    # If no jumps, check for Moves
    for r in range(1, 6):
        for c in range(1, 6):
            if board.get((r, c)) == role:
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 5 and 1 <= nc <= 5:
                        if board.get((nr, nc)) == "blank":
                            return f"move({r},{c},{nr},{nc})"
    
    return ""
