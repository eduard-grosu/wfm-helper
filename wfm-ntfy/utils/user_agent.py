import random


USER_AGENTS = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows; Windows NT 10.1; WOW64; en-US) Gecko/20100101 Firefox/52.8',
    'Mozilla/5.0 (Windows NT 10.4; x64) AppleWebKit/601.14 (KHTML, like Gecko) Chrome/47.0.2017.243 Safari/537.1 Edge/11.60737'
)


def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)
