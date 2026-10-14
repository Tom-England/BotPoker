
from pokerbot.cards import hand_strength
import time

start = time.perf_counter()
strenght = hand_strength(["Ad", "Qc"], ["3h", "4c", "Jh"])
end = time.perf_counter()
print(strenght)
print(f"Elapsed: {(end - start):.3f} s")