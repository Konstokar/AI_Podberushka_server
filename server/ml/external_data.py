import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

def get_bond_data(ticker):
    headers = {'User-Agent': 'Mozilla/5.0'}
    bond_info = {
        'Тикер': ticker,
        'Название': None,
        'Дата погашения': None,
        'Размер купона': None,
        'Частота выплат купонов в год': None,
        'Текущая цена': None,
        'Доходность к погашению (%)': None
    }

    try:
        url = f"https://iss.moex.com/iss/engines/stock/markets/bonds/boards/TQCB/securities/{ticker}.json"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            d = r.json()
            sec_data = d.get('securities', {}).get('data', [])
            sec_cols = d.get('securities', {}).get('columns', [])
            mkt_data = d.get('marketdata', {}).get('data', [])
            mkt_cols = d.get('marketdata', {}).get('columns', [])

            def gv(cols, data, key):
                return data[0][cols.index(key)] if data and key in cols and data[0][cols.index(key)] is not None else None

            bond_info['Название'] = gv(sec_cols, sec_data, 'SHORTNAME')
            bond_info['Дата погашения'] = gv(sec_cols, sec_data, 'MATDATE')
            bond_info['Размер купона'] = gv(sec_cols, sec_data, 'COUPONVALUE')
            bond_info['Текущая цена'] = gv(mkt_cols, mkt_data, 'LAST')
            bond_info['Доходность к погашению (%)'] = gv(mkt_cols, mkt_data, 'YIELD')

            coupon_period = gv(sec_cols, sec_data, 'COUPONPERIOD')
            if coupon_period:
                try:
                    bond_info['Частота выплат купонов в год'] = round(365 / int(coupon_period))
                except:
                    pass
    except Exception as e:
        print(f"Ошибка при получении данных с MOEX для {ticker}: {e}")

    try:
        smart_lab_url = f"https://smart-lab.ru/q/bonds/{ticker}/"
        r = requests.get(smart_lab_url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text()

            def extract(pattern, cast=float):
                match = re.search(pattern, text)
                if match:
                    value = match.group(1).replace(',', '.')
                    try:
                        return cast(value)
                    except:
                        return None
                return None

            if bond_info['Название'] is None:
                name_match = re.search(r"Имя облигации\s*(.*?)\s", text)
                if name_match:
                    bond_info['Название'] = name_match.group(1).strip()

            bond_info['Дата погашения'] = bond_info['Дата погашения'] or extract(r"Дата погашения\s*(\d{2}-\d{2}-\d{4})", str)
            bond_info['Размер купона'] = bond_info['Размер купона'] or extract(r"Купон, руб \(\?\)\s*([\d,.]+)")
            bond_info['Частота выплат купонов в год'] = bond_info['Частота выплат купонов в год'] or extract(r"Частота купона, раз в год\s*([\d,.]+)", float)
            bond_info['Доходность к погашению (%)'] = bond_info['Доходность к погашению (%)'] or extract(r"Доходность\* облигации к погашению составляет\s*([\d,.]+)", float)
            bond_info['Текущая цена'] = bond_info['Текущая цена'] or extract(r"Облигация .*? стоит сейчас\s*([\d,.]+)", float)
    except Exception as e:
        print(f"Ошибка при парсинге smart-lab для {ticker}: {e}")

    try:
        if bond_info['Доходность к погашению (%)'] is None:
            if bond_info['Размер купона'] == 0:
                bond_info['Доходность к погашению (%)'] = 0.0
            elif (bond_info['Размер купона'] and
                  bond_info['Частота выплат купонов в год'] and
                  bond_info['Текущая цена'] and
                  bond_info['Дата погашения']):
                C = float(bond_info['Размер купона'])
                f = float(bond_info['Частота выплат купонов в год'])
                P = float(bond_info['Текущая цена'])
                N = 1000  # номинал
                today = datetime.today()

                try:
                    maturity = datetime.strptime(bond_info['Дата погашения'], "%d-%m-%Y")
                except ValueError:
                    maturity = datetime.strptime(bond_info['Дата погашения'], "%Y-%m-%d")

                years = max((maturity - today).days / 365.25, 0.1)
                n = int(f * years)

                def ytm_objective(r):
                    return sum(C / (1 + r / f) ** i for i in range(1, n + 1)) + N / (1 + r / f) ** n - P

                low, high = 0.0001, 1.0
                for _ in range(100):
                    mid = (low + high) / 2
                    value = ytm_objective(mid)
                    if abs(value) < 1e-4:
                        break
                    if value > 0:
                        low = mid
                    else:
                        high = mid

                bond_info['Доходность к погашению (%)'] = round(mid * 100, 2)
    except Exception as e:
        print(f"Ошибка при численном расчёте доходности для {ticker}: {e}")

    return bond_info

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
        info_url = f"https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker}.json"
        r = requests.get(info_url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            cols = data["securities"]["columns"]
            vals = data["securities"]["data"]
            if vals:
                d = dict(zip(cols, vals[0]))
                stock_info['Название'] = d.get("SECNAME", "Неизвестно")

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

                if stock_info['Стоимость'] is None:
                    stock_info['Стоимость'] = extract(r"Стоимость\s+[A-Z]+\s+на\s+\d{2}\.\d{2}\.\d{4}\s*—\s*([\d\s,.]+)")

                if stock_info['Размер дивиденда'] == 0:
                    stock_info['Размер дивиденда'] = extract(r"Дивиденды\s+([\d\s,.]+)")
                    if stock_info['Размер дивиденда']:
                        stock_info['Наличие дивидендов'] = "Да"
                        stock_info['Частота выплат дивидендов в год'] = 1
                    else:
                        stock_info['Наличие дивидендов'] = "Нет"
                        stock_info['Размер дивиденда'] = 0.0
                        stock_info['Частота выплат дивидендов в год'] = 0

                if max_price is None:
                    max_price = extract(r"максимальная цена\s*—\s*([\d\s,.]+)")

                if min_price is None:
                    min_price = extract(r"минимальная цена\s*—\s*([\d\s,.]+)")

        except Exception as e:
            print(f"Ошибка при парсинге BCS для {ticker}: {e}")

    try:
        if stock_info['Размер дивиденда'] > 0 and stock_info['Стоимость']:
            stock_info['Доходность (%)'] = round((stock_info['Размер дивиденда'] / stock_info['Стоимость']) * 100, 2)
        elif max_price and min_price and min_price > 0:
            growth = ((max_price - min_price) / min_price) * 100
            stock_info['Доходность (%)'] = round(growth, 2)
    except Exception as e:
        print(f"Ошибка при расчёте доходности {ticker}: {e}")

    return stock_info
