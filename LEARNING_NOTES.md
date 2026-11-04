# Learning Notes

## Tue 3 Nov 2026: Environment setup

**Concepts**
- venv: a private copy of Python inside the project. Packages install only there. `(.venv)` in the prompt means it's active.
- PATH: Windows runs the first python.exe it finds in the PATH folder list. Always check with `sys.executable`.

**Decisions (and why)**
- Python 3.13: mature enough that the packages have builds for it; not the 3.9 Anaconda.
- Groq, model openai/gpt-oss-20b: fastest general chat model on my key; 120b kept as a fallback.
- .gitignore created before .env: a key committed once stays in git history forever.

**What broke**
- llama-3.1-8b-instant was retired: 404. (401 = bad key, 404 = bad model/path.)

**Finding**
- Token limit (8K/min, 200K/day) means one careless full run could fail. Keep prompts short, cache responses.

**Interview answer**
- Q: How did you keep your API key out of the repo?
- A: First we create a .gitignore file. Then I create a .env file and mention this in the .gitignore file so that it does not get uploaded to the repo. The lives in the .env file and the code reads it at runtime as an environment variable, so the key is never mentioned in the source code. This ensures that the API key is never commited because anything commited stays in the git history. Then I commit a .env.example file with placeholders so others know which variable to set.To verify, I check git status before committing and a secret scanner can audit the full git history. If a key ever leaked, I'd revoke it with the provider immediately. Rewriting history doesn’t make a leaked key safe again. 

## Wed 4 Nov 2026: Discovery (interviews)

**Decisions (and why)**
- Build and tune on the 500 development tickets, test on the 80 validation tickets. Never adjust the system based on the 80. Otherwise the score is memorised, not earned.

**Finding**
- Interviews are claims, not facts. Check them against the data. Some claims can't be checked with the data we have (e.g. first-reply time isn't in the tickets).