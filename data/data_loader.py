import pandas as pd

def load_transactions(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    # Приведи типы и названия колонок к нужным
    df['Дата операции'] = pd.to_datetime(df['Дата операции'], format='%d.%m.%Y', errors='coerce')
    return df
