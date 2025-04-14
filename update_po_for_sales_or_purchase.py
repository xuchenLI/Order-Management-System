import sqlite3
import uuid

# 数据库路径
db_path = r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询销售订单中 PO_GUID 为空或空字符串的记录
cursor.execute('SELECT "Order Nb" FROM purchase_orders WHERE "PO_GUID" IS NULL OR "PO_GUID" = ""')
rows = cursor.fetchall()

print(f"开始处理销售订单中 PO_GUID 为空的记录，共找到 {len(rows)} 条记录。")

for (order_nb ,) in rows:
    new_guid = str(uuid.uuid4())
    print(f"order_nb {order_nb}: PO_GUID 为空，赋值为 {new_guid}")
    cursor.execute('UPDATE purchase_orders SET "PO_GUID" = ? WHERE "Order Nb" = ?', (new_guid, order_nb))

conn.commit()
conn.close()
print("更新完成。")
