import requests
import re
from bs4 import BeautifulSoup


def get_bond_data(ticker):
    base_url = "https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQCB/securities/{}.json"
    url = base_url.format(ticker)

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Ошибка при запросе данных: {response.status_code}")

    data = response.json()

    securities_data = data.get('securities', {}).get('data', [])
    securities_columns = data.get('securities', {}).get('columns', [])
    marketdata_data = data.get('marketdata', {}).get('data', [])
    marketdata_columns = data.get('marketdata', {}).get('columns', [])

    def get_value(columns, data_list, field):
        if field in columns:
            index = columns.index(field)
            return data_list[0][index] if data_list and data_list[0][index] is not None else None
        return None

    bond_info = {
        'Тикер': ticker,
        'Название': get_value(securities_columns, securities_data, 'SHORTNAME'),
        'Дата погашения': get_value(securities_columns, securities_data, 'MATDATE'),
        'Размер купона': get_value(securities_columns, securities_data, 'COUPONVALUE'),
        'Частота выплат купонов в год': None,
        'Текущая цена': get_value(marketdata_columns, marketdata_data, 'LAST'),
        'Доходность к погашению (%)': get_value(marketdata_columns, marketdata_data, 'YIELD')
    }

    coupon_period = get_value(securities_columns, securities_data, 'COUPONPERIOD')
    if coupon_period:
        try:
            bond_info['Частота выплат купонов в год'] = round(365 / int(coupon_period))
        except ValueError:
            bond_info['Частота выплат купонов в год'] = None

    # Если данные отсутствуют, парсим Smart-Lab
    smart_lab_url = f"https://smart-lab.ru/q/bonds/{ticker}/"
    response = requests.get(smart_lab_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()

        # Название облигации
        name_match = re.search(r"Имя облигации\s*(.*?)\s", text)
        if bond_info['Название'] is None and name_match:
            bond_info['Название'] = name_match.group(1).strip()

        # Дата погашения
        maturity_match = re.search(r"Дата погашения\s*(\d{2}-\d{2}-\d{4})", text)
        if bond_info['Дата погашения'] is None and maturity_match:
            bond_info['Дата погашения'] = maturity_match.group(1)

        # Текущая цена
        price_match = re.search(r"Облигация .*? стоит сейчас ([\d,.]+) руб", text)
        if bond_info['Текущая цена'] is None and price_match:
            bond_info['Текущая цена'] = float(price_match.group(1).replace(',', '.'))

        # Доходность к погашению
        yield_match = re.search(r"Доходность\* облигации к погашению составляет ([\d,.]+)%", text)
        if bond_info['Доходность к погашению (%)'] is None and yield_match:
            bond_info['Доходность к погашению (%)'] = float(yield_match.group(1).replace(',', '.'))

        # Размер купона
        coupon_match = re.search(r"Купон, руб \(\?\)\s*([\d,.]+)", text)
        if bond_info['Размер купона'] is None and coupon_match:
            bond_info['Размер купона'] = float(coupon_match.group(1).replace(',', '.'))

        # Частота выплат купонов
        freq_match = re.search(r"Частота купона, раз в год\s*([\d,.]+)", text)
        if bond_info['Частота выплат купонов в год'] is None and freq_match:
            bond_info['Частота выплат купонов в год'] = round(float(freq_match.group(1)))

    return bond_info


def get_stock_data_moex(ticker):
    headers = {'User-Agent': 'Mozilla/5.0'}

    # --- Получаем данные о бумаге ---
    api_url = f"https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker}.json"
    response = requests.get(api_url, headers=headers, timeout=10)

    stock_info = {
        'Тикер': ticker,
        'Название': None,
        'Стоимость': None,
        'Наличие дивидендов': "Нет",
        'Размер дивиденда': 0.0,
        'Частота выплат дивидендов в год': 0,
        'Доходность (%)': None,
        'CAGR (%)': None  # Среднегодовая доходность
    }

    if response.status_code == 200:
        data = response.json()
        columns = data["securities"]["columns"]
        values = data["securities"]["data"]

        if values:
            stock_data = dict(zip(columns, values[0]))

            stock_info['Название'] = stock_data.get("SECNAME", "Неизвестно")
            stock_info['Стоимость'] = stock_data.get("PREVPRICE", None)  # Предыдущая цена закрытия
            stock_info['Доходность (%)'] = stock_data.get("YIELD", None)  # Доходность из API

    # --- Получаем данные о дивидендах ---
    div_url = f"https://iss.moex.com/iss/securities/{ticker}/dividends.json"
    div_response = requests.get(div_url, headers=headers, timeout=10)

    if div_response.status_code == 200:
        div_data = div_response.json()
        div_columns = div_data["dividends"]["columns"]
        div_values = div_data["dividends"]["data"]

        if div_values:
            dividends = [row[div_columns.index("value")] for row in div_values]
            stock_info['Наличие дивидендов'] = "Да"
            stock_info['Размер дивиденда'] = sum(dividends)
            stock_info['Частота выплат дивидендов в год'] = len(dividends)

    # --- Получаем цену акции год назад ---
    history_url = f"https://iss.moex.com/iss/history/engines/stock/markets/shares/securities/{ticker}.json?period=year"
    history_response = requests.get(history_url, headers=headers, timeout=10)

    if history_response.status_code == 200:
        history_data = history_response.json()
        history_columns = history_data["history"]["columns"]
        history_values = history_data["history"]["data"]

        if history_values:
            price_year_ago = history_values[0][history_columns.index("CLOSE")]  # Цена закрытия год назад

            if price_year_ago and stock_info['Стоимость']:
                # --- Расчёт доходности за счёт изменения цены ---
                price_growth_yield = ((stock_info['Стоимость'] - price_year_ago) / price_year_ago) * 100

                # --- Если нет дивидендов, используем доходность роста цены ---
                if stock_info['Доходность (%)'] is None:
                    stock_info['Доходность (%)'] = round(price_growth_yield, 2)

                # --- Расчёт среднегодовой доходности (CAGR) за 1 год ---
                stock_info['CAGR (%)'] = round(((stock_info['Стоимость'] / price_year_ago) ** (1 / 1) - 1) * 100, 2)

    return stock_info