import re

exclusions = [
    "Senior", "Sr.", "Sr", "Tier 2", "Level 2", "L2", "II", "III", "IV", "Lead", "Leader", "Manager", "Engineer",
    "Director", "Principal", "Architect", "Security Clearance", "Secret Clearance", "Top Secret",
    "TS/SCI", "Clearance Required", "Must be able to obtain clearance"
]



def contains_exclusions(title):
    """Check if the job title contains an excluded term"""
    if any(re.search(rf"\b{re.escape(word)}\b", title, re.I)
            for word in exclusions):
        return True
    return False

