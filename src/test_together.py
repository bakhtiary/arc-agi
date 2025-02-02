from dotenv import load_dotenv
from litellm_interface import LiteLLMInterface


# llm_interface = LiteLLMInterface(vision_model='gpt-4o', text_model='deepseek/deepseek-reasoner')
# llm_interface.chat_with_llm('')


from together import Together
load_dotenv('.secrets')
client = Together()

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    messages=[],
    max_tokens=1000,
    temperature=0.7,
    top_p=0.7,
    top_k=50,
    repetition_penalty=1,
    stop=["<｜end▁of▁sentence｜>"],
    _gl="1*17v8fme*_gcl_au*MTMxMjIyMDA0Ni4xNzM4MDA1NjA5",
    stream=True
)
for token in response:
    if hasattr(token, 'choices'):
        print(token.choices[0].delta.content, end='', flush=True)