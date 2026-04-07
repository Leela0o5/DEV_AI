# Agentic_AI

This repo is my learning playground for **agentic AI**—basically, figuring out what an “AI engineer” actually builds by shipping lots of small, runnable experiments.

It’s **not** meant to be a polished framework. The point is to learn by building and keeping the projects small enough that I can iterate fast.

What I’m practicing here:
- the agent loop: **observe → decide → act**
- tool use (LLMs calling functions/tools)
- prompt + system instruction design
- real-world tradeoffs like cost, latency, and reliability

## What’s inside

Each folder is its own mini-project you can run independently:

- **browser-agent/**  
  A browser automation agent (Playwright + Gemini) that can navigate real websites. Focus: tool loop, extracting a “page skeleton” to save tokens, and clicking by visible text for robustness.

- **coding-agent/**  
  A coding helper agent that works against a local workspace with simple tools.

- **data-analyst-agent/**  
  Experiments with analysis-style workflows (explore → summarize → explain).

- **email-agent/**  
  Agent patterns for drafting, rewriting, and iterating on emails.

- **langgraph-learnings/**  
  Notes + experiments while learning LangGraph patterns.

- **mcp-project-manager/**  
  Experiments around MCP-style tooling and project-management workflows.

- **multi-agent-pipeline/**  
  Experiments chaining multiple “roles” together (planner/researcher/writer, etc.).

- **rag-cli/**  
  RAG experiments packaged as a small CLI-style project.

- **research-agent/**  
  Research workflow patterns: gather sources → filter → synthesize.

- **web-search-agent/**  
  A simple agent that uses web search as a tool to answer questions.

## How to run stuff

Everything is meant to be run per-project. Go into a folder and follow its `README.md`.

Typical flow (varies a bit by project):
1. `cd <project>`
2. `uv sync`
3. copy `.env.example` to `.env` and add your API keys
4. run `uv run main.py`

## Notes

- API keys belong in `.env` files and **should not** be committed.
- Expect rough edges--this repo is intentionally optimized for learning speed, not perfection.
