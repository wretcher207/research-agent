# agent.py
# The core ReAct loop. This is the agent's brain.
# It calls the LLM, checks if it wants to use a tool,
# runs the tool, feeds results back, and repeats until done.

import os
import json
from groq import Groq
from dotenv import load_dotenv
from tools import TOOLS, TOOL_FUNCTIONS

load_dotenv()

# ── Constants ──────────────────────────────────────────────────────────────────
MODEL = MODEL = MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_ITERATIONS = 6   # Safety cap: prevents infinite tool-call loops

SYSTEM_PROMPT = """You are a helpful research assistant with access to a web search tool.

Your job is to answer the user's questions accurately and thoroughly.

Guidelines:
- If you need current information or aren't confident about a fact, use the web_search tool.
- You can search multiple times if needed to get a complete answer.
- After gathering information, synthesize it into a clear, well-organized answer.
- Always cite your sources by mentioning where information came from.
- If search results don't fully answer the question, say so honestly.
"""

# ── LLM client ────────────────────────────────────────────────────────────────
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def run_agent(user_message: str, conversation_history: list) -> tuple[str, list]:
    """
    Runs one full agent turn for a given user message.

    Args:
        user_message:        The user's current question or request.
        conversation_history: List of previous messages (enables multi-turn memory).

    Returns:
        A tuple of (final_answer_string, updated_conversation_history)
    """

    # Add the new user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    print(f"\n{'='*60}")
    print(f"  🧠 Agent thinking...")

    # ── ReAct loop ─────────────────────────────────────────────────────────────
    for iteration in range(MAX_ITERATIONS):

        # Call the LLM with the full conversation + available tools
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history,
            tools=TOOLS,
            tool_choice="auto",    # LLM decides whether to use a tool or answer directly
            max_tokens=2048,
            temperature=0.5
        )

        message = response.choices[0].message

        # ── Case 1: LLM wants to call a tool ───────────────────────────────────
        if message.tool_calls:

            # Add the LLM's tool-call decision to history
            conversation_history.append({
                "role": "assistant",
                "content": message.content,       # may be None
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # Run each requested tool and collect results
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"  🛠️  Tool called: {tool_name}({tool_args})")

                # Look up and execute the tool function
                if tool_name in TOOL_FUNCTIONS:
                    tool_result = TOOL_FUNCTIONS[tool_name](**tool_args)
                else:
                    tool_result = f"Error: unknown tool '{tool_name}'"

                # Add the tool result to history so the LLM sees it next iteration
                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

            # Loop back — LLM will now reason over the tool results
            continue

        # ── Case 2: LLM is done and has a final answer ─────────────────────────
        else:
            final_answer = message.content

            # Add the final answer to history for future turns
            conversation_history.append({
                "role": "assistant",
                "content": final_answer
            })

            print(f"  ✅ Answer ready after {iteration + 1} iteration(s)")
            return final_answer, conversation_history

    # ── Safety fallback: hit MAX_ITERATIONS without a final answer ─────────────
    fallback = "I wasn't able to produce a complete answer after several search attempts. Please try rephrasing your question."
    conversation_history.append({"role": "assistant", "content": fallback})
    return fallback, conversation_history