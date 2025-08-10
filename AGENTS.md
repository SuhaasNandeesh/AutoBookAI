# Agent Instructions

This document provides instructions for AI agents working on the AutoBook AI project.

## Project Overview

AutoBook AI is a website that uses AI agents to fully automate scheduling based on user preferences. The goal is to create a system that is autonomous, proactive, and personalized.

## Development Philosophy

This project is being built entirely by AI tools. We will leverage LLMs, agents, RAG, LangChain, and LangGraph to prototype, iterate, and deploy.

## Key Technologies

- **LangChain & LangGraph:** For building and orchestrating AI agents.
- **RAG (Retrieval-Augmented Generation):** For providing agents with relevant, up-to-date information from a knowledge base.
- **Vector Stores:** For storing and retrieving user preferences and other contextual data.

## Coding Conventions

- All code should be written in Python.
- Follow PEP 8 style guidelines.
- Include docstrings for all modules, classes, and functions.
- Write unit tests for all new functionality.

## Testing

- Use the `pytest` framework for testing.
- Tests should be placed in the `tests/` directory.
- Run tests frequently to ensure that changes do not break existing functionality.
- Before submitting, ensure all tests pass.
- For frontend changes, use Playwright for verification.

## Commits and Pull Requests

- Write clear and descriptive commit messages.
- The commit message subject line should be 50 characters or less.
- The commit message body should explain the "what" and "why" of the change.
- All changes should be submitted via a pull request.
- Ensure the PR description clearly describes the changes.
- Ensure all tests and programmatic checks in `AGENTS.md` pass before submitting.
- Request a code review before submitting.
