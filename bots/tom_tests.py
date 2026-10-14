
from pokerbot.cards import hand_strength
import time

start = time.perf_counter()
strength = hand_strength(["6d", "7c"], ["3h", "4c", "5h"])
end = time.perf_counter()
print(f"strength: {strength}%")
print(f"Elapsed: {(end - start):.3f} s")