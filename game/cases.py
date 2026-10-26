"""Public case API: four equally likely stories per new investigation."""
import random

from game.case_variants import CASE_REVISION, build_case

CASE_IDS = ("link", "usb", "extension", "phishing")

def choose_case():
    return random.choice(CASE_IDS)
