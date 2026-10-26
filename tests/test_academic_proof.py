"""Provas de cada história e rejeição de premissas ou regras adulteradas."""
import unittest
from copy import deepcopy
from pathlib import Path

from game.academic_proof import build_proof, proof_text, verify_proof
from game.cases import CASE_IDS, build_case


class AcademicProofTests(unittest.TestCase):
    def test_exported_slide_texts_match_current_cases(self):
        root = Path(__file__).resolve().parent.parent
        for case_id in CASE_IDS:
            self.assertEqual((root / "docs" / "provas" / f"{case_id}.txt").read_text(encoding="utf-8"),
                             proof_text(build_case(case_id)))

    def test_ten_grounded_propositions_and_checked_steps_in_all_stories(self):
        for revision in (1, 2):
            for case_id in CASE_IDS:
                with self.subTest(case=case_id, revision=revision):
                    case = build_case(case_id, revision)
                    proof = build_proof(case)
                    self.assertEqual(set(proof["definitions"]), set("ABCDEFGHIJ"))
                    self.assertTrue(verify_proof(case, proof))
                    reports = {item["id"]: item["text"] for item in case["evidence"]}
                    for premise in proof["premises"]:
                        self.assertTrue(premise["sources"])
                        for source, quote in premise["quotes"].items():
                            self.assertEqual(quote, reports[source])
                    text = proof_text(case)
                    for rule in ("Modus Ponens", "Modus Tollens", "De Morgan", "conjunção"):
                        self.assertIn(rule, text)

    def test_rejects_invented_premises_wrong_rules_and_foreign_cases(self):
        case = build_case("link")
        proof = build_proof(case)
        forged = deepcopy(proof)
        forged["premises"][0]["expression"] = "B"
        self.assertFalse(verify_proof(case, forged))
        forged = deepcopy(proof)
        forged["steps"][0]["rule"] = "Modus Tollens"
        self.assertFalse(verify_proof(case, forged))
        forged = deepcopy(proof)
        forged["steps"][0]["refs"] = [14]
        self.assertFalse(verify_proof(case, forged))
        self.assertFalse(verify_proof(build_case("usb"), proof))

    def test_current_cases_do_not_claim_a_malicious_phone_in_other_stories(self):
        for case_id in CASE_IDS:
            case = build_case(case_id)
            browser = next(e for e in case["evidence"] if e["id"] == "browser")["text"]
            if case_id == "link":
                self.assertIn("malicioso", browser)
            else:
                self.assertIn("legítimo", browser)
                self.assertIn("Não houve captura de credenciais", next(e for e in case["evidence"] if e["id"] == "credentials")["text"])
            if case_id == "phishing":
                proof = build_proof(case)
                self.assertIn("notebook", proof["definitions"]["C"])
                self.assertEqual(proof["premises"][2]["sources"], ["laptop"])
