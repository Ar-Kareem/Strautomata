
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Initialize memory if empty
    if not memory:
        memory = {
            'move_count': 0,
            'my_stones': set(),
            'opponent_stones': set(),
            'board': np.zeros((19, 19), dtype=int),
            'last_move': None,
            'influence_map': np.zeros((19, 19), dtype=float),
            'territory_map': np.zeros((19, 19), dtype=float),
        }

    # Update memory
    memory['move_count'] += 1
    memory['my_stones'] = set(me)
    memory['opponent_stones'] = set(opponent)
    memory['board'] = np.zeros((19, 19), dtype=int)
    for r, c in me:
        memory['board'][r-1, c-1] = 1
    for r, c in opponent:
        memory['board'][r-1, c-1] = -1

    # --- Opening Phase (first 50 moves) ---
    if memory['move_count'] <= 50:
        # 3-4 point opening
        if memory['move_count'] == 1:
            return ((13, 13), memory)  # Center
        elif memory['move_count'] == 2:
            return ((13, 14), memory)  # 3-4 point
        elif memory['move_count'] == 3:
            return ((14, 13), memory)  # 4-4 point
        elif memory['move_count'] == 4:
            return ((13, 13), memory)  # 3-3 point
        else:
            # Simple influence-based move selection
            influence = np.zeros((19, 19))
            for r, c in me:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = r + dr, c + dc
                        if 1 <= nr <= 19 and 1 <= nc <= 19:
                            influence[nr-1, nc-1] += 1
            for r, c in opponent:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = r + dr, c + dc
                        if 1 <= nr <= 19 and 1 <= nc <= 19:
                            influence[nr-1, nc-1] -= 1
            influence = np.maximum(influence, 0)
            max_influence = np.max(influence)
            candidates = np.argwhere(influence == max_influence)
            if len(candidates) > 0:
                r, c = candidates[0]
                return ((r+1, c+1), memory)
            else:
                return ((13, 13), memory)  # Fallback to center

    # --- Middle Game (50-150 moves) ---
    elif 50 < memory['move_count'] <= 150:
        # Territory-first approach
        territory_map = np.zeros((19, 19))
        for r, c in me:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 19 and 1 <= nc <= 19:
                        territory_map[nr-1, nc-1] += 1
        for r, c in opponent:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 19 and 1 <= nc <= 19:
                        territory_map[nr-1, nc-1] -= 1
        territory_map = np.maximum(territory_map, 0)

        # Liberty reduction
        liberties = defaultdict(int)
        for r, c in opponent:
            liberties[(r, c)] = 0
        for r, c in opponent:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 19 and 1 <= nc <= 19:
                        if (nr, nc) not in opponent and (nr, nc) not in me:
                            liberties[(r, c)] += 1
        liberty_reduction = np.zeros((19, 19))
        for (r, c), lib in liberties.items():
            liberty_reduction[r-1, c-1] = lib

        # Combine territory and liberty reduction
        score = territory_map + liberty_reduction
        max_score = np.max(score)
        candidates = np.argwhere(score == max_score)
        if len(candidates) > 0:
            r, c = candidates[0]
            return ((r+1, c+1), memory)
        else:
            return ((0, 0), memory)  # Pass if no good move

    # --- Endgame (150+ moves) ---
    else:
        # Secure territory and avoid unnecessary fights
        empty_cells = []
        for r in range(1, 20):
            for c in range(1, 20):
                if (r, c) not in me and (r, c) not in opponent:
                    empty_cells.append((r, c))

        # Prioritize filling eyes
        eye_candidates = []
        for (r, c) in empty_cells:
            is_eye = True
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in opponent:
                        is_eye = False
                        break
                if not is_eye:
                    break
            if is_eye:
                eye_candidates.append((r, c))

        if eye_candidates:
            return (eye_candidates[0], memory)

        # Fallback: pass
        return ((0, 0), memory)
