
import numpy as np

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)  # Sort dice to easily pick higher/lower

    def find_moves(order):
        moves = []
        d1, d2 = dice[0], dice[1] if len(dice) > 1 else dice[0]
        
        if order == 'L':
            d1, d2 = d2, d1 if len(dice) > 1 else d1

        def is_legal(start_point, die_roll):
            if my_bar > 0 and start_point != 'B':
                return False
            
            if start_point == 'B':
                target_point = 24 - die_roll
            else:
                target_point = int(start_point[1:]) - die_roll
            
            if target_point < 0:
                # Bearing off
                home_board = all(my_pts[i] == 0 for i in range(6, 24)) and my_bar == 0
                if not home_board:
                    return False
                else:
                    return True #legal move for bearing off
            
            if opp_pts[target_point] >= 2:
                return False
            return True

        def get_target_point(start_point, die_roll):
             if start_point == 'B':
                return 24 - die_roll
             else:
                 return int(start_point[1:]) - die_roll
        
        def generate_moves():
            for start1 in ['B'] + [f'A{i}' for i in range(24) if my_pts[i] > 0] + ['P']:
                if start1 == 'P': #pass is always legal if all other moves are illegal
                    if len(dice)==1:
                       yield ('H:P,P' if order == 'H' else 'L:P,P')
                    else:
                      for start2 in ['P']:
                        yield ('H:P,P' if order == 'H' else 'L:P,P')

                    return
                if start1 != 'P' and not is_legal(start1, d1):
                    continue
                
                for start2 in ['B'] + [f'A{i}' for i in range(24) if my_pts[i] > 0] + ['P']:
                    if start2 == 'P' and len(dice) ==1:
                      continue
                    if start2 != 'P' and not is_legal(start2, d2):
                        continue
                    
                    if start1 != 'P' or start2 != 'P':
                        yield (f'H:{start1},{start2}' if order == 'H' else f'L:{start1},{start2}')
                        
        moves = list(generate_moves())
        return moves

    possible_moves_h = find_moves('H')
    possible_moves_l = find_moves('L')

    if possible_moves_h:
      return possible_moves_h[0]  # Return the first legal move found with H order
    elif possible_moves_l:
      return possible_moves_l[0]  # Return the first legal move found with L order
    else:
      return 'H:P,P'  # Fallback: no legal moves
