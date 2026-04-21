import subprocess

def send_signal_message(account_number, group_id, message):
    app_id = "🍻 GENTLEBOY UPDATE 🍻\n\n"
    message = f'{app_id}{message}'
    command = [
        "/home/hagen/signal-cli/signal-cli",
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
        # Log to a file or monitoring system
        with open("/home/hagen/hagenbund/logs/signal_errors.log", "a") as f:
            f.write(f"{datetime.now()}: {e.stderr}\n")






