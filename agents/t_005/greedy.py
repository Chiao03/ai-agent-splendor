from template import Agent
import random
from Splendor.splendor_model import *

NUM_AGENT = 2
MAX_TIME = 0.99  #in case timeout, set a time limit

class myAgent(Agent):
    def __init__(self,_id):
        super().__init__(_id)
        self.game_rule = SplendorGameRule(num_of_agent=NUM_AGENT)

    def SelectAction(self, actions, game_state):
        total_gems = sum(game_state.agents[self.id].gems.values())
        if total_gems <= 8:
            gem_actions = [action for action in actions if "collect" in action['type']]
            if gem_actions and sum(game_state.board.gems.values()) >= 3:
                return random.choice(gem_actions)
        buy_actions = [action for action in actions if "buy" in action['type']]
        if buy_actions:
            return random.choice(buy_actions)
        reserve_actions = [action for action in actions if "reserve" in action['type']]
        if reserve_actions:
            return random.choice(reserve_actions)
        return random.choice(actions)
