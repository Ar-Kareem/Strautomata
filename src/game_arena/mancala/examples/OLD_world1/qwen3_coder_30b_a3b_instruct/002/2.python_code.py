
import copy

def policy(you: list[int], opponent: list[int]) -> int:
    # Try all possible moves and evaluate them
    best_move = 0
    best_score = -float('inf')
    
    for i in range(6):
        if you[i] == 0:
            continue
            
        # Simulate the move
        new_you, new_opponent, extra_turn = simulate_move(you, opponent, i)
        
        # Evaluate the move
        score = evaluate_move(new_you, new_opponent, extra_turn)
        
        if score > best_score:
            best_score = score
            best_move = i
    
    return best_move

def simulate_move(you: list[int], opponent: list[int], move: int) -> tuple[list[int], list[int], bool]:
    # Make a copy of the current state
    new_you = you[:]
    new_opponent = opponent[:]
    
    # Get the number of seeds to distribute
    seeds = new_you[move]
    new_you[move] = 0
    
    # Distribute seeds in order
    pos = move + 1
    turn = 0  # 0 for you, 1 for opponent
    
    while seeds > 0:
        # Handle the position wraparound
        if turn == 0 and pos == 7:  # Reach your store
            new_you[6] += 1
            seeds -= 1
            if seeds == 0:
                break
            pos = 0
            continue
            
        if turn == 1 and pos == 6:  # Reach opponent's store (skip it)
            turn = 0
            pos = 0
            continue
            
        if turn == 0 and pos == 6:  # Reach your side
            new_you[pos] += 1
            seeds -= 1
            if seeds == 0:
                break
            pos = 0
            turn = 1
            continue
            
        if turn == 1 and pos == 6:  # Reach opponent's side
            new_opponent[pos] += 1
            seeds -= 1
            if seeds == 0:
                break
            pos = 0
            turn = 0
            continue
            
        if turn == 0:
            new_you[pos] += 1
            seeds -= 1
            if seeds == 0:
                break
            pos += 1
        else:
            new_opponent[pos] += 1
            seeds -= 1
            if seeds == 0:
                break
            pos += 1
            
        # Wraparound
        if turn == 0 and pos > 5:
            pos = 0
            turn = 1
        elif turn == 1 and pos > 5:
            return new_you, new_opponent, False
    
    # Check for extra turn
    extra_turn = False
    if pos == 6 and turn == 0:
        extra_turn = True
    
    # Check for capture
    if turn == 0 and pos < 6 and new_you[pos] == 1 and new_opponent[5 - pos] > 0:
        # Capture: move all seeds to your store
        new_you[6] += 1 + new_opponent[5 - pos]
        new_you[pos] = 0
        new_opponent[5 - pos] = 0
    
    return new_you, new_opponent, extra_turn

def evaluate_move(you: list[int], opponent: list[int], extra_turn: bool) -> int:
    # Simple heuristic evaluation
    score = 0
    
    # Prefer moves that give extra turns
    if extra_turn:
        score += 10
    
    # Prefer moves that result in captures
    # We'll just evaluate this based on increasing your store
    # A more complex evaluation would look at potential future captures
    score += you[6] - opponent[6]  # Store difference
    
    # Prefer moves that increase your own seeds in the long run
    # More seeds in your houses suggests better positions
    future_seeds = sum(you[:6])
    score += future_seeds * 0.5
    
    # Minimize seeds in opponent's houses
    score -= sum(opponent[:6]) * 0.5
    
    # Prefer keeping a number of seeds above zero in your houses
    # This prevents easily filled holes that opponent could exploit
    score += sum(1 for x in you[:6] if x > 0) * 2
    
    return score
