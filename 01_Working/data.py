# data.py
import sqlite3
import datetime 
from PyQt6.QtWidgets import QMessageBox 
from PyQt6.QtCore import QObject, pyqtSignal 
     
# 定义共享数据
purchase_orders = []
sales_orders = []
inventory = []
deleted_orders = []
db_fields = [
    ("订单号", "Order Nb"),
    ("Product_ID", "Product_ID"),
    ("Order Type", "Order Type"),
    ("Order Step", "Order Step"),
    ("期望利润", "Expected Profit"),
    ("境内运费(CAD)", "Domestic Freight (CAD)"),
    ("EXW汇率", "EXW Exchange Rate"),
    ("国际运费(€)", "International Freight(€)"),
    ("国际运费汇率", "International Freight Exchange Rate"),
    ("TOTAL Freight", "TOTAL Freight"),
    ("Supplier", "Supplier"),
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
    ("TOTAL AMOUNT(€)", "TOTAL AMOUNT(€)"),
    ("REMARKS", "REMARKS"),
    ("WHOLESALE BTL", "WHOLESALE BTL"),
    ("WHOLESALE CS", "WHOLESALE CS"),
    ("PROFIT PER BT", "PROFIT PER BT"),
    ("PROFIT PER CS", "PROFIT PER CS"), 
    ("PROFIT TOTAL", "PROFIT TOTAL"), 
    ("INVOICE PRICE", "INVOICE PRICE"), 
    ("INVOICE CS", "INVOICE CS"),
    ("Date", "date"),
    # 新增字段
    ("产品到仓库的日期", "Arrival_Date"),
    ("Allocation", "Allocation"),
    ("Sub-allocation", "Sub_allocation"),
]

# 数据管理器，用于发射数据变化信号
class DataManager(QObject):
    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

data_manager = DataManager()

# 初始化数据库
def initialize_database():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    # 创建采购订单表
    field_definitions = ', '.join([f'"{field[1]}" TEXT' for field in db_fields if field[1] != 'Order Nb'])
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS purchase_orders (
            "Order Nb" TEXT PRIMARY KEY,
            {field_definitions}
        )
    ''')

    # 创建销售订单表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_orders (
            "Sales_ID" TEXT PRIMARY KEY,
            "Product_ID" TEXT,
            "Customer_ID" TEXT,
            "Quantity" INTEGER,
            "Price" REAL,
            "Total_Amount" REAL,
            "Order_Date" TEXT,
            "Shipped_Date" TEXT,
            "Remarks" TEXT
        )
    ''')

    # 创建库存表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            "Product_ID" TEXT,
            "Order_Nb" TEXT,
            "Product_Name" TEXT,
            "SKU_CLS" TEXT,
            "Current_Stock_CS" INTEGER,
            "Current_Stock_BTL" INTEGER,
            "BTL PER CS" INTEGER,
            "Last_Update" TEXT,
            "Arrival_Date" TEXT,
            "Creation_Date" TEXT,
            "Allocation" TEXT,
            "Sub-allocation" TEXT,
            PRIMARY KEY ("Product_ID", "Order_Nb")
        )
    ''')

    conn.commit()
    conn.close()

# 加载采购订单
def load_purchase_orders_from_db():
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM purchase_orders')
        rows = cursor.fetchall()
        conn.close()

        purchase_orders.clear()
        reversed_rows = rows[::-1]
        for row in reversed_rows:
            order = {}
            for idx, field in enumerate(cursor.description):
                field_name = field[0]
                order[field_name] = row[idx] if row[idx] is not None else ''
            purchase_orders.append(order)
    except Exception as e:
        print(f"无法从数据库加载采购订单数据：{e}")
        QMessageBox.critical(None, "加载错误", f"无法从数据库加载采购订单数据：{e}")

# 保存采购订单
def save_purchase_order_to_db(order):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        placeholders = ', '.join(['?' for _ in order.keys()])
        field_names = ', '.join([f'"{key}"' for key in order.keys()])
        values = list(order.values())

        cursor.execute(f'''
            INSERT OR REPLACE INTO purchase_orders ({field_names})
            VALUES ({placeholders})
        ''', values)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"保存采购订单时发生错误：{e}")
        QMessageBox.critical(None, "保存错误", f"保存采购订单时发生错误：{e}")

# 删除采购订单
def delete_purchase_order_from_db(order_nb):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM purchase_orders WHERE "Order Nb" = ?', (order_nb,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"删除采购订单时发生错误：{e}")
        QMessageBox.critical(None, "删除错误", f"删除采购订单时发生错误：{e}")

# 加载销售订单
def load_sales_orders_from_db():
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sales_orders')
        rows = cursor.fetchall()
        conn.close()

        sales_orders.clear()
        reversed_rows = rows[::-1]
        for row in reversed_rows:
            order = {}
            for idx, field in enumerate(cursor.description):
                field_name = field[0]
                order[field_name] = row[idx] if row[idx] is not None else ''
            sales_orders.append(order)
    except Exception as e:
        print(f"无法从数据库加载销售订单数据：{e}")
        QMessageBox.critical(None, "加载错误", f"无法从数据库加载销售订单数据：{e}")

# 保存销售订单
def save_sales_order_to_db(order):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        placeholders = ', '.join(['?' for _ in order.keys()])
        field_names = ', '.join([f'"{key}"' for key in order.keys()])
        values = list(order.values())

        cursor.execute(f'''
            INSERT OR REPLACE INTO sales_orders ({field_names})
            VALUES ({placeholders})
        ''', values)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"保存销售订单时发生错误：{e}")
        QMessageBox.critical(None, "保存错误", f"保存销售订单时发生错误：{e}")

# 删除销售订单
def delete_sales_order_from_db(sales_id):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sales_orders WHERE "Sales_ID" = ?', (sales_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"删除销售订单时发生错误：{e}")
        QMessageBox.critical(None, "删除错误", f"删除销售订单时发生错误：{e}")

# 加载库存数据
def load_inventory_from_db():
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM inventory')
        rows = cursor.fetchall()
        conn.close()

        inventory.clear()
        for row in rows:
            product = {}
            for idx, field in enumerate(cursor.description):
                field_name = field[0]
                product[field_name] = row[idx] if row[idx] is not None else ''
            inventory.append(product)
    except Exception as e:
        print(f"无法从数据库加载库存数据：{e}")
        QMessageBox.critical(None, "加载错误", f"无法从数据库加载库存数据：{e}")

# 保存库存数据
def save_inventory_to_db(product):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        placeholders = ', '.join(['?' for _ in product.keys()])
        field_names = ', '.join([f'"{key}"' for key in product.keys()])
        values = list(product.values())

        cursor.execute(f'''
            INSERT OR REPLACE INTO inventory ({field_names})
            VALUES ({placeholders})
        ''', values)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"保存库存数据时发生错误：{e}")
        QMessageBox.critical(None, "保存错误", f"保存库存数据时发生错误：{e}")

# 更新库存数量
#  这里有个问题，就是当售出了一部分产品后，发现采购数目输入多了。这时要是卖出的产品数目已经超过了要修改的数目。
#  这里就会提示库存不足。
def update_inventory(product_id, order_nb, quantity_change_cs, quantity_change_btl, arrival_date, creation_date, item_name, sku_cls, btl_per_cs):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()

        # 查询当前库存
        cursor.execute('SELECT "Current_Stock_CS", "Current_Stock_BTL", "Product_Name" FROM inventory WHERE "Product_ID" = ? AND "Order_Nb" = ?', (product_id, order_nb))
        result = cursor.fetchone()
        if result:
            current_stock_cs = int(result[0])
            current_stock_btl = int(result[1])
            product_name = result[2]
            new_stock_cs = current_stock_cs + quantity_change_cs
            new_stock_btl = current_stock_btl + quantity_change_btl
            if new_stock_cs < 0 or new_stock_btl < 0:
                raise ValueError("库存不足")
            cursor.execute('UPDATE inventory SET "Current_Stock_CS" = ?, "Current_Stock_BTL" = ?, "Last_Update" = ?, "BTL PER CS" = ?, "Product_Name" = ?, "SKU_CLS" = ? WHERE "Product_ID" = ? AND "Order_Nb" = ?',
                           (new_stock_cs, new_stock_btl, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), btl_per_cs, item_name, sku_cls, product_id, order_nb))
        else:
            # 如果产品不存在于库存表，且是增加库存，则新增记录
            if quantity_change_cs > 0 and quantity_change_btl > 0:
                product_name = item_name  # 从采购订单中获取产品名称
                cursor.execute('INSERT INTO inventory ("Product_ID", "Order_Nb", "Product_Name", "SKU_CLS", "Current_Stock_CS", "Current_Stock_BTL", "BTL PER CS", "Last_Update", "Arrival_Date", "Creation_Date") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                               (product_id, order_nb, product_name, sku_cls, quantity_change_cs, quantity_change_btl, btl_per_cs, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), arrival_date, creation_date))
            else:
                raise ValueError("库存中不存在该产品，无法减少库存")
        conn.commit()
        conn.close()

        # 更新内存中的 inventory 列表
        load_inventory_from_db()

    except Exception as e:
        print(f"更新库存时发生错误：{e}")
        raise e

# 更新库存中的 Arrival_Date
def update_inventory_arrival_date(product_id, order_nb, arrival_date):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE inventory SET "Arrival_Date" = ? WHERE "Product_ID" = ? AND "Order_Nb" = ?', (arrival_date, product_id, order_nb))
        conn.commit()
        conn.close()

        # 更新内存中的 inventory 列表
        load_inventory_from_db()
    except Exception as e:
        print(f"更新库存 Arrival_Date 时发生错误：{e}")
        raise e

# 更新库存中的 Allocation 和 Sub-allocation
def update_inventory_allocation(order_nb, allocation, sub_allocation):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE inventory SET "Allocation" = ?, "Sub-allocation" = ? WHERE "Order_Nb" = ?', (allocation, sub_allocation, order_nb))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"更新库存 Allocation 时发生错误：{e}")
        raise e

# 获取总库存
def get_total_stock(product_id):
    total_stock_cs = 0
    total_stock_btl = 0
    for item in inventory:
        if item['Product_ID'] == product_id:
            total_stock_cs += int(item['Current_Stock_CS'])
            total_stock_btl += int(item['Current_Stock_BTL'])
    return total_stock_cs, total_stock_btl

# 扣减库存（用于销售订单）
def deduct_inventory(product_id, quantity_btl):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        # 获取库存记录，按 Arrival_Date 排序（先进先出）
        cursor.execute('SELECT "Product_ID", "Order_Nb", "Current_Stock_CS", "Current_Stock_BTL", "BTL PER CS" FROM inventory WHERE "Product_ID" = ? ORDER BY "Arrival_Date"', (product_id,))
        rows = cursor.fetchall()
        remaining_qty = quantity_btl
        for row in rows:
            prod_id, order_nb, current_stock_cs, current_stock_btl, btl_per_cs = row
            current_stock_cs = int(current_stock_cs)
            current_stock_btl = int(current_stock_btl)
            btl_per_cs = int(btl_per_cs)
            if current_stock_btl == 0:
                continue
            if remaining_qty <= current_stock_btl:
                new_stock_btl = current_stock_btl - remaining_qty
                new_stock_cs = new_stock_btl // btl_per_cs
                cursor.execute('UPDATE inventory SET "Current_Stock_CS" = ?, "Current_Stock_BTL" = ?, "Last_Update" = ? WHERE "Product_ID" = ? AND "Order_Nb" = ?',
                               (new_stock_cs, new_stock_btl, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), prod_id, order_nb))
                remaining_qty = 0
                break
            else:
                remaining_qty -= current_stock_btl
                cursor.execute('UPDATE inventory SET "Current_Stock_CS" = ?, "Current_Stock_BTL" = ?, "Last_Update" = ? WHERE "Product_ID" = ? AND "Order_Nb" = ?',
                               (0, 0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), prod_id, order_nb))
        if remaining_qty > 0:
            raise ValueError("库存不足，无法扣减库存")
        conn.commit()
        conn.close()
        # 更新内存中的 inventory 列表
        load_inventory_from_db()
    except Exception as e:
        print(f"扣减库存时发生错误：{e}")
        raise e

# 根据订单号获取采购订单
def get_purchase_order_by_nb(order_nb):
    return next((order for order in purchase_orders if order['Order Nb'] == order_nb), None)
