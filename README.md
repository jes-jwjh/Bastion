# Bastion

A lightweight runtime protection layer for AI agents. Drop it in front of your OpenAI calls and it automatically stops the three most common ways autonomous agents waste money or break production - before they happen, not after you see the bill.

## The problem

Autonomous AI agents fail in specific, predictable ways:

- **Reasoning loops** - an agent gets stuck rephrasing the same broken question over and over, burning real API calls that produce zero value
- **Retry storms** - a third-party API hiccups, and a poorly-built agent responds by firing dozens or hundreds of retries in seconds
- **Runaway spend** - one broken session or user can rack up a huge bill, and most providers only offer organisation-wide monthly caps - meaning one bad actor takes down your entire account, locking out every other user

Bastion catches all three, in real time, per session - so one broken part never takes down everything else.

## Install

```bash
pip install bastion-runtime


# Before:
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(model="gpt-4o-mini", messages=[...])

# After:
from bastion import Bastion
client = Bastion()
response = client.chat.completions.create(
    session_id="user-123",   # the only new thing you add
    model="gpt-4o-mini",
    messages=[...],
)

ls
