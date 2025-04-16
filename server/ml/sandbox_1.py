import re
import time
import torch
import torch.nn as nn
import torch.optim as optim
import requests
import json
import random
from external_data import get_bond_data, get_stock_data_moex

stocks_url = 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json'
bonds_url = 'https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQOB/securities.json'


def get_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка: статус-код {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return None


def extract_stock_data(data):
    stocks = data.get('securities', {}).get('data', [])
    stock_info = []

    for stock in stocks:
        if len(stock_info) >= 50:  # Остановить, если собрано 50 акций
            break

        ticker = stock[0] if len(stock) > 0 else "Нет данных"
        print(f"Проверяем акцию: {ticker}")

        try:
            stock_details = get_stock_data_moex(ticker)
        except Exception as e:
            print(f"Ошибка при получении данных по акции {ticker}: {e}")
            continue

        price = stock_details["Стоимость"]
        annual_return = stock_details["Доходность (%)"] if stock_details["Доходность (%)"] is not None else \
        stock_details["CAGR (%)"]

        if price is None or annual_return is None:
            print(f"Пропускаем акцию {ticker}: отсутствуют цена или доходность.")
            continue

        stock_info.append({
            'name': stock_details["Название"],
            'ticker': ticker,
            'price': price,
            'is_divids': stock_details["Наличие дивидендов"],
            'dividend': {
                'yield': stock_details["Размер дивиденда"],
                'frequency': stock_details["Частота выплат дивидендов в год"]
            },
            'annual_return': annual_return
        })

    print(f"Выбрано {len(stock_info)} акций.")
    return stock_info


def extract_bond_data(data):
    bonds = data.get('securities', {}).get('data', [])
    bond_info = []

    for bond in bonds:
        if len(bond_info) >= 50:  # Остановить, если собрано 50 облигаций
            break

        ticker = bond[0] if len(bond) > 0 else "Нет данных"
        print(f"Проверяем облигацию: {ticker}")

        try:
            bond_details = get_bond_data(ticker)
        except Exception as e:
            print(f"Ошибка при получении данных по облигации {ticker}: {e}")
            continue

        annual_return = bond_details['Доходность к погашению (%)']
        price = bond_details['Текущая цена']
        maturity_date = bond_details['Дата погашения']
        coupon_size = bond_details['Размер купона']
        coupon_frequency = bond_details['Частота выплат купонов в год']

        if any(val is None for val in [annual_return, price, maturity_date, coupon_size, coupon_frequency]):
            print(f"Пропускаем облигацию {ticker}: отсутствуют важные параметры.")
            continue

        bond_info.append({
            'name': bond_details['Название'],
            'ticker': bond_details['Тикер'],
            'coupon': {
                'size': coupon_size,
                'frequency_per_year': coupon_frequency
            },
            'maturity_date': maturity_date,
            'annual_return': annual_return,
            'price': price
        })

    print(f"Выбрано {len(bond_info)} облигаций.")
    return bond_info


class RiskClassifier(nn.Module):
    def __init__(self):
        super(RiskClassifier, self).__init__()
        self.fc1 = nn.Linear(2, 16)
        self.fc2 = nn.Linear(16, 16)
        self.fc3 = nn.Linear(16, 3)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def prepare_data(stock_data, bond_data):
    X = []
    y = []

    for stock in stock_data:
        try:
            dividend_yield = float(stock['dividend']['yield']) if stock['dividend']['yield'] is not None else 0
        except ValueError:
            dividend_yield = 0
        X.append([0, dividend_yield])

        if dividend_yield < 2:
            y.append(2)  # High risk
        else:
            y.append(1)  # Medium risk

    for bond in bond_data:
        try:
            coupon_freq = int(bond['coupon']['frequency_per_year']) if bond['coupon']['frequency_per_year'] is not None else 1
        except ValueError:
            coupon_freq = 1

        X.append([0, coupon_freq])

        if coupon_freq <= 2:
            y.append(1)  # Medium risk
        else:
            y.append(0)  # Low risk

    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.long)


stocks_data = get_data(stocks_url)
bonds_data = get_data(bonds_url)

random.seed(42)
stock_info = extract_stock_data(stocks_data)
bond_info = extract_bond_data(bonds_data)

X_train, y_train = prepare_data(stock_info, bond_info)
model = RiskClassifier()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)


def train_model(model, criterion, optimizer, X_train, y_train, epochs=100):
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_train)
        loss = criterion(outputs, y_train)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch + 1}/{epochs}], Loss: {loss.item():.4f}")


train_model(model, criterion, optimizer, X_train, y_train)
torch.save(model.state_dict(), 'risk_classifier_model.pth')
print("Модель обучена и сохранена в risk_classifier_model.pth")


def predict_and_save_results(model, stock_data, bond_data):
    model.eval()
    stock_predictions = []
    bond_predictions = []

    for stock in stock_data:
        try:
            stock_details = get_stock_data_moex(stock['ticker'])
            stock['price'] = stock_details["Стоимость"]
        except Exception as e:
            print(f"Ошибка при обновлении данных акции {stock['ticker']}: {e}")
            stock['price'] = 0

        dividend_yield = float(stock['dividend']['yield']) if stock['dividend']['yield'] else 0
        input_data = torch.tensor([[0, dividend_yield]], dtype=torch.float32)
        output = model(input_data)
        risk_level = torch.argmax(output, dim=1).item()
        stock_predictions.append((stock, risk_level))

    for bond in bond_data:
        try:
            bond_details = get_bond_data(bond['ticker'])
            bond['price'] = bond_details["Текущая цена"]
        except Exception as e:
            print(f"Ошибка при обновлении данных облигации {bond['ticker']}: {e}")
            bond['price'] = 0

        coupon_freq = bond['coupon']['frequency_per_year']
        credit_rating = 1 if coupon_freq == "AAA" else 2 if coupon_freq == "AA" else 3
        input_data = torch.tensor([[0, credit_rating]], dtype=torch.float32)
        output = model(input_data)
        risk_level = torch.argmax(output, dim=1).item()
        bond_predictions.append((bond, risk_level))

    result = {
        "Low": {"Bonds": bond_info[:25]},  # Добавляем 25 первых облигаций в Low
        "Medium": {"Stocks": [], "Bonds": []},
        "High": {"Stocks": []}
    }

    risk_map = {0: "Low", 1: "Medium", 2: "High"}

    for stock, risk_level in stock_predictions:
        result[risk_map[risk_level]]["Stocks"].append(stock)

    for bond, risk_level in bond_predictions[25:]:  # Оставшиеся облигации после первых 25
        result[risk_map[risk_level]]["Bonds"].append(bond)

    with open('risk_assessment.json', 'w') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    print("Результаты сохранены в risk_assessment.json")


predict_and_save_results(model, stock_info, bond_info)