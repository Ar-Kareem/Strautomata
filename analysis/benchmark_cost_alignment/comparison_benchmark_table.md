# Comparison benchmark table

Union of benchmarks on the non-saturated Pareto frontier in either panel of the all-model or top-10 view. Membership uses saved point estimates and all eligible costs, before visual axis clipping.

| ID | Benchmark | Saturation Resistant | Requires Reprompting | All Pareto ($/unit) | All Pareto (Total $) | K=10 Pareto ($/unit) | K=10 Pareto (Total $) |
|---:|---|---|---|:---:|:---:|:---:|:---:|
| 11 | AA-Omniscience | 🔴 No (Individual) | No | ✓ | ✗ | ✓ | ✗ |
| 12 | SciCode (AA) | 🔴 No (Individual) | No | ✓ | ✗ | ✗ | ✗ |
| 20 | BugHunt | 🔴 No (Individual) | No | ✗ | ✗ | ✗ | ✓ |
| 21 | FrontierCode | 🔴 No (Individual) | No | ✗ | ✗ | ✓ | ✓ |
| 30 | SimpleBench | 🔴 No (Individual) | No | ✗ | ✓ | ✗ | ✓ |
| 44 | SREBench (Vals) | 🔴 No (Individual) | No | ✓ | ✓ | ✓ | ✓ |
| 24 | Lech Debate | 🟢 Yes (Arena) | Yes | ✓ | ✗ | ✓ | ✗ |
| 22 | **Strautomata** | 🟢 Yes (Arena) | No | ✓ | ✓ | ✓ | ✓ |

SREBench has nine shared models, so its top-10 view uses all nine. “Top 10” selects each benchmark’s highest-consensus available shared models; cohorts can differ. Costs combine Astra and Fable 5.1.

Saturation Resistant denotes opponent-relative evaluation, assuming non-solved games and informative opponent/judge comparisons. No (Individual) denotes no documented participant-adaptive difficulty mechanism in the evaluated version; it does not mean the benchmark is already saturated. See comparison_benchmark_saturation_audit.md.

Requires Reprompting asks whether evaluating a new entrant requires fresh inference from previously evaluated participant models. Lech Debate requires selected existing opponents to generate responses in new interactive debates; it does not require every previous model to be called. Fixed individual evaluations can retain previous participants’ scores. Strautomata reuses stored automata without reprompting their originating models. No does not exclude prompting the new entrant, using a separate LLM grader, or rerunning models after a benchmark revision.
