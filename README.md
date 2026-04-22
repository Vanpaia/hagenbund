# Gentleboys Clubhouse

A private prediction tracking and live quiz app for a group of friends. Members submit predictions across five categories (Politics, Economy, Finance, Science, Entertainment), vote on outcomes, track a stock portfolio, earn achievements, and compete in live buzzer-style quiz rounds. Group notifications are delivered via Signal.

## Features

- **Predictions** — submit, vote on conclusions, earn points and achievements
- **Stock portfolio** — track picks against an initial price using the Financial Modeling Prep API
- **Achievements** — 22 unlockable badges with real-time Socket.IO notifications
- **Live game** — host a buzzer quiz round with pause/resume and round tracking
- **Signal notifications** — group messages on key events via signal-cli

---

## Requirements

- Python 3.10+
- [signal-cli](https://github.com/AsamK/signal-cli) (for group notifications)
- A [Financial Modeling Prep](https://financialmodelingprep.com/) API key (for stock data)

---

## Installation

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd hagenbund
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```ini
# Flask
SECRET_KEY=change-me-to-a-long-random-string

# Financial Modeling Prep (stock data)
FMP_API=your_fmp_api_key_here

# Signal (optional — app works without it, events are just not sent)
PHONE_NUMBER=+1234567890
SIGNAL_GROUP=your_base64_encoded_group_id
SIGNAL_CLI_PATH=/path/to/signal-cli
SIGNAL_LOG_PATH=logs/signal_errors.log
```

#### `config.ini` (optional overrides)

A `config.ini` file in the project root controls a few non-secret values:

```ini
[DEFAULT]
vote_limit = 3      # votes needed to accept/reject a prediction conclusion
```

### 3. Initialise the database

```bash
python setup_db.py
```

This creates all tables and seeds the 22 achievements and the default users. It is idempotent — safe to run again if you add new achievements or users.

If you have run `flask db init` before and want to use Alembic migrations instead:

```bash
flask db upgrade
```

### 4. Run the app

```bash
python run.py
```

The app starts on `http://localhost:5000` with Socket.IO support via gevent.

---

## Getting a Financial Modeling Prep API key

1. Sign up at [financialmodelingprep.com](https://financialmodelingprep.com/developer/docs/)
2. After login, find your API key in the dashboard
3. The free tier supports stock profile lookups and name search, which is all the app needs
4. Set it as `FMP_API` in your `.env`

The app calls two endpoints:
- `GET /stable/search-name?query=…` — stock ticker search
- `GET /stable/profile?symbol=…` — stock profile (price, industry, name)

---

## Setting up signal-cli

The app uses [signal-cli](https://github.com/AsamK/signal-cli) to send messages to a Signal group when predictions are concluded. This section is only needed if you want group notifications.

### 1. Install signal-cli

Download the latest release from [github.com/AsamK/signal-cli/releases](https://github.com/AsamK/signal-cli/releases).

```bash
# Example for Linux (adjust version as needed)
tar -xzf signal-cli-0.x.x.tar.gz
sudo mv signal-cli-0.x.x /opt/signal-cli
export PATH="/opt/signal-cli/bin:$PATH"
```

Requires Java 17+ (`java -version` to check).

### 2. Register or link a phone number

**Option A — register a new number** (needs a phone number that can receive SMS):

```bash
signal-cli -a +1234567890 register
signal-cli -a +1234567890 verify <SMS-code>
```

**Option B — link an existing Signal account** (recommended if you already have Signal on that number):

```bash
signal-cli link --name "server"
```

Scan the QR code from an existing Signal device.

### 3. Find your group ID

```bash
signal-cli -a +1234567890 listGroups
```

Copy the `Id:` value — it is a base64 string that looks like `aBcDeFgH…==`.

### 4. Set the environment variables

```ini
PHONE_NUMBER=+1234567890
SIGNAL_GROUP=aBcDeFgH...==
SIGNAL_CLI_PATH=/opt/signal-cli/bin/signal-cli
```

### 5. Test it

```bash
python scripts/test_signal.py
```

Errors are logged to `SIGNAL_LOG_PATH` (default `logs/signal_errors.log`).

---

## Running tests

```bash
pytest tests/
```

Tests use an in-memory SQLite database and mock all Signal and external API calls. No network access or signal-cli installation required.

---

## Project structure

```
hagenbund/
├── app/
│   ├── auth/           # Login / logout routes
│   ├── main/           # Core routes and Socket.IO events
│   ├── utils/
│   │   ├── signal.py   # Signal-cli wrapper
│   │   └── stocks.py   # FMP API wrapper
│   ├── models.py
│   ├── achievements.py
│   └── live_game.py    # Live quiz game state
├── migrations/         # Alembic migrations
├── scripts/            # One-off utility scripts
├── tests/
├── setup_db.py         # DB initialisation and seeding
├── config.py
├── config.ini
└── run.py
```
