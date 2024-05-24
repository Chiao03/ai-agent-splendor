from template import Agent
import random
import time 
import json
from Splendor.splendor_model import SplendorGameRule as GameRule
from copy import deepcopy

MAX_TIME = 0.9
NUM_PLAYERS = 2
EPSILON = 0.1

GAMMA = 0.8
ALPHA = 0.01


class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)
        self.game_rule = GameRule(NUM_PLAYERS)
        with open("agents/t_005/RL_weight.json", 'r', encoding='utf-8') as fw:
            self.weight = json.load(fw)['weight']

    def calculate_collect_features(self, action, agent, board):
        colour_right = {'black': 0, 'blue': 0, 'green': 0, 'red': 0, 'white': 0, 'yellow': 10}
        numerator = 100
        for dealt_cards in board.dealt:
            for card in dealt_cards:
                if card is None:
                    continue
                for colour, cost in card.cost.items():
                    if cost > len(agent.cards[colour]) + agent.gems[colour]:
                        colour_right[colour] += 1

        right = sum(action['collected_gems'][colour] * colour_right[colour] for colour in action['collected_gems'])
        right -= sum(action['returned_gems'][colour] * colour_right[colour] for colour in action['returned_gems'])
        return [right / numerator]
        # features = []
        # for dealt_cards in board.dealt:
        #     colour_right = {'black': 0, 'blue': 0, 'green': 0, 'red': 0, 'white': 0, 'yellow': 10}
        #     for card in dealt_cards:
        #         if card is not None:
        #             for colour in card.cost:
        #                 if card.cost[colour] > len(agent.cards[colour]) + agent.gems[colour]:
        #                     colour_right[colour] += 1

        #     right = 0
        #     for colour in action['collected_gems']:
        #         right += action['collected_gems'][colour] * colour_right[colour]
        #     for colour in action['returned_gems']:
        #         right -= action['returned_gems'][colour] * colour_right[colour]
        #     features.append(right / 100)
        # # print(features)
        # return features

    def calculate_buy_features(self, action, board):
        card = action['card']
        if card is None:
            return [0, 0, 0]
        buy_feature = card.points / 5
        features = [buy_feature]
        count = sum(card.cost.values())
        sum_feature = count / 15
        features.append(sum_feature)
        has_noble = sum(1 for noble in board.nobles if card.colour in noble[1])
        noble_feature = has_noble / 5
        features.append(noble_feature)
        return features

    def calculate_reserve_features(self, state, action):
        oppo_agent = state.agents[1 - self.id]
        oppo_actions = self.game_rule.getLegalActions(state, 1 - self.id)
        feat = any(card.points >= 3 or ('noble' in action and action['noble'] is not None and
                                        action['noble'][1].get(card.colour, 0) == len(
                    oppo_agent.cards[card.colour]) + 1)
                   for action in oppo_actions if 'buy' in action['type'] for card in [action['card']])
        feat = feat * 0.3
        # feat = feat * 0.5
        return [feat]

    def CalFeatures(self, state, action, id):
        board = state.board
        # agent = state.agents[self.id]
        agent = state.agents[id]
        features = []
        extend_none = [0, 0, 0]
        if 'collect' in action['type']:
            features.extend(self.calculate_collect_features(action, agent, board))
        else:
            features.extend(extend_none)

        if 'buy' in action['type']:
            features.extend(self.calculate_buy_features(action, board))
        else:
            features.extend(extend_none)

        features.append(1 if ('noble' in action) and (action['noble'] is not None) else 0)

        if 'reserve' in action['type']:
            features.extend(self.calculate_reserve_features(state, action))
        else:
            features.append(0)

        # print(self.splendor_heuristic(state, agent, board))
        return features

    def CalQValue(self, state, action, id):
        features = self.CalFeatures(state, action, id)
        try:
            return sum(feature * weight for feature, weight in zip(features, self.weight))
        except TypeError:
            # print('Length of features and weights do not match!')
            return float('-inf')

    def Order_Legal_Action(self, game_state):
        board = game_state.board
        total_gems = sum(game_state.agents[self.id].gems.values())
        actions = self.game_rule.getLegalActions(game_state, self.id)
        buy_actions = []
        gem_action = []
        reserve_action = []
        scored_actions = []
        available_cards = board.dealt
        opponent = 1 - self.id
        opponent_score = game_state.agents[opponent].score
        opponent_gems = game_state.agents[opponent].gems
        self_score = game_state.agents[self.id].score
        # print(actions)
        for action in actions:
            score = 0
            if 'buy' in action['type']:
                card = action['card']
                action['card_score'] = card.points
                buy_actions.append(action)
                # score += 1
                score += (action['card_score'])
                if available_cards[0] is not None and any(
                        card.colour == other_card.cost[gem] for other_card in available_cards[0] if
                        other_card is not None and other_card.cost is not None for gem in other_card.cost):
                    score += 0.5
            elif "reserve" in action['type']:
                # score += 0.1
                card = action['card']
                action['card_score'] = card.points
                reserve_action.append(action)
                score += (action['card_score'])
                # print(reserve_action)
                noble_points = 3 * any(action['noble']) if action['noble'] is not None else 0
                if all(opponent_gems[gem] >= card.cost[gem] for gem in card.cost if gem):
                    if (self_score < opponent_score - 2
                            and self_score > 5):
                        score += 0.2
                    if (card.points + noble_points + opponent_score >= 15
                            or card.points + noble_points + opponent_score - 5 >= self_score):
                        score += (action['card_score'])
                        score += noble_points
                        score += 0.5
            elif "collect" in action['type']:
                if total_gems <= 8 and sum(game_state.board.gems.values()) >= 3:
                    gem_action.append(action)
                    score += 0.4

            # print(scored_actions)
            scored_actions.append((action, score))
            # print(card, action['card_score'])
            buy_actions = sorted(buy_actions, key=lambda action: action['card_score'], reverse=True)
            reserve_action = sorted(reserve_action, key=lambda action: action['card_score'], reverse=True)
            scored_actions.sort(key=lambda x: x[1], reverse=True)
        # print(buy_actions)
        # print(buy_actions)
        # # print(gem_action)
        # print(scored_actions)
        # if buy_actions:
        #     return buy_actions[0]
        # if gem_action:
        #     return gem_action[0]
        # if reserve_action:
        #     return reserve_action[0]
        # # action = "random"
        # return random.choice(actions)
        # print(scored_actions)
        # print(scored_actions)
        return scored_actions[0][0] if scored_actions else random.choice(actions)

    def splendor_heuristic(self, state, agent, board):
        # # Get the current player's gems and cards
        # player_gems = agent.gems
        # player_cards =agent.cards

        # # Get the available cards in the game
        # available_cards = board.dealt

        # # Initialize the best score and action
        # best_score = -float('inf')
        # best_action = None

        # # Iterate over all available cards
        # for card in available_cards:
        #     # Calculate the score for this card
        #     for individual_card in card:
        #         if individual_card:
        #             card_score = individual_card.points
        #             # If the player can afford this card, add a bonus to the score
        #             if all(player_gems[gem] >= individual_card.cost[gem] for gem in individual_card.cost if gem):
        #                 card_score += 10
        #             # If this card provides a gem that the player needs for other cards, add a bonus to the score
        #             if any(individual_card.colour == other_card.cost[gem] for other_card in available_cards[0] if other_card is not None for gem in other_card.cost):                        card_score += 5
        #             # If this card's score is the best so far, update the best score and action
        #             if card_score > best_score:
        #                 best_score = card_score
        #                 best_action = ('buy', individual_card)
        #     # If no card can be bought, reserve a card
        #     if best_action is None:
        #         for card in available_cards:
        #             best_action = ('reserve', card)
        #             break
        #     # If no card can be reserved, take gems
        #     if best_action is None:
        #         best_action = ('take', 'different')
        # return best_action
        # Get the current player's gems and cards
        player_gems = agent.gems
        player_cards = agent.cards

        # Get the available actions in the game
        legal_actions = self.game_rule.getLegalActions(state, self.id)

        # Initialize the best score and action
        best_score = -float('inf')
        best_action = None
        available_cards = board.dealt
        # Iterate over all legal actions
        for action in legal_actions:
            action_type = action['type']

            if action_type == 'buy':
                card = action['card']
                # Calculate the score for this card
                card_score = card.points
                # If the player can afford this card, add a bonus to the score
                if card.cost is not None and all(player_gems.get(gem, 0) >= card.cost.get(gem, 0) for gem in card.cost):
                    card_score += 1
                # If this card provides a gem that the player needs for other cards, add a bonus to the score
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

    def SelectAction(self, actions, game_state):
        start_time = time.time()
        # best_action = self.splendor_heuristic(game_state, game_state.agents[self.id], game_state.board)
        # print(best_action)
        best_action = self.Order_Legal_Action(game_state)
        # best_action = random.choice(actions)
        best_Q_value = float('-inf')
        # print(best_action)
        for action in actions:
            if time.time() - start_time > MAX_TIME:
                break
            Q_value = self.CalQValue(game_state, action, self.id)
            if Q_value > best_Q_value:
                best_Q_value = Q_value
                best_action = action
        # print(best_action)
        # print(Q_value, best_action)
        # print(best_action)
        return best_action
#         with open("agents/t_005/weight.json", 'r', encoding='utf-8') as fw:
#             self.weight = json.load(fw)['weight']
#         # best_action = random.choice(actions)
#         # print(best_action)
#         best_action = self.splendor_heuristic(game_state, game_state.agents[self.id], game_state.board)
#         print(best_action)

#         best_Q_value = float('-inf')
#         if len(actions) > 1:
#             if random.uniform(0,1) < 1 - EPSILON:
#                 for action in actions:
#                     if time.time() - start_time > MAX_TIME:
#                         break
#                     Q_value = self.CalQValue(game_state, action, self.id)
#                     if Q_value > best_Q_value:
#                         best_Q_value = Q_value
#                         best_action = action
#             else:
#                 Q_values = self.CalQValue(game_state, best_action, self.id)
#                 best_Q_value = Q_values
#             next_state = deepcopy(game_state)
#             self.game_rule.generateSuccessor(next_state, best_action, self.id)

#             oppo_actions = self.game_rule.getLegalActions(next_state, 1 - self.id)
#             oppo_best_action = random.choice(oppo_actions)
#             oppo_best_Q_value = float('-inf')
#             if len(oppo_actions) > 1:
#                 for action in oppo_actions:
#                     oppo_Q_value = self.CalQValue(next_state, action, 1 - self.id)
#                     if oppo_Q_value > oppo_best_Q_value:
#                         oppo_best_Q_value =oppo_Q_value
#                         oppo_best_action = action
#             self.game_rule.generateSuccessor(next_state, oppo_best_action, 1-self.id)
#             reward = next_state.agents[self.id].score
#             if reward >= 15:
#                 # If so, assign a large reward
#                 reward = 1000
#             next_actions = self.game_rule.getLegalActions(next_state, self.id)
#             best_next_Q_value = float('-inf')
#             for action in next_actions:
#                 Q_value = self.CalQValue(next_state, action, self.id)
#                 best_next_Q_value = max(best_next_Q_value, Q_value)
#             features = self.CalFeatures(game_state, best_action, self.id)
#             delta = reward + GAMMA * best_next_Q_value - best_Q_value
#             for i in range(len(features)):
#                 self.weight[i] += ALPHA * delta * features[i]
#             with open("agents/t_005/weight.json", 'w', encoding='utf-8') as fw:
#                 json.dump({'weight': self.weight}, fw)
#         # print(best_action)
#         return best_action
