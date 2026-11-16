
def policy(state: list[list[object]], role: str) -> str:
    # Parse the state to build the board representation
    board = {}
    empty_cells = []
    
    for prop in state:
        if prop[0] == "cell":
            row, col, value = prop[1], prop[2], prop[3]
            board[(row, col)] = value
            if value == "b":
                empty_cells.append((row, col))
    
    # Determine opponent
    opponent = "o" if role == "x" else "x"
    
    # Define all winning lines (rows, columns, diagonals)
    winning_lines = [
        [("1", "1"), ("1", "2"), ("1", "3")],  # Row 1
        [("2", "1"), ("2", "2"), ("2", "3")],  # Row 2
        [("3", "1"), ("3", "2"), ("3", "3")],  # Row 3
        [("1", "1"), ("2", "1"), ("3", "1")],  # Col 1
        [("1", "2"), ("2", "2"), ("3", "2")],  # Col 2
        [("1", "3"), ("2", "3"), ("3", "3")],  # Col 3
        [("1", "1"), ("2", "2"), ("3", "3")],  # Diagonal \
        [("1", "3"), ("2", "2"), ("3", "1")],  # Diagonal /
    ]
    
    def count_in_line(line, player):
        """Count how many of a player's marks are in a line"""
        count = 0
        for pos in line:
            if board.get(pos) == player:
                count += 1
        return count
    
    def find_winning_move(player):
        """Find a move that would win for the given player"""
        for pos in empty_cells:
            for line in winning_lines:
                if pos in line:
                    my_count = count_in_line(line, player)
                    empty_in_line = sum(1 for p in line if board.get(p) == "b")
                    if my_count == 2 and empty_in_line == 1:
                        return pos
        return None
    
    def find_fork_move(player):
        """Find a move that creates two winning threats"""
        for pos in empty_cells:
            threats = 0
            for line in winning_lines:
                if pos in line:
                    my_count = count_in_line(line, player)
                    empty_in_line = sum(1 for p in line if board.get(p) == "b")
                    if my_count == 1 and empty_in_line == 2:
                        threats += 1
            if threats >= 2:
                return pos
        return None
    
    # Priority 1: Win immediately if possible
    win_move = find_winning_move(role)
    if win_move:
        return f"mark({win_move[0]},{win_move[1]})"
    
    # Priority 2: Block opponent's winning move
    block_move = find_winning_move(opponent)
    if block_move:
        return f"mark({block_move[0]},{block_move[1]})"
    
    # Priority 3: Create a fork (two winning threats)
    fork_move = find_fork_move(role)
    if fork_move:
        return f"mark({fork_move[0]},{fork_move[1]})"
    
    # Priority 4: Block opponent's fork
    opp_fork = find_fork_move(opponent)
    if opp_fork:
        return f"mark({opp_fork[0]},{opp_fork[1]})"
    
    # Priority 5: Take center if available
    if ("2", "2") in empty_cells:
        return "mark(2,2)"
    
    # Priority 6: Take a corner
    corners = [("1", "1"), ("1", "3"), ("3", "1"), ("3", "3")]
    for corner in corners:
        if corner in empty_cells:
            return f"mark({corner[0]},{corner[1]})"
    
    # Priority 7: Take an edge
    edges = [("1", "2"), ("2", "1"), ("2", "3"), ("3", "2")]
    for edge in edges:
        if edge in empty_cells:
            return f"mark({edge[0]},{edge[1]})"
    
    # Fallback: take any available cell
    if empty_cells:
        pos = empty_cells[0]
        return f"mark({pos[0]},{pos[1]})"
    
    return "mark(1,1)"
