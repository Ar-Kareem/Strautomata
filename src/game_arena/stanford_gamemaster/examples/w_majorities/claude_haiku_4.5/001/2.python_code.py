
def policy(state: list[list[object]], role: str) -> str:
    # Parse the state
    cells = {}
    line_counts = {}
    num_lines = {}
    
    for fact in state:
        if fact[0] == "cell":
            letter, number, player = fact[1], fact[2], fact[3]
            cells[(letter, number)] = player
        elif fact[0] == "line_count":
            line_id, player, count = fact[1], fact[2], int(fact[3])
            line_counts[(line_id, player)] = count
        elif fact[0] == "num_letter_lines":
            player = fact[1]
            num_lines[("letter", player)] = int(fact[2])
        elif fact[0] == "num_number_lines":
            player = fact[1]
            num_lines[("number", player)] = int(fact[2])
        elif fact[0] == "num_vertical_lines":
            player = fact[1]
            num_lines[("vertical", player)] = int(fact[2])
    
    opponent = "blue" if role == "red" else "red"
    
    # Generate valid moves (all empty cells on the board)
    letters = "abcdefghi"
    numbers = "123456789"
    
    valid_moves = []
    for letter in letters:
        for number in numbers:
            if (letter, number) not in cells:
                valid_moves.append((letter, number))
    
    if not valid_moves:
        return f"place({letters[0]},{numbers[0]})"
    
    best_score = -float('inf')
    best_move = valid_moves[0]
    
    for letter, number in valid_moves:
        score = 0
        
        # Get the three line identifiers for this cell
        line_ids = [letter, number, letter + number]
        
        for line_id in line_ids:
            my_count = line_counts.get((line_id, role), 0)
            opp_count = line_counts.get((line_id, opponent), 0)
            
            # Bonus for extending my lines
            score += my_count * 2
            
            # Penalty for blocking opponent
            score -= opp_count * 1.5
            
            # Big bonus if this completes a majority in a line
            if my_count + 1 >= 3 and opp_count == 0:
                score += 10
            
            # Penalty for letting opponent complete
            if opp_count + 1 >= 3 and my_count == 0:
                score -= 8
        
        # Bonus for moves that help us win directions
        my_letter_lines = num_lines.get(("letter", role), 0)
        my_number_lines = num_lines.get(("number", role), 0)
        my_vertical_lines = num_lines.get(("vertical", role), 0)
        
        opp_letter_lines = num_lines.get(("letter", opponent), 0)
        opp_number_lines = num_lines.get(("number", opponent), 0)
        opp_vertical_lines = num_lines.get(("vertical", opponent), 0)
        
        # If we're close to winning a direction, boost moves in that direction's lines
        if my_letter_lines >= 4:
            if line_counts.get((letter, role), 0) + 1 >= 3:
                score += 20
        if my_number_lines >= 4:
            if line_counts.get((number, role), 0) + 1 >= 3:
                score += 20
        if my_vertical_lines >= 4:
            if line_counts.get((letter + number, role), 0) + 1 >= 3:
                score += 20
        
        # Prefer central moves early
        center_bonus = 0
        if letter in "cdefg" and number in "456":
            center_bonus = 1
        score += center_bonus
        
        if score > best_score:
            best_score = score
            best_move = (letter, number)
    
    return f"place({best_move[0]},{best_move[1]})"
