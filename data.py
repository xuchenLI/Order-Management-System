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
products = []
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
    ("供应商发票号", "Supplier Order Number"),
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
    ("UCC14", "UCC14"),
    ("UCC13", "UCC13"),
]

# 数据管理器，用于发射数据变化信号
class DataManager(QObject):
    data_changed = pyqtSignal()
    inventory_changed = pyqtSignal()
    products_changed = pyqtSignal()
    def __init__(self):
        super().__init__()

data_manager = DataManager()

# 初始化数据库
def initialize_database():
    conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
    cursor = conn.cursor()

    # 创建采购订单表
    field_definitions = ', '.join([f'"{field[1]}" TEXT' for field in db_fields if field[1] != 'Order Nb'])
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS purchase_orders (
            "PO_GUID" TEXT PRIMARY KEY,
            "Order Nb" TEXT,
            {field_definitions},
            UNIQUE("Order Nb")
        )
    ''')

    # 创建销售订单表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_orders (
            "SO_GUID" TEXT PRIMARY KEY,
            "Sales_ID" TEXT,
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
            "Product_Name" TEXT,
            "BTL_PER_CS" INTEGER,
            "PO_GUID" TEXT
        )
    ''')

    # 创建库存表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            "PO_GUID" TEXT PRIMARY KEY,
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
            "Pick_up_Date" TEXT
        )
    ''')
    #创建产品表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            "SKU_CLS" TEXT PRIMARY KEY,
            "ITEM_Name" TEXT,
            "Category" TEXT,
            "Size" REAL,
            "ALC" REAL,
            "BTL_PER_CS" INTEGER,
            "Supplier" TEXT,
            "Creation_Date" TEXT
        )
    ''')
    conn.commit()
    conn.close()

# 加载采购订单
def load_purchase_orders_from_db():
    try:
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
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
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
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
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
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
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
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
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
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
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
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
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
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
    # 移除不属于库存数据表的字段，比如 "Order_Type"
    product.pop("Order_Type", None)
    try:
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
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

#从库存表中查找对应的PO_GUID
def get_po_guid_for_inventory(product_id, order_nb):
    """
    根据产品编号和订单号，从库存表中查找对应的 PO_GUID。
    如果找不到，返回 None；如果找到多条记录，返回第一条记录的 PO_GUID（你也可以自行调整处理逻辑）。
    """
    # 请确保这里的 db_path 与你实际使用的一致
    db_path = r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # 使用 TRIM 处理可能的空格问题
        cursor.execute('''
            SELECT "PO_GUID"
            FROM inventory
            WHERE TRIM("Product_ID") = ? AND TRIM("Order_Nb") = ?
        ''', (product_id.strip(), order_nb.strip()))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        else:
            return None
    except Exception as e:
        print(f"Error retrieving PO_GUID for Product_ID='{product_id}', Order_Nb='{order_nb}': {e}")
        return None

# 测试代码
if __name__ == '__main__':
    # 示例调用，修改下面的参数为实际存在的值
    po_guid = get_po_guid_for_inventory("P001", "ORD123")
    if po_guid:
        print(f"找到 PO_GUID: {po_guid}")
    else:
        print("未找到对应的 PO_GUID。")

# 更新库存数量
def update_inventory(po_guid,product_id, order_nb, quantity_change_cs, arrival_date, creation_date, item_name, sku_cls, btl_per_cs, operation_type, sale_date=None, sales_orders=None, operation_subtype=None, Pick_up_Date=None ):
    try:
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
        cursor = conn.cursor()
        
        # 查询当前库存
        cursor.execute('SELECT "Current_Stock_CS", "BTL PER CS", "Sales_Orders"  FROM inventory WHERE "PO_GUID" = ?', (po_guid,))
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
                    cursor.execute('DELETE FROM inventory WHERE "PO_GUID" = ?', (po_guid,))
                else:
                    # 正常销售导致库存为零，保留库存记录
                    cursor.execute('UPDATE inventory SET "Product_ID" = ?, "Order_Nb" = ?, "Product_Name" = ?, "SKU_CLS" = ?, "Current_Stock_CS" = 0, "BTL PER CS" = ?, "Last_Update" = ?, "Arrival_Date" = ?, "Creation_Date" = ?, "Sale_Date" = ?, "Sales_Orders" = ? WHERE "PO_GUID" = ?',
                                   (product_id, order_nb, item_name, sku_cls, btl_per_cs, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), arrival_date, creation_date, sale_date or datetime.datetime.now().strftime("%Y-%m-%d"), updated_sales_orders_str, po_guid))
            else:
                # 库存数量不为零，更新库存记录
                cursor.execute('UPDATE inventory SET "Product_ID" = ?, "Order_Nb" = ?, "Product_Name" = ?, "SKU_CLS" = ?, "Current_Stock_CS" = ?, "BTL PER CS" = ?, "Last_Update" = ?, "Arrival_Date" = ?, "Creation_Date" = ?, "Sale_Date" = NULL, "Sales_Orders" = ? WHERE "PO_GUID" = ?',
                               (product_id, order_nb, item_name, sku_cls, new_stock_cs, btl_per_cs, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), arrival_date, creation_date, updated_sales_orders_str, po_guid))

        else:
            # 库存记录不存在
            if quantity_change_cs > 0:#or quantity_change_btl > 0:
                # 增加库存，新增库存记录
                cursor.execute('INSERT INTO inventory ("PO_GUID", "Product_ID", "Order_Nb", "Product_Name", "SKU_CLS", "Current_Stock_CS", "BTL PER CS", "Last_Update", "Arrival_Date", "Creation_Date") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                               (po_guid, product_id, order_nb, item_name, sku_cls, quantity_change_cs, btl_per_cs, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), arrival_date, creation_date))
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
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
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

            # 更新库存
            po_guid = get_po_guid_for_inventory(product_id, order_nb)
            update_inventory(
                po_guid,
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

# 加载产品数据
def load_products_from_db():
    try:
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products')
        rows = cursor.fetchall()
        conn.close()

        products.clear()
        for row in rows:
            product = {}
            for idx, field in enumerate(cursor.description):
                field_name = field[0]
                product[field_name] = row[idx] if row[idx] is not None else ''
            products.append(product)
    except Exception as e:
        print(f"无法从数据库加载产品数据：{e}")
        QMessageBox.critical(None, "加载错误", f"无法从数据库加载产品数据：{e}")

# 保存产品
def save_product_to_db(product):
    try:
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
        cursor = conn.cursor()
        placeholders = ', '.join(['?' for _ in product.keys()])
        field_names = ', '.join([f'"{key}"' for key in product.keys()])
        values = list(product.values())

        cursor.execute(f'''
            INSERT OR REPLACE INTO products ({field_names})
            VALUES ({placeholders})
        ''', values)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"保存产品时发生错误：{e}")
        QMessageBox.critical(None, "保存错误", f"保存产品时发生错误：{e}")

# 删除产品
def delete_product_from_db(sku_cls):
    try:
        conn = sqlite3.connect(r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE "SKU_CLS" = ?', (sku_cls,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"删除产品时发生错误：{e}")
        QMessageBox.critical(None, "删除错误", f"删除产品时发生错误：{e}")

# 根据 SKU_CLS 获取产品
def get_product_by_sku(sku_cls):
    return next((product for product in products if product['SKU_CLS'] == sku_cls), None)

# 在采购订单添加时检查并添加新产品
def check_and_add_new_product(order):
    sku_cls = str(order.get('SKU CLS', '')).strip()
    product = get_product_by_sku(sku_cls)
    if not product:
        # 产品不存在，自动添加到产品列表
        new_product = {
            'SKU_CLS': sku_cls,
            'ITEM_Name': order.get('ITEM Name', ''),
            'Category': order.get('CATEGORY', ''),
            'Size': float(order.get('SIZE', 0)),
            'ALC': float(order.get('ALC.', 0)),
            'BTL_PER_CS': int(order.get('BTL PER CS', 0)),
            'Supplier': order.get('Supplier', ''),
            'Creation_Date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        products.append(new_product)
        save_product_to_db(new_product)
        data_manager.products_changed.emit()
        QMessageBox.information(None, "新产品添加", f"产品 {sku_cls} 为新产品，已自动添加到产品列表中。")
    else:
        # 产品已存在，验证信息一致性
        inconsistencies = []
        fields_to_check = ['ITEM_Name', 'Category', 'Size', 'ALC', 'BTL_PER_CS', 'Supplier']
        for field in fields_to_check:
            order_field = order.get(field.replace('_', ' '), '')
            product_field = product.get(field, '')
            if str(order_field).strip() != str(product_field).strip():
                print(f"order_field{order_field}")
                print(f"order_field{product_field}")
                inconsistencies.append(field)
        if inconsistencies:
            QMessageBox.warning(None, "产品信息不一致", f"产品 {sku_cls} 的以下信息与产品列表不一致：{', '.join(inconsistencies)}。请检查。")

def cascade_update_purchase_order_by_guid(po_guid, new_order_nb=None, new_order_data=None):
    """
    根据采购订单的 PO_GUID 进行级联更新。
    参数:
      po_guid: 要更新的采购订单 GUID
      new_order_nb: 若需要更新采购订单的 'Order Nb'，则传入新的订单号；否则为 None
      new_order_data: 需要同时更新的其它字段(dict)，例如 {'Supplier': 'NewSupplier'} 等
    """

    # 1. 在内存中找到对应的采购订单
    purchase_order = next((po for po in purchase_orders if po.get('PO_GUID') == po_guid), None)
    if not purchase_order:
        print(f"[级联更新] 未找到 PO_GUID = {po_guid} 的采购订单，无法更新。")
        return
    # 保存旧的订单号以便后续更新销售订单扣减详情
    old_order_nb = purchase_order.get("Order Nb", "")
    # 2. 更新采购订单显示字段
    if new_order_nb is not None:
        purchase_order['Order Nb'] = new_order_nb
    if new_order_data:
        purchase_order.update(new_order_data)

    # 写回数据库
    save_purchase_order_to_db(purchase_order)

    # 3. 级联更新库存记录
    #   找到所有与该 PO_GUID 匹配的库存记录，若需要同步更新 'Order_Nb' 等字段，则在此处理
    for item in inventory:
        if item.get("PO_GUID") == po_guid:
            if new_order_nb is not None:
                item["Order_Nb"] = new_order_nb
            if new_order_data:
                if "Product_ID" in new_order_data:
                    item["Product_ID"] = new_order_data["Product_ID"]
                if "ITEM Name" in new_order_data:
                    item["Product_Name"] = new_order_data["ITEM Name"]  # 假设库存中字段为 Product_Name
                if "BTL PER CS" in new_order_data:
                    item["BTL PER CS"] = new_order_data["BTL PER CS"]
            save_inventory_to_db(item)

    # 4. 级联更新销售订单
    #   因为销售订单可能存储多个 PO_GUID（用逗号分隔），需要逐一检查
    for s_order in sales_orders:
        po_guid_list_str = s_order.get('PO_GUID', '')
        po_guid_list = [guid.strip() for guid in po_guid_list_str.split(',') if guid.strip()]

        # 如果该销售订单中包含当前 po_guid，则执行更新
        if po_guid in po_guid_list:
            # 销售订单中 'Order_Nb' 字段也可能存储多个采购订单号，
            # 需要逐一替换旧的订单号为新的订单号 (如有必要)
            # 简化处理：如果你业务上只存了一个订单号或只想更新第一个，则可以直接改
            if new_order_nb is not None:
                # 将旧的 s_order['Order_Nb'] 用逗号分割，逐一替换
                old_nbs = [nb.strip() for nb in s_order.get('Order_Nb', '').split(',') if nb.strip()]
                # 这里可以根据实际需求决定是替换第一个匹配还是全部替换为 new_order_nb
                # 简单做法：全部替换
                new_nbs = [new_order_nb for _ in old_nbs]
                s_order['Order_Nb'] = ','.join(new_nbs)
                deductions = s_order.get("Deduction_Details", [])
                for ded in deductions:
                    if ded.get("Order_Nb") == old_order_nb:
                        ded["Order_Nb"] = new_order_nb
                s_order["Deduction_Details"] = deductions
            if new_order_data:
                if "Product_ID" in new_order_data:
                    s_order["Product_ID"] = new_order_data["Product_ID"]
                if "ITEM Name" in new_order_data:
                    s_order["Product_Name"] = new_order_data["ITEM Name"]
                if "BTL PER CS" in new_order_data:
                    s_order["BTL_PER_CS"] = new_order_data["BTL PER CS"]
                    # 重新计算总销售瓶数：销售瓶数 = 销售箱数 * 更新后的 BTL PER CS
                    try:
                        qty_cs_sold = int(s_order.get("Quantity_CS_Sold", 0))
                    except Exception:
                        qty_cs_sold = 0
                    s_order["Total_Quantity_BTL_Sold"] = qty_cs_sold * int(new_order_data["BTL PER CS"])
            
            save_sales_order_to_db(s_order)

    # 5. 刷新内存与界面
    data_manager.data_changed.emit()
    data_manager.inventory_changed.emit()
    print(f"[级联更新] 已根据 PO_GUID={po_guid} 完成采购订单和关联记录的更新。")

def delete_purchase_order_by_guid(po_guid):
    """
    根据采购订单的 PO_GUID 删除采购订单，并级联处理库存记录。
    如果该采购订单已被销售（通过销售订单引用或库存数量小于原始数量），则不允许删除，
    并提示“该订单已售出，无法删除”。
    """
    global purchase_orders

    # 1. 在内存中找到对应的采购订单
    po_to_delete = next((po for po in purchase_orders if po.get("PO_GUID") == po_guid), None)
    if not po_to_delete:
        QMessageBox.warning(None, "删除错误", f"找不到 PO_GUID={po_guid} 的采购订单！")
        return

    # 2. 检查销售订单中是否引用了此 PO_GUID
    for s_order in sales_orders:
        # 假设销售订单中的 PO_GUID 字段存储为逗号分隔的字符串
        po_guid_list = [guid.strip() for guid in s_order.get("PO_GUID", "").split(',') if guid.strip()]
        if po_guid in po_guid_list:
            QMessageBox.warning(None, "删除错误", f"采购订单已被销售订单 {s_order.get('Sales_ID')} 引用，无法删除！ 请先删除销售订单")
            return

    # 3. 检查库存记录是否显示库存已售出
    import sqlite3
    import datetime
    db_path = r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT "Current_Stock_CS" FROM inventory WHERE "PO_GUID" = ?', (po_guid,))
    row = cursor.fetchone()
    if row:
        current_stock = int(row[0])
        # 假设采购订单中存有原始库存数量字段"QUANTITY CS"
        original_qty = int(po_to_delete.get("QUANTITY CS", 0))
        if current_stock < original_qty:
            QMessageBox.warning(None, "删除错误", "该采购订单已部分售出，无法删除！请先删除销售订单")
            conn.close()
            return

    # 4. 如果检测无异常，级联删除库存记录和采购订单记录
    cursor.execute('DELETE FROM inventory WHERE "PO_GUID" = ?', (po_guid,))
    cursor.execute('DELETE FROM purchase_orders WHERE "PO_GUID" = ?', (po_guid,))
    conn.commit()
    conn.close()

    # 同步更新内存数据
    purchase_orders = [po for po in purchase_orders if po.get("PO_GUID") != po_guid]
    data_manager.data_changed.emit()
    data_manager.inventory_changed.emit()
    QMessageBox.information(None, "成功", f"采购订单 (PO_GUID={po_guid}) 已删除。")

