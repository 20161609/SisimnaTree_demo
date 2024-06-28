import sqlite3
import os
from lib_branch import Branch

import pandas as pd

# Class for communicating with SQLite3 SQL database.
file_path_tree = 'finance-tree.xlsx'
db_name = 'AccountBook.db'
table_name = 'expenditures'


class DatabaseController:
    def __init__(self):
        self.db_name = db_name
        self.database = sqlite3.connect(db_name)
        self.cursor = self.database.cursor()
        self.table_name = table_name
        self.headers = [("_Date", "DATE"), ("_Branch", "STR"), ("_CashFlow", "INT"), ("_Description", "STR")]
        self.init_database()
        self.get_data()

    def init_database(self):
        # 1. Delete all tables in DB
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for table in self.cursor.fetchall():
            self.cursor.execute(f"DROP TABLE {table[0]}")

        # 2. Create table
        create_query = f'''CREATE TABLE IF NOT EXISTS {table_name} (
            _Date DATE, 
            _Branch TEXT, 
            _Description TEXT,
            _CashFlow INT
        );'''
        self.cursor.execute(create_query)

        self.cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_date ON {table_name} (_Date);")
        self.cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_branch ON {table_name} (_Branch);")

        self.database.commit()

    def get_data(self):
        try:
            os.makedirs('transactions', exist_ok=True)
            for file_name in os.listdir('transactions'):
                try:
                    sql_query = f"INSERT INTO {table_name}"
                    sql_query += " ({})".format(",".join([col for col, col_type in self.headers]))

                    value_box = []
                    info_txt = file_name.split('.')[0]
                    _date, _branch, _cashflow, _content = info_txt.split('_')

                    # Date
                    value_box.append(f"'{_date}'")

                    # Branch
                    value_box.append(f"'{_branch.replace('-', '/')}'")

                    # Transaction
                    value_box.append(f'{int(_cashflow)}')

                    # Content
                    value_box.append(f"'{_content}'")
                    sql_query += " VALUES({})".format(",".join(value_box))
                    self.cursor.execute(sql_query)
                    self.database.commit()
                except Exception as e:
                    pass

        except:
            pass

        return


def make_daily_box(branch: Branch, db: DatabaseController, period: list):
    select_query = f"SELECT _Date AS DATE, _Branch, _CashFlow, _Description FROM {db.table_name}"
    where_query = " WHERE _Branch LIKE '{}%'".format(branch.path)

    begin_date, end_date = period
    where_query += " AND (_Date BETWEEN '{}' AND '{}')".format(begin_date, end_date)
    order_query = " ORDER BY _Date;"

    sql_query = select_query + where_query + order_query
    db.cursor.execute(sql_query)

    return db.cursor.fetchall()


def make_monthly_box(branch: Branch, db: DatabaseController, period: list):
    begin_date, end_date = period
    select_query = f'''SELECT 
        STRFTIME('%Y-%m', _Date) AS MONTHLY, 
        SUM(CASE WHEN _CashFlow > 0 THEN _CashFlow ELSE 0 END) AS CASH_IN,
        SUM(CASE WHEN _CashFlow < 0 THEN _CashFlow ELSE 0 END) AS CASH_OUT
    FROM {db.table_name}'''

    # 기간 설정
    where_query = "\n   WHERE _Branch LIKE '{}%'".format(branch.path)
    where_query += " AND (_Date BETWEEN '{}' AND '{}')".format(begin_date, end_date)

    # SQL: GROUP
    group_query = " GROUP BY MONTHLY"

    # SQL: ORDER
    order_query = " ORDER BY MONTHLY;"

    # SQL 실행
    sql_query = select_query + where_query + group_query + order_query
    db.cursor.execute(sql_query)
    return db.cursor.fetchall()


def make_graph_box(branch: Branch, db: DatabaseController, period: list, data_type: str = 'BALANCE'):
    # SQL 쿼리 조건 구성
    begin_date, end_date = period
    path = branch.path

    where_query = f" WHERE _Branch LIKE '{path}%' AND (_Date BETWEEN '{begin_date}' AND '{end_date}')"

    # SQL 쿼리 선택 구성
    if data_type == 'BALANCE':
        select_query = f"SELECT STRFTIME('%Y-%m', _Date) AS MONTHLY, SUM(CASE WHEN _CashFlow > 0 THEN _CashFlow ELSE 0 END) AS CASH_IN, SUM(CASE WHEN _CashFlow < 0 THEN _CashFlow ELSE 0 END) AS CASH_OUT"
    else:
        column = 'CASH_IN' if data_type == 'IN' else 'CASH_OUT'
        sign = '>' if data_type == 'IN' else '<'
        select_query = f"SELECT STRFTIME('%Y-%m', _Date) AS MONTHLY, SUM(CASE WHEN _CashFlow {sign} 0 THEN _CashFlow ELSE 0 END) AS {column}"

    # SQL 쿼리 실행 및 데이터 처리
    sql_query = f"{select_query} FROM {db.table_name}{where_query} GROUP BY MONTHLY ORDER BY MONTHLY;"
    db.cursor.execute(sql_query)
    return db.cursor.fetchall()
