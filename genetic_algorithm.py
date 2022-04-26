import os
import random
import time
from multiprocessing import Process
from operator import attrgetter

import neat


class Game:

    def __init__(self):
        self.player = Player(self)
        self.house = House(self)
        self.score = [0, 0]  # (Wins, Losses)
        self.deck = []
        self.turns = 0
        self.reset = False
        self.reset_game()

    def run(self):
        if not self.reset:
            self.update_totals()
            self.check_state()
        else:
            self.reset_game()

    def check_state(self):
        if self.house.total > 21:
            # print('You win!')
            self.score[0] += 1
            self.house.reveal()
            self.reset = True
        if self.player.total > 21:
            # print('You busted!')
            self.score[1] += 1
            self.house.reveal()
            self.reset = True
        if self.player.total == 21:
            # print('Blackjack!')
            self.player.stand = True
            self.house.reveal()
        if self.player.stand:
            house_cards = self.house.cards
            cards = self.player.cards
            house_cards[1].flip()
            diff = len(cards) - len(house_cards)
            if diff != 0:
                while self.house.total < 17:
                    self.house.hit(1)
                # if self.house.total < 21:
                # print('House stands')
            else:
                while self.house.total < self.player.total:
                    self.house.hit(1)
            if self.player.total < self.house.total <= 21 and self.player.total != 21:
                # print('You lose!')
                self.score[1] += 1
                self.reset = True
            else:
                if self.player.total == self.house.total:
                    # print('Tie!')
                    self.reset = True
                else:
                    # print('You win!')
                    self.score[0] += 1
                    self.reset = True

    def update_totals(self):
        self.player.total = get_sum(self.player.cards)
        self.house.total = get_sum(self.house.cards)
        if len(self.deck) == 0:
            self.shuffle_deck()

    def reset_game(self):
        # print(f'Your cards: {self.player.cards} {self.player.total}')
        # print(f'House cards: {self.house.cards} {self.house.total}')
        self.init_cards()
        # print(f'Score: {self.score}')
        # screen.blit(bg, (0, 0))
        self.player.stand = False
        self.reset = False

    def shuffle_deck(self):
        for suit in range(0, 4):
            for value in range(0, 13):
                self.deck.append(Card(value + 1, suit + 1))

    def init_cards(self):
        self.house.cards.clear()
        self.player.cards.clear()
        if len(self.deck) == 0:
            self.shuffle_deck()
        self.house.hit(2)
        self.house.cards[1].flip()
        self.player.hit(2)


class Player:

    def __init__(self, game):
        self.cards = []
        self.game = game
        self.stand = False
        self.total = 0
        self.score = 0

    def hit(self, amount):
        for i in range(0, amount):
            card = random.choice(self.game.deck)
            self.game.deck.remove(card)
            self.cards.append(card)
            self.game.update_totals()


class House:

    def __init__(self, game):
        self.cards = []
        self.game = game
        self.score = 0
        self.total = 0

    def hit(self, amount):
        for i in range(0, amount):
            card = random.choice(self.game.deck)
            self.game.deck.remove(card)
            self.cards.append(card)
            self.game.update_totals()

    def reveal(self):
        for card in self.cards:
            if card.flipped:
                card.flip()


class Card:
    # 11 = J, 12 = Q, 13 = K, A = 1
    MAX_VALUE = 10

    def __init__(self, value, suit):
        self.value = value
        self.is_face = False
        self.set_suit(suit)
        self.flipped = False
        self.ace = False
        if value > self.MAX_VALUE:
            self.is_face = True
            self.set_face(value)
            self.value = self.MAX_VALUE

        elif value == 1:
            self.ace = True

    def __le__(self, other):
        return self.value <= other.value

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __eq__(self, other):
        if self.is_face and other.is_face:
            return self.face == other.face and self.suit == other.suit
        elif self.is_face or other.is_face:
            return False
        else:
            return self.value == other.value and self.suit == other.suit

    def __repr__(self):
        if self.flipped:
            return 'Flipped'
        if self.is_face:
            return f'{self.face} {self.suit}'
        elif self.value == 1:
            return f'Ace {self.suit}'
        else:
            return f'{self.value} {self.suit}'

    def flip(self):
        self.flipped = not self.flipped

    def set_face(self, value):
        if value == 11:
            self.face = 'Jack'
        elif value == 12:
            self.face = 'Queen'
        elif value == 13:
            self.face = 'King'
        else:
            raise Exception("Value cannot exceed 13!")

    def set_suit(self, suit):
        if suit == 1:
            self.suit = 'Spades'
        elif suit == 2:
            self.suit = 'Clubs'
        elif suit == 3:
            self.suit = 'Diamonds'
        elif suit == 4:
            self.suit = 'Hearts'
        else:
            raise Exception("Wrong suit!")


# Returns the highest possible sum
def get_sum(cards):
    sum1 = sum([card.value for card in cards if not card.ace])
    aces = [card for card in cards if card.ace]
    if len(aces) == 0:
        return sum1
    else:
        sum2 = sum1 + sum([11 for _ in aces])
        sum1 = sum1 + sum([1 for _ in aces])
        if sum2 > 21:
            return sum1
        else:
            return sum2


def main_loop(games, genomes, nets):
    while len(games) > 0:

        best_game = games[0]

        for i, game in enumerate(games):
            game.run()

            # AI stuff

            # AI dies if ratio of losses to wins is greater than 2:1
            if (game.score[0] != 0 and ((game.score[1] / game.score[0] > 2 and game.score[0] + game.score[1] > 50)
                                        or (game.score[1] / game.score[0] > 3 and game.score[0] + game.score[1] > 20))) \
                    or (game.score[0] == 0 and game.score[1] > 8) or game.score[0] + game.score[1] > 100:
                genomes.pop(i)
                nets.pop(i)
                games.pop(i)
            else:
                if game.score[1] != 0:
                    genomes[i].fitness = game.score[0] / (game.score[0] + game.score[1])
                else:
                    genomes[i].fitness = 1

                output = nets[i].activate((game.player.total, game.house.cards[0].value, get_sum(game.deck)))

                if output[0] > 0.5:
                    game.player.hit(1)
                else:
                    game.player.stand = True


gen = 0


def main(genomes=None, config=None):
    global gen
    if config is None:
        config = []
    if genomes is None:
        genomes = []

    games = []
    gen += 1
    nets = []
    ge = []
    for i, g in genomes:
        net = neat.nn.RecurrentNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0
        ge.append(g)
        games.append(Game())
    main_loop(games, ge, nets)


def run():
    local_dir = os.path.dirname(__file__)
    config_file = os.path.join(local_dir, 'strategies/config-feedforward.txt')
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    # p.add_reporter(neat.Checkpointer(5))

    # Run for up to 50 generations.
    winner = p.run(main, 50)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))
    print(f'Win percentage: {winner.fitness * 100}%')





