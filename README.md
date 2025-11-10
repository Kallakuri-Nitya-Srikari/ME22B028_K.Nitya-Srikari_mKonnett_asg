     
1. Open Spyder and set working directory to project root (where README.md sits).
2. Install dependencies: `pip install -r requirements.txt` (use venv recommended).
3. Copy `.env.example` to `.env` and add `OPENAI_API_KEY` if you want polished LLM answers.
4. In Spyder, open `src/agent.py` and **Run -> Configure** set command line options, e.g.:
   `--query "What were our best-selling items yesterday?"`
5. Run the script. Output appears in the console.

## Files
- `src/agent.py` — main program
- `src/sales_api.py` — API client + caching
- `src/llm.py` — LLM wrapper

## Notes
- If no OPENAI_API_KEY is present, the agent still computes metrics locally and prints a simple summary.
