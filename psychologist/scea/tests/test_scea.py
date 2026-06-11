#!/usr/bin/env python3
import unittest
from scea import SCEA
from scea.core.models import EmotionVector, NeurochemicalState, Need
from scea.neurochemistry import NeurochemicalSystem
from scea.needs_engine import NeedsEngine
from scea.emotional_physics import EmotionalPhysicsEngine


class TestSCEACore(unittest.TestCase):
    def test_scea_initialization(self):
        scea = SCEA()
        self.assertIsNotNone(scea.state)
        self.assertEqual(scea.state.step, 0)
        self.assertIsNotNone(scea.state.emotions)
        self.assertIsNotNone(scea.state.neurochemistry)

    def test_scea_single_step(self):
        scea = SCEA()
        initial_step = scea.state.step
        result = scea.step()
        self.assertEqual(scea.state.step, initial_step + 1)
        self.assertIn('neurochemistry', result)
        self.assertIn('emotions', result)
        self.assertIn('decision', result)


class TestNeurochemistry(unittest.TestCase):
    def test_initial_state(self):
        nc = NeurochemicalSystem()
        self.assertGreaterEqual(nc.state.dopamine, 0)
        self.assertLessEqual(nc.state.dopamine, 1)

    def test_update_with_trigger(self):
        nc = NeurochemicalSystem()
        initial_dop = nc.state.dopamine
        nc.update({'reward': 0.8})
        self.assertNotEqual(nc.state.dopamine, initial_dop)


class TestEmotionVector(unittest.TestCase):
    def test_initialization(self):
        ev = EmotionVector()
        self.assertIn('joy', ev.emotions)
        self.assertEqual(ev.emotions['joy'], 0.0)

    def test_dominant_emotion(self):
        ev = EmotionVector()
        ev.emotions['joy'] = 0.8
        self.assertEqual(ev.get_dominant_emotion(), 'joy')


class TestNeedsEngine(unittest.TestCase):
    def test_initialization(self):
        ne = NeedsEngine()
        self.assertIn('knowledge', ne.needs)
        self.assertIn('social', ne.needs)

    def test_pressing_need(self):
        ne = NeedsEngine()
        pressing = ne.get_most_pressing_need()
        self.assertIsInstance(pressing, Need)


if __name__ == '__main__':
    unittest.main()
