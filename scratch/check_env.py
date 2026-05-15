import os
from dotenv import load_dotenv

load_dotenv()

print(f"EMBED_ACCESS_URL: {os.environ.get('EMBED_ACCESS_URL')}")
print(f"EMBED_ACCESS_KEY: {os.environ.get('EMBED_ACCESS_KEY')}")
print(f"INTERNAL_API_TOKEN: {os.environ.get('INTERNAL_API_TOKEN')}")
