import litellm

from simple_lens_state_machine import SimpleLensStateMachine
from solver import add_text_to_content
from task_utils import read_task

AKGrid = list[list[int]]
AKGridTuple = tuple[tuple[tuple[int]]]

LLM_MODEL='gpt-4o'

class StateMachineSolver:
    def __init__(self,state_machine_class, llm_wrapper):
        self.state_machine_class = state_machine_class
        self.llm_wrapper = llm_wrapper

    def __call__(self, task_id, dataset, num_beams, log_dir, msg):
        task = read_task(task_id, dataset)
        (log_dir / task_id).mkdir(parents=True, exist_ok=True)
        results: list[list[AKGrid]] = []
        print(f'Solving {task_id} [{msg}]')
        log_file = log_dir / task_id / f'{1}.json'

        cur_state_machine: SimpleLensStateMachine = self.state_machine_class(dataset, task_id)
        cur_state_name = cur_state_machine.start_state
        messages = []
        add_content_to_messages(messages, 'system', 'You are an intelligent assistant and a Python expert.')
        while cur_state_name:
            print(cur_state_name)
            cur_state = cur_state_machine.states[cur_state_name]
            response = None
            if "message_to_send" in cur_state:
                message = cur_state["message_to_send"]()
                add_content_to_messages(messages, "user", message)
                self.chat_with_llm(messages)
                response = messages[-1]['content'][0]['text']

            if "do_work" in cur_state:
                do_work = cur_state["do_work"]
                do_work(response)

            next_state_name = cur_state["next_state"]
            if isinstance(next_state_name, str) or next_state_name is None:
                cur_state_name = next_state_name
            else:
                cur_state_name = next_state_name(response)

    def chat_with_llm(self, messages):
        response = self.llm_wrapper.completion(
            messages=messages,
            stream=False,
            model=LLM_MODEL,
            max_tokens=4096,
            temperature=0,
        )
        assistant_reply = response
        add_content_to_messages(messages, 'assistant', assistant_reply)
        return assistant_reply

def add_content_to_messages(messages, role, content):
    assert isinstance(content, list) or isinstance(content, str)
    if isinstance(content, str):
        content_str = content
        content = []
        add_text_to_content(content, content_str)

    messages.append({
        'role': role,
        'content': content
    })
