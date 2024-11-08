from llm_utils import HistoryManager
from log_utils import create_empty_log, add_string_to_log

AKGrid = list[list[int]]
AKGridTuple = tuple[tuple[tuple[int]]]

DEFAULT_LLM='gpt-4o'

class StateMachineSolver:
    def __init__(self,state_machine_class):
        self.state_machine_class = state_machine_class

    def __call__(self, task_id, dataset, log_dir, log_file=None): # --> task_id, dataset, log_file, solutions
        # task = dataset.read_task(task_id)
        if log_file is None:
            log_file = log_dir / task_id / f'{1}.full.md'
        create_empty_log(log_file)
        print(f'Solving {task_id}: http://127.0.0.1:5000/#{log_dir.parent.name}/{log_dir.name}/{task_id}/{log_file.name}')
        
        cur_state_machine = self.state_machine_class(task_id, dataset)
        cur_state_name = cur_state_machine.start_state
        history_manager = HistoryManager(log_file)
        history_manager.add_singletone_text_message('system', 
            'You are an intelligent assistant and a Python expert.', 'any-llm')

        def callable_as_list(obj):
            if isinstance(obj, list):
                return obj
            else:
                assert callable(obj)
                return [obj]

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
            
            llm = cur_state['llm']() if 'llm' in cur_state else DEFAULT_LLM
            if 'message_to_send' in cur_state:
                with history_manager.start_new_message('user', llm):
                    state_message_funcs = callable_as_list(cur_state['message_to_send'])
                    for state_message_func in state_message_funcs:
                        state_message_ret = state_message_func()
                        if isinstance(state_message_ret, tuple):
                            state_message_type, state_message = state_message_ret
                        else:
                            state_message_type, state_message = 'text', state_message_ret
                        
                        assert state_message_type in ['image', 'text', 'list']
                        if state_message_type == 'image':
                            history_manager.add_image(state_message)                         
                        elif state_message_type == 'text':
                            history_manager.add_text(state_message)
                        elif state_message_type == 'list': # state_message itself is a list of tuples
                            for state_message_type, state_message  in state_message:
                                assert state_message_type in ['image', 'text']
                                if state_message_type == 'image':
                                    history_manager.add_image(state_message)                         
                                elif state_message_type == 'text':
                                    history_manager.add_text(state_message)

                
                response = self.chat_with_llm(history_manager, llm)
                history_manager.add_singletone_text_message('assistant', response, llm)
                
            if 'do_work' in cur_state:
                do_work_funcs = callable_as_list(cur_state['do_work'])
                for do_work_func in do_work_funcs:
                    do_work_func(response)

            # if 'message_to_send' in cur_state:
            #     if 'message_ttl' in cur_state:
            #         ttls[-1], ttls[-2]  = cur_state['message_ttl']()
                        
            next_state_name = cur_state['next_state']
            if next_state_name is None or isinstance(next_state_name, str):
                cur_state_name = next_state_name
            else:
                cur_state_name = next_state_name(response)

        add_string_to_log(f"state machine finished, result is {cur_state_machine.solution}\n", log_file)

        return task_id, dataset, log_file, cur_state_machine.solution

    def chat_with_llm(self, history_manager: HistoryManager, llm: str):
        return history_manager.chat_with_llm(llm)