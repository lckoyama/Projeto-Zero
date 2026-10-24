"""Testes do motor de lógica proposicional, independentes do Pygame."""
import unittest

from game.logic import counterexamples, entails, equivalent, evaluate, truth_table
from game.puzzles import PUZZLES, validate


class LogicTests(unittest.TestCase):
    def test_connective_tables(self):
        columns = {
            "and": [True, False, False, False],
            "or": [True, True, True, False],
            "implies": [True, False, True, True],
            "iff": [True, False, False, True],
        }
        for operator, expected in columns.items():
            with self.subTest(operator=operator):
                self.assertEqual(
                    [result for _, result in truth_table((operator, "P", "Q"))],
                    expected,
                )
        self.assertEqual(
            [result for _, result in truth_table(("not", "P"))],
            [False, True],
        )

    def test_modus_ponens_and_modus_tollens(self):
        self.assertTrue(entails(["P", ("implies", "P", "Q")], "Q"))
        self.assertTrue(entails(
            [("implies", "P", "Q"), ("not", "Q")], ("not", "P")
        ))

    def test_invalid_inferences(self):
        self.assertEqual(
            counterexamples([("implies", "P", "Q"), "Q"], "P"),
            [{"P": False, "Q": True}],
        )
        self.assertFalse(entails(
            [("implies", "P", "Q"), ("not", "P")], ("not", "Q")
        ))
        self.assertFalse(entails(["Earlier"], "Caused"))

    def test_equivalences(self):
        self.assertTrue(equivalent(
            ("not", ("and", "P", "Q")),
            ("or", ("not", "P"), ("not", "Q")),
        ))
        self.assertTrue(equivalent(
            ("implies", "P", "Q"), ("or", ("not", "P"), "Q")
        ))
        self.assertFalse(equivalent(("or", "P", "Q"), ("and", "P", "Q")))

    def test_constants_and_empty_premises(self):
        self.assertEqual(truth_table(True), [({}, True)])
        self.assertTrue(entails([], ("or", "P", ("not", "P"))))
        self.assertFalse(entails([], "P"))
        # Na lógica clássica, premissas inconsistentes não têm modelo.
        self.assertTrue(entails(["P", ("not", "P")], "Q"))

    def test_invalid_input(self):
        for expression in [("and", "P"), ("xor", "P", "Q"), (), 1]:
            with self.assertRaises(ValueError):
                truth_table(expression)
        with self.assertRaises(ValueError):
            evaluate("P", {"P": 1})
        with self.assertRaises(KeyError):
            evaluate("P", {})

    def test_each_puzzle_has_one_valid_answer(self):
        for puzzle in PUZZLES:
            with self.subTest(title=puzzle["title"]):
                answers = [validate(puzzle, index)[0]
                           for index in range(len(puzzle["options"]))]
                self.assertEqual(sum(answers), 1)


if __name__ == "__main__":
    unittest.main()
