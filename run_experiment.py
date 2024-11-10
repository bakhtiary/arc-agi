# Todo:
#   Test
#   Add A critic/summarizer LLM
#   Add tools (like shape counts, etc), sp. based on another LLMs recommendation (similar to RAG)
#   Run python function in a seperate process for a limitted amount of time

from datetime import datetime
from pathlib import Path
import warnings

from llm_utils import LiteLLMInterface
warnings.filterwarnings('ignore', category=UserWarning, module='pydantic.main')
from dotenv import load_dotenv
load_dotenv('.secrets')

import litellm
litellm.drop_params=True

from dataset import LocalDataset, KaggleDataset
from experimenter import experiment

from state_machine_solver import StateMachineSolver
from state_machine_multi_solver import StateMachineMultiSolver, StateMachineSolverWithRestart

from simple_state_machine_distinct_pairs import SimpleStateMachineDistinctPairs
from simple_state_machine_distinct_pairs_with_tools import SimpleStateMachineDistinctPairswithTools

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
    result = SimpleStateMachineDistinctPairswithTools(task_id, dataset, which_pairs='all')
    result.max_num_failed = 1
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
    t1 = ['c8f0f002','952a094c'] # very easy, very hard
    t1_easy = ['c8f0f002'] # the easy
    t1_hard = ['952a094c'] # o1 experiments, the hard


    t_is_hole = ['b2862040']
    t_order_bars_by_color = ['beb8660c']
    
    hard_ids = ['beb8660c', '72ca375d', '82819916', 'b2862040', '846bdb03', '855e0971', '05269061', '72322fa7', 
        '56dc2b01', '6d75e8bb']
    average_ids = ['91714a58', '50cb2852', 'a61f2674', '85c4e7cd', 'd0f5fe59', '49d1d64f', 'b60334d2', 'd511f180', 
        'e98196ab', '56ff96f3']
    simple_ids = ['623ea044', '4347f46a', 'd4a91cb9', '913fb3ed', 'd631b094']
    super_simple_ids = ['ce22a75a', 'c8f0f002']
    pre_dealine_mix = hard_ids + average_ids + simple_ids + super_simple_ids
    
    tX = ['50cb2852'] #jsonl error at http://127.0.0.1:5000/#logs/20241106-201845/50cb2852/1.full.md
    
    for_dsl = ['beb8660c', '85c4e7cd', 'a2fd1cf0']

    task_ids = t1_easy
    # task_ids = pre_dealine_mix
    # task_ids = t_order_bars_by_color
    # task_ids = pre_dealine_mix

    # task_ids = ['ce22a75a'] # uses lens code alot
    # md analysis by amir --> ff28f65a
    # task_ids = ['c8f0f002', '623ea044', 'a2fd1cf0', 'd4a91cb9', 'ce22a75a', '23581191', '913fb3ed', 'b1948b0a',
    #             'b6afb2da', '27a28665', '4258a5f9', 'e9afcf9a', 'd23f8c26', '42a50994','ea786f4a', '91714a58', '4be741c5', '50cb2852', '5582e5ca', 'a61f2674', '85c4e7cd', 'd0f5fe59',
    #              'd364b489', '49d1d64f', 'd511f180', '56ff96f3', '6f8cd79b', 'd4469b4b', '5614dbcf', 'aedd82e4',
    #              'c9f8e694', '445eab21', '68b16354', 'bda2d7a6', 'a699fb00', 'a416b8f3', 'bdad9b1f', 'e9614598',
    #              'f25ffba3', '253bf280', '3618c87e', '1cf80156', '2dee498d', 'bb43febb', 'd631b094', 'dc1df850',
    #              'a9f96cdd','72ca375d', '82819916', 'b2862040', '846bdb03', '855e0971', '05269061', '72322fa7', '6d75e8bb',
    #           '67385a82', '36d67576', '6d0160f0', '4938f0c2', '746b3537', 'dc433765', '8efcae92', '1e32b0e9',
    #           '6430c8c4', '5521c0d9', 'a64e4611', 'c9e6f938', '9ecd008a', '1f85a75f', '3de23699', '54d9e175',
    #           '7ddcd7ec', 'b27ca6d3', '6aa20dc0', 'b527c5c6', '25ff71a9', '6e02f1e3', 'c1d99e64', '97a05b5b']
    # task_ids = ['dc1df850', '49d1d64f', 'bb43febb']
    # task_ids = ['ce22a75a', '49d1d64f']
    
    # task_ids = ['4258a5f9', '5582e5ca', '623ea044', '913fb3ed', '445eab21', 'd4a91cb9','23581191', 'e9afcf9a'
    #             'd364b489', '68b16354', 'd631b094', 'a2fd1cf0', '4347f46a', '4be741c5', 'd23f8c26', '42a50994',
    #             'a416b8f3', '3618c87e', 'ea786f4a', 'aabf363d', 'b6afb2da', 'bdad9b1f', 'a699fb00', '50cb2852', '49d1d64f', 'b60334d2', 'aedd82e4',
    # '1f876c06', '5614dbcf', 'be94b721', '91714a58', 'f25ffba3', 'c9f8e694',
    # 'd0f5fe59', '56ff96f3', 'a9f96cdd', '253bf280', '2dee498d', 'a61f2674',
    # 'e98196ab', '85c4e7cd', 'a740d043', '6f8cd79b', '1cf80156', 'dc1df850',
    # 'd511f180', 'bb43febb', '27a28665', '44f52bb0', 'e9614598', 'bda2d7a6', 'd4469b4b'
    #             ] # the ones with a 'signal' what ever that means!
    
    llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='o1-mini')
    
    # state_machine_solver = StateMachineSolver(SimpleStateMachineOneState)
    # state_machine_solver = StateMachineSolver(SimpleStateMachineWithO1)
    # state_machine_solver = StateMachineSolver(SimpleStateMachineWithRestart)
    # state_machine_solver = StateMachineSolver(SimpleStateMachineDistinctPairs)

    # state_machine_solver = StateMachineMultiSolver([
    #     SimpleStateMachineAllInOne, SimpleStateMachineSinglePair])
    

    state_machine_solver = StateMachineSolverWithRestart(SimpleStateMachineDistinctPairswithTools_factory, llm_interface, num_restarts=1)
    # state_machine_solver = StateMachineSolver(SimpleStateMachineDistinctPairswithTools)
    
    dataset = LocalDataset('training')
    
    experiment(state_machine_solver, task_ids, dataset, LOG_DIR, pool_size=6)


if __name__ == '__main__':
    kaggle_main()
    # local_main()