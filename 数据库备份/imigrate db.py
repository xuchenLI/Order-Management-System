import csv
import sqlite3

# 数据库字段列表（顺序固定）
db_fields = [
    ("Order Nb"),
    ("Order Type"),
    ("Order Step"),
    ("Expected Profit"),
    ("Domestic Freight (CAD)"),
    ("EXW Exchange Rate"),
    ("International Freight(€)"),
    ("International Freight Exchange Rate"), 
    ( "TOTAL Freight"), 
    ("Supplier"), 
    ("BCMB"),
    ("SKU CLS"),
    ("Supplier Order Number"),
    ("ITEM Name"),
    ("CATEGORY"),
    ("SIZE"),
    ("ALC."),
    ("QUANTITY CS"),
    ("BTL PER CS"),
    ("QUANTITY BTL"),
    ("EXW(€)"), 
    ("TOTAL AMOUNT"), 
    ("REMARKS"), 
    ("WHOLESALE BTL"), 
    ("WHOLESALE CS"), 
    ("PROFIT PER BT"), 
    ("PROFIT PER CS"), 
    ("PROFIT TOTAL"), 
    ("INVOICE PRICE"), 
    ("INVOICE CS"),
]

def import_csv_to_new_db():
    conn = sqlite3.connect('new_orders.db')
    cursor = conn.cursor()

    # 创建一个映射从 CSV 列名（例如 "订单号"）到数据库字段名（例如 "Order Nb"）
    field_mapping = {csv_field: db_field for csv_field, db_field in db_fields}  # 修正了映射方向

    with open('old_orders_data.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)  # 使用 DictReader 自动将列名作为字典的键
        for row in reader:
            # 动态生成数据库字段和插入的值
            db_columns = []
            db_values = []

            for csv_col_name, csv_value in row.items():
                # 检查 CSV 列名是否在映射中
                if csv_col_name in field_mapping:
                    db_columns.append(f'"{field_mapping[csv_col_name]}"')  # 数据库列名
                    db_values.append(csv_value)  # CSV 中对应的值

            if db_columns:  # 如果找到匹配的列才执行插入操作
                # 构建 SQL 插入语句
                insert_query = f'''
                    INSERT INTO new_orders ({', '.join(db_columns)})
                    VALUES ({', '.join(['?' for _ in db_values])})
                '''

                # 执行插入操作
                cursor.execute(insert_query, db_values)

    conn.commit()
    conn.close()
    print("CSV 数据已导入到新数据库")

# 执行 CSV 导入操作
import_csv_to_new_db()
