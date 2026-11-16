import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'corewar'))

import random
import numpy as np
from tqdm import tqdm
from corewar_util import SimulationArgs, parse_warrior_from_file, run_multiple_rounds, run_single_round, MyMARS

simargs = SimulationArgs(rounds=50, cycles=80000)  # 
"""
5,160,97,65,204,253
"""

_, warrior1 = parse_warrior_from_file(simargs, "../human_warriors/imp.red")
_, warrior2 = parse_warrior_from_file(simargs, "../human_warriors/dwarf.red")
_, warrior3 = parse_warrior_from_file(simargs, "../human_warriors/burp.red")
_, warrior4 = parse_warrior_from_file(simargs, "../human_warriors/mice.red")
_, warrior5 = parse_warrior_from_file(simargs, "../human_warriors/rato.red")
warriors = [warrior1, warrior2, warrior3, warrior4, warrior5]
# battle_results = run_multiple_rounds(simargs, warriors, n_processes=24, timeout=100)
# print(battle_results['score'].mean(axis=-1))

for seed in tqdm(range(simargs.rounds)):
    print(f"Running round {seed}")
    random.seed(seed)
    simulation = MyMARS(warriors=warriors, minimum_separation=simargs.distance, max_processes=simargs.processes, randomize=True)
    score = np.zeros(len(warriors), dtype=float)
    alive_score = np.zeros(len(warriors), dtype=float)

    prev_nprocs = np.array([len(w.task_queue) for w in simulation.warriors], dtype=int)
    total_spawned_procs = np.zeros(len(simulation.warriors), dtype=int)

    # memory_coverage = [set(w.task_queue) for w in simulation.warriors]
    for t in tqdm(range(simargs.cycles)):
        simulation.step()

        nprocs = np.array([len(w.task_queue) for w in simulation.warriors], dtype=int)

        alive_flags = (nprocs>0).astype(int)
        n_alive = alive_flags.sum()
        if n_alive==0:
            break
        score += (alive_flags * (1./n_alive)) / simargs.cycles
        alive_score += alive_flags / simargs.cycles

        total_spawned_procs = total_spawned_procs + np.maximum(0, nprocs - prev_nprocs)
        prev_nprocs = nprocs

        # memory_coverage = [mc.union(set(w.task_queue)) for mc, w in zip(memory_coverage, simulation.warriors)]
    # memory_coverage = np.array([len(mc) for mc in memory_coverage], dtype=int)
    memory_coverage = np.array([cov.sum() for cov in simulation.warrior_cov.values()], dtype=int)
    score = score * len(warriors)
    outputs = dict(score=score, alive_score=alive_score, total_spawned_procs=total_spawned_procs, memory_coverage=memory_coverage)
    print(outputs)