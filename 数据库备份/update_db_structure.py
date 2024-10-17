import sqlite3

def update_db_structure():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    # 获取现有的列
    cursor.execute("PRAGMA table_info(orders)")
    existing_columns = [column[1] for column in cursor.fetchall()]

    # 需要添加的新列
    new_columns = [
        ('Supplier', 'TEXT'),
        ('allocation', 'TEXT'),
        ('Sub_allocation', 'TEXT'),
        ('date', 'TEXT'),
        ('status', 'TEXT'),
        ('"QUANTITY CS"', 'TEXT'),
        ('"EXW(€)"', 'TEXT'),
        ('"TOTAL AMOUNT(€)"', 'TEXT')
    ]

    # 添加新列（如果不存在）
    for column, data_type in new_columns:
        if column.replace('"', '') not in existing_columns:
            cursor.execute(f'ALTER TABLE orders ADD COLUMN {column} {data_type}')

    # 更新现有记录
    cursor.execute('''
        UPDATE orders
        SET Supplier = COALESCE(Supplier, 'Unknown'),
            allocation = COALESCE(allocation, 'Unknown'),
            Sub_allocation = COALESCE(Sub_allocation, 'Unknown'),
            date = COALESCE(date, CURRENT_TIMESTAMP),
            status = COALESCE(status, 'new'),
            "QUANTITY CS" = COALESCE("QUANTITY CS", ''),
            "EXW(€)" = COALESCE("EXW(€)", ''),
            "TOTAL AMOUNT(€)" = COALESCE("TOTAL AMOUNT(€)", '')
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_db_structure()
    print("数据库结构已更新")