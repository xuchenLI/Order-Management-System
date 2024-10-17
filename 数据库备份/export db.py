import sqlite3
import csv

def export_old_data_to_csv():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    
    # 选择所有数据
    cursor.execute('SELECT * FROM orders')
    rows = cursor.fetchall()
    
    # 将数据写入 CSV 文件
    with open('old_orders_data.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([i[0] for i in cursor.description])  # 写入列名
        writer.writerows(rows)  # 写入数据行
    
    conn.close()
    print("老数据库数据已导出到 CSV 文件")

# 执行备份操作
export_old_data_to_csv()
