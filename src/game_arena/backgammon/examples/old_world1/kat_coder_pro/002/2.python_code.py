
import random
import math
from collections import defaultdict

def policy(state: dict) -> str:
    # Extract board state
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    # If no dice, return pass
    if not dice:
        return "H:P,P"
    
    # If opponent has won, return pass
    if opp_off >= 15:
        return "H:P,P"
    
    # If I have won, return pass
    if my_off >= 15:
        return "H:P,P"
    
    # Determine priority of moves
    # 1. Get checkers off the bar
    # 2. Hit opponent blots
    # 3. Move checkers forward
    # 4. Bear off checkers
    
    # If I have checkers on the bar, I must move them first
    if my_bar > 0:
        # Try to enter with each die
        for die in sorted(dice, reverse=True):  # Try higher die first
            target = 24 - die  # Target point for entering from bar
            if target >= 0 and target < 24:
                if opp_pts[target] < 2:  # Can enter
                    # Find a point to move to after entering
                    for i in range(24):
                        if i != target and my_pts[i] > 0:
                            # Check if we can move from i to i-die
                            target2 = i - die
                            if target2 >= 0 and opp_pts[target2] < 2:
                                # This is a valid move
                                if die == max(dice):
                                    return f"H:B,A{i}"
                                else:
                                    return f"L:B,A{i}"
        # If we get here, we couldn't move
        return "H:P,P"
    
    # If opponent has checkers on the bar, try to hit them
    if opp_bar > 0:
        for die in sorted(dice, reverse=True):
            target = die - 1  # Target point for hitting from bar
            if target >= 0 and target < 24:
                if my_pts[target] > 0 and opp_pts[target] == 1:
                    # We can hit
                    if die == max(dice):
                        return f"H:A{target},P"
                    else:
                        return f"L:A{target},P"
    
    # Try to make a move that hits an opponent blot
    for die in sorted(dice, reverse=True):
        for i in range(24):
            if my_pts[i] > 0:
                target = i - die
                if target >= 0 and target < 24:
                    if opp_pts[target] == 1:  # We can hit
                        # Find a second move
                        for j in range(24):
                            if j != i and my_pts[j] > 0:
                                target2 = j - (dice[0] if dice[1] == die else dice[1])
                                if target2 >= 0 and target2 < 24:
                                    if opp_pts[target2] < 2:
                                        if die == max(dice):
                                            return f"H:A{i},A{j}"
                                        else:
                                            return f"L:A{i},A{j}"
                        # If we get here, we couldn't find a second move
                        if die == max(dice):
                            return f"H:A{i},P"
                        else:
                            return f"L:A{i},P"
    
    # Try to move checkers forward
    # Prioritize moving checkers from the back
    for die in sorted(dice, reverse=True):
        for i in range(23, -1, -1):
            if my_pts[i] > 0:
                target = i - die
                if target >= 0 and target < 24:
                    if opp_pts[target] < 2:
                        # Find a second move
                        for j in range(23, -1, -1):
                            if j != i and my_pts[j] > 0:
                                target2 = j - (dice[0] if dice[1] == die else dice[1])
                                if target2 >= 0 and target2 < 24:
                                    if opp_pts[target2] < 2:
                                        if die == max(dice):
                                            return f"H:A{i},A{j}"
                                        else:
                                            return f"L:A{i},A{j}"
                        # If we get here, we couldn't find a second move
                        if die == max(dice):
                            return f"H:A{i},P"
                        else:
                            return f"L:A{i},P"
    
    # Try to bear off checkers
    if all(i < 6 for i, count in enumerate(my_pts) if count > 0):
        for die in sorted(dice, reverse=True):
            for i in range(5, -1, -1):
                if my_pts[i] > 0:
                    if i + 1 == die:  # Exact bear off
                        # Find a second move
                        for j in range(5, -1, -1):
                            if j != i and my_pts[j] > 0:
                                if j + 1 == (dice[0] if dice[1] == die else dice[1]):
                                    if die == max(dice):
                                        return f"H:A{i},A{j}"
                                    else:
                                        return f"L:A{i},A{j}"
                        # If we get here, we couldn't find a second move
                        if die == max(dice):
                            return f"H:A{i},P"
                        else:
                            return f"L:A{i},P"
                    elif i + 1 < die:  # Bear off using a higher die
                        # Find a second move
                        for j in range(5, -1, -1):
                            if j != i and my_pts[j] > 0:
                                if j + 1 == (dice[0] if dice[1] == die else dice[1]):
                                    if die == max(dice):
                                        return f"H:A{i},A{j}"
                                    else:
                                        return f"L:A{i},A{j}"
                        # If we get here, we couldn't find a second move
                        if die == max(dice):
                            return f"H:A{i},P"
                        else:
                            return f"L:A{i},P"
    
    # If we get here, we couldn't find a legal move
    return "H:P,P"
