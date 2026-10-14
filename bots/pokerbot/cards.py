"""
Card helpers.

A card is a 2-character string: rank then suit.
    "As" = Ace of spades, "Td" = Ten of diamonds, "2c" = Two of clubs

Ranks: 2 3 4 5 6 7 8 9 T J Q K A
Suits: c (clubs), d (diamonds), h (hearts), s (spades)
"""
from collections import Counter
import itertools
from multiprocessing import Process, Queue
from math import ceil

RANKS = "23456789TJQKA"
RANK_NAMES = {"2": "Two", "3": "Three", "4": "Four", "5": "Five", "6": "Six",
              "7": "Seven", "8": "Eight", "9": "Nine", "T": "Ten", "J": "Jack",
              "Q": "Queen", "K": "King", "A": "Ace"}
SUIT_NAMES = {"c": "Clubs", "d": "Diamonds", "h": "Hearts", "s": "Spades"}

# Hand types from weakest to strongest
HAND_TYPES = ["High card", "Pair", "Two pair", "Three of a kind", "Straight",
              "Flush", "Full house", "Four of a kind", "Straight flush"]

AHEAD = 0
TIED = 1
BEHIND = 2

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

def gen_possible_rivers (my_cards: list[str], board: list[str], case: list[str]) -> str:
    remaining_cards = get_oppcards(my_cards, board)
    for card in case:
        remaining_cards.remove(card)
    remaining_river_endings = list(itertools.combinations(remaining_cards, 5 - len(board)))
    remaining_rivers = [board + list(a) for a in remaining_river_endings]
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

def resolve_high_card_ties(my_cards: list[str], case: list[str]) -> int:
    index = -1

    player_ranks = [rank(my_cards[0]),rank(my_cards[1])]
    opp_ranks = [rank(case[0]),rank(case[1])]
    player_max_rank = max(player_ranks)
    opp_max_rank = max(opp_ranks)
    if player_max_rank > opp_max_rank:
        index = AHEAD
    elif player_max_rank == opp_max_rank:
        player_min_rank = min(player_ranks)
        opp_min_rank = min(opp_ranks)
        if player_min_rank > opp_min_rank:
            index = AHEAD
        elif player_min_rank == opp_min_rank:
            index = TIED
        else:
            index = BEHIND
    else:
        index = BEHIND
    return index

def possible_river_thread_calc(work_queue: Queue, done_queue: Queue):
    for (my_cards, case, rivers, index) in iter(work_queue.get, "STOP"):
        tempHP = [
            [0,0,0],
            [0,0,0],
            [0,0,0]
        ]
        for river in rivers:
            ourbest = hand_type(my_cards + river)
            oppbest = hand_type(case + river)
            if (ourbest > oppbest):
                tempHP[index][AHEAD] += 1
            elif (ourbest == oppbest):
                index2 = resolve_high_card_ties(my_cards, case)
                tempHP[index][index2] += 1
            else:
                tempHP[index][BEHIND] += 1
        done_queue.put(tempHP)
           


def chunk(list: list[str], n: int) -> list[list[str]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(list), n):
        yield list[i:i + n]

def hand_potential(my_cards: list[str], board: list[str]) -> float:

    
    THREAD_COUNT = 10

    HP = [
        [0,0,0],
        [0,0,0],
        [0,0,0]
	]
    HPTotal = [0,0,0]
    ourrank = hand_type(my_cards + board)
    oppcards = get_oppcards(my_cards, board)

    index = AHEAD

    
    i = 0
    j = 0
    opphands = list(gen_opphand(oppcards))

    work_queue = Queue()
    done_queue = Queue()

    thread_pool = []
    #RIVER_THREAD_DICTIONARY = {}
    for c in range(THREAD_COUNT):
        t = Process(target=possible_river_thread_calc, args=(work_queue, done_queue))
        thread_pool.append(t)
    for t in thread_pool:
        t.start()

    for case in opphands:
        i += 1
        j = 0
        opprank = hand_type(list(case) + board)
        if (ourrank > opprank):
            index = AHEAD
        elif (ourrank == opprank):
            index = resolve_high_card_ties(my_cards, list(case))
        else:
            index = BEHIND
        HPTotal[index] += 1
        #print(f"{i}/{len(opphands)} - {j}/{len(possible_rivers)}")
        
        possible_rivers = gen_possible_rivers(my_cards, board, list(case))
        #print(f"{len(possible_rivers)}")
        river_chunks = chunk(possible_rivers, ceil(len(possible_rivers) / THREAD_COUNT))

        for rchunk in river_chunks:
            work_queue.put((my_cards, list(case), rchunk, index))

#my_cards, list(case), c, index,
        #print(RIVER_THREAD_DICTIONARY)
        #print(f"Found {len(RIVER_THREAD_DICTIONARY.keys())} keys")
        for thread in thread_pool:
            result = done_queue.get()

            HP[0][0] += result[0][0]
            HP[1][0] += result[1][0]
            HP[2][0] += result[2][0]

            HP[0][1] += result[0][1]
            HP[1][1] += result[1][1]
            HP[2][1] += result[2][1]

            HP[0][2] += result[0][2]
            HP[1][2] += result[1][2]
            HP[2][2] += result[2][2]

        """
        for river in possible_rivers:
            j+=1
            ourbest = hand_type(my_cards + river)
            oppbest = hand_type(list(case) + river)
            if (ourbest > oppbest):
                HP[index][AHEAD] += 1
            elif (ourbest == oppbest):
                index2 = resolve_high_card_ties(my_cards, list(case))
                HP[index][index2] += 1
            else:
                HP[index][BEHIND] += 1
        """

    print (HP)
    print (HPTotal)
    for t in thread_pool:
        work_queue.put("STOP")
    for t in thread_pool:
        t.join()

    p_pot = ((HP[BEHIND][AHEAD] + (HP[BEHIND][TIED] / 2) + (HP[TIED][AHEAD] / 2)) / (HPTotal[BEHIND] + HPTotal[TIED])) / 1000
    n_pot = ((HP[AHEAD][BEHIND] + (HP[TIED][BEHIND] / 2) + (HP[AHEAD][TIED] / 2)) / (HPTotal[AHEAD] + HPTotal[TIED])) / 1000

    return [p_pot, n_pot]

def hand_strength(my_cards: list[str], board: list[str]) -> float:
    [p_pot, n_pot] = hand_potential(my_cards, board)
    HS = local_hand_strength (my_cards, board)

    print(f"HS = {HS}, p_pot = {p_pot}, n_pot = {n_pot}")
	
    return (HS * (1-n_pot)) + ((1-HS) * p_pot)