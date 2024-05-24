from template import Agent
import random
import time
from copy import deepcopy
from Splendor.splendor_model import *
from collections import deque

NUM_AGENT = 2
MAX_TIME = 0.99  # in case timeout, set a time limit


class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)
        self.game_rule = SplendorGameRule(num_of_agent=NUM_AGENT)

    def Order_Legal_Action(self, game_state):
        total_gems = sum(game_state.agents[self.id].gems.values())
        actions = self.game_rule.getLegalActions(game_state, self.id)
        buy_actions = []
        gem_action = []
        reserve_action = []
        for action in actions:
            if 'buy' in action['type']:
                buy_actions.append(action)
        if buy_actions:
            return buy_actions, action
        for action in actions:
            if total_gems <= 8:
                if "collect" in action['type'] and sum(game_state.board.gems.values()) >= 3:
                    gem_action.append(action)
        if gem_action:
            return gem_action, action
        for action in actions:
            if "reserve" in action['type']:
                reserve_action.append(action)
        if reserve_action:
            return reserve_action, action
        action = "random"
        return [random.choice(actions)], action

    def SelectAction(self, actions, game_state):
        path = []
        start_time = time.time()
        queue = deque([(deepcopy(game_state), [])])
        selected_actions = self.Order_Legal_Action(game_state)[0]
        score = self.game_rule.calScore(game_state, self.id)
        while len(queue) > 0 and time.time() - start_time < MAX_TIME:
            curr_state, curr_path = queue.popleft()
            new_score = self.game_rule.calScore(curr_state, self.id)
            if path and (new_score >= 15 or new_score - score >= 2):
                return path[0]
            selected_action = self.Order_Legal_Action(curr_state)
            if len(selected_action) == 1:
                return selected_action[0]
            update_action, action_type = selected_action
            if "buy" in action_type:
                self.processBuyAction(update_action, curr_state, curr_path, queue)
            elif "reserve" in action_type:
                self.processReserveAction(update_action, curr_state, curr_path, queue)
            elif "collect" in action_type:
                self.processCollectAction(update_action, curr_state, curr_path, queue)
        if len(path):
            return path[0]
        # elif selected_actions:
        return random.choice(selected_actions)
        # print(self.Order_Legal_Action(game_state))
        # return random.choice(actions)

    # Buy action
    def processBuyAction(self, actions, state, path, queue):
        state = deepcopy(state)
        actions.sort(key=lambda x: x['card'].points, reverse=True)
        for action in actions:
            if action['card'].points >= 1:
                update_state = self.game_rule.generateSuccessor(state, action, self.id)
                update_path = path + [action]
                queue.append((update_state, update_path))
                return

    # Collect action
    def processCollectAction(self, actions, state, path, queue):
        state = deepcopy(state)
        for action in actions:
            if self.gemisNeeded(action, state):
                update_state = self.game_rule.generateSuccessor(state, action, self.id)
                update_path = path + [action]
                queue.append((update_state, update_path))

    # Reserve action
    def processReserveAction(self, actions, state, path, queue):
        state = deepcopy(state)
        for action in actions:
            if action['card'].points >= 2:
                update_state = self.game_rule.generateSuccessor(state, action, self.id)
                update_path = path + [action]
                queue.append((update_state, update_path))

    # If the gem is needed, choose the nost valuable one
    def gemisNeeded(self, action, state):
        need_gems = {'black': 0, 'blue': 0, 'green': 0, 'red': 0, 'white': 0}
        cards = state.board.dealt_list()
        for card in cards:
            for colour, cost in card.cost.items():
                need_gems[colour] += cost
        need_colour = max(need_gems, key=need_gems.get)
        get_needed_gem = need_colour in action['collected_gems'].keys()
        return get_needed_gem
