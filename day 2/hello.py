# quickstart.py
import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key="mstrl_FogicadWA467fGQB4d4gE7dDsbyzhfAH_4cUBiP")

response = client.chat.complete(
    model="mistral-small-latest",
    messages=[
        {"role": "system",
         
          "content": "your library name is Prelytix , there was books that name Prelytix tools,gen ai, python , uiux."
          
          },
        {
            "role": "user",
            "content": "your book price?"
        }
    ],
)

print(response.choices[0].message.content)