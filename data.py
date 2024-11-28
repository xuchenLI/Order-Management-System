# data.py
import sqlite3
import datetime
import json
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
    ("境内运费(CAD)", "Domestic Freight CAD"),
    ("EXW汇率", "EXW Exchange Rate"),
    ("国际运费(€)", "International Freight EURO"),
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
    ("EXW(€)", "EXW EURO"),
    ("TOTAL AMOUNT(€)", "TOTAL AMOUNT EURO"),
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
]

# 数据管理器，用于发射数据变化信号
class DataManager(QObject):
    data_changed = pyqtSignal()
    inventory_changed = pyqtSignal()

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
            "Quantity_CS_Sold" INTEGER,
            "Quantity_BTL_Sold" INTEGER,
            "Total_Quantity_BTL_Sold" INTEGER,
            "Price_per_bottle" REAL,
            "Total_Amount" REAL,
            "Order_Date" TEXT,
            "Shipped_Date" TEXT,
            "Remarks" TEXT,
            "Deduction_Details" TEXT,
            "Order_Nb" TEXT,
            "Product_Name",
            "BTL_PER_CS" INTEGER
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
            "BTL PER CS" INTEGER,
            "Last_Update" TEXT,
            "Arrival_Date" TEXT,
            "Creation_Date" TEXT,
            "Sale_Date" TEXT,
            "Sales_Orders" TEXT,
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
                if field_name == 'Deduction_Details':
                    order[field_name] = json.loads(row[idx]) if row[idx] else []
                else:
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

        # 序列化 Deduction_Details
        deduction_details_json = json.dumps(order.get('Deduction_Details', []))
        # 创建一个副本用于保存，不修改原始 order 对象
        order_to_save = order.copy()
        order_to_save['Deduction_Details'] = deduction_details_json

        placeholders = ', '.join(['?' for _ in order_to_save.keys()])
        field_names = ', '.join([f'"{key}"' for key in order_to_save.keys()])
        values = list(order_to_save.values())

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
        global inventory
        conn = sqlite3.connect('orders.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM inventory')
        rows = cursor.fetchall()
        conn.close()

        inventory.clear()
        for row in rows:
            product = dict(row)
            # 从采购订单中获取对应的 Order Type
            order_nb = product.get('Order_Nb', '')
            purchase_order = get_purchase_order_by_nb(order_nb)
            product['Order_Type'] = purchase_order.get('Order Type', '') if purchase_order else ''
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
def update_inventory(product_id, order_nb, quantity_change_cs, arrival_date, creation_date, item_name, sku_cls, btl_per_cs, operation_type, sale_date=None, sales_orders=None, operation_subtype=None ):
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        
        # 查询当前库存
        cursor.execute('SELECT "Current_Stock_CS", "BTL PER CS", "Sales_Orders" FROM inventory WHERE "Product_ID" = ? AND "Order_Nb" = ?', (product_id, order_nb))
        result = cursor.fetchone()
        if result:
            # 如果库存记录存在，更新库存数量
            current_stock_cs = int(result[0])
            #current_btl_per_cs = int(result[1])
            new_stock_cs = current_stock_cs + quantity_change_cs

            if new_stock_cs < 0: #or new_stock_btl < 0:
                raise ValueError("库存不足，无法减少库存")
            
            # 获取当前 Sales_Orders
            existing_sales_orders = set(result[2].split(',')) if result[2] else set()
            if operation_subtype == 'remove_sales_order':
                # 移除指定值
                remove_sales_orders = set(sales_orders.split(',')) if sales_orders else set()
                updated_sales_orders = existing_sales_orders - remove_sales_orders
                updated_sales_orders_str = ','.join(sorted(updated_sales_orders))
            else:
                new_sales_orders = set(sales_orders.split(',')) if sales_orders else set()
                updated_sales_orders_str = ','.join(sorted(existing_sales_orders.union(new_sales_orders)))
            print(f"operation_subtype: {operation_subtype}")
            # 更新库存
            if new_stock_cs == 0: #and new_stock_btl == 0:
                if operation_type == 'revoke_purchase_order':
                    # 撤销采购订单导致库存为零，删除库存记录
                    cursor.execute('DELETE FROM inventory WHERE "Product_ID" = ? AND "Order_Nb" = ?', (product_id, order_nb))
                else:
                    # 正常销售导致库存为零，保留库存记录
                    cursor.execute('UPDATE inventory SET "Product_ID" = ?, "Order_Nb" = ?, "Product_Name" = ?, "SKU_CLS" = ?, "Current_Stock_CS" = 0, "BTL PER CS" = ?, "Last_Update" = ?, "Arrival_Date" = ?, "Creation_Date" = ?, "Sale_Date" = ?, "Sales_Orders" = ? WHERE "Product_ID" = ? AND "Order_Nb" = ?',
                                   (product_id, order_nb, item_name, sku_cls, btl_per_cs, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), arrival_date, creation_date, sale_date or datetime.datetime.now().strftime("%Y-%m-%d"), updated_sales_orders_str, product_id, order_nb))
            else:
                # 库存数量不为零，更新库存记录
                cursor.execute('UPDATE inventory SET "Product_ID" = ?, "Order_Nb" = ?, "Product_Name" = ?, "SKU_CLS" = ?, "Current_Stock_CS" = ?, "BTL PER CS" = ?, "Last_Update" = ?, "Arrival_Date" = ?, "Creation_Date" = ?, "Sale_Date" = NULL, "Sales_Orders" = ? WHERE "Product_ID" = ? AND "Order_Nb" = ?',
                               (product_id, order_nb, item_name, sku_cls, new_stock_cs, btl_per_cs, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), arrival_date, creation_date, updated_sales_orders_str, product_id, order_nb))

        else:
            # 库存记录不存在
            if quantity_change_cs > 0:#or quantity_change_btl > 0:
                # 增加库存，新增库存记录
                cursor.execute('INSERT INTO inventory ("Product_ID", "Order_Nb", "Product_Name", "SKU_CLS", "Current_Stock_CS", "BTL PER CS", "Last_Update", "Arrival_Date", "Creation_Date") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                               (product_id, order_nb, item_name, sku_cls, quantity_change_cs, btl_per_cs, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), arrival_date, creation_date))
            else:
                # 减少库存，且库存记录不存在，抛出异常
                raise ValueError("库存中不存在该产品，无法减少库存")

        conn.commit()
        conn.close()

        # 更新内存中的 inventory 列表
        load_inventory_from_db()
        # 发射 inventory_changed 信号
        data_manager.inventory_changed.emit()

    except Exception as e:
        print(f"更新库存时发生错误：{e}")
        raise e

# 获取库存记录
def get_inventory_item(product_id, order_nb):
    for item in inventory:
        if item['Product_ID'] == product_id and item['Order_Nb'] == order_nb:
            return item
    return None
#获取产品信息
def get_inventory_info(product_id, order_nb):
    for item in inventory:
        if item['Product_ID'] == product_id and item['Order_Nb'] == order_nb:
            return item.get('Product_Name', ''), int(item.get('BTL PER CS', 0))
    return '', 0

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
        data_manager.inventory_changed.emit()
    except Exception as e:
        print(f"更新库存 Arrival_Date 时发生错误：{e}")
        raise e

# 恢复库存（用于删除销售订单）
def restore_inventory(sales_order):
    try:
        # 从销售订单中获取扣减详情
        deduction_details = sales_order.get('Deduction_Details', [])
        if not deduction_details:
            raise ValueError("销售订单中缺少扣减详情，无法恢复库存")

        for deduction in deduction_details:
            # 确保 deduction 是一个字典
            if not isinstance(deduction, dict):
                raise ValueError(f"扣减详情格式错误：{deduction}")

            product_id = sales_order['Product_ID']
            order_nb = deduction['Order_Nb']
            add_cs = deduction['Deduct_CS']

            # 获取库存记录的信息
            inventory_item = get_inventory_item(product_id, order_nb)
            if not inventory_item:
                raise ValueError(f"无法找到库存记录，产品ID: {product_id}, 订单号: {order_nb}")

            btl_per_cs = int(inventory_item.get('BTL PER CS', 0))
            current_stock_cs = int(inventory_item.get('Current_Stock_CS', 0))
            arrival_date = inventory_item.get('Arrival_Date')
            creation_date = inventory_item.get('Creation_Date')
            product_name = inventory_item.get('Product_Name')
            sku_cls = inventory_item.get('SKU_CLS')
            # 计算新的瓶数和箱数
            new_stock_cs = current_stock_cs + add_cs
            '''# 获取现有的 Sales_Orders
            existing_sales_orders = inventory_item.get('Sales_Orders', '')
            if existing_sales_orders:
                # 将字符串转换为集合
                existing_sales_orders_set = set(existing_sales_orders.split(','))
                # 从集合中移除当前销售订单号
                updated_sales_orders_set = existing_sales_orders_set - {sales_order['Sales_ID']}
                # 转换回字符串
                updated_sales_orders = ','.join(sorted(updated_sales_orders_set))
            else:
                updated_sales_orders = None'''
            # 更新库存
            update_inventory(
                product_id,
                order_nb,
                new_stock_cs - current_stock_cs,
                arrival_date,
                creation_date,
                product_name,
                sku_cls,
                btl_per_cs,
                operation_type='restore_sales',
                sales_orders = sales_order['Sales_ID'],
                operation_subtype = 'remove_sales_order'
            )

    except Exception as e:
        print(f"恢复库存时发生错误：{e}")
        raise e


# 根据订单号获取采购订单
def get_purchase_order_by_nb(order_nb):
    return next((order for order in purchase_orders if order['Order Nb'] == order_nb), None)

# 根据 Product_ID 获取采购订单
def get_purchase_order_by_product_id(product_id):
    for order in purchase_orders:
        if order['Product_ID'] == product_id:
            return order
    return None

# 获取 BTL_PER_CS
def get_btl_per_cs(product_id):
    order = get_purchase_order_by_product_id(product_id)
    if order:
        return int(order.get('BTL PER CS', 0))
    else:
        return 0

# 获取 WHOLESALE BTL
def get_WHOLESALE_BTL_price(product_id):
    order = get_purchase_order_by_product_id(product_id)
    if order:
        wholesale_btl = order.get('WHOLESALE BTL', 0)
        # 检查 wholesale_btl 是否为字符串，如果不是，转换为字符串
        if not isinstance(wholesale_btl, str):
            wholesale_btl = str(wholesale_btl)
        # 检查是否为空字符串或无法转换成浮点数
        if wholesale_btl.strip() == '':
            wholesale_btl = '0'  # 如果为空字符串，将其设置为 '0'
        try:
            return float(wholesale_btl)
        except ValueError:
            # 处理转换错误，返回默认值或抛出更具体的错误
            print(f"Invalid value for WHOLESALE BTL: {wholesale_btl}")
            return 0.0  # 返回默认值
        #print(f"获取到的WHOLESALE BTL 为：{wholesale_btl}")
    else:
        return 0.0
