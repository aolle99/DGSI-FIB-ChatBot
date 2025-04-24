# import requests

# url = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf"
# filename = "llama.gguf"

# with open(filename, "wb") as f:
#     f.write(requests.get(url).content)

# print("下载完成！")

from llama_cpp import Llama

llm = Llama(model_path="./model/llama/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
response =  llm("How are you?")["choices"][0]["text"]
print(response)