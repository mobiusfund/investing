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


import os, time, random
import bittensor as bt
import Sταking.core.api as api
import Sταking.core.etc as etc

# import base validator class which takes care of most of the boilerplate
from template.base.validator import BaseValidatorNeuron

# Bittensor Validator Template:
from template.validator import forward


class Validator(BaseValidatorNeuron):
    """
    Your validator neuron class. You should use this class to define your validator's behavior. In particular, you should replace the forward function with your own logic.

    This class inherits from the BaseValidatorNeuron class, which in turn inherits from BaseNeuron. The BaseNeuron class takes care of routine tasks such as setting up wallet, subtensor, metagraph, logging directory, parsing config, etc. You can override any of the methods in BaseNeuron if you need to customize the behavior.

    This class provides reasonable default behavior for a validator such as keeping a moving average of the scores of the miners and using them to set weights at the end of each epoch. Additionally, the scores are reset for new hotkeys at the end of each epoch.
    """

    def __init__(self, config=None):
        super(Validator, self).__init__(config=config)

        bt.logging.info("load_state()")
        self.load_state()

        # TODO(developer): Anything specific to your use case you can do here

    async def forward(self):
        """
        Validator forward pass. Consists of:
        - Generating the query
        - Querying the miners
        - Getting the responses
        - Rewarding the miners
        - Updating the scores
        """
        # TODO(developer): Rewrite this function based on your protocol definition.
        return await forward(self)

    def score(self, x):
        time.sleep(60)
        while True:
            if int(time.strftime('%M')) in [25, 55]: break
            time.sleep(1)
        time.sleep(random.randint(25, 55))
        try:
            pl = api.pnl()
            da = api.days()
            if not len(pl): return
            bt.logging.info('Calculating score...')
            self.scores = etc.score(pl, da, self.metagraph.n)
        except: pass


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    bt.logging.enable_info()
    with Validator() as validator:
        validator.loop.run_until_complete = validator.score
        validator.concurrent_forward = lambda: ...
        step = 0
        while True:
            if step % 60 == 0: bt.logging.info(f"Validator running... {time.time()}")
            if step % 3600 == 0:
                try: err = etc.update()
                except: err = None
                if err == 0:
                    print('Restarting...')
                    exit() # restart w/ pm2
            time.sleep(1)
            step += 1
