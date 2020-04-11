import poker
from player_type.base_player import Player
from collections import defaultdict, deque

class StatsPlayer(Player):

    def __init__(self, name, chips, alpha, debug):
        ''' Stats Player constructor. '''
        super().__init__(name, chips)
        self.alpha = alpha
        self.debug = debug != '0' and debug.lower() != 'false'

    def __repr__(self):
        ''' String representation with alpha value. '''
        return repr((self.name, self.chips, self.alpha))

    def getAction(self, to_call, table_cards, pot_size, in_play_names, blinds):
        ''' Returns bet based on probability of winning '''
        if self.debug: print('Hand: ' , poker.returnCardStringShort(self.hand))
        if len(table_cards) == 0:
            # Evaluate starting hand by pairs then card value
            return self.evaluateStartingHand(to_call, pot_size, blinds)
        else:
            # Get all possible hands your opponents can have
            opponent_permutations = self.getPermutations(table_cards, 2, self.hand)
            opponent_possibilities = sum([len(x) for x in opponent_permutations.values()])

            hand, score = poker.returnHandScore(self.hand + table_cards)
            hand_sum = poker.returnTieBreakScore(hand, score)
            opponent_win_probability = sum([len(opponent_permutations[x]) / opponent_possibilities for x in opponent_permutations if x > score])

            # Tie-break evaluation
            for same_score_hand in opponent_permutations[score]:
                tie_hand, tie_score = poker.returnHandScore(table_cards + list(same_score_hand))
                tie_hand_sum = poker.returnTieBreakScore(tie_hand, tie_score)
                if tie_hand_sum > hand_sum:opponent_win_probability += 1 / opponent_possibilities

            # Scale probability to all opponents losing
            opponent_win_probability = 1 - (1 - opponent_win_probability) ** len(in_play_names)
            if self.debug: print('Probability of losing: %f' % (opponent_win_probability))
            
        return self.getBetSize(opponent_win_probability, to_call, pot_size, blinds)
 

    def evaluateStartingHand(self, to_call, pot_size, blinds):
        ''' Rough evaluation of starting hand '''
        # Any pair gets 12 points
        # Plus sum of both digits if > 24 * (1 - self.alpha)
        # Call or raise
        hand_score = int(self.hand[0] % 13 == self.hand[1] % 13) * 12
        if (hand_score + sum(self.hand)) / 24 >= (1 - self.alpha):
            return to_call
        if to_call / pot_size <= self.alpha: 
            return to_call
        return -1

    def getBetSize(self, opponent_win_probability, to_call, pot_size, blinds):
        ''' Return appropriate bet size based on winning probability. '''
        bet = 0
        if self.alpha >= opponent_win_probability or (to_call != 0 and to_call / pot_size <= self.alpha):
            bet = self.getMaxBet(to_call, (1 - opponent_win_probability) * (pot_size - to_call), blinds)
        elif to_call != 0: bet = -1
        return bet
        
    def getMaxBet(self, to_call, intended_bet, blinds):
        # Call if player wants to bet less
        # Bet intended value if it's greater than to call
        if to_call < intended_bet:
            return int(max(to_call, min(intended_bet, self.chips) // blinds * blinds))
        else:
            return int(min(to_call, min(intended_bet, self.chips) // blinds * blinds))

    def getPermutations(self, base_cards, cards_to_guess, excluded_cards=[]):
        ''' 
        Generate all possible hands based on cards provided.
        Can exclude specific cards during the process.
        '''
        probability_table = defaultdict(deque)
        if cards_to_guess == 2:
            for card_1 in range(52):
                if card_1 in (base_cards + excluded_cards): continue
                for card_2 in range(card_1 + 1, 52):
                    if card_2 in (base_cards + excluded_cards): continue
                    hand, score = poker.returnHandScore(base_cards + [card_1, card_2])
                    probability_table[score] += [(card_1, card_2)]

        elif cards_to_guess == 1:
            for card in range(52):
                if card in (base_cards + excluded_cards): continue
                hand, score = poker.returnHandScore(base_cards + [card])
                probability_table[score] += [card]
        return probability_table
