import subprocess

def send_signal_message(account_number, group_id, message):
    command = [
        "signal-cli",
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

