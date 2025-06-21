Setting up .env file with following items

OPENAI_API_KEY=<OPENAI_API_KEY>
GOOGLE_TOKEN_PATH=token.pickle
GOOGLE_CREDENTIALS_JSON=credentials.json
TIMEZONE=US/Pacific

Download google credentials json from Google console.

## Example

```
>>> from scheduler_agent import SchedulerAgent
>>> agent = SchedulerAgent()
>>> agent.schedule("Set a sync call with Sarah tomorrow at 2pm")
"📝 Simulated: 'Sync call with Sarah' at 2024-05-22 02:00 PM UTC"
```

The agent now composes event titles in the form `"<title> with <person>"`.
