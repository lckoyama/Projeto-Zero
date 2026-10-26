"""Public case API: four equally likely stories per new investigation."""
import random

from game.case_variants import CASE_REVISION, build_case as build_variant
from game.link_topics import add_link_topics

CASE_IDS = ("link", "usb", "extension", "phishing")

def build_case(case_id="link", revision=CASE_REVISION):
    case = build_variant(case_id, revision)
    add_link_topics(case)
    return case

def choose_case():
    return random.choice(CASE_IDS)
