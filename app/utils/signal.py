import subprocess
from datetime import datetime
from config import Config


def send_signal_message(account_number, group_id, message):
    app_id = "🍻 GENTLEBOY UPDATE 🍻\n\n"
    message = f'{app_id}{message}'
    command = [
        Config.SIGNAL_CLI_PATH,
        "-a", account_number,
        "send",
        "-g", group_id,
        "-m", message
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("Message sent successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error sending message: {e.stderr}")
        with open(Config.SIGNAL_LOG_PATH, "a") as f:
            f.write(f"{datetime.now()}: {e.stderr}\n")
