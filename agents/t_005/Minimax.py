from template import Agent
import time
from copy import deepcopy

# from general_game_runner import *
from Splendor.splendor_model import *
from collections import deque
import random

NUM_AGENT = 2
MAX_TIME = 0.95 # in case timeout, set a time limit


class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)
        self.game_rule = SplendorGameRule(num_of_agent=NUM_AGENT)

    def SelectAction(self, actions, game_state):
        self.start_time = time.time()
        best_action = None

        for i in range(1, 8):
            try:
                best_action = self.start_minimax(actions, game_state, i)
            except TimeoutError:
                print("Timeout")
                break

        return best_action

    def start_minimax(self, actions, game_state, depth):
        best_actions = []
        best_score = float("-inf")

        self.count = 0

        for action in actions:
            successor_state = self.game_rule.generateSuccessor(
                deepcopy(game_state), action, self.id
            )
            eval_score = self.minimax(
                successor_state, depth - 1, 1 - self.id, float("-inf"), float("inf")
            )
            if eval_score > best_score:
                best_score = eval_score
                best_actions = []

            if eval_score == best_score:
                best_actions.append(action)

        best_action = random.choice(best_actions)

        # print("minimaxxed: ", self.count)
        # print("best_action", best_action)
        # print("best_score", best_score)
        # print("num actions", len(actions))
        print("depth", depth)

        # return random choice of best_actions
        return best_action

    def minimax(self, game_state, depth, my_agentid, alpha, beta):
        if time.time() - self.start_time > MAX_TIME:
            raise TimeoutError()
        self.count += 1
        # Maybe also check if game lost
        if depth == 0:
            return self.evaluate_state(game_state)

        maximizing = my_agentid == self.id
        legal_actions = self.game_rule.getLegalActions(game_state, my_agentid)

        if maximizing:
            max_eval = float("-inf")
            for action in legal_actions:
                successor_state = self.game_rule.generateSuccessor(
                    deepcopy(game_state), action, my_agentid
                )
                eval_score = self.minimax(
                    successor_state, depth - 1, 1 - my_agentid, alpha, beta
                )
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval

        else:
            min_eval = float("inf")
            for action in legal_actions:
                successor_state = self.game_rule.generateSuccessor(
                    deepcopy(game_state), action, my_agentid
                )
                eval_score = self.minimax(
                    successor_state, depth - 1, 1 - my_agentid, alpha, beta
                )
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def evaluate_state(self, state):
        # opponent = 1 - self.id
        self_score = self.game_rule.calScore(state, self.id)
        # opponent_score = self.game_rule.calScore(state, opponent)
        # assert self_score >= 0 and opponent_score >= 0
        return self_score
        # return self_score - opponent_score
