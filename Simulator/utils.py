# utils.py
import math
import random
from datetime import date, timedelta

def hour_of_day(env):
    return (env.now / 60) % 24

def day_of_year(env, start_day):
    return start_day + int(env.now / (60 * 24))

def season_from_day(day):
    if 80 <= day < 172:
        return "Spring"
    if 172 <= day < 264:
        return "Summer"
    if 264 <= day < 355:
        return "Fall"
    return "Winter"

def daily_cloud_coverage(season_probs):
    categories = [
        random.uniform(0.0, 0.2),
        random.uniform(0.2, 0.6),
        random.uniform(0.6, 0.8),
        random.uniform(0.8, 0.9),
    ]
    return random.choices(categories, weights=season_probs, k=1)[0]
