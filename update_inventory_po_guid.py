import sqlite3
import sys

# 请修改为你的数据库路径
db_path = r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db'

def update_inventory_po_guid():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询库存表中PO_GUID为空或空字符串的记录
    cursor.execute('''
        SELECT "Order_Nb", "Product_ID", rowid
        FROM inventory
        WHERE "PO_GUID" IS NULL OR "PO_GUID" = ''
    ''')
    inventory_rows = cursor.fetchall()
    print(f"共找到 {len(inventory_rows)} 条库存记录缺少 PO_GUID")

    for order_nb, product_id, rowid in inventory_rows:
        # 根据库存记录中的 Order_Nb 在采购订单表中查找对应记录
        cursor.execute('''
            SELECT "PO_GUID"
            FROM purchase_orders
            WHERE TRIM(LOWER("Order Nb")) = TRIM(LOWER(?))
        ''', (order_nb,))
        purchase_rows = cursor.fetchall()

        if len(purchase_rows) == 0:
            print(f"【未找到】库存记录(rowid={rowid})的 Order_Nb={order_nb} 在采购订单表中未找到对应记录。")
        elif len(purchase_rows) > 1:
            guids = [pr[0] for pr in purchase_rows]
            print(f"【重复】库存记录(rowid={rowid})的 Order_Nb={order_nb} 对应多个采购订单：{guids}")
        else:
            po_guid = purchase_rows[0][0]
            # 更新库存记录，把 PO_GUID 填上
            cursor.execute('''
                UPDATE inventory SET "PO_GUID" = ? WHERE rowid = ?
            ''', (po_guid, rowid))
            print(f"【更新】库存记录(rowid={rowid})的 Order_Nb={order_nb} 已更新为 PO_GUID={po_guid}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_inventory_po_guid()
