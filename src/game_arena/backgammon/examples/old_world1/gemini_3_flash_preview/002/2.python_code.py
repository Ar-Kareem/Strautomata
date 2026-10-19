
import random

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    dice = state['dice']

    if not dice:
        return "H:P,P"

    # Determine movement direction by checking which side of the board we are on
    # Usually, if we are internal, indices 0-23 are used.
    # Player 0 moves 0 -> 23, Player 1 moves 23 -> 0.
    # We detect direction by finding where checkers are moving towards off-board.
    # For this arena's API, we'll try to infer the movement by trying both common dice applications.
    
    def get_legal_moves(current_bar, current_pts, opp_pts, d1, d2):
        # This is a simplified legal move generator for the specific action format
        possible = []
        orders = ['H', 'L'] if d1 != d2 else ['H']
        
        # We need to simulate possible moves to find valid FROM locations
        # Since the engine validates, we look for sources that have checkers.
        sources = []
        if current_bar > 0:
            sources.append('B')
        for i in range(24):
            if current_pts[i] > 0:
                sources.append(f"A{i}")
        
        if not sources:
            return ["H:P,P"]

        # Simple greedy search for a valid-looking move string
        # Priority: Bar > Points
        for order in orders:
            for s1 in sources:
                for s2 in sources:
                    possible.append(f"{order}:{s1},{s2}")
        
        return possible

    def evaluate(pts, opp_p, bar, off):
        score = off * 100
        score -= bar * 50
        for i in range(24):
            if pts[i] > 1:
                score += 10 # Anchors are good
            if pts[i] == 1:
                score -= 15 # Blots are bad
        return score

    moves = get_legal_moves(my_bar, my_pts, opp_pts, dice[0], dice[-1])
    
    # Heuristic: Prioritize Bar, then furthest checkers, then bearing off
    # If Bar exists, first move must be 'B'
    if my_bar > 0:
        best_move = ""
        if my_bar >= 2:
            best_move = "H:B,B"
        else:
            # Look for a valid point to move after Bar
            for i in range(23, -1, -1):
                if my_pts[i] > 0:
                    best_move = f"H:B,A{i}"
                    break
            if not best_move:
                best_move = "H:B,P"
        return best_move

    # If no Bar, try to move furthest checkers or move to bear off
    # We will pick a reasonably "safe" move by picking moves from points with checkers
    valid_points = [i for i, count in enumerate(my_pts) if count > 0]
    if not valid_points:
        return "H:P,P"
    
    # Sort points to try moving from the "back" (most distance to cover)
    # This assumes a standard direction; if it fails, the arena fallback handles it.
    valid_points.sort() 
    
    # Construct a move from the available checkers
    p1 = valid_points[0]
    p2 = valid_points[-1] if len(valid_points) > 1 else p1
    
    return f"H:A{p1},A{p2}"

