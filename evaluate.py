import re
from config import load

config = load()
exclusions = config["exclusions"]


def contains_exclusions(title):
    return any(re.search(rf"(?<!\w){re.escape(word)}(?!\w)", title, re.I)
               for word in exclusions)

