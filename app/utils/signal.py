import subprocess

def send_signal_message(account_number, recipient_number, message):
    command = [
        "signal-cli",
        "-a", account_number,
        "send",
        "-m", message,
        recipient_number
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("Message sent successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error sending message: {e.stderr}")

