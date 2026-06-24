# Graph Report - C:\Users\AMezi\Desktop\DistributionDataPrototype  (2026-06-23)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 28 nodes · 50 edges · 6 communities (5 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]

## God Nodes (most connected - your core abstractions)
1. `ask()` - 8 edges
2. `main()` - 7 edges
3. `seed()` - 7 edges
4. `main()` - 4 edges
5. `interactive_mode()` - 4 edges
6. `demo_mode()` - 4 edges
7. `build_system_prompt()` - 3 edges
8. `get_sql_from_claude()` - 3 edges
9. `build_accounts()` - 3 edges
10. `show_dirty_data()` - 2 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `build_system_prompt()`  [EXTRACTED]
  queryEngine.py → queryEngine.py  _Bridges community 5 → community 4_
- `ask()` --calls--> `get_sql_from_claude()`  [EXTRACTED]
  queryEngine.py → queryEngine.py  _Bridges community 3 → community 2_
- `interactive_mode()` --references--> `Anthropic`  [EXTRACTED]
  queryEngine.py →   _Bridges community 3 → community 4_
- `interactive_mode()` --calls--> `ask()`  [EXTRACTED]
  queryEngine.py → queryEngine.py  _Bridges community 2 → community 4_

## Import Cycles
- None detected.

## Communities (6 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.36
Nodes (9): build_accounts(), build_losses(), build_policies(), build_quotes(), build_submission_groups(), build_submissions(), make_dirty(), -generate fake insurance data for testing -includes intentional dirty data to p (+1 more)

### Community 1 - "Community 1"
Cohesion: 0.70
Nodes (4): clean_accounts(), clean_brokers(), main(), show_dirty_data()

### Community 2 - "Community 2"
Cohesion: 0.60
Nodes (4): ask(), format_results(), query_engine.py Plain English → SQL → Results using Claude API + your data dicti, run_sql()

### Community 3 - "Community 3"
Cohesion: 0.67
Nodes (3): Anthropic, demo_mode(), get_sql_from_claude()

### Community 4 - "Community 4"
Cohesion: 0.67
Nodes (3): interactive_mode(), load_data_dictionary(), main()

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_system_prompt()` connect `Community 5` to `Community 2`, `Community 4`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 4` to `Community 2`, `Community 3`, `Community 5`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **What connects `query_engine.py Plain English → SQL → Results using Claude API + your data dicti`, `Builds the system prompt by injecting:     1. Business glossary     2. Table des`, `-generate fake insurance data for testing -includes intentional dirty data to p` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._