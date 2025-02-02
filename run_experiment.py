from datetime import datetime
from pathlib import Path
import warnings

from llm_utils import LLMInterface
from simple_state_machine_with_tools_and_larc import SimpleStateMachineWithToolsAndLarc
from simple_state_machine_with_tools_and_lens_2 import SimpleStateMachineWithToolsAndLens2
from simple_state_machine_with_tools_and_lens_3 import SimpleStateMachineWithToolsAndLens3
from simple_state_machine_with_tools_and_lens_4 import SimpleStateMachineWithToolsAndLens4
warnings.filterwarnings('ignore', category=UserWarning, module='pydantic.main')

import litellm
litellm.drop_params=True

from dotenv import load_dotenv
load_dotenv('.secrets', verbose=True)

from litellm_interface import LiteLLMInterface

from dataset import LocalDataset, KaggleDataset
from experimenter import experiment

from state_machine_solver import StateMachineSolver
from state_machine_multi_solver import StateMachineMultiSolver, StateMachineSolverWithRestart

from simple_state_machine_distinct_pairs import SimpleStateMachineDistinctPairs
from simple_state_machine_distinct_pairs_with_tools import SimpleStateMachineDistinctPairsWithTools

from simple_lens_state_machine import SimpleLensStateMachine
from simple_state_machine_all_in_one import SimpleStateMachineAllInOne
from simple_state_machine_single_pair import SimpleStateMachineSinglePair
from simple_state_machine_one_state import SimpleStateMachineOneState
from simple_state_machine_with_restart import SimpleStateMachineWithRestart
from simple_state_machine_with_o1 import SimpleStateMachineWithO1


LOG_DIR = Path('logs') / datetime.now().strftime('%Y%m%d-%H%M%S')

def crappy_solve(task_id, dataset, log_dir):
    print('crap')
    return task_id, dataset, log_dir, []

# No lambda because --> Can't pickle <function <lambda> at ...
# Not local to local_main because --> Can't pickle local object 'local_main.<locals>.factory'
def SimpleStateMachineDistinctPairswithTools_factory(task_id, dataset):
    result = SimpleStateMachineDistinctPairsWithTools(task_id, dataset, which_pairs='all')
    result.max_num_failed = 10
    return result

def SimpleStateMachineWithToolsAndLens2_factory(task_id, dataset):
    result = SimpleStateMachineWithToolsAndLens2(task_id, dataset, which_pairs='all')
    result.max_num_failed = 20
    # text-advanced prevents the images being passed to the llm
    # result.states['ask_for_code']['llm'] = lambda: LLMInterface.VISION
    # result.states['mapping_code_failed']['llm'] = lambda: LLMInterface.VISION
    return result

def SimpleStateMachineWithToolsAndLens3_factory(task_id, dataset):
    result = SimpleStateMachineWithToolsAndLens3(task_id, dataset, which_pairs='all')
    result.max_num_failed = 20
    # text-advanced prevents the images being passed to the llm
    # result.states['ask_for_code']['llm'] = lambda: LLMInterface.VISION
    # result.states['mapping_code_failed']['llm'] = lambda: LLMInterface.VISION
    return result

def SimpleStateMachineWithToolsAndLens4_factory(task_id, dataset):
    result = SimpleStateMachineWithToolsAndLens4(task_id, dataset, which_pairs='all')
    result.max_num_failed = 10
    # text-advanced prevents the images being passed to the llm
    # result.states['ask_for_code']['llm'] = lambda: LLMInterface.VISION
    # result.states['mapping_code_failed']['llm'] = lambda: LLMInterface.VISION
    return result

def SimpleStateMachineWithToolsAndLarc_factory(task_id, dataset):
    result = SimpleStateMachineWithToolsAndLarc(task_id, dataset, which_pairs='all')
    result.max_num_failed = 10
    # text-advanced prevents the images being passed to the llm
    # result.states['ask_for_code']['llm'] = lambda: LLMInterface.VISION
    # result.states['mapping_code_failed']['llm'] = lambda: LLMInterface.VISION
    return result

def kaggle_main():
    from local_llm_interface import QwenLocalLLMInterface
 
    llm_interface = QwenLocalLLMInterface(timeout_seconds=1)

    state_machine_solver = StateMachineSolverWithRestart(SimpleStateMachineDistinctPairswithTools_factory, llm_interface, num_restarts=1)

    dataset = LocalDataset('training')
    # dataset = KaggleDataset('arc-agi_test_challenges.json', 'data/kaggle')

    task_ids = dataset.get_all_task_ids()
    t1_easy = ['c8f0f002'] # the easy

    task_ids = task_ids[:10]

    experiment(state_machine_solver, task_ids, dataset, LOG_DIR, pool_size=6, timeout_seconds=10)


def local_main():
    # DeepSeek-R1-Q4_K_M
    # llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='llama.cpp/deepseek/deepseek-reasoner/DeepSeek-R1-GGUF/DeepSeek-R1-UD-IQ1_S/')
    # llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='deepseek/deepseek-reasoner')
    # llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='fireworks/accounts/fireworks/models/deepseek-r1')
    # llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='o1-mini')
    llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='gpt-4o')
    
    dataset = LocalDataset('training')
    #dataset = LocalDataset('evaluation')

    t1_easy = ['c8f0f002'] # the easy
    t1_hard = ['952a094c'] # o1 experiments, the hard

    hard_ids = ['beb8660c', '72ca375d', '82819916', 'b2862040', '846bdb03', '855e0971', '05269061', '72322fa7', 
        '56dc2b01', '6d75e8bb']
    average_ids = ['91714a58', '50cb2852', 'a61f2674', '85c4e7cd', 'd0f5fe59', '49d1d64f', 'b60334d2', 'd511f180', 
        'e98196ab', '56ff96f3']
    simple_ids = ['623ea044', '4347f46a', 'd4a91cb9', '913fb3ed', 'd631b094']
    super_simple_ids = ['ce22a75a', 'c8f0f002']
    pre_dealine_mix = hard_ids + average_ids + simple_ids + super_simple_ids
    
    at_deadline_ids = ['9def23fe', '6f473927', '00dbd492', '33b52de3', '12eac192', '351d6448', 'e6de6e8f', 'e760a62e', '62ab2642', 'c8b7cc0f', '48131b3c', '4364c1c4', '25094a63', '55783887', '8fbca751', '3490cc26', 'e7a25a18', '90347967', '93c31fbe', '456873bc']
    
    # task_ids = ['c8f0f002']
    task_ids = pre_dealine_mix
    #task_ids = t1_easy # smoke test
    
    state_machine_solver = StateMachineSolverWithRestart(
        SimpleStateMachineWithToolsAndLarc, llm_interface, num_restarts=1)
    
    experiment(state_machine_solver, task_ids, dataset, LOG_DIR, pool_size=6)


if __name__ == '__main__':
    # kaggle_main()
    local_main()