from llm_utils import add_all_in_one_images_to_content, add_content_to_messages_and_log, add_image_to_content, add_text_to_content
from log_utils import create_empty_log, add_string_to_log
from simple_lens_state_machine import SimpleLensStateMachine
import litellm

AKGrid = list[list[int]]
AKGridTuple = tuple[tuple[tuple[int]]]

DEFAULT_LLM='gpt-4o'

class StateMachineSolver:
    def __init__(self,state_machine_class):
        self.state_machine_class = state_machine_class

    def __call__(self, task_id, dataset, log_dir): # --> task_id, dataset, log_file, solutions
        # task = dataset.read_task(task_id)
        log_file = log_dir / task_id / f'{1}.full.md'
        create_empty_log(log_file)
        print(f'Solving {task_id}: http://127.0.0.1:5000/#{log_dir.parent.name}/{log_dir.name}/{task_id}/{1}.full.md')
        

        cur_state_machine: SimpleLensStateMachine = self.state_machine_class(task_id, dataset)
        cur_state_name = cur_state_machine.start_state
        messages = []
        add_content_to_messages_and_log(messages, 'system', 'You are an intelligent assistant and a Python expert.', log_file)

        def callable_as_list(obj):
            if isinstance(obj, list):
                return obj
            else:
                assert callable(obj)
                return [obj]

        while cur_state_name:
            print(cur_state_name)
            content = []
            cur_state = cur_state_machine.states[cur_state_name]
            response = None
            if 'pre_work' in cur_state:
                pre_work_funcs = callable_as_list(cur_state['pre_work'])
                for pre_work_func in pre_work_funcs:
                    pre_work_func()
            if 'message_to_send' in cur_state:
                state_message_funcs = callable_as_list(cur_state['message_to_send'])
                for state_message_func in state_message_funcs:
                    state_message_ret = state_message_func()
                    if isinstance(state_message_ret, tuple):
                        state_message_type, state_message = state_message_ret
                    else:
                        state_message_type, state_message = 'text', state_message_ret
                    
                    assert state_message_type in ['image', 'text', 'list']
                    if state_message_type == 'image':
                        add_image_to_content(content, state_message)                         
                    elif state_message_type == 'text':
                        add_text_to_content(content, state_message)
                    elif state_message_type == 'list': # state_message itself is a list of tuples
                        for state_message_type, state_message  in state_message:
                            assert state_message_type in ['image', 'text']
                            if state_message_type == 'image':
                                add_image_to_content(content, state_message)                         
                            elif state_message_type == 'text':
                                add_text_to_content(content, state_message)

                if 'llm' in cur_state:
                    llm = cur_state['llm']()
                else:
                    llm = DEFAULT_LLM

                add_content_to_messages_and_log(messages, 'user', content, log_file, llm=llm)
                self.chat_with_llm(messages, log_file, llm)
                response = messages[-1]['content'][0]['text']
            if 'do_work' in cur_state:
                do_work_funcs = callable_as_list(cur_state['do_work'])
                for do_work_func in do_work_funcs:
                    do_work_func(response)

            next_state_name = cur_state['next_state']
            if next_state_name is None or isinstance(next_state_name, str):
                cur_state_name = next_state_name
            else:
                cur_state_name = next_state_name(response)

        add_string_to_log(f"state machine finished, result is {cur_state_machine.solution}\n", log_file)

        return task_id, dataset, log_file, cur_state_machine.solution

    def chat_with_llm(self, messages, log_file, llm):
        if 'o1' in llm:
            response = litellm.completion(
                messages=messages,
                stream=False,
                model=llm,
                max_completion_tokens=25000,
                temperature=0,
            )
        else:
            response = litellm.completion(
                messages=messages,
                stream=False,
                model=llm,
                max_tokens=4096,
                temperature=0,
            )

        # assistant_reply = response
        assistant_reply = response['choices'][0]['message']['content'].strip()
        add_content_to_messages_and_log(messages, 'assistant', assistant_reply, log_file, llm=llm)
        return assistant_reply