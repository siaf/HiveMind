import os
from dotenv import load_dotenv
from models import AgentConfig
from agent import Agent

# Load environment variables
load_dotenv()

# Create two agents with different configurations
agent1_config = AgentConfig(
    name="Agent1",
    system_prompt="You are a friendly and curious AI assistant who loves to learn new things and ask questions. Keep responses concise and under 3 sentences. End with a question.",
    backend="ollama",
    model_name="deepseek-r1:14b"
)

agent2_config = AgentConfig(
    name="Agent2",
    system_prompt="You are a knowledgeable AI assistant who enjoys sharing information and explaining complex topics simply. Keep responses concise and under 3 sentences. End with a question.",
    backend="ollama",
    model_name="deepseek-r1:14b"
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
    print(f"{agent1_config.name}:\n")
    response1 = agent1.generate_response(current_prompt)
    # print(f"{agent1_config.name}: {response1}\n")
    
    # Agent 2's turn
    print(f"{agent2_config.name}:\n")
    response2 = agent2.generate_response(response1)
    # print(f"{agent2_config.name}: {response2}\n")
    
    # Update the prompt for the next turn
    current_prompt = response2

print("Conversation ended.")