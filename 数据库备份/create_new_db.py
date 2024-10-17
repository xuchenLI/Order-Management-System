import sqlite3
from PyQt6.QtWidgets import QMessageBox
def initialize_new_database():
    conn = sqlite3.connect('new_orders.db')
    cursor = conn.cursor()
    
    # 数据库字段列表（顺序固定）
    db_fields = [
        ("订单号", "Order Nb"),
        ("Order Type", "Order Type"),
        ("Order Step", "Order Step"),
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
        # 创建订单表，使用 db_fields
    field_definitions = ', '.join([f'"{field[1]}" TEXT' for field in db_fields if field[1] != 'Order Nb'])
    cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS new_orders (
            "Order Nb" TEXT PRIMARY KEY,
            {field_definitions}
            )
        ''')
        
    conn.commit()
    conn.close()
    print("新数据库结构已创建")

# 初始化新的数据库
initialize_new_database()
