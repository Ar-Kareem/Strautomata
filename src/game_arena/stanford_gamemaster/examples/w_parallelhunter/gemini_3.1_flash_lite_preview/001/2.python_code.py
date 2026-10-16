
def policy(state: list[list[object]], role: str) -> str:
    # Identify the current position of our knight
    knight_pos = None
    cells = {}
    for fact in state:
        if fact[0] == "cell":
            # Fact format: ["cell", owner, x, y, type]
            # We only care about our own pieces/board
            if fact[1] == role:
                cells[(int(fact[2]), int(fact[3]))] = fact[4]
                if fact[4] == "knight":
                    knight_pos = (int(fact[2]), int(fact[3]))

    if not knight_pos:
        return "tick"

    kx, ky = knight_pos

    # Standard Knight moves
    moves = [
        (kx + 1, ky + 2), (kx + 1, ky - 2),
        (kx - 1, ky + 2), (kx - 1, ky - 2),
        (kx + 2, ky + 1), (kx + 2, ky - 1),
        (kx - 2, ky + 1), (kx - 2, ky - 1)
    ]

    # Find a move that lands on a pawn
    for (nx, ny) in moves:
        if (nx, ny) in cells and cells[(nx, ny)] == "pawn":
            return f"move({role},{kx},{ky},{nx},{ny})"

    # If no capture available, try to move to a random legal square 
    # Or just return 'tick' if no immediate capture is found
    # Looking at game logs, 'tick' is a common fallback
    return "tick"
