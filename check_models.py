from google import genai

client = genai.Client(
    api_key="AIzaSyCluHRykXYKQdDYzEvdfu90wZBkwQrWtSk"
)

models = client.models.list()

print("AVAILABLE MODELS:\n")

for m in models:
    print(m.name)
