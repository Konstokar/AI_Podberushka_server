import requests
import re
from bs4 import BeautifulSoup

def get_stock_data_moex(ticker):
    headers = {'User-Agent': 'Mozilla/5.0'}
    stock_info = {
        'Тикер': ticker,
        'Название': None,
        'Стоимость': None,
        'Наличие дивидендов': "Нет",
        'Размер дивиденда': 0.0,
        'Частота выплат дивидендов в год': 0,
        'Доходность (%)': None,
        'CAGR (%)': None
    }

    max_price = None
    min_price = None

    try:
        # --- API MOEX: Название и marketdata ---
        info_url = f"https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker}.json"
        r = requests.get(info_url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            cols = data["securities"]["columns"]
            vals = data["securities"]["data"]
            if vals:
                d = dict(zip(cols, vals[0]))
                stock_info['Название'] = d.get("SECNAME", "Неизвестно")

        # --- Цена (LAST) ---
        price_url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
        r = requests.get(price_url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            cols = data["marketdata"]["columns"]
            vals = data["marketdata"]["data"]
            if vals:
                d = dict(zip(cols, vals[0]))
                stock_info['Стоимость'] = d.get("LAST")
                max_price = d.get("HIGH")
                min_price = d.get("LOW")

        # --- Последний дивиденд ---
        div_url = f"https://iss.moex.com/iss/securities/{ticker}/dividends.json"
        r = requests.get(div_url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            cols = data["dividends"]["columns"]
            vals = data["dividends"]["data"]
            if vals:
                last_div = vals[0][cols.index("value")]
                stock_info['Наличие дивидендов'] = "Да"
                stock_info['Размер дивиденда'] = last_div
                stock_info['Частота выплат дивидендов в год'] = 1
            else:
                stock_info['Размер дивиденда'] = 0.0
                stock_info['Частота выплат дивидендов в год'] = 0

    except Exception as e:
        print(f"Ошибка при запросе API MOEX для {ticker}: {e}")

    # --- Парсинг BCS ---
    if (stock_info['Стоимость'] is None or stock_info['Размер дивиденда'] == 0 or max_price is None or min_price is None):
        try:
            bcs_url = f"https://bcs.ru/markets/{ticker.lower()}/tqbr"
            r = requests.get(bcs_url, headers=headers, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                text = soup.get_text(" ", strip=True)

                def extract(pattern, cast=float):
                    match = re.search(pattern, text)
                    if match:
                        try:
                            return cast(match.group(1).replace(',', '.').replace(' ', ''))
                        except:
                            return None
                    return None

                # Цена
                if stock_info['Стоимость'] is None:
                    stock_info['Стоимость'] = extract(r"Стоимость\s+[A-Z]+\s+на\s+\d{2}\.\d{2}\.\d{4}\s*—\s*([\d\s,.]+)")

                # Дивиденды
                if stock_info['Размер дивиденда'] == 0:
                    stock_info['Размер дивиденда'] = extract(r"Дивиденды\s+([\d\s,.]+)")
                    if stock_info['Размер дивиденда']:
                        stock_info['Наличие дивидендов'] = "Да"
                        stock_info['Частота выплат дивидендов в год'] = 1
                    else:
                        stock_info['Наличие дивидендов'] = "Нет"
                        stock_info['Размер дивиденда'] = 0.0
                        stock_info['Частота выплат дивидендов в год'] = 0

                # Максимум и минимум
                if max_price is None:
                    max_price = extract(r"максимальная цена\s*—\s*([\d\s,.]+)")

                if min_price is None:
                    min_price = extract(r"минимальная цена\s*—\s*([\d\s,.]+)")

        except Exception as e:
            print(f"Ошибка при парсинге BCS для {ticker}: {e}")

    # --- Расчёт доходности ---
    try:
        if stock_info['Размер дивиденда'] > 0 and stock_info['Стоимость']:
            stock_info['Доходность (%)'] = round((stock_info['Размер дивиденда'] / stock_info['Стоимость']) * 100, 2)
        elif max_price and min_price and min_price > 0:
            growth = ((max_price - min_price) / min_price) * 100
            stock_info['Доходность (%)'] = round(growth, 2)
    except Exception as e:
        print(f"Ошибка при расчёте доходности {ticker}: {e}")

    return stock_info

print(get_stock_data_moex("BSPBP"))
print(get_stock_data_moex("BANE"))