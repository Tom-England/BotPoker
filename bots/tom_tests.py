
from pokerbot.cards import hand_strength
import time

start = time.perf_counter()
strenght = hand_strength(["5s", "4d"], ["As", "2d", "3c"])
end = time.perf_counter()
print(strenght)
print(f"Elapsed: {(end - start):.3f} s")