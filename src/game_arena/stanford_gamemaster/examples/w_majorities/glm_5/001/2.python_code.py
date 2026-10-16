
import random

def policy(state: list[list[object]], role: str) -> str:
    opponent = "blue" if role == "red" else "red"
    
    occupied = set()
    line_counts = {}
    
    for fact in state:
        if fact[0] == "cell":
            _, letter, number, color = fact
            occupied.add((letter, number))
        elif fact[0] == "line_count":
            _, line_id, color, count = fact
            if line_id not in line_counts:
                line_counts[line_id] = {}
            line_counts[line_id][color] = int(count)
    
    valid_ranges = {
        'a': [5, 6, 7, 8, 9],
        'b': [4, 5, 6, 7, 9],
        'c': [3, 4, 5, 6, 7, 8, 9],
        'd': [2, 3, 4, 5, 7, 8, 9],
        'e': [1, 3, 5, 6, 7, 8, 9],
        'f': [1, 2, 3, 4, 6, 7, 8],
        'g': [1, 2, 3, 4, 5, 6, 7],
        'h': [1, 2, 3, 4, 6],
        'i': [1, 2, 3, 4, 5]
    }
    
    legal_moves = []
    for letter, numbers in valid_ranges.items():
        for number in numbers:
            cell = (letter, str(number))
            if cell not in occupied:
                legal_moves.append(cell)
    
    if not legal_moves:
        return "place(a,5)"
    
    def get_diagonal(letter, number):
        letter_idx = ord(letter) - ord('a')
        num = int(number)
        total = letter_idx + num
        if 5 <= total <= 9:
            return f"a{total}"
        elif 10 <= total <= 13:
            return f"{chr(ord('a') + total - 9)}9"
        return None
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for cell in legal_moves:
        letter, number = cell
        diag = get_diagonal(letter, number)
        
        score = 0
        for line_id in [letter, number] + ([diag] if diag else []):
            counts = line_counts.get(line_id, {})
            my_count = counts.get(role, 0)
            opp_count = counts.get(opponent, 0)
            
            diff = my_count - opp_count
            score += diff * 25
            
            if my_count >= 3 and opp_count == 0:
                score += 250
            elif my_count >= 2 and opp_count == 0:
                score += 100
            
            if opp_count >= 3 and my_count == 0:
                score += 200
            elif opp_count >= 2 and my_count == 0:
                score += 75
            
            if my_count >= 1:
                score += 20
        
        score += random.random() * 5
        
        if score > best_score:
            best_score = score
            best_move = cell
    
    letter, number = best_move
    return f"place({letter},{number})"
