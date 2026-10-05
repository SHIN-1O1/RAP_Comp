# System Architecture

## Architecture Overview
The system implements a strictly budgeted document question-answering agent without RAG, embeddings, or vector databases.

```text
                         USER
                           |
                           v
                    User Question
                           |
                           v
              +-------------------------+
              | CALL 1: LLM             |
              | Question Analysis       |
              | + Initial Strategy      |
              +-----------+-------------+
                          |
                          v
              +-------------------------+
              | GLOBAL BUDGET MANAGER   |
              | MAX = 6 PRE-FINAL CALLS |
              +-----------+-------------+
                          |
                          v
              +-------------------------+
              | ADAPTIVE RETRIEVAL      |
              |                         |
              | list_headings           |
              | search_keyword          |
              | get_page                |
              +-----------+-------------+
                          |
                          v
                  Evidence Store
                          |
                          v
                 Need More Evidence?
                    /           \
                  YES            NO
                   |              |
                   v              |
             Calls Remaining?     |
              /          \        |
            YES           NO      |
             |             |      |
             +-------------+------+
                           |
                           v
                  FINAL ANSWER CALL
                           |
             +-------------+-------------+
             |                           |
             v                           v
       Evidence supports          Evidence insufficient
             |                           |
             v                           v
         Answer                  "Insufficient information"
```

## Call Budget Lifecycle
- Shared budget of max 6 pre-final calls: Planning LLM calls + document-tool calls (`list_documents`, `list_headings`, `search_keyword`, `get_page`).
- Attempting a 7th pre-final call triggers `BudgetExceededError` in Python code.
- Final Answer is a separate call invoked at most once (`final_answer_generated = True`).
