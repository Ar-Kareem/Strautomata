
def policy(state, role):
    # Parse board
    board = {}
    for fact in state:
        if fact[0] == "cell":
            # fact: ["cell", x, y, val, color]
            board[(int(fact[1]), int(fact[2]))] = (int(fact[3]), fact[4])

    def can_capture(attacker_val, defender_val):
        # 1 eats 5, otherwise smaller/equal eats larger/equal doesn't apply?
        # Game rule: a number can "eat" any smaller or equal number, 
        # except that number 1 can eat 5 but 5 cannot eat 1.
        if attacker_val == 1 and defender_val == 5: return True
        if attacker_val == 5 and defender_val == 1: return False
        return attacker_val <= defender_val

    moves = []
    direction = 1 if role == "red" else -1
    
    for (x, y), (val, color) in board.items():
        if color == role:
            # Possible move offsets: forward, diagonal forward, diagonal backward
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    nx, ny = x + dx, y + dy
                    if 1 <= nx <= 5 and 1 <= ny <= 5:
                        # Capture rule: diagonally only
                        if (nx, ny) in board:
                            target_val, target_color = board[(nx, ny)]
                            if target_color != role and abs(dx) > 0 and abs(dy) > 0:
                                if can_capture(val, target_val):
                                    moves.append(f"move({x},{y},{nx},{ny})")
                        else:
                            # Empty square: orthogonally or diagonally forward
                            # Actually, rule says "forward", let's assume relative to role
                            # Red moves x+1, Green moves x-1
                            is_forward = (role == "red" and dx > 0) or (role == "green" and dx < 0)
                            if is_forward or (abs(dx) > 0 and abs(dy) > 0):
                                moves.append(f"move({x},{y},{nx},{ny})")

    # Greedy return
    return moves[0] if moves else ""
