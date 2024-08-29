# DailyCuckoo

A daily portfolio value notifier for long-term investors.

DailyCuckoo is a script for long-term investors who still appreciate a daily reminder of their Net Liquidation Value (NLV). It uses the `sina` stock API for stock data and `bark` for notifications.

## How to use
1. Make sure you have installed Python 3.9 or higher (3.6+ may work but is not guaranteed)
2. Install the required dependencies by running `pip install -r requirements.txt`
3. Edit `settings.json` to configure your personal settings (see "settings.json" section below)
4. Edit `portfolio.json` to input your portfolio details (see "portfolio.json" section below)
5. Add `dailycuckoo.py` to your `cron` file (Linux/Mac) or Windows Task Scheduler to run it automatically

## settings.json

- `bark_key`: Your Bark API key
- `bark_group`: The group name which Bark uses
- `benchmark_index`: The benchmark index (e.g., `$ixic` for NASDAQ, `$inx` for S&P500, `$dji` for Dow Jones)
- `benchmark_name`: The display name for the `benchmark_index`, which will appear in the notification title
- `market_comments`: Comments about the market when it's in certain ranges, to be displayed in the notification title
- `threshold`: The threshold for index percentage change. When the change percentage is less than this value, the corresponding comment will be applied. Always fits the first criteria.

Example:
```json
{
  "bark_key": "your_bark_key",
  "bark_group": "your_group_name",
  "benchmark_index": "$ixic",
  "benchmark_name": "NASDAQ",
  "market_comments": [
    {
      "threshold": -2.0,
      "comment": "📉 U.S. Economy Collapses! {benchmark_name} {percentage}"
    },
    {
      "threshold": -1.0,
      "comment": "💥 Market Turmoil! {benchmark_name} {percentage}"
    },
    {
      "threshold": -0.5,
      "comment": "🔻 Market Decline. {benchmark_name} {percentage}"
    },
    {
      "threshold": 0.5,
      "comment": "🔹 Market Stable. {benchmark_name} {percentage}"
    },
    {
      "threshold": 1.0,
      "comment": "🔼 Market Uptick. {benchmark_name} {percentage}"
    },
    {
      "threshold": 2.0,
      "comment": "📈 Strong Market Rally. {benchmark_name} {percentage}"
    },
    {
      "threshold": Infinity,
      "comment": "🚀 To the MOON! {benchmark_name} {percentage}"
    }
  ]
}
```

## portfolio.json

A JSON dictionary specifying your portfolio. The key is the stock symbol, and the value is the number of shares. Use the `cash_balance` key to specify your cash holdings.

Example:
```json
{
  "AAPL": 120,
  "NVDA": 200,
  "QQQ": 110,
  "SPY": 200,
  "cash_balance": 888.88
}
```

### Options

The script supports the following options:

- `--help` or `-h`: display help message
- `--show` or `-s`: output the report as a string
- `--json` or `-j`: output the report as a JSON string


## Dependencies

see `requirements.txt`

## DISCLAIMER

The script is for educational or research purposes only.

The information provided in this script is for informational purposes only. It should not be relied upon for making investment decisions.