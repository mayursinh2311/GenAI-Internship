# Day 26: Bank account specialist with a tool loop

A CLI support bot built on Mistral. A router reads the customer question and sends it to one
specialist: cinema booking, snacks, bank account, or general. The bank account specialist is
new. Unlike the other specialists, it runs a loop: it keeps calling tools until the model
stops asking for them, with a hard cap of 5 rounds.

## How it works

1. You type a question such as `What is my balance for account 100000001234?` or
   `Block card CARD1234`.
2. A router call (temperature 0) replies with one label: `booking`, `snacks`, `account`,
   or `general`.
3. The matching specialist answers:
   - **booking**: has `track_booking(booking_id)` for cinema bookings.
   - **snacks**: has `get_menu()` and `check_price(item)` for the snacks menu.
   - **account**: has `get_balance`, `list_transactions`, `block_card` and
     `transfer_money`. It loops over tools for up to 5 rounds.
   - **general**: no tools, plain polite answer.
4. For the account specialist, each round prints the round number and the tools called:
   ```
   Round 1: get_balance
   get_balance => Account ********1234 (Asha Kumar): balance Rs 45230.50
   ```
5. The final answer is printed after `Support:`.

## Guardrails

- **Loop limit**: the account specialist stops when the model returns no tool calls, and
  never runs more than 5 rounds.
- **Human confirmation**: `block_card` and `transfer_money` ask for a `yes` answer in code
  before they change anything. Any other answer cancels the action.
- **PII masking**: account numbers are masked to the last 4 digits in tool results and in
  every final reply. A 12-digit account `100000001234` appears as `********1234`.
- **Tool errors**: a tool exception becomes an error string that goes back to the model, so
  the bot can explain the problem instead of crashing.

## Demo data

- Accounts: `100000001234` (Asha Kumar), `100000005678` (Ravi Sharma),
  `100000009999` (Neha Verma).
- Cards: `CARD1234` and `CARD5678`, both active at the start.
- Transactions: a few demo entries per account.
- Transfer limit: Rs 50,000 per source account per day.
- Cinema bookings: `BK201` and `BK202`.
- Snacks: popcorn, nachos, coke, water, coffee, samosa.

## Files

- `bank_agent.py`: router, specialists, account loop, tools, masking, confirmation and CLI.
- `tests.py`: 5 tests for masking, loop stopping, the 5-round cap and confirmation.
- `requirements.txt`: the Python packages you need.
- `.env.example`: the key the app expects.

## Setup

Install the packages:

```bash
pip install -r requirements.txt
```

Create a `.env` file in this folder:

```
MISTRAL_API_KEY=your_mistral_key_here
```

## Run

```bash
python bank_agent.py
```

## Run the tests

The tests mock the Mistral call, so they do not need an API key.

```bash
python tests.py
```

## Test inputs

Account:

- What is my balance for account 100000001234?
- Show the last 3 transactions for account 100000001234.
- Block card CARD1234.
- Transfer 5000 from 100000001234 to 100000005678.

Booking:

- Where is my booking BK201?

Snacks:

- How much is popcorn?

General:

- What are your support hours?

## Notes

- Account ids are 12-digit strings. The bot masks them before showing any reply.
- `block_card` asks `Confirm blocking card CARD1234? (yes/no):` in the terminal. Type
  `yes` to block it. Anything else cancels.
- `transfer_money` asks for confirmation too, and rejects a transfer above the daily limit.
- The account loop prints `Round N: tool1, tool2` before running the tools for that round.
- `.env` holds the real key. It is ignored by git.
