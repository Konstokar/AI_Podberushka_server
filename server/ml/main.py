import torch
import torch.nn as nn
import torch.optim as optim
import requests
import json
import random

from external_data import get_bond_data, get_stock_data_moex
from models.risk_assessment_model import RiskAssessment

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

    for stock in stocks[:50]:
        ticker = stock[0] if len(stock) > 0 else "Нет данных"
        print(ticker)

        try:
            stock_details = get_stock_data_moex(ticker)
        except Exception as e:
            print(f"Ошибка при получении данных по облигации {ticker}: {e}")
            continue


        info = {
            'name': stock_details["Название"],
            'ticker': ticker,
            'price': stock_details["Стоимость"],
            'is_divids': stock_details["Наличие дивидендов"],
            'dividend': {
                'yield': stock_details["Размер дивиденда"],
                'frequency': stock_details["Частота выплат дивидендов в год"]
            },
            'annual_return': stock_details["Доходность (%)"]
        }
        stock_info.append(info)
    return stock_info


def extract_bond_data(data):
    bonds = data.get('securities', {}).get('data', [])
    bond_info = []

    for bond in bonds[:50]:
        ticker = bond[0] if len(bond) > 0 else "Нет данных"
        print(ticker)

        try:
            bond_details = get_bond_data(ticker)
        except Exception as e:
            print(f"Ошибка при получении данных по облигации {ticker}: {e}")
            continue

        bond_info.append({
            'name': bond_details['Название'],
            'ticker': bond_details['Тикер'],
            'coupon': {
                'size': bond_details['Размер купона'],
                'frequency_per_year': bond_details['Частота выплат купонов в год']
            },
            'maturity_date': bond_details['Дата погашения'],
            'annual_return': bond_details['Доходность к погашению (%)'],
            'price': bond_details['Текущая цена']
        })
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
            dividend_yield = float(stock['dividend']['yield'])
        except (ValueError, TypeError):
            dividend_yield = 0
        X.append([0, dividend_yield])

        if dividend_yield < 2:
            y.append(2)  # High risk
        else:
            y.append(1)  # Medium risk

    for bond in bond_data:
        coupon_freq = bond['coupon']['frequency_per_year']
        credit_rating = 1 if coupon_freq == "AAA" else 2 if coupon_freq == "AA" else 3
        X.append([0, credit_rating])

        if credit_rating == 3:
            y.append(1)  # Medium risk
        else:
            y.append(0)  # Low risk

    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.long)

def train_model(model, criterion, optimizer, X_train, y_train, epochs=100):
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_train)
        loss = criterion(outputs, y_train)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch + 1}/{epochs}], Loss: {loss.item():.4f}")

def run_analysis():
    print("Запуск анализа рынка пошёл")
    stocks_data = get_data(stocks_url)
    bonds_data = get_data(bonds_url)

    random.seed(42)
    stock_info = random.sample(extract_stock_data(stocks_data), min(50, len(stocks_data['securities']['data'])))
    bond_info = random.sample(extract_bond_data(bonds_data), min(50, len(bonds_data['securities']['data'])))

    X_train, y_train = prepare_data(stock_info, bond_info)
    model = RiskClassifier()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    train_model(model, criterion, optimizer, X_train, y_train)
    torch.save(model.state_dict(), 'ml/risk_classifier_model.pth')
    print("Модель обучена и сохранена в risk_classifier_model.pth")

    def predict_and_save_results(model, stock_data, bond_data):
        model.eval()
        stock_predictions = []
        bond_predictions = []

        for stock in stock_data:
            try:
                dividend_yield = float(stock['dividend']['yield'])
            except (ValueError, TypeError):
                dividend_yield = 0
            input_data = torch.tensor([[0, dividend_yield]], dtype=torch.float32)
            output = model(input_data)
            risk_level = torch.argmax(output, dim=1).item()
            stock_predictions.append((stock, risk_level))

        for bond in bond_data:
            coupon_freq = bond['coupon']['frequency_per_year']
            credit_rating = 1 if coupon_freq == "AAA" else 2 if coupon_freq == "AA" else 3
            input_data = torch.tensor([[0, credit_rating]], dtype=torch.float32)
            output = model(input_data)
            risk_level = torch.argmax(output, dim=1).item()
            bond_predictions.append((bond, risk_level))

        result = {
            "Low": {"Bonds": []},
            "Medium": {"Stocks": [], "Bonds": []},
            "High": {"Stocks": []}
        }

        risk_map = {0: "Low", 1: "Medium", 2: "High"}

        if len(result["Low"]["Bonds"]) == 0:
            result["Low"]["Bonds"] = bond_info[:50]

        if len(result["Medium"]["Stocks"]) == 0:
            result["Medium"]["Stocks"] = stock_info[:50]

        if len(result["High"]["Stocks"]) == 0:
            result["High"]["Stocks"] = stock_info[:50]

        for stock, risk_level in stock_predictions:
            result[risk_map[risk_level]]["Stocks"].append(stock)

        for bond, risk_level in bond_predictions:
            result[risk_map[risk_level]]["Bonds"].append(bond)
        with open('ml/risk_assessment.json', 'w') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        RiskAssessment.save(result)
        print("Результаты сохранены в risk_assessment.json и базу данных")

    predict_and_save_results(model, stock_info, bond_info)

if __name__ == "__main__":
    run_analysis()