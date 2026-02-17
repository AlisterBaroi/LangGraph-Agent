# LangGraph <span style="color: red">Search Agent</span>
<img src="https://miro.medium.com/v2/1*_zS2qyJ-rDFe1w3P37w2ag.png"  width="350" align="right" title="LangGraph" alt="LangGraph Logo" >

This project is to demo an AI Agent using [LangGraph](https://www.langchain.com/langgraph), the open-source tool by LangChain designed to build stateful, multi-actor applications by modeling AI workflows as cyclical graphs, allowing for complex loops, decision-making, and persistent memory.

<!-- ![LangGraph Logo](https://miro.medium.com/v2/0*je-yj93ERqG0BEoQ.png) -->

## Prerequisites 
The project uses Google Gemini as the base LLM and depends on Gemini API Key for integration. Visit [Google AI Studio](https://aistudio.google.com/api-keys) to generate an API key.


> [!IMPORTANT]  
> Make sure to copy the `.env.local` file, renaming it as `.env` and paste-in the API key for the `GOOGLE_API_KEY` variable, no need to add quotations (""). The `.env` file should look something like:
> ```sh
> GOOGLE_API_KEY=AIzasYc4 .... ashIU
> MODEL_NAME=gemini-2.5-flash
> ``` 

## Setup
1. Clone the GitHub repo, cd into the project, and open in IDE:
    ```sh
    git clone https://github.com/AlisterBaroi/LangGraph-Agent.git
    cd LangGraph-Agent
    
    # Make sure to be in the project folder 
    pwd # Linux cmd
    ```

2. Create a virtual environment (named ENV) for the python project:
    ```sh
    python -m venv ENV
    # or 
    # python3 -m venv ENV
    ```
    Optional: If the virtual environment doesn't open by default in IDE/terminal, use the following command:
    ```sh
    # For Mac/Linux
    source ENV/bin/activate
    
    # For Windows
    ENV\Scripts\activate
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```


## Demo
To demo the project with Web UI, run the streamlit command to execute `app.py` file while in the virtual environment:
```sh
streamlit run app.py
```
## Development
For the standalone agent (for development), run `agent.py` file while in the virtual environment:
```sh
python agent.py
# or 
# python3 agent.py
```

## Clean up
To clean-up the project, deactivate the virtual environment and delete it:
```sh
# Deactivate virtual environment
deactivate 

# Delete virtual environment (for Mac/Linux)
rm -r -f ENV/

# (for Windows CMD)
# rd /s /q ENV    

# (for Windows PowerShell)
# rm -rf ENV      
``` 
