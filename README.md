<div align="center">

# **Sταking**
## Optimizing Staking Strategies
[Dashboard](https://stakingalpha.com) • [Discord](https://discord.gg/bittensor) • [X](https://x.com/StakingAlpha88)
</div>

---
- [Intro](#Intro)
- [Installation](#installation)
- [Mining](#Mining)
- [Scoring](#Scoring)
- [Disclaimer](#Disclaimer)
- [License](#license)

## Intro

Sταking is the Bittensor subnet that optimizes staking strategies in the Tao/Alpha ecosystem. By the community and for the community, it also provides services for outside retail and institutional investors.

Miners share their strategies, while validators evaluate them using a [scoring algorithm](#Scoring). All results are displayed on the [StakingAlpha.com dashboard](https://stakingalpha.com).

The business model and innovations will apply across crypto and other more traditional markets, extract alpha from these markets, minimize risks, and deliver optimized portfolio returns to a broad range of investors in the global [145 trillion dollar](https://www.pwc.com/ng/en/press-room/global-assets-under-management-set-to-rise.html) asset management industry.

## Installation

#### Setup

```bash
git clone https://github.com/mobiusfund/staking
cd staking
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
    --name staking-miner -- \
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
    --name staking-validator -- \
    --wallet.name {coldkey} \
    --wallet.hotkey {hotkey} \
    --netuid 88 #339 --subtensor.network test
```

## Mining

When a strategy is filed under the `Sταking/strat/` directory, it will be automatically submitted by the miner. Please see [README](https://github.com/mobiusfund/staking/tree/main/Sταking/strat) for further info.

A strategy can be revised or "rebalanced" whenever necessary. It will be automatically resubmitted based on the timestamp. Rebalancing can happen when updating the timestamp without changing the strategy file. A change in subnet allocation will incur slippage costs.

All strategy updates will be shown on the dashboard immediately. Daily score calculation will take place after midnight UTC.

One machine can run multiple miners with their corresponding strategies. However a new or revised strategy that is overly similar to a pre-existing one will receive a reduced score.

A newly registered miner goes live on the dashboard after day 1, with an immunity period of 3 days.

#### Testnet

Testnet can be used for connection testing. Testnet strategies will not be accepted nor evaluated. Both testnet and mainnet miners can easily evaluate their strategies using the `Sταking/bin/simst` command.

## Scoring

Due to differences in investment style, risk tolerance, available capital, time horizon etc., there is no single "best" strategy that fits all investors. Our scoring algorithm takes into account many factors including return, volatility, drawdown, slippage, and timeframe. The algorithm is defined as follows and will be refined and updated over time.

A simple number $$score$$ is used to evaluate strategies, where:

```math
\begin{aligned}
& fund = initial\ capital \\
\\
& days = days\ staking \\
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
& yield = \sum_{1}^{days} pnl = fund_{days} - fund \\
\\
& yield\% = \frac {\ yield\ } {\ fund\ } \cdot 100 \\
\\
& risk\% = max\ drawdown\% \\
\\
& mar = \frac {\ yield\%\ } {\ risk\%\ } \\
\\
& lsr = \frac {\ \sum_{1}^{days} pnl\ } {\ \sum_{1}^{days} |pnl|\ } \\
\\
& odds\% = 50 + \frac {\ kelly\ } {\ 2\ } \cdot 100 \\
\\
& daily\% = \left( 1 + \frac {\ yield\%\ } {\ 100\ } \right) ^ {\frac {\ 1\ } {\ days\ }} \cdot 100 - 100 \\
\\
& apy\% = \left( 1 + \frac {\ daily\%\ } {\ 100\ } \right) ^ {365} \cdot 100 - 100 \\
\\
& score = mar \cdot lsr \cdot odds\% \cdot daily\% \\
\\
\end{aligned}
```

Two parameters here are developed exclusively by Mobius Fund: $$odds\\%$$ is essentially winning odds normalized using Kelly's equation, with the profit/loss ratio normalized to 1 while the Kelly factor remaining the same; $$lsr$$ is >0.99 correlated to Sharpe Ratio and mathematically more sound. Empirically $$lsr \approx \frac {\ sharpe\ ratio\ } {\ 11\ }$$.

There are two edge cases when a strategy is getting started: All days are loss days, where $$kb = 0$$, and $$kelly = \text{–}\infty$$ therefore $$\text{–}1$$; All days are profit days, where $$kb = \infty$$, $$kelly = 1$$, $$risk\\% = 0$$, and empirically we define $$mar = \frac { \sqrt { days\ }\ } {\ 5\ } \cdot yield\\%$$.

We assume $$fund = 1000τ$$ as the initial capital and take slippage into account. Profit and loss are calculated daily at midnight UTC. Yield is determined by price performance of allocated subnets, plus estimated dividends from validator delegation with the default 18% take.

At the subnet launch, a strategy's ranking is based on a single score calculated over a continuous timeframe. As the subnet grows, it will incorporate multiple weighted timeframes, for example, $$30\ days$$, $$90\ days$$, $$1\ year$$, and $$5\ years$$.

#### Performance

Miners are encouraged to emphasize long-term strategies with portfolio management, in contrast to short-term trading in isolated instruments. The general goal is to consistently outperform the market by boosting alpha while reducing beta. For miners new to portfolio management, the concept of MPT and CAPM can be a good starting point in optimizing strategies and portfolios using machine learning.

The stand-alone tool `Sταking/bin/simst` (Sim Stake/Strat) can be convenient for back testing strategies and tuning performance based on historical market data.

## Disclaimer
Past performance is no guarantee of future results. The subnet does not provide financial advice of any kind. Investing carries inherent risks, including the risk of partial or total loss of capital. The subnet is not responsible for any profit or loss resulting from any strategies shared by the community.

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
