
from pokerbot.cards import hand_strength
import time

from multiprocessing import Process, Queue
from random import randint

if __name__ == '__main__':
    start = time.perf_counter()
    strength = hand_strength(["6d", "7c"], ["3h", "4c", "5h"])
    end = time.perf_counter()
    print(f"strength: {strength}%")
    print(f"Elapsed: {(end - start):.3f} s")


"""
def test(input,output):
    id = randint(0,100000)

    output.put([
        [id,0,0],
        [0,0,0],
        [0,0,id]
    ])

if __name__ == '__main__':
    thread_pool = []

    task_queue = Queue()
    done_queue = Queue()

    for i in range(0,10):
        p = Process(target=test, args=(task_queue,done_queue))
        thread_pool.append(p)

    for t in thread_pool:
        t.start()

    for t in thread_pool:
        t.join()

    for i in range(0,10):
        print(done_queue.get())

"""