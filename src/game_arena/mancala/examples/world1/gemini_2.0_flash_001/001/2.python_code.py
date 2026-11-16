
def policy(you: list[int], opponent: list[int]) -> int:
    """
    Prioritizes moves that result in an extra turn or a capture.
    If no such move exists, chooses the first available house with seeds.
    """
    for i in range(6):
        if you[i] > 0:
            seeds = you[i]
            current_pos = i
            board_size = 14 # 6 houses per side + 2 stores
            final_pos = (current_pos + seeds) % board_size
            
            if final_pos == 6: # Your store. extra turn!
                return i
                
    for i in range(6):
        if you[i] > 0:
            # Simulate the move
            seeds = you[i]
            temp_you = you[:] 
            temp_opponent = opponent[:]

            temp_you[i] = 0
            
            current_house = i
            seeds_to_distribute = seeds
            
            while seeds_to_distribute > 0:
                current_house = (current_house + 1) % 14
                
                if current_house == 6: # your store
                    temp_you[6] += 1
                elif current_house == 13: # opponent's store
                    pass 
                elif current_house < 6: # your houses
                    temp_you[current_house] += 1
                else:  # opponent houses: current_house = 7 to 12
                    temp_opponent[current_house - 7] += 1

                seeds_to_distribute -= 1
                        
            # check for a capture after the move
            final_house = current_house 
            if final_house < 6:  # check if the last seed landed on your house
                new_house_index = final_house
                seeded_house_value_before = you[new_house_index] 
                if seeded_house_value_before == 0 and (you[i]-seeds+ seeds) == you[i] :
                    capture_house = 5 - new_house_index
                    if opponent[capture_house] > 0:
                        return i
            
    # No special moves were found pick first empty house
    for i in range(6):
        if you[i] > 0:
            return i
    return -1  # Should never happen
