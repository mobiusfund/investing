#### Live Mining

- This directory contains strategy files
- A valid strategy filename matches the corresponding miner's hotkey ss58 string
- A valid strategy is a single Python dict representing subnet allocations
- A valid strategy dict holds only int keys and float values
- Subnet 0 and nonexistent subnet allocations count as cash with 0% dividend
- The miner will automatically submit a strategy based on the timestamp

#### Sim Strat

- Quick start: `../bin/simst simst.csv`
- More info: `../bin/simst -h`
