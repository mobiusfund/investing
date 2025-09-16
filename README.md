<div align="center">

# Investing - Decentralized AUM
[Dashboard](https://db.investing88.ai) • [Discord](https://discord.com/channels/799672011265015819/1358854051634221328) • [X](https://x.com/Investing88ai)
</div>

---
- [Intro](#Intro)
- [Roadmap](#Roadmap)
- [Installation](#installation)
- [Mining](#Mining)
- [Scoring](#Scoring)
- [Disclaimer](#Disclaimer)
- [License](#license)

## Intro

Envisioned as the world's first Decentralized AUM, leveraging a worldwide network of both human and artificial intelligence, Investing is the Bittensor subnet with the mission to provide investment services for both retail and institutional investors.

The initial phase at launch is optimizing staking strategies in the Tao/Alpha ecosystem, by the community and for the community.

The resulting business model and innovations will apply across crypto and other more traditional markets, extract alpha from these markets, minimize risks, and deliver optimized portfolio returns to a broad range of investors in the global [145 trillion dollar](https://www.pwc.com/ng/en/press-room/global-assets-under-management-set-to-rise.html) asset management industry.

## Roadmap

Phase I - Live at launch: Staking strategies ✓ 04/25 \
Phase II - 3 to 6 months: Portfolio management with US stocks ✓ 07/25 \
Phase III - 6 months to 1 year: Multi-class asset management in global markets \
Phase IV - 1 year and beyond: Fully realized, Decentralized AUM \
In parallel - Ongoing: A frontend AUM app serving real-world investors

## Installation

Please avoid using the root account, and make sure Python3 is available as command `python` under a regular user account. Ubuntu 22.04 is the only officially supported OS, although many other OSes can also work with minimum tweaks, including macOS. For first-time miners, please follow the [Bittensor document](https://docs.learnbittensor.org/miners/) to register a hotkey.

#### Setup

```bash
sudo apt update
sudo apt install npm -y
sudo npm install pm2 -g
git clone https://github.com/mobiusfund/investing
cd investing
# optional
python -m venv .venv
. .venv/bin/activate
#
python -m pip install -e .
```

#### Miner

```bash
# optional
. .venv/bin/activate
#
pm2 start neurons/miner.py \
    --name investing-miner -- \
    --wallet.name {coldkey} \
    --wallet.hotkey {hotkey} \
    --netuid 88 #339 --subtensor.network test
```

#### Validator

```bash
# optional
. .venv/bin/activate
#
pm2 start neurons/validator.py \
    --name investing-validator -- \
    --wallet.name {coldkey} \
    --wallet.hotkey {hotkey} \
    --netuid 88 #339 --subtensor.network test
```

## Mining

When a strategy is filed under the `Investing/strat/` directory, it will be automatically submitted by the miner. Please see [README](https://github.com/mobiusfund/investing/tree/main/Investing/strat) for further info.

A strategy can be revised or "rebalanced" whenever necessary. It will be automatically resubmitted based on the file timestamp. Rebalancing can happen when updating the timestamp without changing the strategy file. A change in asset allocation will incur [slippage](https://docs.learnbittensor.org/learn/slippage) costs as well as [staking/unstaking](https://github.com/opentensor/subtensor/pull/1386) fees for Tao/Alpha, and transaction fees for other assets.

For US stocks, rebalancing is currently supported via two order types in a trading session: Market on Open (MOO) and Market on Close (MOC), to take advantage of maximum liquidity. Per NYSE and NASDAQ rules, only strategies submitted before 09:28 and 15:50 Eastern time will be counted. Currently supported [ticker symbols](https://api.investing88.ai/assets) are generally large cap assets.

To accommodate multiple asset classes, the UID space and subnet emissions are partitioned based on [asset ratio](https://api.investing88.ai/ratio), which will be adjusted over time as the subnet evolves.

All strategy updates are shown on the [dashboard](https://db.investing88.ai) immediately. Daily score calculation takes place at 04:00 UTC. The dashboard emphasizes raw performance rankings and comparisons between asset classes. To see adjusted rankings and scores set by validators that match on-chain incentives, use the `Investing/bin/validator` command.

One machine can run multiple miners with their corresponding strategies, with an extra argument e.g. `--axon.port 8092` added to the `pm2` command. However a new or revised strategy that is overly similar to a pre-existing one will receive a reduced score.

To curb UID spam, each miner requires a certain amount of alpha token stake. The total required stake is reflected on the coldkey.

A newly registered miner goes live on the dashboard after day 1, with an immunity period of 3 days.

#### Testnet

Testnet can be used for connection testing. Testnet strategies will not be accepted nor evaluated. Both testnet and mainnet miners can easily evaluate their strategies using the `Investing/bin/simst` command.

## Scoring

Due to differences in investment style, risk tolerance, available capital, time horizon etc., there is no single "best" strategy that fits all investors. Our scoring algorithm takes into account many factors including return, volatility, drawdown, slippage, and timeframe. The algorithm is defined as follows and will be refined and updated over time.

A simple number $$score$$ is used to evaluate strategies, where:

```math
\begin{aligned}
& fund = initial\ capital \\
\\
& days = days\ investing \\
\\
& pnl = daily\ profit\ or\ loss \\
\\
& prob = \frac {\ days\ in\ profit\ } {\ days\ } \\
\\
& pavg\% = \frac {\ profit\%\ total\ } {\ days\ in\ profit\ } \\
\\
& lavg\% = \frac {\ loss\%\ total\ } {\ days\ in\ loss\ } \\
\\
& kb = \frac {\ pavg\% \ } {\ lavg\% \ } \\
\\
& kelly = \frac {\ prob \cdot \left( kb + 1 \right) - 1\ } {\ kb\ } \\
\\
& kelly = \text{–}1,\ if < \text{–}1 \\
\\
& return = \sum_{1}^{days} pnl = fund_{days} - fund \\
\\
& return\% = \frac {\ return\ } {\ fund\ } \cdot 100 \\
\\
& risk\% = max\ drawdown\% \\
\\
& mar = \frac {\ return\%\ } {\ risk\%\ } \\
\\
& lsr = \frac {\ \sum_{1}^{days} pnl\ } {\ \sum_{1}^{days} |pnl|\ } \\
\\
& odds\% = 50 + \frac {\ kelly\ } {\ 2\ } \cdot 100 \\
\\
& daily\% = \left( 1 + \frac {\ return\%\ } {\ 100\ } \right) ^ {\frac {\ 1\ } {\ days\ }} \cdot 100 - 100 \\
\\
& apr\% = \left( 1 + \frac {\ daily\%\ } {\ 100\ } \right) ^ {365} \cdot 100 - 100 \\
\\
& score = mar \cdot lsr \cdot odds\% \cdot daily\% \\
\\
\end{aligned}
```

Two parameters here are developed exclusively by Mobius Fund: $$odds\\%$$ is essentially winning odds normalized using Kelly's equation, with the profit/loss ratio normalized to 1 while the Kelly factor remaining the same; $$lsr$$ is >0.99 correlated to Sharpe Ratio and mathematically more sound. Empirically $$lsr \approx \frac {\ sharpe\ ratio\ } {\ 11\ }$$.

There are two edge cases when a strategy is getting started: All days are loss days, where $$kb = 0$$, and $$kelly = \text{–}\infty$$ therefore $$\text{–}1$$; All days are profit days, where $$kb = \infty$$, $$kelly = 1$$, and $$risk\\% = 0$$. Since $$mar$$ is inherently a long-term parameter, we make an empirical adjustment in live code to account for short-term effects in Bittensor, where $$R_{init} = 5$$ for Tao/Alpha, and $$R_{init} = 1$$ for US stocks:
```math
\begin{aligned}
& mar = return\% / max( risk\%,\ \frac {\ R_{init}\ } {\ \sqrt { days\ }\ } )
\\
\end{aligned}
```

To reduce short-term random effects, we clip daily profit outliers in live code where $$N = 2$$, and limit a new miner's score:
```math
\begin{aligned}
& top\ N\ profit\% = top\ (N\text{+}1) ^ {th}\ profit\% \\
\\
& score = score\ *\ \frac {\ days\ } {\ 30\ },\ if\ days < 30 \\
\\
\end{aligned}
```

To encourage allocations in assets other than cash, we adjust score in live code:
```math
\begin{aligned}
& score = score\ *\ max( 1 - cash\ alloc,\ 0.01 )
\\
\end{aligned}
```

To encourage active rebalancing on a regular basis, we introduce DEC - Dynamic Emission Control in live code:
```math
\begin{aligned}
& dec = \left( \frac {\ last\ active\ } {\ 30\ } \right) ^ {2},\ if\ days > 7 \\
\\
& score = score\ *\ \left( 1 - min( dec,\ 1 ) \right) \\
\\
\end{aligned}
```

Finally, a rolling window is applied depending on markets and asset classes. The window size is currently set at 30 days for all assets. It will be adjusted over time as the subnet evolves.

As the initial capital, we assume $$fund = 1000\ Tao$$ for Tao/Alpha, and $$fund = 10M\ USD$$ for US stocks. Profit and loss are calculated daily at 04:00 UTC. Return is determined by price performance of allocated assets plus dividends. For Tao/Alpha, dividends are calculated from validator delegation with the default 18% take.

#### Performance

Miners are encouraged to emphasize long-term strategies with portfolio management, in contrast to short-term trading in isolated instruments. The general goal is to consistently outperform the market by boosting alpha while reducing beta. For miners new to portfolio management, the concept of MPT and CAPM can be a good starting point in optimizing strategies and portfolios using machine learning.

The stand-alone tool `Investing/bin/simst` (Sim Strat) can be convenient for back testing strategies and tuning performance based on historical market data.

Note that in contrast to live mining, `simst` may simulate block-level precision based on limited market data. The difference in results should not be far off especially in a long-term timeframe.

## Disclaimer
Past performance is no guarantee of future results. The subnet does not provide financial advice of any kind. Investing carries inherent risks, including the risk of partial or total loss of capital. The subnet is not responsible for any profit or loss resulting from any strategies shared by the Bittensor community.

## License
This repository is licensed under the MIT License.
```text
# The MIT License (MIT)
# Copyright © 2024 Opentensor Foundation

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
```
