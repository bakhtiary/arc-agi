from state_machine_solver_utils import extract_and_run_mapping_code, extract_and_run_lens_code


# تکستت و عکس را به جی پیتی قور اوه می دهیم.
# .بدون کد جنریشتن رابطه ورودی و خروجی را بگو.
# با استقاده از عکس کلی
# از خودش بپرسه که به اندازه کافی کانکریت هست یا نه؟
# اگر نه یه کدی بنویسی که باهاش عکس رو بهتر ببینی؟مثلا تعداد رنگهای مختلف در عکس ورودی و خروجی یا تعداد مربع ها
# کد را ران کرده و خروجی را به آن می‌دهیم.
# این پروسس رو ان بار تکرار می کنیم. شرط خروجیاماکس لیمیت. یا جواب بگیره که آره کانکریت هست.
# تابعی بنویس که ورودی را به خروجی مپ بنماید
# پایان
# فارسی!


class SimpleLensStateMachine:
    def __init__(self, task_id, dataset):
        self.start_state = "entry_point"
        self.states = {}
        self.dataset = dataset
        self.run_results = []
        self.task_id = task_id
        self.max_num_failed = 5
        self.num_failed = 0
        self.solution = None
        self.states["entry_point"] = dict(
            message_to_send=[lambda: "Given this image please give me a hypothesis about the relationship between "
                            "the inputs (left) and the outputs (right)", lambda: "{all_in_one_images}"], # use {{x}} if this is an f-string
            next_state="is_concrete"
        )
        self.states["is_concrete"] = dict(
            message_to_send=[lambda: "is the hypothesis that you just described, concrete enough "
                "to write a code that maps the input to the output? answer with a simple yes or no, nothing else"],
            next_state= lambda response: "get_mapping_code" if "yes" in response.lower() else "get_lens_code"
        )
        self.states["get_mapping_code"] = dict(
            message_to_send=[lambda :"please generate the mapping code for this hypothesis"],
            next_state=lambda response: "success" if self.extract_and_run_mapping_code_works(response) else "mapping_code_failed"
        )
        self.states["get_lens_code"] = dict(
            message_to_send=[lambda: "can you write one or more functions that query the input or output "
                "images and give useful information about them. Think of these functions as lenses that help "
                "you see better. Notes: in both cases, your function should accept each grid as a Python "
                "list of lists. Each element of the list represents one color as an integer from 0 to 9. "
                "I will execute the function or functions and give you the results."],
            do_work=self.extract_and_run_lens_code,
            next_state = "present_result",
        )
        self.states["present_result"] = dict(
            message_to_send=[lambda:f"We ran the given code on the following inputs and got "
                f"{self.run_results[-1]}\n"
                "Use the result of this code to refine the hypothesis."] ,
            next_state="is_concrete"
        )
        self.states["success"] = dict(
            do_work=self.extract_and_save_solution,
            next_state=None
        )
        self.states["mapping_code_failed"] = dict(
            message_to_send=[lambda: f"We ran the given code on the following inputs and got "
                f"{self.run_results[-1]}\ntry to fix this error and try again"],
            do_work=self.mapping_code_failed_work,
            next_state= lambda response: "success" if self.extract_and_run_mapping_code_works(response) else "mapping_code_failed" if self.num_failed < self.max_num_failed else "total_failure"
        )
        self.states["total_failure"] = dict(
            next_state=None
        )

    def mapping_code_failed_work(self, response):
        self.num_failed += 1

    def extract_and_run_lens_code(self, response):
        self.run_results.append(extract_and_run_lens_code(response, self.task_id, self.dataset))

    def extract_and_run_mapping_code_works(self, response):
        result = extract_and_run_mapping_code(response, self.task_id, self.dataset)
        self.run_results.append(result)
        return "<successful run>" in result

    def extract_and_save_solution(self, response):
        self.solution = eval(self.run_results[-1].split("<successful run>")[1])