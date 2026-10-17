
def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return the index (0..5) of a legal move for the current player.

    This simple policy selects the first non‑empty house.
    The game guarantees that at least one house contains seeds,
    so the returned index is always legal.
    """
    for i, seeds in enumerate(you[:6]):  # houses only, ignore the store at index 6
        if seeds > 0:
            return i
    # Should never reach here because a legal move is always available.
    raise ValueError("No legal moves available")
