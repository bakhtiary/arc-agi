from datetime import datetime
import unittest
from pathlib import Path
from unittest.mock import Mock

import litellm

from simple_lens_state_machine import SimpleLensStateMachine
from state_machine_solver import StateMachineSolver

LOG_DIR = Path('tmp') / datetime.now().strftime('%Y%m%d-%H%M%S')

class StateMachineSolverTest(unittest.TestCase):

    def setUp(self):
        self.llm_wrapper_mock = Mock(litellm)
        self.sms = StateMachineSolver(SimpleLensStateMachine, llm_wrapper=self.llm_wrapper_mock)

    def testCallWorks(self):
        self.llm_wrapper_mock.completion.return_value = "yes hassan"
        self.sms.__call__("c8f0f002", "training", 5, LOG_DIR, "hassan")
