from template import Agent
import random
from Splendor.splendor_model import *
import time
from copy import deepcopy
import math


NUM_AGENT = 2
MAX_TIME = 0.7  #in case timeout, set a time limit


class Node:
    def __init__(self, state, action = None, parent=None, id = -1):
        self.state = state
        self.parent = parent
        self.children = []
        self.action = action
        self.visits = 0
        self.score = 0
        self.game_rule = SplendorGameRule(num_of_agent=NUM_AGENT)
        self.id = id
    def fully_expanded(self):
        for child in self.children:
            if child.visits == 0:
                return False
        return True
    def get_unexpanded_move(self):
        for child in self.children:
            if child.visits == 0:
                return child
        return None
    def select_child(self):
        # Experiment 1: UCB = 1
        # return max(self.children, key = lambda c: c.score/c.visits + math.sqrt(2) * math.sqrt(math.log(self.visits) / c.visits))
        # Experiment 2: UCB = 0.05
        # return max(self.children, key = lambda c: c.score/c.visits + 0.05 * math.sqrt(math.log(self.visits) / c.visits))
        # Experiment 3: Epsilon = 0.1     
        epsilon = 0.1  
        if random.random() < epsilon:
            return random.choice(self.children)
        else:
            return max(self.children, key = lambda c: c.score/c.visits + 0.5 * math.sqrt(math.log(self.visits) / c.visits))
    def expand(self):
        action = random.choice(self.game_rule.getLegalActions(self.state, self.id))
        next_state = self.game_rule.generateSuccessor(self.state, action, self.id)
        child = Node(next_state, action, self, self.id)
        self.children.append(child)
        return child
        # actions = self.game_rule.getLegalActions(self.state, self.id)
        # for action in actions:
        #     self.children.append(Node(self.game_rule.generateSuccessor(self.state, action, self.id), action, self, self.id)
    def update(self, result):
        self.visits += 1
        self.score += result
class MCTS:
    def __init__(self, state, id):
        self.game_state = state 
        self.id = id
        self.game_rule = SplendorGameRule(num_of_agent=NUM_AGENT)
    def search(self,num_iterations, startTime):
        root = Node(self.game_state, self.id)
        for i in range(num_iterations):
            if time.time() - startTime > MAX_TIME:
                break
            node = self.select(root)
            score = self.simulate(node, startTime)
            self.backpropagate(node, score)
        best_child = max(root.children, key = lambda child: child.visits) if root.children else None
        return best_child.action if best_child else None
    def select(self, node):
        while not node.fully_expanded():
            if not node.children:
                return node.expand()
            node = node.select_child()
        return node
    #naive move 
    def simulate(self, node, startTime):
        state = deepcopy(node.state)
        while time.time() - startTime < MAX_TIME:
            if self.game_rule.calScore(state, self.id) < 15:
                actions = self.game_rule.getLegalActions(state, node.id)
                if actions: 
                    action = actions[0] 
                    state = self.game_rule.generateSuccessor(state, action, self.id)
        return self.game_rule.calScore(state, self.id)
    #heuristic
    # def simulate(self, node, startTime):
    #     state = deepcopy(node.state)
    #     while self.game_rule.calScore(state, self.id) < 15 and time.time() - startTime < MAX_TIME:
    #         # actions = self.game_rule.getLegalActions(state, node.id)
    #         # Use a simple heuristic to rank the actions
    #         # ranked_actions = self.Order_Legal_Action(state)
    #         action = myAgent.Order_Legal_Action(self,state)[:3]
    #         # action = random.choice(ranked_actions[:3])  # Choose randomly among the top 3 actions
    #         state = self.game_rule.generateSuccessor(state, action, self.id)
    #     return self.game_rule.calScore(state, self.id)
    
    def backpropagate(self, node, result):
        while node:
            node.update(result)
            node = node.parent
        
class myAgent(Agent):
    def __init__(self,_id):
        super().__init__(_id)
        self.game_rule = SplendorGameRule(num_of_agent=NUM_AGENT)
        self.round = 0

    def splendor_heuristic(self,actions, game_state):
        agent = game_state.agents[self.id]
        board = game_state.board
        player_gems = agent.gems
        player_cards = agent.cards
        legal_actions = self.game_rule.getLegalActions(game_state, self.id)
        best_score = -float('inf')
        best_action = None
        available_cards = board.dealt

        for action in legal_actions:
            action_type = action['type']
            if action_type == 'buy':
                card = action['card']
                card_score = card.points
                # buy action
                if card.cost is not None and all(player_gems.get(gem, 0) >= card.cost.get(gem, 0) for gem in card.cost):
                    card_score += 1
                # collect: a gem that the player needs for other cards
                if available_cards[0] is not None and any(
                        card.colour == other_card.cost[gem] for other_card in available_cards[0] if
                        other_card is not None and other_card.cost is not None for gem in other_card.cost):
                    card_score += 0.5
                # If this card's score is the best so far, update the best score and action
                if card_score > best_score:
                    best_score = card_score
                    best_action = action
        if best_action is None:
            best_action = random.choice(legal_actions)
        return best_action
    
    def GreedySearch(self,actions, game_state):
        total_gems = sum(game_state.agents[self.id].gems.values())
        buy_actions = []
        gem_action = []
        reserve_action = []
        for action in actions:
            if 'buy' in action['type']:
                buy_actions.append(action)
            elif total_gems <= 8:
                if "collect" in action['type'] and sum(game_state.board.gems.values()) >= 3:
                    gem_action.append(action)
            elif "reserve" in action['type']:
                reserve_action.append(action)
        if buy_actions:
            return random.choice(buy_actions)
        if gem_action:
            return random.choice(gem_action)
        if reserve_action:
            return random.choice(reserve_action)
        return random.choice(actions)
    
    def SelectAction(self, actions, game_state):
        self.start_time = time.time()
        self.round += 1
        best_action = self.splendor_heuristic(actions, game_state)
        while time.time() - self.start_time < MAX_TIME:
            mcts = MCTS(game_state, self.id)
            best_action = mcts.search(1, self.start_time)
        if best_action:   
            if (best_action not in actions):
                action =  self.splendor_heuristic(actions, game_state)
            else:
                action = best_action
        else:
            action = self.splendor_heuristic(actions, game_state)
        return action
