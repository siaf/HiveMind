# Directory Analysis Agent

This project implements an intelligent agent system that analyzes directory contents and provides summaries of text files.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)

## Installation

1. Clone the repository or download the source code

2. Create and activate a virtual environment:
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root directory and add your environment variables (if required)

## Usage

The main script can be run from the terminal using the following command:

```bash
python main.py [options]
```

### Command Line Options

- `-p PATH, --path PATH`: Specify the directory path to analyze (default: current directory)
- `-v, --verbose`: Enable verbose mode for detailed output

### Examples

1. Analyze the current directory:
```bash
python main.py
```

2. Analyze a specific directory with verbose output:
```bash
python main.py -p /path/to/directory -v
```

3. Analyze a specific directory without verbose output:
```bash
python main.py --path /path/to/directory
```

## Features

- Directory content analysis
- Text file summarization
- Support for multiple agent types:
  - Directory Analyzer: Lists and analyzes directory contents
  - Text Analyzer: Provides detailed summaries of text files

## Project Structure

- `main.py`: Main entry point of the application
- `agent.py`: Implementation of the agent system
- `models.py`: Data models and configurations
- `system_prompts.py`: System prompt definitions
- `task_queue.py`: Task queue management
- `workflow.py`: Workflow implementation
- `requirements.txt`: Project dependencies