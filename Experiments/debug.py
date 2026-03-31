import sys

print("🔍 DETECTIVE REPORT:")
print("1. Python kahan se chal raha hai:", sys.executable)

try:
    import langchain
    print("2. Langchain library kahan save hai:", langchain.__file__)
    print("3. Langchain ka version kya hai:", langchain.__version__)
except Exception as e:
    print("❌ Langchain import error:", e)