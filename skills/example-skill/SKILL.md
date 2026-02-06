---
name: example-skill
description: An example skill demonstrating the Skill Shop structure
homepage: https://github.com/yourusername/skill-shop
metadata: {"openclaw":{"emoji":"📦","requires":{"bins":["python"],"env":[]},"primaryEnv":""}}
---

# Example Skill

## Purpose
This is an example skill that demonstrates the standard Skill Shop structure and format.

## Inputs
- `input`: A string input parameter (required)

## Outputs
- Returns a JSON object with the processed input

## Usage
Command: `./run.sh --input "Hello, World!"`

Or via JSON stdin:
```bash
echo '{"input": "Hello, World!"}' | ./run.sh
```

## Failure modes
- Missing input: Returns error message
- Invalid JSON: Returns parsing error

## When to use
Use this as a template when creating new skills.

## When not to use
This is just an example - replace with actual skill logic.
