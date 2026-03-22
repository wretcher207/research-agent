# main.py
# Entry point. Runs the agent as an interactive CLI chat loop.
# Maintains conversation history across turns so the agent has memory.

from agent import run_agent

def main():
    print("\n" + "="*60)
    print("  🤖 Research Agent — powered by Groq + Tavily")
    print("  Type your question and press Enter.")
    print("  Type 'quit' or 'exit' to stop.")
    print("  Type 'clear' to reset conversation memory.")
    print("="*60 + "\n")

    conversation_history = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("Goodbye.")
            break

        if user_input.lower() == "clear":
            conversation_history = []
            print("  🗑️  Conversation memory cleared.\n")
            continue

        answer, conversation_history = run_agent(user_input, conversation_history)

        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()