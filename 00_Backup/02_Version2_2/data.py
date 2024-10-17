# data.py

import sqlite3
from PyQt6.QtWidgets import QMessageBox

# 定义共享数据
orders = []
last_action = ""  # 记录用户的上一步操作
deleted_orders = []  # 保存被删除的订单列表

fields = [
    ("订单号", "Order Nb"),
    ("Order Type", "Order Type"),
    ("ORDER STEP", "ORDER STEP"),
    ("期望利润", "Expected Profit"),
    ("境内运费(CAD)", "Domestic Freight (CAD)"),
    ("EXW汇率", "EXW Exchange Rate"),
    ("国际运费(€)", "International Freight(€)"),
    ("国际运费汇率", "International Freight Exchange Rate"),
    ("TOTAL Freight", "TOTAL Freight"),
    ("供应商", "Supplier"),
    ("BCMB", "BCMB"),
    ("SKU CLS", "SKU CLS"),
    ("Supplier Order Number", "Supplier Order Number"),
    ("ITEM Name", "ITEM Name"),
    ("CATEGORY", "CATEGORY"),
    ("SIZE", "SIZE"),
    ("ALC.", "ALC."),
    ("QUANTITY CS", "QUANTITY CS"),
    ("BTL PER CS", "BTL PER CS"),
    ("QUANTITY BTL", "QUANTITY BTL"),
    ("EXW(€)", "EXW(€)"),
    ("TOTAL AMOUNT(€)", "TOTAL AMOUNT"),
    ("REMARKS", "REMARKS"),
    ("WHOLESALE BTL", "WHOLESALE BTL"),
    ("WHOLESALE CS", "WHOLESALE CS"),
    ("PROFIT PER BT", "PROFIT PER BT"),
    ("PROFIT PER CS", "PROFIT PER CS"),
    ("PROFIT TOTAL", "PROFIT TOTAL"),
    ("INVOICE PRICE", "INVOICE PRICE"),
    ("INVOICE CS", "INVOICE CS"),
]

order_details_window = None  # 定义全局变量

# 初始化数据库
def initialize_database():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    # 创建订单表
    # 排除 "Order Nb" 字段，因为它已经在主键中定义
    field_definitions = ', '.join([f'"{field[1]}" TEXT' for field in fields if field[1] != 'Order Nb'])
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS orders (
            "Order Nb" TEXT PRIMARY KEY,
            {field_definitions}
        )
    ''')
    conn.commit()
    conn.close()

# 从数据库加载订单数据
def load_orders_from_db():
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders')
        rows = cursor.fetchall()
        conn.close()

        orders.clear()
        for row in rows:
            order = {}
            for idx, field in enumerate(cursor.description):
                field_name = field[0]
                order[field_name] = row[idx] if row[idx] is not None else ''
            orders.append(order)
        print(f"成功从数据库加载了 {len(orders)} 个订单")
    except Exception as e:
        print(f"无法从数据库加载订单数据：{e}")
        QMessageBox.critical(None, "加载错误", f"无法从数据库加载订单数据：{e}")

# 将订单数据保存到数据库
def save_order_to_db(order):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        placeholders = ', '.join(['?' for _ in fields if _[1] != 'Order Nb'])
        field_names = ', '.join([f'"{field[1]}"' for field in fields if field[1] != 'Order Nb'])
        values = [order.get(field[1], '') for field in fields if field[1] != 'Order Nb']

        cursor.execute(f'''
            INSERT OR REPLACE INTO orders ("Order Nb", {field_names})
            VALUES (?, {placeholders})
        ''', [order['Order Nb']] + values)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"保存订单数据时发生错误：{e}")
        QMessageBox.critical(None, "保存错误", f"保存订单数据时发生错误：{e}")

# 从数据库中删除订单
def delete_order_from_db(order_nb):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM orders WHERE "Order Nb" = ?', (order_nb,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"删除订单时发生错误：{e}")
        QMessageBox.critical(None, "删除错误", f"删除订单时发生错误：{e}")

# 更新订单数据到数据库
def update_order_in_db(order):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        set_clause = ', '.join([f'"{field[1]}" = ?' for field in fields if field[1] != 'Order Nb'])
        values = [order.get(field[1], '') for field in fields if field[1] != 'Order Nb']
        values.append(order['Order Nb'])
        cursor.execute(f'''
            UPDATE orders SET {set_clause} WHERE "Order Nb" = ?
        ''', values)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"更新订单数据时发生错误：{e}")
        QMessageBox.critical(None, "更新错误", f"更新订单数据时发生错误：{e}")

# 在程序启动时初始化数据库和加载订单数据
initialize_database()
load_orders_from_db()
