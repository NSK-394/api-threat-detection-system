<<<<<<< HEAD
from collections import defaultdict, deque

score_history = defaultdict(lambda: deque(maxlen=100))

def add_score(api_key, score):
    score_history[api_key].append(score)
=======
from collections import defaultdict, deque

score_history = defaultdict(lambda: deque(maxlen=100))

def add_score(api_key, score):
    score_history[api_key].append(score)
>>>>>>> 9bb96fc1704738af7cb1e060a1c04464eba38937
