import os
from dotenv import load_dotenv
import argparse
from models import AgentConfig
from agent import Agent

def main():
    parser = argparse.ArgumentParser(description='Run the agent with optional verbose mode')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode for detailed output')
    args = parser.parse_args()

    # Color constants
    AGENT1_THINK = "\033[94m"  # Light blue
    AGENT1_RESPOND = "\033[34m"  # Dark blue
    AGENT2_THINK = "\033[92m"  # Light green
    AGENT2_RESPOND = "\033[32m"  # Dark green
    RESET = "\033[0m"  # Reset color

    # Load environment variables
    load_dotenv()

    # Create two agents with different configurations
    agent1_config = AgentConfig(
        name="Agent1",
        system_prompt="You are a friendly and curious AI assistant who loves to learn new things and ask questions. Keep responses concise and under 3 sentences. End with a question.",
        backend="ollama",
        model_name="deepseek-r1:14b",
        verbose=args.verbose
    )

    agent2_config = AgentConfig(
        name="Agent2",
        system_prompt="You are a knowledgeable AI assistant who enjoys sharing information and explaining complex topics simply. Keep responses concise and under 3 sentences. End with a question.",
        backend="ollama",
        model_name="deepseek-r1:14b",
        verbose=args.verbose
    )

    # Initialize agents
    agent1 = Agent(agent1_config)
    agent2 = Agent(agent2_config)

    # Start the conversation
    max_turns = 2
    current_prompt = "What's your favorite color and why?"

    print("Starting conversation between agents...\n")

    for turn in range(max_turns):
        print(f"\n--- Turn {turn + 1} ---")
        
        # Agent 1's turn
        print(f"{AGENT1_THINK}{agent1_config.name} thinking...{RESET}")
        response1 = agent1.generate_response(current_prompt)
        print(f"{AGENT1_RESPOND}{agent1_config.name}: {response1}{RESET}\n")
        
        # Agent 2's turn
        print(f"{AGENT2_THINK}{agent2_config.name} thinking...{RESET}")
        response2 = agent2.generate_response(response1)
        print(f"{AGENT2_RESPOND}{agent2_config.name}: {response2}{RESET}\n")
        
        # Update the prompt for the next turn
        current_prompt = response2

    print("Conversation ended.")

if __name__ == "__main__":
    main()