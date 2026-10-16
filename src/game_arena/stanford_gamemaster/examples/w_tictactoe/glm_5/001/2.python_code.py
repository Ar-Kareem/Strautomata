
def policy(state: list[list[object]], role: str) -> str:
    """
    Optimal Tic-Tac-Toe policy following strategic priorities:
    Win > Block > Fork > Block Fork > Center > Opposite Corner > Corner > Edge
    """
    # Parse the board state from propositions
    board = {}
    for prop in state:
        if prop[0] == "cell":
            row, col, val = prop[1], prop[2], prop[3]
            board[(row, col)] = val
    
    opponent = "o" if role == "x" else "x"
    
    # All possible winning lines (rows, columns, diagonals)
    lines = [
        [("1", "1"), ("1", "2"), ("1", "3")],  # Row 1
        [("2", "1"), ("2", "2"), ("2", "3")],  # Row 2
        [("3", "1"), ("3", "2"), ("3", "3")],  # Row 3
        [("1", "1"), ("2", "1"), ("3", "1")],  # Column 1
        [("1", "2"), ("2", "2"), ("3", "2")],  # Column 2
        [("1", "3"), ("2", "3"), ("3", "3")],  # Column 3
        [("1", "1"), ("2", "2"), ("3", "3")],  # Main diagonal
        [("1", "3"), ("2", "2"), ("3", "1")],  # Anti-diagonal
    ]
    
    def find_winning_move(player):
        """Find a cell that would complete a winning line."""
        for line in lines:
            player_count = sum(1 for pos in line if board.get(pos) == player)
            blank_positions = [pos for pos in line if board.get(pos) == "b"]
            if player_count == 2 and len(blank_positions) == 1:
                return blank_positions[0]
        return None
    
    def find_fork_move(player):
        """Find a move that creates two winning threats simultaneously."""
        for r in ["1", "2", "3"]:
            for c in ["1", "2", "3"]:
                if board.get((r, c)) == "b":
                    threats = 0
                    for line in lines:
                        if (r, c) in line:
                            player_count = sum(1 for pos in line if board.get(pos) == player)
                            blank_count = sum(1 for pos in line if board.get(pos) == "b")
                            # After placing here, this line becomes a threat
                            if player_count == 1 and blank_count == 2:
                                threats += 1
                    if threats >= 2:
                        return (r, c)
        return None
    
    # Priority 1: Win if possible
    move = find_winning_move(role)
    if move:
        return f"mark({move[0]},{move[1]})"
    
    # Priority 2: Block opponent's winning move
    move = find_winning_move(opponent)
    if move:
        return f"mark({move[0]},{move[1]})"
    
    # Priority 3: Create a fork (two winning threats)
    move = find_fork_move(role)
    if move:
        return f"mark({move[0]},{move[1]})"
    
    # Priority 4: Block opponent's fork
    move = find_fork_move(opponent)
    if move:
        return f"mark({move[0]},{move[1]})"
    
    # Priority 5: Take center if available
    if board.get(("2", "2")) == "b":
        return "mark(2,2)"
    
    # Priority 6: Take opposite corner when opponent has a corner
    opposite = {("1", "1"): ("3", "3"), ("1", "3"): ("3", "1"),
                ("3", "1"): ("1", "3"), ("3", "3"): ("1", "1")}
    for corner, opp_corner in opposite.items():
        if board.get(corner) == opponent and board.get(opp_corner) == "b":
            return f"mark({opp_corner[0]},{opp_corner[1]})"
    
    # Priority 7: Take any available corner
    corners = [("1", "1"), ("1", "3"), ("3", "1"), ("3", "3")]
    for corner in corners:
        if board.get(corner) == "b":
            return f"mark({corner[0]},{corner[1]})"
    
    # Priority 8: Take any available edge
    edges = [("1", "2"), ("2", "1"), ("2", "3"), ("3", "2")]
    for edge in edges:
        if board.get(edge) == "b":
            return f"mark({edge[0]},{edge[1]})"
    
    # Fallback: return any empty cell
    for r in ["1", "2", "3"]:
        for c in ["1", "2", "3"]:
            if board.get((r, c)) == "b":
                return f"mark({r},{c})"
    
    return "mark(1,1)"  # Ultimate fallback (should never reach)
