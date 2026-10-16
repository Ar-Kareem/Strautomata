
import itertools

def policy(state: list[list[object]], role: str) -> str:
    # Define board boundaries based on game observation
    letters = 'abcdefghi'
    numbers = '123456789'
    
    occupied = set()
    for fact in state:
        if fact[0] == "cell":
            occupied.add((fact[1], fact[2]))
            
    # Find all empty cells
    possible_moves = []
    for l in letters:
        for n in numbers:
            if (l, n) not in occupied:
                possible_moves.append(f"place({l},{n})")
    
    # Simple strategy: prioritize based on heuristic if possible, 
    # but always return a legal move. 
    # We choose the first available move as a fallback which is legal
    # because the game engine ensures control and legality.
    if not possible_moves:
        return ""
    
    # Try to pick a move that adds to existing counts (very simple lookahead)
    # For now, return the lexicographically first available move
    # The GameMaster handles the legality of the move.
    return possible_moves[0]

