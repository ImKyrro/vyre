import secrets
import string

SIGNUP_URL = "https://www.roblox.com/CreateAccount"

_ADJECTIVES = [
    "Swift", "Silent", "Cosmic", "Frost", "Shadow", "Golden", "Crimson", "Lunar",
    "Turbo", "Mighty", "Rapid", "Neon", "Iron", "Solar", "Vivid", "Rogue",
    "Pixel", "Cyber", "Storm", "Blaze", "Echo", "Nova", "Hyper", "Arctic",
]
_NOUNS = [
    "Falcon", "Wolf", "Comet", "Raptor", "Tiger", "Phoenix", "Viper", "Drake",
    "Panther", "Hawk", "Fox", "Bison", "Cobra", "Lynx", "Otter", "Raven",
    "Shark", "Bolt", "Ghost", "Titan", "Ranger", "Pilot", "Nomad", "Rider",
]
_SYMBOLS = "!@#$%"


def random_username() -> str:
    name = secrets.choice(_ADJECTIVES) + secrets.choice(_NOUNS) + str(secrets.randbelow(9000) + 1000)
    return name[:20]


def random_password(length: int = 14) -> str:
    length = max(10, length)
    pools = [string.ascii_uppercase, string.ascii_lowercase, string.digits, _SYMBOLS]
    chars = [secrets.choice(pool) for pool in pools]
    everything = string.ascii_letters + string.digits + _SYMBOLS
    chars += [secrets.choice(everything) for _ in range(length - len(chars))]
    for index in range(len(chars) - 1, 0, -1):
        swap = secrets.randbelow(index + 1)
        chars[index], chars[swap] = chars[swap], chars[index]
    return "".join(chars)


def generate_pairs(count: int) -> list:
    return [(random_username(), random_password()) for _ in range(max(1, count))]
