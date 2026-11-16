
def policy(state: list[list[object]], role: str) -> str:
    import random

    # Parse board
    board = {}
    for fact in state:
        if fact[0] == "cell":
            board[(fact[1], int(fact[2]))] = fact[3]

    my_pieces = [pos for pos, color in board.items() if color == role]
    
    # Knight move offsets
    offsets = [
        (1, 2), (1, -2), (-1, 2), (-1, -2),
        (2, 1), (2, -1), (-2, 1), (-2, -1)
    ]

    def to_file_idx(f): return ord(f) - ord('a')
    def from_file_idx(i): return chr(i + ord('a'))

    valid_moves = []
    capture_moves = []

    for (f, r) in my_pieces:
        f_idx = to_file_idx(f)
        for df, dr in offsets:
            nf_idx, nr = f_idx + df, r + dr
            if 0 <= nf_idx < 8 and 1 <= nr <= 8:
                nf = from_file_idx(nf_idx)
                target = board.get((nf, nr))
                
                # Check occupancy
                if target is None:
                    valid_moves.append(f"move({f},{r},{nf},{nr})")
                elif target != role:
                    capture_moves.append(f"move({f},{r},{nf},{nr})")

    # Priority: 1. Capture, 2. Move
    if capture_moves:
        return random.choice(capture_moves)
    if valid_moves:
        return random.choice(valid_moves)

    # Fallback to a default move if no legal moves are found (though state logic should prevent this)
    return ""
