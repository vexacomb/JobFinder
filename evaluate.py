import re

exclusions = [
    "Senior", "Sr.", "Sr", "Tier 2", "Level 2", "L2", "II", "III", "IV", "Lead", "Leader", "Manager", "Engineer",
    "Director", "Principal", "Architect", "Security Clearance", "Secret Clearance", "Top Secret",
    "TS/SCI", "Clearance Required", "Must be able to obtain clearance"
]



def contains_exclusions(title):
    return any(re.search(rf"(?<!\w){re.escape(word)}(?!\w)", title, re.I)
               for word in exclusions)

