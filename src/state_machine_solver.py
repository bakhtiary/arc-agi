from multiprocessing import Pool
import traceback
from dataset import Dataset
from llm_utils import HistoryManager, LLMInterface, chat_with_llm
from log_utils import create_empty_log, add_string_to_log

AKGrid = list[list[int]]
AKGridTuple = tuple[tuple[tuple[int]]]

def callable_as_list(obj):
    if isinstance(obj, list):
        return obj
    else:
        assert callable(obj)
        return [obj]
    

def run_single_solver(args):
    try:
        state_machine_factory, task_id, dataset, llm_interface, log_dir, log_file = args
        solver = StateMachineSolver(state_machine_factory, llm_interface)
        return solver(task_id, dataset, log_dir, log_file)
    except Exception as e:
        print(f'Exception: {e}')
        print(traceback.format_exception(e))


class StateMachineFactoryForSingleHypo:
    def __init__(self, state_machine_class, hypo):
        self.state_machine_class = state_machine_class
        self.hypo = hypo

    def __call__(self, task_id, dataset):
        state_machine = self.state_machine_class(task_id, dataset)
        state_machine.hypothesis = self.hypo
        return state_machine

class StateMachineSolverNestedMultiprocessing:
    def __init__(self, state_machine_class, llm_interface: LLMInterface, pool_size=5, num_hypos=10):
        self.state_machine_class = state_machine_class
        self.llm_interface = llm_interface
        self.pool_size = pool_size
        self.num_hypos = num_hypos

    def __call__(self, task_id, dataset: Dataset, log_dir, log_file=None): # --> task_id, dataset, log_file, solutions
        if hasattr(self.state_machine_class, 'get_hypos_prompt'):
            raise ValueError('To use StateMachineSolverNestedMultiprocessing, state machine should have a class method get_hypos')

        temp_state_machine = self.state_machine_class(task_id, dataset)
        meta_log_file = log_dir / task_id / 'meta_log.md'
        hypos = temp_state_machine.get_hypos(self.llm_interface, meta_log_file, num_hypos=self.num_hypos)
    
        all_job_args = [(StateMachineFactoryForSingleHypo(self.state_machine_class, hypo),
                task_id, dataset, self.llm_interface, log_dir, log_dir / task_id / f'{i}.full.md')
            for i, hypo in enumerate(hypos)]
            
        solutions = []
        
        p = None

        def _task_done(result):
            task_id, dataset, log_file, solution = result
            print('/////////////////////////')
            if solution is not None:
                solutions.append(solution)
                if p:
                    p.terminate()

        def _task_error(e):
            print(f'Exception: {e}')
            print(traceback.format_exception(e))
            
        try:
            if self.pool_size == -1:
                for job_args in all_job_args:
                    try:
                        result = run_single_solver(job_args)
                        _task_done(result)
                    except Exception as e:
                        raise e
                        # _task_error(e)
                        pass
            else:
                with Pool(self.pool_size) as p:
                    for job_args in all_job_args:
                        p.apply_async(
                            run_single_solver,
                            args=(job_args,),
                            callback=_task_done,
                            error_callback=_task_error
                        )

                    p.close()
                    p.join()
        except Exception as e:
            print(f'Exception: {e}')
            print(traceback.format_exception(e))
            raise e
        
        return task_id, dataset, meta_log_file, None if len(solutions) == 0 else solutions[0]
 

class StateMachineSolver:
    def __init__(self, state_machine_class, llm_interface: LLMInterface):
        self.state_machine_class = state_machine_class
        self.llm_interface = llm_interface

    def __call__(self, task_id, dataset: Dataset, log_dir, log_file=None): # --> task_id, dataset, log_file, solutions
        # task = dataset.read_task(task_id)
        if log_file is None:
            log_file = log_dir / task_id / f'{1}.full.md'
        create_empty_log(log_file)
        sm_name = getattr(self.state_machine_class, '__name__', f'{self.state_machine_class}')
        add_string_to_log(f'''# Task summary
Task id: {task_id}
Dataset: {dataset.string_encode()}
LLMInterface: {self.llm_interface.get_llms_mapping()}
StateMachine: {sm_name}
\n\n''', log_file)
        print(f'Solving {task_id}: http://127.0.0.1:5000/#{log_dir.parent.name}/{log_dir.name}/{task_id}/{log_file.name}')
        
        cur_state_machine = self.state_machine_class(task_id, dataset)
        cur_state_name = cur_state_machine.start_state
        history_manager = HistoryManager(log_file)
        history_manager.add_singletone_text_message('system', 
            'You are an intelligent assistant and a Python expert.', 'any-llm')

        round_no = -1
        while cur_state_name:            
            print(cur_state_name)
            content = []
            cur_state = cur_state_machine.states[cur_state_name]
            response = None
            if 'pre_work' in cur_state:
                pre_work_funcs = callable_as_list(cur_state['pre_work'])
                for pre_work_func in pre_work_funcs:
                    pre_work_func()
            
            llm = cur_state['llm']() if 'llm' in cur_state else 'vision'
            any_message_sent = False
            if 'message_to_send' in cur_state:
                round_no += 1
                any_message_sent = self.add_state_machine_messages(
                    cur_state['message_to_send'], llm, history_manager, tst=round_no)                
                response = chat_with_llm(self.llm_interface, history_manager, llm, cur_tst=round_no)
                
                
            if 'do_work' in cur_state:
                do_work_funcs = callable_as_list(cur_state['do_work'])
                for do_work_func in do_work_funcs:
                    do_work_func(response)

            # if 'message_to_send' in cur_state:
                # We Don't want this: we want a **moving** windows, such as a queue
                # if 'keep_last_pair_of_messages' in cur_state:
                #     if not cur_state['keep_last_pair_of_messages']():
                #         if any_message_sent:
                #             history_manager.pop_messages(2)
                #         else:
                #             history_manager.pop_messages(1)

            if 'message_to_send' in cur_state:
                if 'message_ttl' in cur_state:
                    # TODO: include ttl in log
                    one_before_last_ttl, last_ttl = cur_state['message_ttl']()
                    if any_message_sent:
                        history_manager.set_ttl_last_pair(one_before_last_ttl, last_ttl)
                    else:
                        history_manager.set_ttl_last_elem(last_ttl)
                        
            next_state_name = cur_state['next_state']
            if next_state_name is None or isinstance(next_state_name, str):
                cur_state_name = next_state_name
            else:
                cur_state_name = next_state_name(response)

        add_string_to_log(f"state machine finished, result is {cur_state_machine.solution}\n", log_file)

        return task_id, dataset, log_file, cur_state_machine.solution

    def add_state_machine_messages(self, cur_state_messages, llm: str, history_manager: HistoryManager, tst=None):
        any_message_added = False
        with history_manager.start_new_message('user', llm, tst=tst):                    
            state_message_funcs = callable_as_list(cur_state_messages)
            for state_message_func in state_message_funcs:
                state_message_ret = state_message_func()
                if isinstance(state_message_ret, tuple):
                    state_message_type, state_message = state_message_ret
                else:
                    state_message_type, state_message = 'text', state_message_ret
                        
                assert state_message_type in ['image', 'text', 'list']
                if state_message_type == 'image':
                    history_manager.add_image(state_message)
                    any_message_added = True
                elif state_message_type == 'text':
                    history_manager.add_text(state_message)
                    any_message_added = True
                elif state_message_type == 'list': # state_message itself is a list of tuples
                    for state_message_type, state_message  in state_message:
                        assert state_message_type in ['image', 'text']
                        if state_message_type == 'image':
                            history_manager.add_image(state_message)
                            any_message_added = True
                        elif state_message_type == 'text':
                            history_manager.add_text(state_message)
                            any_message_added = True
        
        return any_message_added