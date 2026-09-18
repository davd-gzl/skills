# Prose that asserts behaviour is not trivial

A diff that changes no behaviour and states plenty of it carries the round's whole risk in its claims, and a class keyed on behaviour alone hands it to one agent.

- A 260-line JSON-RPC reference, twenty endpoints of parameter, default and cap assertions, ran as one solo agent, 2 agents and 46k output, where the plan projected 17 agents and 493k; nothing in it changed code and every line was a claim about code.

Source: [gnolang/gno#6182](https://github.com/gnolang/gno/pull/6182), `./scripts/review-retro.py` over its round against `./scripts/review-plan.py --preset standard`.

Changes: the trivial row of the triage table and the triage prompt exclude prose asserting runtime behaviour, which classes normal with the claims angle over more than one context.
