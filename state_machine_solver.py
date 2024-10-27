from llm_utils import add_all_in_one_images_to_content, add_content_to_messages, add_text_to_content
from log_utils import create_empty_log, save_log
from simple_lens_state_machine import SimpleLensStateMachine
from task_utils import read_task

AKGrid = list[list[int]]
AKGridTuple = tuple[tuple[tuple[int]]]

LLM_MODEL='gpt-4o'

class StateMachineSolver:
    def __init__(self,state_machine_class, llm_wrapper):
        self.state_machine_class = state_machine_class
        self.llm_wrapper = llm_wrapper

    def __call__(self, task_id, dataset, log_dir): # --> task_id, dataset, log_file, solutions
        task = read_task(task_id, dataset)
        (log_dir / task_id).mkdir(parents=True, exist_ok=True)
        log_file = log_dir / task_id / f'{1}.json'
        create_empty_log(log_file)
        results: list[list[AKGrid]] = []
        print(f'Solving {task_id}: http://127.0.0.1:5000/#{log_dir.parent.name}/{log_dir.name}/{task_id}/{1}.full.md')
        

        cur_state_machine: SimpleLensStateMachine = self.state_machine_class(task_id, dataset)
        cur_state_name = cur_state_machine.start_state
        messages = []
        add_content_to_messages(messages, 'system', 'You are an intelligent assistant and a Python expert.')

        while cur_state_name:
            print(cur_state_name)
            content = []
            cur_state = cur_state_machine.states[cur_state_name]
            response = None
            if 'message_to_send' in cur_state:
                state_message_funcs = cur_state['message_to_send']
                assert callable(state_message_funcs) or isinstance(state_message_funcs, list)
                if callable(state_message_funcs):
                    state_message_funcs = [state_message_funcs]
                for state_message_func in state_message_funcs:
                    state_message = state_message_func()
                    if state_message == '{all_in_one_images}':
                        add_all_in_one_images_to_content(content, task['train'])
                    else:
                        add_text_to_content(content, state_message)
                add_content_to_messages(messages, 'user', content)
                 
                self.chat_with_llm(messages)
                response = messages[-1]['content'][0]['text']

            if 'do_work' in cur_state:
                do_work = cur_state['do_work']
                do_work(response)

            next_state_name = cur_state['next_state']
            if isinstance(next_state_name, str) or next_state_name is None:
                cur_state_name = next_state_name
            else:
                cur_state_name = next_state_name(response)

            save_log(messages, log_file)

        return task_id, dataset, log_file, cur_state_machine.solution
        # results = ...

    def chat_with_llm(self, messages):
        response = self.llm_wrapper.completion(
            messages=messages,
            stream=False,
            model=LLM_MODEL,
            max_tokens=4096,
            temperature=0,
        )
        # assistant_reply = response
        assistant_reply = response['choices'][0]['message']['content'].strip()
        add_content_to_messages(messages, 'assistant', assistant_reply)
        return assistant_reply