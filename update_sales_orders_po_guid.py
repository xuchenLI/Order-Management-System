import sqlite3
import sys

# 修改为你的数据库路径
db_path = r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db'

def update_sales_orders_po_guid():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查询销售订单表中 PO_GUID 为空或空字符串的记录
    cursor.execute('''
        SELECT "Order_Nb", rowid
        FROM sales_orders
        WHERE "PO_GUID" IS NULL OR "PO_GUID" = ''
    ''')
    sales_rows = cursor.fetchall()
    print(f"共找到 {len(sales_rows)} 条销售订单记录缺少 PO_GUID")
    
    for order_nb, rowid in sales_rows:
        if not order_nb:
            print(f"[销售订单] rowid={rowid} 的 Order_Nb 为空，无法更新 PO_GUID。")
            continue

        # 将 Order_Nb 按逗号拆分，处理可能存在多个采购订单的情况
        order_nbs = [nb.strip() for nb in order_nb.split(',') if nb.strip()]
        po_guid_list = []
        
        # 遍历每个订单号，去采购订单表中查找对应的 PO_GUID
        for onb in order_nbs:
            cursor.execute('''
                SELECT "PO_GUID"
                FROM purchase_orders
                WHERE "Order Nb" = ?
            ''', (onb,))
            purchase_rows = cursor.fetchall()
            
            if len(purchase_rows) == 0:
                print(f"[销售订单][未找到] rowid={rowid} 的 Order_Nb='{onb}' 在采购订单中未找到对应记录。")
            elif len(purchase_rows) > 1:
                guids = [pr[0] for pr in purchase_rows]
                print(f"[销售订单][重复] rowid={rowid} 的 Order_Nb='{onb}' 对应多个 PO_GUID：{guids}")
            else:
                po_guid = purchase_rows[0][0]
                if po_guid:
                    po_guid_list.append(po_guid)
                else:
                    print(f"[销售订单][警告] rowid={rowid} 的 Order_Nb='{onb}' 对应的采购订单 PO_GUID 为空。")
        
        if po_guid_list:
            # 将多个 PO_GUID 用逗号连接后写入销售订单记录
            new_po_guid_str = ','.join(po_guid_list)
            cursor.execute('''
                UPDATE sales_orders
                SET "PO_GUID" = ?
                WHERE rowid = ?
            ''', (new_po_guid_str, rowid))
            print(f"[销售订单][更新] rowid={rowid} 的 Order_Nb='{order_nb}' 更新为 PO_GUID='{new_po_guid_str}'")
        else:
            print(f"[销售订单] rowid={rowid} 的 Order_Nb='{order_nb}' 没有找到有效的 PO_GUID。")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_sales_orders_po_guid()
