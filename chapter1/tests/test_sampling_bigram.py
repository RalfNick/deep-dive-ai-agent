from __future__ import annotations

import unittest

import numpy as np

from chapter1.bigram_lm import CORPUS, generate, train
from chapter1.sampling_demo import LOGITS, softmax


def entropy(probabilities: np.ndarray) -> float:
    """Return Shannon entropy for a strictly positive toy distribution."""
    return -float(np.sum(probabilities * np.log(probabilities)))


class TemperatureTest(unittest.TestCase):
    def test_temperature_must_be_positive(self) -> None:
        for temperature in (0.0, -1.0):
            with self.subTest(temperature=temperature):
                with self.assertRaises(ValueError):
                    softmax(LOGITS, temperature)

    def test_higher_temperature_increases_entropy_for_fixed_logits(self) -> None:
        cold = softmax(LOGITS, 0.5)
        hot = softmax(LOGITS, 2.0)

        self.assertGreater(entropy(hot), entropy(cold))


class BigramTest(unittest.TestCase):
    def test_generation_is_reproducible_for_a_fixed_seed(self) -> None:
        transitions = train(CORPUS)

        first = generate(transitions, max_new_chars=120, seed=7)
        second = generate(transitions, max_new_chars=120, seed=7)

        self.assertEqual(first, second)
        self.assertLessEqual(len(first), 120)


if __name__ == "__main__":
    unittest.main()
