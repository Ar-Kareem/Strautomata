
import random
import numpy as np

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)
    
    # Convert dice to higher and lower values, default to 0 if not set
    if len(dice) == 0:
        return "H:P,P"
    elif len(dice) == 1:
        high = dice[0]
        low = 0
    else:
        high = dice[0]
        low = dice[1]

    # Helper to determine valid moves
    def is_valid_point(point):
        if point < 0 or point >= 24:
            return False
        return my_pts[point] > 0

    # Helper to determine legal off moves
    def can_bear_off():
        # Check if all checkers are in home board (points 0-5)
        for i in range(6):
            if my_pts[i] > 0:
                # Check if they are on points that could be made
                # This is a simplification - just check if we have a point that can bear off with our roll
                pass
        # Simplified check: if we're not on bar, we can bear off
        return True  # We'll do a proper check later

    def is_bearing_off_possible():
        # All remaining checkers must be in home board
        # Points 0 to 5 (inner board)
        non_home_checkers = sum(my_pts[i] for i in range(6, 24))
        if non_home_checkers == 0:
            # Check if we can bear off
            # List checkers in inner board
            inner_board_checkers = sum(my_pts[i] for i in range(0, 6))
            return True
        return False

    # Function to determine if a point is in the home board for current player
    def is_home_board(point):
        return point >= 0 and point <= 5  # Home board for current player (0-5)

    def get_legal_moves():
        moves = []
        
        # If there are checkers on the bar, only bar moves can be considered
        if my_bar > 0:
            # Try to move checkers from the bar
            # For bar, can move from 23 down to 18 if 23 is empty or has 1 checker
            # Since there are 24 points, point 0 is the lowest (absolute index 0)
            # But as we're moving from 23 to 0 (away from opponent's home board)
            # and I am the player with points 0 and 23 as endpoints I move from 23 to 0
            # So when I have checkers on the bar I need to move them to 23 - die
            # But actually they can only go to points that are available
            # Let's simplify and consider we want to place each checker on a valid point (non-opponent 2+ checkers)
            # but puzzle the point not available is not making a legal move
            # Use a simple logic that for now tries to place from bar to legal spots
            # but there are many suitable ways for that
            
            # we try points in range 0 to 5 for the bar move (negative dice is not possible)  
            for die_val in dice:
                target_point = 23 - die_val
                if target_point >= 0:
                    if not (opp_pts[target_point] >= 2):  # Only place if not blocked
                        moves.append(["B", target_point])
                        # When placing a checker from the bar, no second move possible unless player chooses to
            return moves

        # Else not on bar, regular moves
        # At most 2 moves from 2 different points, one for each die
        # Generation of all legal moves based on available checkers and dice
        # Create list of move sets
        pts_with_checkers = []
        for point in range(24):
            if my_pts[point] > 0:
                pts_with_checkers.append(point)

        valid_moves = []
        
        # Go through all checker points and try all combinations 
        # We're short of generating all (safe) moves by proper sequential logic, but
        # For this attempt, let's just do a safer brute force.
        
        # Strategy 1: Try only legal moves that make sense
        # let's enumerate the uses:
        # one move only/pair of moves etc. check all possible valid combinations.
        # we want both dice played (if can)
        
        # Let's make this workable and lean
        
        # First, we derive board-based legality and pre-process the information
        # Slow but straightforward approach - attempts 1 or 2 moves
        # Limits exploration due to time constraints
        
        # When dice are equal, we play all 4 moves from same points 
        if high == low and high != 0:
            # plays 4 moves from same point
            for point in pts_with_checkers:
                if my_pts[point] >= 4:
                    valid_moves.append(
                        (["H", point, point, point, point])  # 4 moves, use high die 4 times
                    )
        else:
            # Prepare list of all valid moves for 1 or 2 plays
            points = []

            for point in pts_with_checkers:
                if my_pts[point] > 0:
                    points.append(point)
            
            # now in 2 moves when using two dice
            # i.e., from point1 (with die1) and from point2 (with die2)
            # Use the dice values for okay moves
            # Try all combinations
            
            for point1 in pts_with_checkers:
                # Try first move with high die
                dest1 = point1 - high
                # Valid destination? not out of bounds, not blocked
                # Note: move from point1 to dest1 (optional: doesn't go over board)
                if dest1 >= 0 and not (opp_pts[dest1] >= 2):
                    for point2 in pts_with_checkers:
                        if point1 == point2:
                            continue  # Don't move same point twice in case of double win
                        dest2 = point2 - low
                        # Destination valid for move 2 with low die
                        if dest2 >= 0 and not (opp_pts[dest2] >= 2):
                            valid_moves.append(["H", point1, point2])
            # Try invert for L option
            for point1 in pts_with_checkers:
                dest1 = point1 - low
                if dest1 >= 0 and not (opp_pts[dest1] >= 2):
                    for point2 in pts_with_checkers:
                        if point1 == point2:
                            continue
                        dest2 = point2 - high
                        if dest2 >= 0 and not (opp_pts[dest2] >= 2):
                            valid_moves.append(["L", point1, point2])
            
        # Lastly if no valid moves
        if not valid_moves:
            return [["H", "P", "P"]]

        # Return a single good move
        # Weighted towards ones with better look ahead
        scores = []
        for move in valid_moves:
            score = evaluate_move(move, my_pts, opp_pts, my_off)
            scores.append(score)

        best_move = valid_moves[np.argmax(scores)]
        return best_move

    # Evaluation scoring for potential moves
    def evaluate_move(move, my_board, opp_board, my_off):
        # Simple heuristic to guess good move
        # Priority: 1. bear off, 2. reduce vulnerability, 3. secure position
        # Evaluation based on built up safety / avoided hits, etc.
        score = 0
        
        # If one of moves is empty (i.e. pass)
        if move[1] == 'P':
            return 0
        
        # Only evaluate actual number of actions
        if len(move) > 2 and not isinstance(move[2], str):
            # Has second move
            if move[0] == 'H': 
                # High die played first
                score += 10
            elif move[0] == 'L':
                score += 5
        else:
            score += 5
            
        # Bonus for bearing off when possible (simplified check)
        # If we are home board and are moving, make sure not deadly
        return score

    # Find legal move and return it in string format
    legal_moves = get_legal_moves()
    
    # Time to return the move according to specified format
    if len(legal_moves) == 0:
        return "H:P,P"
    else:
        move = legal_moves[0]
        if move[1] == "P":
            return "H:P,P"
        else:
            if len(move) > 2:
                order = move[0]
                from1 = move[1] if isinstance(move[1], str) else "A" + str(move[1])
                from2 = move[2] if isinstance(move[2], str) else "A" + str(move[2])
                
                if from1 == "B" or from2 == "B":
                    # Use 'B' if it's a bar move
                    pass
                if from1[0] != "A" and from1 != "B":
                    from1 = "A" + str(from1)
                if from2[0] != "A" and from2 != "B":
                    from2 = "A" + str(from2)
                return order + ":" + from1 + "," + from2
            else:
                # For terminal cases
                return "H:P,P"

    # Default fallback
    return "H:P,P"
