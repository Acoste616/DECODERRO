Cloud

Copy page
Ollama’s cloud is currently in preview.
​
Cloud Models
Ollama’s cloud models are a new kind of model in Ollama that can run without a powerful GPU. Instead, cloud models are automatically offloaded to Ollama’s cloud service while offering the same capabilities as local models, making it possible to keep using your local tools while running larger models that wouldn’t fit on a personal computer.
Ollama currently supports the following cloud models, with more coming soon:
deepseek-v3.1:671b-cloud
gpt-oss:20b-cloud
gpt-oss:120b-cloud
kimi-k2:1t-cloud
qwen3-coder:480b-cloud
glm-4.6:cloud
minimax-m2:cloud
​
Running Cloud models
Ollama’s cloud models require an account on ollama.com. To sign in or create an account, run:

Copy
ollama signin
CLI
Python
JavaScript
cURL
To run a cloud model, open the terminal and run:

Copy
ollama run gpt-oss:120b-cloud
​
Cloud API access
Cloud models can also be accessed directly on ollama.com’s API. In this mode, ollama.com acts as a remote Ollama host.
​
Authentication
For direct access to ollama.com’s API, first create an API key.
Then, set the OLLAMA_API_KEY environment variable to your API key.

Copy
export OLLAMA_API_KEY=your_api_key
​
Listing models
For models available directly via Ollama’s API, models can be listed via:

Copy
curl https://ollama.com/api/tags
​
Generating a response
Python
JavaScript
cURL
First, install Ollama’s Python library

Copy
pip install ollama
Then make a request

Copy
import os
from ollama import Client

client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + os.environ.get('OLLAMA_API_KEY')}
)

messages = [
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
]

for part in client.chat('gpt-oss:120b', messages=messages, stream=True):
  print(part['message']['content'], end='', flush=True)