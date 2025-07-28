#### Live Mining

- This directory contains strategy files
- Empty files (size 0) are ignored
- A valid strategy filename matches the corresponding miner's hotkey ss58 string
- A valid strategy is a single Python dict representing asset allocations
- A special key `'_'` denotes the asset class with default value `0` if missing
- `'_':0` denotes Tao/Alpha where all other keys should be integers
- Subnet 0 and nonexistent subnet allocations count as Tao/cash with 0% dividend
- `'_':1` denotes US stocks where all other keys should be case-sensitive strings
- A special key `''` (empty string) and unsupported ticker symbols count as USD/cash
- Shorting is supported with negative allocation values for US stocks
- The miner will automatically submit a strategy based on the file timestamp

#### Sim Strat

- Quick start: \
`../bin/simst alpha.csv` \
`../bin/simst stock.csv` \
`../bin/simst simst.csv`
- More info: \
`../bin/simst -h`
