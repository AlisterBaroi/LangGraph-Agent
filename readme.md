# LangGraph AI Agent
This project is to demo a basic AI Agent using [LangGraph](https://www.langchain.com/langgraph), the open-source tool by LangChain designed to build stateful, multi-actor applications by modeling AI workflows as cyclical graphs, allowing for complex loops, decision-making, and persistent memory.

## Prerequisites 
The is project uses Google Gemini as the base LLM and depends on Gemini API Key for integration. Visit [Google AI Studio](https://aistudio.google.com/api-keys) to generate an API key.


> [!IMPORTANT]  
> Make sure to copy-paste the `.env.local` file, renaming it as `.env` and paste the API key for the `GOOGLE_API_KEY` variable, no need to add quotations (""). The `.env` file should look something like this:
> ```env
> GOOGLE_API_KEY=AIzasYc4 .... ashIU
> ``` 

## Setup
1. Clone the GitHub repo, open IDE and cd into the project:
    ```python
    git clone https://github.com/AlisterBaroi/LangGraph-Agent-Demo
    cd LangGraph-Agent-Demo
    # Make sure you're in the project folder 
    pwd 
    ```

2. Create a virtual enviornment (named env) for the python project:
    ```python
    python -m venv env
    # or use the following for linux:
    # python -m venv venv
    ```

3. Install the required dependencies:
    ```python
    pip install -r requirements.txt
    ```


## Demo
To demo the project, just run the `app.py` file while in the virtual enviornment:
```python
python app.py
# or 
# python3 app.py
```