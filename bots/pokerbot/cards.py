"""
Card helpers.

A card is a 2-character string: rank then suit.
    "As" = Ace of spades, "Td" = Ten of diamonds, "2c" = Two of clubs

Ranks: 2 3 4 5 6 7 8 9 T J Q K A
Suits: c (clubs), d (diamonds), h (hearts), s (spades)
"""
from collections import Counter
import itertools

RANKS = "23456789TJQKA"
RANK_NAMES = {"2": "Two", "3": "Three", "4": "Four", "5": "Five", "6": "Six",
              "7": "Seven", "8": "Eight", "9": "Nine", "T": "Ten", "J": "Jack",
              "Q": "Queen", "K": "King", "A": "Ace"}
SUIT_NAMES = {"c": "Clubs", "d": "Diamonds", "h": "Hearts", "s": "Spades"}

# Hand types from weakest to strongest
HAND_TYPES = ["High card", "Pair", "Two pair", "Three of a kind", "Straight",
              "Flush", "Full house", "Four of a kind", "Straight flush"]


def rank(card: str) -> int:
    """The card's rank as a number: 2-10, Jack = 11, Queen = 12, King = 13, Ace = 14.

    >>> rank("As")
    14
    """
    return RANKS.index(card[0]) + 2


def suit(card: str) -> str:
    """The card's suit letter: 'c', 'd', 'h' or 's'."""
    return card[1]


def card_name(card: str) -> str:
    """A readable name, e.g. 'Ace of Spades'."""
    return f"{RANK_NAMES[card[0]]} of {SUIT_NAMES[card[1]]}"


def is_pair(cards: list[str]) -> bool:
    """True if the two cards have the same rank, e.g. ["Kh", "Kd"]."""
    return len(cards) == 2 and rank(cards[0]) == rank(cards[1])


def is_suited(cards: list[str]) -> bool:
    """True if the two cards have the same suit, e.g. ["Ah", "7h"]."""
    return len(cards) == 2 and suit(cards[0]) == suit(cards[1])


def _has_straight(ranks: set[int]) -> bool:
    if 14 in ranks:
        ranks = ranks | {1}          # an Ace can also be low: A-2-3-4-5
    return any(all(r + i in ranks for i in range(5)) for r in range(1, 11))


def hand_type(cards: list[str]) -> int:
    """
    The best hand type you can make from these cards, as an index into
    HAND_TYPES (0 = High card ... 8 = Straight flush).
    Pass in your hole cards plus the board.
    """
    if not cards:
        return 0
    counts = sorted(Counter(rank(c) for c in cards).values(), reverse=True)
    by_suit = Counter(suit(c) for c in cards)
    flush_suit, flush_count = by_suit.most_common(1)[0]
    flush = flush_count >= 5
    straight = _has_straight({rank(c) for c in cards})

    if flush and _has_straight({rank(c) for c in cards if suit(c) == flush_suit}):
        return 8
    if counts[0] == 4:
        return 7
    if counts[0] == 3 and len(counts) > 1 and counts[1] >= 2:
        return 6
    if flush:
        return 5
    if straight:
        return 4
    if counts[0] == 3:
        return 3
    if counts[0] == 2 and len(counts) > 1 and counts[1] == 2:
        return 2
    if counts[0] == 2:
        return 1
    return 0


def describe_hand(my_cards: list[str], board: list[str]) -> str:
    """The name of your best hand so far, e.g. 'Two pair'."""
    return HAND_TYPES[hand_type(my_cards + board)]


def get_oppcards (my_cards: list[str], board: list[str]) -> str:
    split_ranks = [rank for rank in RANKS]
    suits = list(SUIT_NAMES.keys())
    iterations = list(itertools.product(split_ranks,suits))
    total_cards = [a+b for (a,b) in iterations]
    for card in my_cards:
        total_cards.remove(card)
    for card in board:
        total_cards.remove(card)
    #print (f"There are {len(my_cards)} and {len(board)} cards so total cards = {len(total_cards)}")
    return total_cards

def gen_opphand(oppcards):
    return itertools.combinations(oppcards,2)

def gen_possible_rivers (my_cards: list[str], board: list[str]) -> str:
    remaining_cards = get_oppcards(my_cards, board)
    remaining_river_endings = list(itertools.combinations(remaining_cards, 2))
    remaining_rivers = [board + [a, b] for [a, b] in remaining_river_endings]
    return remaining_rivers

def local_hand_strength(my_cards: list[str], board: list[str]) -> float:
    """
    ahead = tied = behind = 0
    ourrank = Rank(ourcards, boardcards)

    for each case(oppcards) {
        opprank = Rank(oppcards, boardcards)
        if (ourrank > opprank) ahead += 1
        else if (ourrank == opprank) tied += 1
        else behind += 1
    }

    handstrength = (ahead + tied / 2) / (ahead + tied + behind)

    return handstrength
    """
    ahead = 0
    tied = 0
    behind = 0

    ourrank = hand_type(my_cards + board)
    oppcards = get_oppcards(my_cards, board)
    
    for case in gen_opphand(oppcards):
        opprank = hand_type(list(case) + board)
        if (ourrank > opprank):
            ahead += 1
        elif (ourrank == opprank):
            tied += 1
        else:
            behind += 1

    hand_strength = (ahead + (tied / 2)) / (ahead + tied + behind)
    return hand_strength

def hand_potential(my_cards: list[str], board: list[str]) -> float:
    AHEAD = 0
    TIED = 1
    BEHIND = 2
    
    HP = [
        [0,0,0],
        [0,0,0],
        [0,0,0]
	]
    HPTotal = [0,0,0]
    ourrank = hand_type(my_cards + board)
    oppcards = get_oppcards(my_cards, board)

    index = AHEAD

    possible_rivers = gen_possible_rivers(my_cards, board)
    i = 0
    j = 0
    opphands = list(gen_opphand(oppcards))
    for case in opphands:
        i += 1
        j = 0
        opprank = hand_type(list(case) + board)
        if (ourrank > opprank):
            index = AHEAD
        elif (ourrank == opprank):
            player_max_rank = max(rank(my_cards[0]),rank(my_cards[1]))
            opp_max_rank = max(rank(case[0]),rank(case[1]))
            if player_max_rank > opp_max_rank:
                index = AHEAD
            elif player_max_rank == opp_max_rank:
                if min(rank(my_cards[0]),rank(my_cards[1])) > min(rank(case[0]),rank(case[1])):
                    index = AHEAD
                elif min(rank(my_cards[0]),rank(my_cards[1])) == min(rank(case[0]),rank(case[1])):
                    index = TIED
                else:
                    index = BEHIND
            else:
                index = BEHIND
        else:
            index = BEHIND
        HPTotal[index] += 1
        #print(f"{i}/{len(opphands)} - {j}/{len(possible_rivers)}")
        """
        for river in possible_rivers:
            j+=1
            
            possible = True
            for card in river: 
                if card in case or card in my_cards:
                    possible = False 
            if possible:
                ourbest = hand_type(my_cards + river)
                oppbest = hand_type(list(case) + river)
                if (ourbest > oppbest):
                    HP[index][AHEAD] += 1
                elif (ourbest == oppbest):
                    HP[index][TIED] += 1
                else:
                    HP[index][BEHIND] += 1"""
                    

    print (HP)
    print (HPTotal)

    p_pot = (HP[BEHIND][AHEAD] + (HP[BEHIND][TIED] / 2) + (HP[TIED][AHEAD] / 2)) / (HPTotal[BEHIND] + HPTotal[TIED])
    n_pot = (HP[AHEAD][BEHIND] + (HP[TIED][BEHIND] / 2) + (HP[AHEAD][TIED] / 2)) / (HPTotal[AHEAD] + HPTotal[TIED])

    return [p_pot, n_pot]

def hand_strength(my_cards: list[str], board: list[str]) -> float:
    [p_pot, n_pot] = hand_potential(my_cards, board)
    HS = local_hand_strength (my_cards, board)

    print(f"HS = {HS}, p_pot = {p_pot}, n_pot = {n_pot}")
	
    return (HS * (1-n_pot)) + ((1-HS) * p_pot)