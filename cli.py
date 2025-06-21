from scheduler_agent import SchedulerAgent
from config import Config

def main():
    agent = SchedulerAgent()
    print("Meeting Scheduler - Example prompts:")
    for p in Config.KNOWN_CONTACTS.keys():
        pass  # Use in real UI
    while True:
        txt = input('You: ')
        if txt.lower() in ('exit','quit'):
            print('Goodbye!')
            break
        print(agent.schedule(txt))

if __name__ == '__main__':
    main()