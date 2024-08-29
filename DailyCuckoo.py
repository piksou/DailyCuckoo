import argparse
import requests
import json
import re
import urllib.parse
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StockData:
    symbol: str
    name: str
    price: float
    change_percentage: float
    timestamp: datetime
    change_value: float
    open: float
    high: float
    low: float
    year_high: float
    year_low: float
    volume: int
    avg_volume: int
    market_cap: float
    earnings_per_share: float
    price_to_earnings_ratio: str
    dividend_yield: float
    capital: int
    pre_market_after_hours_price: float
    pre_market_after_hours_price_change_percent: float
    pre_market_after_hours_price_change_value: float
    pre_market_after_hours_price_time: str
    last_trade_time: str
    prev_close: float
    pre_market_after_hours_volume: int
    year: int


class StockDataFetcher:
    BASE_URL = "https://hq.sinajs.cn/etag.php"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://stock.finance.sina.com.cn/",
        }

    def fetch_data(self, symbols: List[str]) -> str:
        rn = int(datetime.now().timestamp() * 1000)
        symbol_list = ",".join(f"gb_{symbol.lower()}" for symbol in symbols)
        url = f"{self.BASE_URL}?rn={rn}&list={symbol_list}"
        response = requests.get(url, headers=self.headers)
        return response.text


class StockDataParser:
    @staticmethod
    def safe_convert(value: str, type_: type) -> Optional[Union[int, float, str]]:
        if not value:
            return None
        try:
            return type_(value)
        except ValueError:
            return None

    @classmethod
    def parse_data(cls, data: str) -> Dict[str, StockData]:
        result = {}
        pattern = r'var hq_str_gb_(\S+?)="(.+?)";'
        matches = re.findall(pattern, data)
        for match in matches:
            symbol, values = match
            fields = values.split(",")
            result[symbol.upper()] = StockData(
                symbol=symbol.upper(),
                name=fields[0],
                price=cls.safe_convert(fields[1], float),
                change_percentage=cls.safe_convert(fields[2], float),
                timestamp=(
                    datetime.strptime(fields[3], "%Y-%m-%d %H:%M:%S")
                    if fields[3]
                    else None
                ),
                change_value=cls.safe_convert(fields[4], float),
                open=cls.safe_convert(fields[5], float),
                high=cls.safe_convert(fields[6], float),
                low=cls.safe_convert(fields[7], float),
                year_high=cls.safe_convert(fields[8], float),
                year_low=cls.safe_convert(fields[9], float),
                volume=cls.safe_convert(fields[10], int),
                avg_volume=cls.safe_convert(fields[11], int),
                market_cap=cls.safe_convert(fields[12], float),
                earnings_per_share=cls.safe_convert(fields[13], float),
                price_to_earnings_ratio=fields[14],
                dividend_yield=cls.safe_convert(fields[17], float),
                capital=cls.safe_convert(fields[19], int),
                pre_market_after_hours_price=cls.safe_convert(fields[21], float),
                pre_market_after_hours_price_change_percent=cls.safe_convert(
                    fields[22], float
                ),
                pre_market_after_hours_price_change_value=cls.safe_convert(
                    fields[23], float
                ),
                pre_market_after_hours_price_time=fields[24],
                last_trade_time=fields[25],
                prev_close=cls.safe_convert(fields[26], float),
                pre_market_after_hours_volume=cls.safe_convert(fields[27], int),
                year=cls.safe_convert(fields[29], int),
            )
        return result


class PortfolioManager:
    def __init__(self, settings_file: str):
        self.portfolio: Dict[str, int] = {}
        self.cash: float = 0
        self.fetcher = StockDataFetcher()
        self.parser = StockDataParser()
        self.stock_data: Dict[str, StockData] = {}
        self.settings = self.load_settings(settings_file)
        self.benchmark_index = self.settings["benchmark_index"]
        self.benchmark_name = self.settings["benchmark_name"]

    def load_settings(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_portfolio(self, file_path: str):
        with open(file_path, "r") as f:
            data = json.load(f)
            self.portfolio = {k: v for k, v in data.items() if k != "cash_balance"}
            self.cash = data.get("cash_balance", 0)

    def save_portfolio(self, file_path: str):
        data = {**self.portfolio, "cash_balance": self.cash}
        with open(file_path, "w") as f:
            json.dump(data, f)

    def update_stock_data(self):
        symbols = list(self.portfolio.keys()) + [self.benchmark_index]
        raw_data = self.fetcher.fetch_data(symbols)
        self.stock_data = self.parser.parse_data(raw_data)

    def calculate_nlv(self) -> Dict[str, Any]:
        nlv = self.cash
        prev_nlv = self.cash
        stock_details = {}

        for symbol, quantity in self.portfolio.items():
            if symbol not in self.stock_data:
                print(f"Warning: No data available for {symbol}")
                continue

            stock = self.stock_data[symbol]
            current_value = stock.price * quantity
            prev_value = stock.prev_close * quantity

            nlv += current_value
            prev_nlv += prev_value

            change = current_value - prev_value
            change_percentage = (change / prev_value) * 100 if prev_value != 0 else 0

            stock_details[symbol] = {
                "quantity": quantity,
                "current_price": stock.price,
                "prev_price": stock.prev_close,
                "change": change,
                "change_percentage": change_percentage,
            }

        total_change = nlv - prev_nlv
        total_change_percentage = (
            (total_change / prev_nlv) * 100 if prev_nlv != 0 else 0
        )

        market_comment = self.get_market_comment()

        return {
            "nlv": nlv,
            "change": total_change,
            "change_percentage": total_change_percentage,
            "stock_details": stock_details,
            "market_comment": market_comment,
        }

    def get_market_comment(self) -> str:
        benchmark_data = self.stock_data.get(self.benchmark_index.upper())
        if not benchmark_data:
            return f"Unable to retrieve {self.benchmark_name} index data"

        change_percentage = benchmark_data.change_percentage
        percentage_str = (
            f"{'+' if change_percentage > 0 else ''}{change_percentage:.2f}%"
        )

        for comment_config in self.settings["market_comments"]:
            if change_percentage < comment_config["threshold"]:
                return comment_config["comment"].format(
                    benchmark_name=self.benchmark_name, percentage=percentage_str
                )

        return self.settings["market_comments"][-1]["comment"].format(
            benchmark_name=self.benchmark_name, percentage=percentage_str
        )

    def generate_report_json(self) -> str:
        nlv_data = self.calculate_nlv()
        report = {
            "market_comment": nlv_data["market_comment"],
            "benchmark_index": self.benchmark_name,
            "benchmark_change": self.stock_data[
                self.benchmark_index.upper()
            ].change_percentage,
            "nlv": {
                "current": round(nlv_data["nlv"], 2),
                "change": round(nlv_data["change"], 2),
                "change_percentage": round(nlv_data["change_percentage"], 2),
            },
            "stock_details": {
                symbol: {
                    "quantity": details["quantity"],
                    "current_price": round(details["current_price"], 2),
                    "change": round(details["change"], 2),
                    "change_percentage": round(details["change_percentage"], 2),
                }
                for symbol, details in nlv_data["stock_details"].items()
            },
        }
        return json.dumps(report, indent=2)

    def generate_report_string(self, include_market_comment: bool = True) -> str:
        nlv_data = self.calculate_nlv()
        report = []

        if include_market_comment:
            report.extend(
                ["Market Commentary", "-" * 30, nlv_data["market_comment"], ""]
            )

        report.extend(
            [
                "NLV Report",
                "-" * 30,
                f"Current NLV: ${nlv_data['nlv']:.2f}",
                f"Change: ${nlv_data['change']:.2f}",
                f"Change Percentage: {nlv_data['change_percentage']:+.2f}%",
                "",
                "Detailed Stock Report",
                "-" * 45,
                f"{'Symbol':<10}{'Quantity':<10}{'NLV Change':<15}{'Change %':<10}",
                "-" * 45,
            ]
        )

        for symbol, details in nlv_data["stock_details"].items():
            report.append(
                f"{symbol:<10}{details['quantity']:<10}${details['change']:<14.2f}{details['change_percentage']:+.2f}%"
            )
        return "\n".join(report)


class NotificationService:
    @staticmethod
    def send_bark_notification(settings: Dict[str, Any], title: str, body: str):
        try:
            encoded_title = urllib.parse.quote(title)
            encoded_body = urllib.parse.quote(body)

            url = f"https://api.day.app/{settings['bark_key']}/{encoded_title}/{encoded_body}?group={settings['bark_group']}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            print("Bark notification sent successfully")
        except requests.RequestException as e:
            print(f"Failed to send Bark notification: {e}")
        except Exception as e:
            print(f"Unexpected error when sending Bark notification: {e}")


def main():

    parser = argparse.ArgumentParser(
        description="A daily portfolio value notifier for long-term investors"
    )

    parser.add_argument(
        "-s", "--show", action="store_true", help="Output the report as a string"
    )
    parser.add_argument(
        "-j", "--json", action="store_true", help="Output the report as a JSON"
    )

    args = parser.parse_args()

    if args.show and args.json:
        print("Error: Please choose either --show or --json")
        return

    portfolio_manager = PortfolioManager("settings.json")
    portfolio_manager.load_portfolio("portfolio.json")
    portfolio_manager.update_stock_data()

    if args.json:
        print(portfolio_manager.generate_report_json())
    elif args.show:
        print(portfolio_manager.generate_report_string())
    else:
        market_comment = portfolio_manager.get_market_comment()
        NotificationService.send_bark_notification(
            settings=portfolio_manager.settings,
            title=market_comment,
            body=portfolio_manager.generate_report_string(False),
        )


if __name__ == "__main__":
    main()
