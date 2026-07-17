# Bastion

A lightweight runtime protection layer for AI agents. Drop it in front of your OpenAI calls and it automatically stops the three most common ways autonomous agents waste money or break production - before they happen, not after you see the bill.

## The problem

Autonomous AI agents fail in specific, predictable ways:

- Reasoning loops - an agent gets stuck rephrasing the same broken question over and over, burning real API calls that produce zero value
- Retry storms - a third-party API hiccups, and a poorly-built agent responds by firing dozens or hundreds of retries in seconds
- Runaway spend - one broken session or user can rack up a huge bill, and most providers only offer organization-wide monthly caps - meaning one bad actor takes down your entire account, locking out every other user

Bastion catches all three, in real time, per session - so one broken part never takes down everything else.

## Usage - one line swap

This is all you need to get started. Install the package, then swap two lines in your existing code.

Install:

    pip install bastion-runtime

Your code currently looks like this (shown for comparison only, do not paste this part):

    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(model="gpt-4o-mini", messages=[])

Change it to this (paste this part):

    from bastion import Bastion
    client = Bastion()
    response = client.chat.completions.create(
        session_id="user-123",
        model="gpt-4o-mini",
        messages=[],
    )

session_id identifies which user, agent, or workflow a call belongs to. Bastion tracks each session independently - if one session gets blocked, every other session keeps working normally.

Everything below this point is optional. Bastion works fully with the defaults shown above - only read further if you want to handle errors specifically or change any settings.

## What it catches

Semantic Loop Detector - converts recent messages into embeddings and measures actual similarity. If a session asks a near-duplicate question 3 times in a row, even reworded, it kills that session.

Retry Storm Detector - if a session fires more than 10 calls in a 1-second window, Bastion forces an immediate cooldown.

Micro-Budget Circuit Breaker - tracks spend and call count for each individual session separately. If one session goes over its limit, only that session gets blocked. Every other user or agent in your app carries on working normally. Completely unaffected.

## Handling blocks (optional)

If you want to catch and respond to Bastion blocking something specifically, paste this instead of a plain try/except:

    from bastion import LoopDetected, RetryStormDetected, BudgetExceeded

    try:
        response = client.chat.completions.create(session_id="user-123")
    except LoopDetected as e:
        pass
    except RetryStormDetected as e:
        pass
    except BudgetExceeded as e:
        pass

## Configuration (optional)

Every setting below already has a sensible default. You only need this if you want to change something specific - for example, a stricter loop detector or a higher budget cap:

    from bastion import Bastion, BastionConfig

    config = BastionConfig(
        loop_similarity_threshold=0.75,
        retry_max_calls=10,
        max_cost_usd_per_session=2.00,
        reset_period_seconds=2592000,
    )
    client = Bastion(config=config)

## Running tests

    pip install pytest
    pytest test_bastion.py -v

Tests use a fake embedding function so they run instantly, with no API key required.

## License

This project is licensed under the Business Source License 1.1 - free to use, modify, and self-host, but not to resell as a competing commercial service. See LICENSE for details.

## Status

Core protection logic is built and tested, including live verification against the OpenAI API. Currently OpenAI-only; other providers planned.
