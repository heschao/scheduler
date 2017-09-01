from pulp import allcombinations

n_shows = 10
max_shows_per_day = 3
shows = list(range(n_shows))
print('allcombinations')
combinations = [c for c in allcombinations(shows, max_shows_per_day)]
print(len(combinations))
