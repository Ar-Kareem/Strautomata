
import random

def policy(state: list[list[object]], role: str) -> str:
    # Extract board state
    occupied = {}
    phase = "place"
    for fact in state:
        if fact[0] == "cellholds":
            # [quadrant, row, col, color]
            occupied[(int(fact[1]), int(fact[2]), int(fact[3]))] = fact[4]
        elif fact[0] == "phase":
            phase = fact[1]

    if phase == "place":
        # Strategy: Prefer valid moves, prioritize center/mid-spots
        for q in range(1, 5):
            for r in range(1, 4):
                for c in range(1, 4):
                    if (q, r, c) not in occupied:
                        return f"place({q},{r},{c})"
    
    else:  # rotate phase
        # Basic heuristic: rotate quadrant 1 clockwise, 
        # but cycle to prevent getting stuck in local patterns
        choices = ["clockwise", "counterclockwise"]
        q = random.randint(1, 4)
        rot = random.choice(choices)
        return f"rotate({q},{rot})"

    # Fallback to absolute basics if logic fails
    return "place(1,1,1)"
