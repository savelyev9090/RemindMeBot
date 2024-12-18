import json

def load_messages_and_buttons(language: str):
    try:
        with open(f"/Users/leonidserbin/Downloads/RemindMe/source/messages/{language}.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file for language '{language}' was not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: The file for language '{language}' contains invalid JSON.")
        return {}

data = load_messages_and_buttons("ru")

MESSAGES = data.get("messages", {})
BUTTONS = data.get("buttons", {})