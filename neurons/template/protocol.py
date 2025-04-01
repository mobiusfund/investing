# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2025 Mobius Fund

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

import typing
import bittensor as bt

# This is the protocol for the strategy miner and validator.
# It is a simple request-response protocol where the validator sends a request
# to the miner, and the miner responds with a strategy response.

# ---- miner ----
# Example usage:
#   def strategy( synapse: Strategy ) -> Strategy:
#       synapse.strategy_output = synapse.strategy_input + 1
#       return synapse
#   axon = bt.axon().attach( strategy ).serve(netuid=...).start()

# ---- validator ---
# Example usage:
#   dendrite = bt.dendrite()
#   strategy_output = dendrite.query( Strategy( strategy_input = 1 ) )
#   assert strategy_output == 2


class Strategy(bt.Synapse):
    """
    A simple strategy protocol representation which uses bt.Synapse as its base.
    This protocol helps in handling strategy request and response communication between
    the miner and the validator.

    Attributes:
    - strategy_input: An integer value representing the input request sent by the validator.
    - strategy_output: An optional integer value which, when filled, represents the response from the miner.
    """

    # Required request input, filled by sending dendrite caller.
    strategy_input: int

    # Optional request output, filled by receiving axon.
    strategy_output: typing.Optional[int] = None

    def deserialize(self) -> int:
        """
        Deserialize the strategy output. This method retrieves the response from
        the miner in the form of strategy_output, deserializes it and returns it
        as the output of the dendrite.query() call.

        Returns:
        - int: The deserialized response, which in this case is the value of strategy_output.

        Example:
        Assuming a Strategy instance has a strategy_output value of 5:
        >>> strategy_instance = Strategy(strategy_input=4)
        >>> strategy_instance.strategy_output = 5
        >>> strategy_instance.deserialize()
        5
        """
        return self.strategy_output
