# Bastion

A lightweight runtime protection layer for AI agents. Drop it in front of your OpenAI calls and it automatically stops the three most common ways autonomous agents waste money or break production - before they happen, not after you see the bill.

## The problem

Autonomous AI agents fail in specific, predictable ways:

- **Reasoning loops** - an agent gets stuck rephrasing the same broken question over and over, burning real API calls that produce zero value
- **Retry storms** - a third-party API hiccups, and a poorly-built agent responds by firing dozens or hundreds of retries in seconds
- **Runaway spend** - one broken session or user can rack up a huge bill, and most providers only offer organisation-wide monthly caps - meaning one bad actor takes down your entire account, locking out every other user

Bastion catches all three, in real time, per session - so one broken part never takes down everything else.

## Install

pip install bastion-runtime

## Usage - one line swap

Before:
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(model="gpt-4o-mini", messages=[...])

After:
from bastion import Bastion
client = Bastion()
response = client.chat.completions.create(
    session_id="user-123",
    model="gpt-4o-mini",
    messages=[...],
)

session_id identifies which user, agent, or workflow a call belongs to. Bastion tracks each session independently - if one session gets blocked, every other session keeps working normally.

## What it catches

Semantic Loop Detector - converts recent messages into embeddings and measures actual similarity. If a session asks a near-duplicate question 3 times in a row, even reworded, it kills that session.

Retry Storm Detector - if a session fires more than 10 calls in a 1-second window, Bastion forces an immediate cooldown.

Micro-Budget Circuit Breaker - tracks spend and call count for each individual session separately. If one session goes over its limit, only that session gets blocked. Every other user or agent in your app carries on working normally. Completely unaffected.

## Running tests

pip install pytest
pytest test_bastion.py -v

Tests use a fake embedding function so they run instantly, with no API key required.

## Status

Core protection logic is built and tested, including live verification against the OpenAI API. Currently OpenAI-only; other providers planned.
