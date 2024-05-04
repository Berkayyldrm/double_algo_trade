from datetime import datetime
import time
import traceback
from binance.client import Client
import numpy as np
from binance.enums import *
from google.cloud import secretmanager
import logging

class CustomLogger:
    def __init__(self, name, log_file, level=logging.DEBUG):
        self.log_file = log_file
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            formatter = logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', '%H:%M:%S')
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger
    
    def clear_log_file(self):
        open(self.log_file, 'w').close()

class Main:
    def __init__(self):
        self.logger = CustomLogger('general', 'general.log').get_logger()
        self.symbol = "WLDUSDT"
        self.bnb_future_api_key, self.bnb_future_secret_key = self.gcloud_secret("project_id", "btrder", "1")
        self.leverage = 2
        self.symbol_precision = 0 
        self.client = Client(self.bnb_future_api_key, self.bnb_future_secret_key)
        self.raise_rate = 0.02
        self.close_position_roi = self.raise_rate * self.leverage * 100
        try:
            self.client.futures_change_margin_type(symbol=self.symbol, marginType="ISOLATED")
        except: # NO_NEED_TO_CHANGE_MARGIN_TYPE
            pass
        self.client.futures_change_leverage(symbol=self.symbol, leverage=self.leverage)
    
    def gcloud_secret(self, project_id, secret_id, version_id):
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(name=name)
        future_api_key, future_secret_key = response.payload.data.decode('UTF-8').split()
        return future_api_key.split("=")[1], future_secret_key.split("=")[1]

    def calculate_quantity(self, amount):
        amount = amount * self.leverage
        price = self.client.futures_symbol_ticker(symbol=self.symbol)["price"]
        price = float(price)
        quantity = amount/price
        scaled_number = quantity * (10 ** self.symbol_precision)
        floored_number = np.floor(scaled_number)
        quantity = floored_number / (10 ** self.symbol_precision)
        return quantity - 1
    
    def position_info(self):
        positions = self.client.futures_position_information(symbol=self.symbol)
        long_roi = 0
        long_amount = 0
        if positions:
            for pos in positions:
                position_amount = float(pos["positionAmt"])
                position_entryPrice = float(pos["entryPrice"])
                position_markPrice = float(pos["markPrice"])
                position_leverage = float(pos["leverage"])
                if position_amount > 0:
                    long_amount = position_amount
                    long_roi = position_leverage * 100 * (position_markPrice - position_entryPrice) / position_entryPrice
        print(datetime.now(), long_roi, long_amount)
        return long_roi, long_amount
    
    def update_position(self):
        while True:
            time.sleep(0.2)
            try:
                long_roi, long_amount = self.position_info()
            except Exception:
                self.logger.info(traceback.format_exc())
            if long_roi >= self.close_position_roi:
                self.logger.info(f"Long roi {long_roi}")
                quantity = long_amount
                self.client.futures_create_order(
                                    symbol=self.symbol,
                                    side=SIDE_SELL,
                                    type=ORDER_TYPE_MARKET,
                                    quantity=quantity
                                    )
                self.logger.info(f"Position closed {quantity}")
                BUY_AMOUNT = self.get_usdt_balance()
                self.logger.info(f"New buy amount {BUY_AMOUNT}")
                quantity = self.calculate_quantity(BUY_AMOUNT)
                self.logger.info(f"Position Opening {quantity}")
                try:
                    self.client.futures_create_order(
                                        symbol=self.symbol,
                                        side=SIDE_BUY,
                                        type=ORDER_TYPE_MARKET,
                                        quantity=quantity
                                        )
                except Exception:
                    self.logger.info(traceback.format_exc())

    def get_usdt_balance(self):
        acc_balance = self.client.futures_account_balance()
        for check_balance in acc_balance:
            if check_balance["asset"] == "USDT":
                usdt_balance = check_balance["balance"]
        return float(usdt_balance)
                    
if __name__ == "__main__":
    main_obj = Main()
    main_obj.update_position()
