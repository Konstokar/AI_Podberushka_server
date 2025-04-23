import torch
import torch.nn as nn
import torch.optim as optim
import json
import random


class RiskEvaluationNN(nn.Module):
    def __init__(self):
        super(RiskEvaluationNN, self).__init__()
        self.fc1 = nn.Linear(4, 8)
        self.fc2 = nn.Linear(8, 4)
        self.fc3 = nn.Linear(4, 1)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def generate_training_data(num_samples=1000):
    training_data = []
    for _ in range(num_samples):
        answers = [random.randint(0, 4) for _ in range(4)]
        avg_answer = sum(answers) / len(answers)

        if avg_answer < 1.5:
            risk_level = 0
        elif avg_answer < 2.5:
            risk_level = 1
        else:
            risk_level = 2

        training_data.append((answers, risk_level))
    return training_data


def prepare_training_data(training_data):
    X, y = [], []
    for answers, risk_level in training_data:
        X.append(answers)
        y.append(risk_level)
    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)


def train_model(model, criterion, optimizer, X_train, y_train, epochs=100):
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_train).squeeze()
        loss = criterion(outputs, y_train)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch + 1}/{epochs}], Loss: {loss.item():.4f}")


def test_model(model, test_data):
    X_test, y_test = prepare_training_data(test_data)
    model.eval()
    predictions = model(X_test).squeeze().round().detach().numpy()
    correct = sum(predictions == y_test.numpy())
    print(f"Accuracy: {correct / len(y_test) * 100:.2f}%")


def select_securities(risk_level, securities_data):
    def is_valid_security(security):
        # Проверка: все параметры не None и, если это облигация — купон > 0
        if any(value is None for value in security.values()):
            return False
        if "coupon" in security:
            coupon = security["coupon"]
            return coupon and coupon.get("size", 0) > 0
        return True

    risk_categories = ["Low", "Medium", "High"]
    category = risk_categories[risk_level]

    # Фильтрация
    valid_bonds = [bond for bond in securities_data[category].get("Bonds", []) if is_valid_security(bond)]
    valid_stocks = [stock for stock in securities_data[category].get("Stocks", []) if is_valid_security(stock)]

    # Перемешивание
    random.shuffle(valid_bonds)
    random.shuffle(valid_stocks)

    return {
        "Bonds": valid_bonds[:10],
        "Stocks": valid_stocks[:10]
    }


def calculate_expected_return(selection, weighted=False):
    total_return = 0.0
    total_weight = 0.0
    count = 0

    for bond in selection["Bonds"]:
        r = bond.get("annual_return", 0) / 100  # Приводим к десятичной дроби (10% -> 0.1)
        w = bond.get("price", 1)  # Цена в рублях
        if weighted:
            total_return += r * w
            total_weight += w
        else:
            total_return += r
            count += 1

    for stock in selection["Stocks"]:
        r = stock.get("annual_return", 0) / 100
        w = stock.get("price", 1)
        if weighted:
            total_return += r * w
            total_weight += w
        else:
            total_return += r
            count += 1

    if weighted and total_weight > 0:
        return round((total_return / total_weight) * 100, 2)  # Преобразуем обратно в проценты
    elif count > 0:
        return round((total_return / count) * 100, 2)
    else:
        return 0.0


def get_risk_category(risk_level):
    categories = ["Низкий", "Средний", "Высокий"]
    return categories[risk_level]


def main(user_answers_path, securities_path, output_path):
    user_answers = load_json(user_answers_path)
    securities_data = load_json(securities_path)

    user_input = [
        user_answers["question_1"]["answer_grade"],
        user_answers["question_2"]["answer_grade"],
        user_answers["question_3"]["answer_grade"],
        user_answers["question_4"]["answer_grade"]
    ]

    model = RiskEvaluationNN()
    model.load_state_dict(torch.load('user_risk_model.pth'))
    model.eval()

    user_input_tensor = torch.tensor([user_input], dtype=torch.float32)
    risk_level = int(round(model(user_input_tensor).item()))
    risk_level = min(max(risk_level, 0), 3)
    selected_securities = select_securities(risk_level, securities_data)

    result = {
        "Bonds": selected_securities["Bonds"],
        "Stocks": selected_securities["Stocks"],
        "risk_category": get_risk_category(risk_level),
        "expected_return": calculate_expected_return(selected_securities, weighted=True)
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    print(f"Результаты сохранены в {output_path}")


def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    print("Запуск генераци подборки пошёл")
    training_data = generate_training_data()
    X_train, y_train = prepare_training_data(training_data)

    model = RiskEvaluationNN()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    train_model(model, criterion, optimizer, X_train, y_train)
    torch.save(model.state_dict(), 'user_risk_model.pth')
    print("Модель обучена и сохранена в user_risk_model.pth")

    test_data = generate_training_data(num_samples=200)
    test_model(model, test_data)

    user_answers_path = 'ml/user_answers.json'
    securities_path = 'ml/risk_assessment.json'
    output_path = 'ml/selected_securities.json'

    main(user_answers_path, securities_path, output_path)
