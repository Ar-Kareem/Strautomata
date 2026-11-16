
import collections

def policy(state: list[list[object]], role: str) -> str:
    board = {}
    for prop in state:
        if prop[0] == "cell":
            board[(int(prop[1]), int(prop[2]))] = prop[3]

    def is_valid(r, c):
        return 1 <= r <= 5 and 1 <= c <= 5

    opponent = "black" if role == "red" else "red"
    
    # Identify moves
    jumps = []
    moves = []

    for (r, c), occupant in board.items():
        if occupant == role:
            # Possible move directions (including diagonals)
            # In Alquerque, pieces move to any adjacent empty spot connected by a line.
            # Grid connectivity is 1..5.
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    
                    nr, nc = r + dr, c + dc
                    if is_valid(nr, nc):
                        if board.get((nr, nc)) == "blank":
                            moves.append(f"move({r},{c},{nr},{nc})")
                        elif board.get((nr, nc)) == opponent:
                            # Check jump
                            jr, jc = nr + dr, nc + dc
                            if is_valid(jr, jc) and board.get((jr, jc)) == "blank":
                                jumps.append(f"jump({r},{c},{nr},{nc},{jr},{jc})")

    if jumps:
        return jumps[0]
    if moves:
        return moves[0]
    
    # Fallback to no-op or random if no moves, though legal move is required.
    return None
