
import random

def policy(state: list[list[object]], role: str) -> str:
    """
    Decide the next action for the given role in the parallelbuttonsandlights game.
    """
    # If we have already played this turn, we must tick.
    if any(fact[0] == "played" and fact[1] == role for fact in state):
        return "tick"

    # Determine opponent role.
    opponent = "right" if role == "left" else "left"

    # Try to read opponent's last pressed button from the state.
    # The fact may be ["p", opponent, button] (three elements) or just ["p", opponent].
    opponent_button = None
    for fact in state:
        if fact[0] == "p" and len(fact) >= 3 and fact[1] == opponent:
            opponent_button = fact[2]
            break

    # Choose a button: match opponent if we know it, otherwise pick uniformly at random.
    buttons = ["a", "b", "c"]
    if opponent_button and opponent_button in buttons:
        chosen = opponent_button
    else:
        chosen = random.choice(buttons)

    # Return the action in Stanford syntax, e.g. a(left)
    return f"{chosen}({role})"
