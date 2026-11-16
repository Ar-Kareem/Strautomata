```python
def apply_move(player, opponent, pit):
    new_player = player[:]
    new_opponent = opponent[:]
    seeds = new_player[pit]
    new_player[pit] = 0
    start_slot = pit + 1
    for step in range(seeds):
        slot = (start_slot + step) %