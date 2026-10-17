
import random

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Selects a legal move for Kalah.

    Args:
        you: Your houses and store.
        opponent: Opponent's houses and store.

    Returns:
        A legal move (0-5).
    """

    def simulate_move(you: list[int], opponent: list[int], move: int) -> tuple[list[int], list[int], bool]:
        """Simulates a move and returns the updated boards and whether another move is granted."""
        you = you[:]
        opponent = opponent[:]
        seeds = you[move]
        you[move] = 0
        current_index = move + 1
        board = 0  # 0 for you, 1 for opponent

        while seeds > 0:
            if board == 0:
                if current_index == 6:
                    you[6] += 1
                    seeds -= 1
                    if seeds == 0:
                        return you, opponent, True  # Extra move
                else:
                    you[current_index] += 1
                    seeds -= 1
            else:
                if current_index == 6:
                    current_index = 0
                    board = 0
                    continue
                else:
                    opponent[current_index] += 1
                    seeds -= 1

            current_index += 1

            if board == 0 and current_index > 6:
                current_index = 0
                board = 1
            elif board == 1 and current_index > 6:
                current_index = 0
                board = 0

        # Check for capture
        if board == 0 and current_index > 0 and current_index <= 6:
            landed_index = current_index -1
            if landed_index < 6 and you[landed_index] == 1 and opponent[5 - landed_index] > 0:
                you[6] += 1 + opponent[5 - landed_index]
                you[landed_index] = 0
                opponent[5 - landed_index] = 0

        return you, opponent, False

    # Prioritize captures and extra moves
    for move in range(6):
        if you[move] > 0:
            temp_you, temp_opponent, extra_move = simulate_move(you, opponent, move)

            if extra_move:
                return move

            # Simulate and check for captures
            seeds = you[move]
            current_index = move + 1

            board = 0
            landed_index = -1
            while seeds > 0:
                if board == 0:
                    if current_index == 6:
                         seeds -= 1
                         if seeds == 0:
                             break # landed in store, not a capture
                    else:
                        seeds -= 1
                else:
                   if current_index == 6:
                       current_index = 0
                       board = 0
                       continue
                   else:
                       seeds -=1

                current_index += 1

                if board == 0 and current_index > 6:
                    current_index = 0
                    board = 1
                elif board == 1 and current_index > 6:
                    current_index = 0
                    board = 0

            if board == 0 and current_index > 0 and current_index <= 6:
                landed_index = current_index - 1
                temp_you = you[:] #need to reinitialize since previous extra move may have mutated
                temp_opponent = opponent[:] #need to reinitialize since previous extra move may have mutated
                temp_you[move] = 0
                new_landed_index = move

                seeds = you[move]
                current_index = move + 1
                board = 0

                while seeds > 0:
                   if board == 0:
                       if current_index == 6:
                           seeds -= 1
                       else:
                           temp_you[current_index] += 1
                           seeds -= 1
                   else:
                       if current_index == 6:
                            current_index = 0
                            board = 0
                            continue
                       else:
                           temp_opponent[current_index] += 1
                           seeds -= 1

                   current_index += 1
                   if board == 0 and current_index > 6:
                       current_index = 0
                       board = 1
                   elif board == 1 and current_index > 6:
                       current_index = 0
                       board = 0
                landed_index = current_index - 1
                if board == 0 and current_index > 0 and current_index <= 6:
                    landed_index = current_index - 1

                    if temp_you[landed_index] - you[landed_index] == 1 and temp_you[landed_index] == 1 and opponent[5 - landed_index] > 0:
                        return move


    # If no captures are available, pick the first legal move
    for move in range(6):
        if you[move] > 0:
            return move
    return -1  # Should never happen because policy isn't called when no legal moves exist.
