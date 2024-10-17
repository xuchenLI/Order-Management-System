# main.py

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
import sys

from data import (
    initialize_database,
    load_purchase_orders_from_db,
    load_sales_orders_from_db,
    load_inventory_from_db
)
from order_details import OrderDetailsWindow
from inventory_management import InventoryManagementWindow
from sales_order import SalesOrderWindow

# 创建主窗口
app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("订单管理系统")
window.setGeometry(100, 100, 800, 600)

# 程序启动时加载数据
initialize_database()
load_purchase_orders_from_db()
load_sales_orders_from_db()
load_inventory_from_db()

# 布局设置
layout_main = QVBoxLayout()

# 按钮区域
layout_buttons = QHBoxLayout()

button_order_details = QPushButton("采购订单管理")
button_order_details.clicked.connect(lambda: open_order_details_window())

button_sales_order = QPushButton("销售订单管理")
button_sales_order.clicked.connect(lambda: open_sales_order_window())

button_inventory_management = QPushButton("库存管理")
button_inventory_management.clicked.connect(lambda: open_inventory_management_window())

layout_buttons.addWidget(button_order_details)
layout_buttons.addWidget(button_sales_order)
layout_buttons.addWidget(button_inventory_management)

layout_main.addLayout(layout_buttons)

# 定义窗口实例
order_details_window = None
sales_order_window = None
inventory_management_window = None

# 打开采购订单窗口
def open_order_details_window():
    global order_details_window
    try:
        if order_details_window is None:
            order_details_window = OrderDetailsWindow()
        else:
            order_details_window.update_order_table()
        order_details_window.show()
    except Exception as e:
        print(f"打开采购订单窗口时发生错误：{e}")
        QMessageBox.critical(None, "错误", f"打开采购订单窗口时发生错误：{e}")

# 打开销售订单窗口
def open_sales_order_window():
    global sales_order_window
    try:
        if sales_order_window is None:
            sales_order_window = SalesOrderWindow()
        else:
            sales_order_window.update_sales_order_table()
        sales_order_window.show()
    except Exception as e:
        print(f"打开销售订单窗口时发生错误：{e}")
        QMessageBox.critical(None, "错误", f"打开销售订单窗口时发生错误：{e}")

# 打开库存管理窗口
def open_inventory_management_window():
    global inventory_management_window
    try:
        if inventory_management_window is None:
            inventory_management_window = InventoryManagementWindow()
        else:
            inventory_management_window.update_inventory_tables()
        inventory_management_window.show()
    except Exception as e:
        print(f"打开库存管理窗口时发生错误：{e}")
        QMessageBox.critical(None, "错误", f"打开库存管理窗口时发生错误：{e}")

# 设置主布局
window.setLayout(layout_main)
window.show()

sys.exit(app.exec())
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
# order_details.py
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QGridLayout, QComboBox
)
from PyQt6.QtCore import Qt
import pandas as pd

from data import (
    purchase_orders, deleted_orders, db_fields, delete_purchase_order_from_db,
    save_purchase_order_to_db, data_manager, update_inventory, inventory,
    update_inventory_arrival_date, get_purchase_order_by_nb
)
from price_calculator import open_price_calculator

class OrderDetailsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("采购订单管理")
        self.setGeometry(200, 200, 1400, 700)

        self.layout_main = QVBoxLayout()

        # 输入区域
        self.layout_inputs = QGridLayout()
        self.layout_inputs.setHorizontalSpacing(10)
        self.entries = {}

        # 左侧字段
        left_fields = [
            ('订单号', 'Order Nb'),
            ('产品编号', 'Product_ID'),
            ('Order Type', 'Order Type'),
            ('Order Step', 'Order Step'),
            ('期望利润', "Expected Profit"),
            ('境内运费', 'Domestic Freight (CAD)'),
            ('国际运费', 'International Freight(€)'),
            ('EXW 汇率', 'EXW Exchange Rate'),
            ('国际运费汇率', 'International Freight Exchange Rate'),
            # 新增字段
            ("产品到仓库的日期", "Arrival_Date"),
        ]

        # 右侧字段
        right_fields = [
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
            ("EXW(€)", "EXW(€)"),
            ("REMARKS", "REMARKS"),
        ]

        # 左侧字段
        for row, (label_text, field_name) in enumerate(left_fields):
            label = QLabel(label_text + ":")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if field_name == "Order Type":
                entry = QComboBox()
                entry.addItems(["Allocation", "In Stock"])
                entry.setCurrentText("Allocation")
            elif field_name == "Order Step":
                entry = QComboBox()
                entry.addItems(["Offer", "Order", "Delivery"])
                entry.setCurrentText("Offer")
            elif field_name == "Expected Profit":
                entry = QLineEdit()
                entry.setText("0.05")
            elif field_name == "Domestic Freight (CAD)":
                entry = QLineEdit()
                entry.setText("35")
            elif field_name == "International Freight(€)":
                entry = QLineEdit()
                entry.setText("0")
            elif field_name == "EXW Exchange Rate":
                entry = QLineEdit()
                entry.setText("0")
            elif field_name == "International Freight Exchange Rate":
                entry = QLineEdit()
                entry.setText("0")
            elif field_name == "Arrival_Date":
                entry = QLineEdit()
                entry.setPlaceholderText("YYYY-MM-DD")
            else:
                entry = QLineEdit()
            entry.setFixedWidth(500)
            entry.setStyleSheet("border: 1px solid lightgray;")
            self.entries[field_name] = entry
            self.layout_inputs.addWidget(label, row, 0)
            self.layout_inputs.addWidget(entry, row, 1)

        # 右侧字段
        for row, (label_text, field_name) in enumerate(right_fields):
            label = QLabel(label_text + ":")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if field_name == "Supplier": 
                entry = QComboBox() 
                entry.addItems(["Filips", "CVBG", "DULONG", "BONCHATEAU"]) 
            elif field_name == "CATEGORY": 
                entry = QComboBox() 
                entry.addItems(["RED", "WHITE"]) 
                entry.setCurrentText("RED")
            elif field_name == "SIZE":
                entry = QComboBox()
                entry.addItems(["0.75", "1.5", "3", "6", "9"])
                entry.setCurrentText("0.75")
            else:
                entry = QLineEdit()
            entry.setFixedWidth(500)
            entry.setStyleSheet("border: 1px solid lightgray;")
            self.entries[field_name] = entry
            self.layout_inputs.addWidget(label, row, 2)
            self.layout_inputs.addWidget(entry, row, 3)

        self.layout_main.addLayout(self.layout_inputs)
        # 按钮区域
        layout_buttons = QHBoxLayout()

        self.button_add = QPushButton("添加采购订单")
        self.button_add.clicked.connect(self.add_order)

        self.button_update = QPushButton("更新采购订单")
        self.button_update.clicked.connect(self.update_order)

        self.entry_search = QLineEdit()
        self.entry_search.setMaxLength(15)
        self.entry_search.setFixedWidth(100)
        button_search = QPushButton("查找订单")
        button_search.clicked.connect(self.find_order)

        self.entry_delete = QLineEdit()
        self.entry_delete.setMaxLength(15)
        self.entry_delete.setFixedWidth(100)
        button_delete = QPushButton("删除订单")
        button_delete.clicked.connect(self.delete_order)

        undo_button = QPushButton("撤销删除")
        undo_button.clicked.connect(self.undo_delete_order)

        button_export = QPushButton("导出订单")
        button_export.clicked.connect(self.export_orders)

        button_price_calculator = QPushButton("价格计算器")
        button_price_calculator.clicked.connect(lambda: self.open_price_calculator())

        layout_buttons.addWidget(self.button_add)
        layout_buttons.addWidget(self.button_update)
        layout_buttons.addWidget(button_search)
        layout_buttons.addWidget(self.entry_search)
        layout_buttons.addWidget(button_delete)
        layout_buttons.addWidget(self.entry_delete)
        layout_buttons.addWidget(undo_button)
        layout_buttons.addWidget(button_export)
        layout_buttons.addWidget(button_price_calculator)

        self.layout_main.addLayout(layout_buttons)

        # 订单列表显示区域
        display_fields = [field for field in db_fields]
        self.order_table = QTableWidget()
        self.order_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.order_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.order_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.order_table.setColumnCount(len(display_fields))
        self.order_table.setHorizontalHeaderLabels([label_text for label_text, field_name in display_fields])
        self.order_table.verticalHeader().setVisible(False)
        self.order_table.horizontalHeader().setStretchLastSection(True)
        self.order_table.setWordWrap(True)
        self.order_table.resizeColumnsToContents()

        # 连接订单表格的选择信号到处理函数
        self.order_table.selectionModel().selectionChanged.connect(self.on_order_selected)

        self.layout_main.addWidget(self.order_table)

        self.setLayout(self.layout_main)

        self.update_order_table()

    def on_order_selected(self, selected, deselected):
        try:
            indexes = self.order_table.selectionModel().selectedRows()
            if indexes:
                index = indexes[0]
                row = index.row()
                order = purchase_orders[row]
                for field_name, entry in self.entries.items():
                    value = order.get(field_name, "")
                    if isinstance(entry, QComboBox):
                        combo_index = entry.findText(str(value))
                        if combo_index >= 0:
                            entry.setCurrentIndex(combo_index)
                        else:
                            entry.setCurrentText(str(value))
                    else:
                        entry.setText(str(value))
            else:
                for entry in self.entries.values():
                    if isinstance(entry, QComboBox):
                        entry.setCurrentIndex(-1)
                    else:
                        entry.clear()
        except Exception as e:
            print(f"处理订单选择时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"处理订单选择时发生错误：{e}")

    def add_order(self):
        try:
            new_order = {}
            for field_name, entry in self.entries.items():
                if isinstance(entry, QComboBox):
                    value = entry.currentText().strip()
                else:
                    value = entry.text().strip()

                # 处理需要整数的字段
                if field_name in ["QUANTITY CS", "BTL PER CS"]:
                    if not value:
                        QMessageBox.warning(self, "输入错误", f"{field_name} 不能为空！")
                        return
                    try:
                        value = int(value)  # 转换为整数
                    except ValueError:
                        QMessageBox.warning(self, "输入错误", f"{field_name} 必须是一个有效的整数！")
                        return

                # 处理需要浮点数的字段
                elif field_name in ["Expected Profit", "Domestic Freight (CAD)", "EXW(€)", "International Freight(€)", "EXW Exchange Rate", "International Freight Exchange Rate"]:
                    if not value:
                        QMessageBox.warning(self, "输入错误", f"{field_name} 不能为空！")
                        return
                    try:
                        value = float(value)  # 转换为浮点数
                    except ValueError:
                        QMessageBox.warning(self, "输入错误", f"{field_name} 必须是一个有效的数字！")
                        return

                new_order[field_name] = value

            # 自动添加日期
            new_order['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 检查订单号是否为空
            if not new_order['Order Nb']:
                QMessageBox.warning(self, "添加失败", "订单号不能为空！")
                return

            # 检查产品编号是否为空
            product_id = new_order.get('Product_ID', '')
            if not product_id:
                QMessageBox.warning(self, "添加失败", "产品编号不能为空！")
                return

            # 检查订单号是否已存在
            if any(order['Order Nb'] == new_order['Order Nb'] for order in purchase_orders):
                QMessageBox.warning(self, "添加失败", "该订单号已存在！")
                return

            # 更新库存
            quantity_cs = int(new_order.get('QUANTITY CS', 0))
            btl_per_cs = int(new_order.get('BTL PER CS', 0))
            quantity_btl = quantity_cs * btl_per_cs

            arrival_date = new_order.get('Arrival_Date', '')
            creation_date = new_order.get('date', '')
            item_name = new_order.get('ITEM Name', '')
            sku_cls = new_order.get('SKU CLS', '')

            update_inventory(
                product_id,
                new_order['Order Nb'],
                quantity_cs,
                quantity_btl,
                arrival_date,
                creation_date,
                item_name,
                sku_cls,
                btl_per_cs
            )

            # 保存采购订单
            purchase_orders.append(new_order)
            save_purchase_order_to_db(new_order)
            data_manager.data_changed.emit()

            self.update_order_table()

            QMessageBox.information(self, "成功", f"订单 {new_order['Order Nb']} 已添加。")

        except Exception as e:
            print(f"添加订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"添加订单时发生错误：{e}")

    def update_order(self):
        try:
            order_nb = self.entries['Order Nb'].text().strip()
            if not order_nb:
                QMessageBox.warning(self, "更新失败", "请输入订单号！")
                return

            # 获取现有订单数据
            existing_order = get_purchase_order_by_nb(order_nb)
            if not existing_order:
                QMessageBox.warning(self, "更新失败", "订单号不存在！")
                return

            # 准备更新后的订单数据
            updated_order = {}
            for field_name, entry in self.entries.items():
                if isinstance(entry, QComboBox):
                    value = entry.currentText().strip()
                else:
                    value = entry.text().strip()

                # 处理需要整数的字段
                if field_name in ["QUANTITY CS", "BTL PER CS"]:
                    if not value:
                        QMessageBox.warning(self, "输入错误", f"{field_name} 不能为空！")
                        return
                    try:
                        value = int(value)
                    except ValueError:
                        QMessageBox.warning(self, "输入错误", f"{field_name} 必须是一个有效的整数！")
                        return

                # 处理需要浮点数的字段
                elif field_name in ["Expected Profit", "Domestic Freight (CAD)", "EXW(€)", "International Freight(€)", "EXW Exchange Rate", "International Freight Exchange Rate"]:
                    if not value:
                        QMessageBox.warning(self, "输入错误", f"{field_name} 不能为空！")
                        return
                    try:
                        value = float(value)
                    except ValueError:
                        QMessageBox.warning(self, "输入错误", f"{field_name} 必须是一个有效的数字！")
                        return

                updated_order[field_name] = value

            # 更新日期
            updated_order['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 计算数量差异
            old_quantity_cs = int(existing_order.get('QUANTITY CS', 0))
            new_quantity_cs = int(updated_order.get('QUANTITY CS', 0))
            delta_quantity_cs = new_quantity_cs - old_quantity_cs

            old_btl_per_cs = int(existing_order.get('BTL PER CS', 0))
            new_btl_per_cs = int(updated_order.get('BTL PER CS', 0))
            old_quantity_btl = old_quantity_cs * old_btl_per_cs
            new_quantity_btl = new_quantity_cs * new_btl_per_cs
            delta_quantity_btl = new_quantity_btl - old_quantity_btl

            # 更新库存数量
            product_id = updated_order.get('Product_ID', '')
            arrival_date = updated_order.get('Arrival_Date', '')
            creation_date = updated_order.get('date', '')
            item_name = updated_order.get('ITEM Name', '')
            sku_cls = updated_order.get('SKU CLS', '')
            btl_per_cs = updated_order.get('BTL PER CS', 0)

            update_inventory(
                product_id,
                order_nb,
                delta_quantity_cs,
                delta_quantity_btl,
                arrival_date,
                creation_date,
                item_name,
                sku_cls,
                btl_per_cs
            )

            # 保存更新后的订单
            index = purchase_orders.index(existing_order)
            purchase_orders[index] = updated_order
            save_purchase_order_to_db(updated_order)
            data_manager.data_changed.emit()

            # 更新库存中的 Arrival_Date
            update_inventory_arrival_date(product_id, order_nb, arrival_date)

            self.update_order_table()
            QMessageBox.information(self, "成功", f"订单 {order_nb} 已更新。")
        except Exception as e:
            print(f"更新订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"更新订单时发生错误：{e}")

    # 其余方法保持不变

    def open_price_calculator(self):
        open_price_calculator(self)

    def find_order(self):
        # 方法代码保持不变
        pass

    def delete_order(self):
        # 方法代码保持不变
        pass

    def undo_delete_order(self):
        # 方法代码保持不变
        pass

    def export_orders(self):
        # 方法代码保持不变
        pass

    def update_order_table(self):
        # 更新订单表格显示
        display_fields = [field for field in db_fields]
        self.order_table.setRowCount(0)
        self.order_table.setRowCount(len(purchase_orders))
        for row, order in enumerate(purchase_orders):
            for col, (label_text, field_name) in enumerate(display_fields):
                value = order.get(field_name, "")
                item = QTableWidgetItem(str(value))
                self.order_table.setItem(row, col, item)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_order_table()
# sales_order.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt
import datetime
from data import (
    sales_orders, inventory, save_sales_order_to_db, delete_sales_order_from_db,
    update_inventory, load_sales_orders_from_db, get_total_stock, deduct_inventory
)

class SalesOrderWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("销售订单管理")
        self.setGeometry(200, 200, 1000, 600)

        self.layout_main = QVBoxLayout()

        # 输入区域
        self.layout_inputs = QGridLayout()
        self.entries = {}

        fields = [
            ('销售订单号', 'Sales_ID'),
            ('产品编号', 'Product_ID'),
            ('客户编号', 'Customer_ID'),
            ('数量', 'Quantity'),
            ('单价', 'Price'),
            ('备注', 'Remarks')
        ]

        for row, (label_text, field_name) in enumerate(fields):
            label = QLabel(label_text + ":")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            entry = QLineEdit()
            entry.setFixedWidth(300)
            entry.setStyleSheet("border: 1px solid lightgray;")
            self.entries[field_name] = entry
            self.layout_inputs.addWidget(label, row, 0)
            self.layout_inputs.addWidget(entry, row, 1)

        self.layout_main.addLayout(self.layout_inputs)

        # 按钮区域
        layout_buttons = QHBoxLayout()

        self.button_add = QPushButton("添加销售订单")
        self.button_add.clicked.connect(self.add_sales_order)

        self.button_delete = QPushButton("删除销售订单")
        self.button_delete.clicked.connect(self.delete_sales_order)

        layout_buttons.addWidget(self.button_add)
        layout_buttons.addWidget(self.button_delete)

        self.layout_main.addLayout(layout_buttons)

        # 销售订单列表
        self.sales_order_table = QTableWidget()
        self.sales_order_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sales_order_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sales_order_table.setColumnCount(len(fields))
        self.sales_order_table.setHorizontalHeaderLabels([label_text for label_text, field_name in fields])
        self.sales_order_table.verticalHeader().setVisible(False)
        self.sales_order_table.horizontalHeader().setStretchLastSection(True)
        self.sales_order_table.setWordWrap(True)
        self.sales_order_table.resizeColumnsToContents()

        self.layout_main.addWidget(self.sales_order_table)

        self.setLayout(self.layout_main)

        # 加载销售订单数据
        load_sales_orders_from_db()
        self.update_sales_order_table()

    def add_sales_order(self):
        try:
            new_order = {}
            for field_name, entry in self.entries.items():
                value = entry.text().strip()
                new_order[field_name] = value

            # 自动添加订单日期
            new_order['Order_Date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_order['Shipped_Date'] = ''

            # 检查必要字段
            if not new_order['Sales_ID']:
                QMessageBox.warning(self, "添加失败", "销售订单号不能为空！")
                return

            # 检查库存是否足够
            product_id = new_order['Product_ID']
            quantity = int(new_order['Quantity'])
            total_stock_cs, total_stock_btl = get_total_stock(product_id)
            if total_stock_btl < quantity:
                QMessageBox.warning(self, "库存不足", "库存不足，无法添加销售订单！")
                return

            # 更新库存
            # 从库存中扣减对应数量的瓶数
            deduct_inventory(product_id, quantity)

            # 保存销售订单
            sales_orders.append(new_order)
            save_sales_order_to_db(new_order)

            self.update_sales_order_table()

            QMessageBox.information(self, "成功", f"销售订单 {new_order['Sales_ID']} 已添加。")

        except Exception as e:
            print(f"添加销售订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"添加销售订单时发生错误：{e}")

    def delete_sales_order(self):
        try:
            selected_rows = self.sales_order_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "删除错误", "请先选择要删除的销售订单！")
                return

            for index in selected_rows:
                row = index.row()
                sales_id = self.sales_order_table.item(row, 0).text()
                # 恢复库存
                order = next((o for o in sales_orders if o['Sales_ID'] == sales_id), None)
                if order:
                    product_id = order['Product_ID']
                    quantity = int(order['Quantity'])
                    # 将库存增加对应的数量
                    update_inventory(product_id, '', 0, quantity, '', '', '', 0, '')

                # 从列表和数据库中删除
                sales_orders.remove(order)
                delete_sales_order_from_db(sales_id)

            self.update_sales_order_table()

            QMessageBox.information(self, "成功", "选中的销售订单已删除。")

        except Exception as e:
            print(f"删除销售订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"删除销售订单时发生错误：{e}")

    def update_sales_order_table(self):
        self.sales_order_table.setRowCount(0)
        self.sales_order_table.setRowCount(len(sales_orders))
        for row, order in enumerate(sales_orders):
            for col, (label_text, field_name) in enumerate(self.entries.items()):
                value = order.get(field_name, "")
                item = QTableWidgetItem(str(value))
                self.sales_order_table.setItem(row, col, item)
# price_calculator.py

from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QDialog, QMessageBox
)
from data import purchase_orders, save_purchase_order_to_db
import math

# 默认配置参数
config_params = {
    'Total COGS': {
        'New_listing_SKU_cfg': 84,
        'Storage_cfg': 0.47,
        'Predict_Storage_Days': 100,
        'Allocation_Fee_cfg': 0.16,
        'Administration_cfg': 0.24,
        'Receiving_cfg': 0.46,
        'Assembly_cfg': 1.14,
        'Barcode_cfg': 0.44,
        'Damage_And_Retention_Sample_cfg': 0
    },
    'CIF': {
        'Strip Label Cost EURO': 0.37,
        'Total Freight CAD': 35
    },
    'WHLSE': {
        'RECYCLE RATE': 0.09,
        'PLUS DUTY': 0
    }
}

def open_price_calculator(order_details_window):
    calculator_window = QDialog()
    calculator_window.setWindowTitle("价格计算器")
    layout = QVBoxLayout()

    # 订单号输入字段
    order_nb_entry = QLineEdit()
    layout.addWidget(QLabel("订单号:"))
    layout.addWidget(order_nb_entry)

    # 显示计算结果的字段
    results_labels = {
        'INVOICE PRICE': QLineEdit(),
        'INVOICE CS': QLineEdit(),
        'WHOLESALE BTL': QLineEdit(),
        'WHOLESALE CS': QLineEdit(),
        'TOTAL Freight CAD': QLineEdit(),
        'PROFIT PER BT': QLineEdit(),
        'PROFIT PER CS': QLineEdit(),
        'PROFIT TOTAL': QLineEdit(),
        'QUANTITY BTL': QLineEdit(),
        'TOTAL AMOUNT': QLineEdit()
    }

    # 设置这些字段为只读
    for key, entry in results_labels.items():
        entry.setReadOnly(True)
        layout.addWidget(QLabel(f"{key}:"))
        layout.addWidget(entry)

    # 计算和配置按钮
    calc_button = QPushButton("计算")
    calc_button.clicked.connect(lambda: calculate_and_display(order_nb_entry.text(), results_labels))
    layout.addWidget(calc_button)

    update_button = QPushButton("更新")
    update_button.clicked.connect(lambda: update_order(order_nb_entry.text(), results_labels, order_details_window))
    layout.addWidget(update_button)

    calculator_window.setLayout(layout)
    calculator_window.exec()

def calculate_and_display(order_nb, results_labels):
    try:
        # 根据订单号获取订单
        order = next((o for o in purchase_orders if o['Order Nb'] == order_nb), None)
        if not order:
            QMessageBox.warning(None, "错误", "订单号不存在")
            return
        # 检查 EXW 汇率是否为 0
        EXW_rate = float(order.get('EXW Exchange Rate', 0))
        if EXW_rate == 0:
            QMessageBox.warning(None, "错误", "EXW 汇率不能为 0，请检查订单信息")
            return  # 如果汇率为 0，则终止计算
        # 计算 QUANTITY BTL 和 TOTAL AMOUNT
        QUANTITY_CS = int(order.get('QUANTITY CS', 0))
        BTL_PER_CS = int(order.get('BTL PER CS', 0))
        EXW = float(order.get('EXW(€)', 0))

        QUANTITY_BTL = QUANTITY_CS * BTL_PER_CS
        TOTAL_AMOUNT = EXW * QUANTITY_BTL

        # 计算其他价格
        INVOICE_PRICE, INVOICE_CS, CIF, TOTAL_Freight_CAD, Total_COGS = calculate_invoice_price(order)
        WHOLESALE_BTL, WHOLESALE_CS = calculate_wholesale(order, INVOICE_CS)

        # 计算 PROFIT PER BT、PROFIT PER CS 和 PROFIT TOTAL
        expected_profit = float(order.get('Expected Profit', 0))
        PROFIT_PER_BT = INVOICE_PRICE - Total_COGS
        PROFIT_PER_CS = PROFIT_PER_BT * BTL_PER_CS
        PROFIT_TOTAL = PROFIT_PER_CS * QUANTITY_CS

        # 显示结果
        results_labels['INVOICE PRICE'].setText(str(round(INVOICE_PRICE, 2)))
        results_labels['INVOICE CS'].setText(str(round(INVOICE_CS, 2)))
        results_labels['WHOLESALE BTL'].setText(str(round(WHOLESALE_BTL, 2)))
        results_labels['WHOLESALE CS'].setText(str(round(WHOLESALE_CS, 2)))
        results_labels['TOTAL Freight CAD'].setText(str(round(TOTAL_Freight_CAD, 2)))
        results_labels['PROFIT PER BT'].setText(str(round(PROFIT_PER_BT, 2)))
        results_labels['PROFIT PER CS'].setText(str(round(PROFIT_PER_CS, 2)))
        results_labels['PROFIT TOTAL'].setText(str(round(PROFIT_TOTAL, 2)))
        results_labels['QUANTITY BTL'].setText(str(QUANTITY_BTL))
        results_labels['TOTAL AMOUNT'].setText(str(round(TOTAL_AMOUNT, 2)))

        QMessageBox.information(None, "计算成功", "价格计算完成")
    except Exception as e:
        print(f"计算时发生错误：{e}")
        QMessageBox.critical(None, "计算错误", f"计算时发生错误：{e}")

def update_order(order_nb, results_labels, order_details_window):
    if not order_nb:
        QMessageBox.warning(None, "更新错误", "订单号为空")
        return

    try:
        # 获取订单对象
        order = next((o for o in purchase_orders if o['Order Nb'] == order_nb), None)
        if not order:
            QMessageBox.warning(None, "更新错误", "订单不存在")
            return

        # 更新订单的数据
        updated_fields = {}
        for key in ['INVOICE PRICE', 'INVOICE CS', 'WHOLESALE BTL', 'WHOLESALE CS', 'TOTAL Freight CAD',
                    'PROFIT PER BT', 'PROFIT PER CS', 'PROFIT TOTAL', 'QUANTITY BTL', 'TOTAL AMOUNT']:
            value = results_labels[key].text().strip()
            if value:
                if key == 'TOTAL Freight CAD':
                    order['TOTAL Freight'] = value
                elif key == 'TOTAL AMOUNT':
                    order['TOTAL AMOUNT(€)'] = value
                else:
                    order[key] = value
                updated_fields[key] = value

        # 将更新后的订单保存到数据库
        save_purchase_order_to_db(order)

        # 更新表格显示
        if order_details_window:
            order_details_window.update_order_table()

        QMessageBox.information(None, "更新成功", f"订单 {order_nb} 已成功更新")
    except Exception as e:
        print(f"更新订单时发生错误：{e}")
        QMessageBox.critical(None, "更新错误", f"更新订单时发生错误：{e}")

def calculate_invoice_price(order):
    try:
        # 验证并提取数据
        EXW = float(order.get('EXW(€)', 0))
        EXW_rate = float(order.get('EXW Exchange Rate', 0))
        BTL_PER_CS = int(order.get('BTL PER CS', 0))
        QUANTITY_CS = int(order.get('QUANTITY CS', 0))
        expected_profit = float(order.get('Expected Profit', 0))
        domestic_freight = float(order.get('Domestic Freight (CAD)', 0))
        international_freight = float(order.get('International Freight(€)', 0))
        international_freight_rate = float(order.get('International Freight Exchange Rate', 0))

        # CIF Calculation
        Strip_Label_Cost_CAD = config_params['CIF']['Strip Label Cost EURO'] * EXW_rate
        TOTAL_Freight_CAD = domestic_freight + international_freight * international_freight_rate
        EXW_CAD = EXW * EXW_rate
        CIF = EXW_CAD + Strip_Label_Cost_CAD + TOTAL_Freight_CAD

        # Total COGS Calculation
        New_listing_SKU = config_params['Total COGS']['New_listing_SKU_cfg'] / (BTL_PER_CS * QUANTITY_CS)
        Storage = config_params['Total COGS']['Storage_cfg'] / 30 / BTL_PER_CS * config_params['Total COGS']['Predict_Storage_Days']
        Allocation_Fee = config_params['Total COGS']['Allocation_Fee_cfg'] / BTL_PER_CS
        Administration = config_params['Total COGS']['Administration_cfg'] / BTL_PER_CS
        Receiving = config_params['Total COGS']['Receiving_cfg'] / BTL_PER_CS
        Assembly = config_params['Total COGS']['Assembly_cfg'] / BTL_PER_CS
        Barcode = config_params['Total COGS']['Barcode_cfg'] / BTL_PER_CS
        Damage = config_params['Total COGS']['Damage_And_Retention_Sample_cfg']
        GST_Service_AGLC = (
            New_listing_SKU + Storage + Allocation_Fee + Administration + Receiving + Assembly + Barcode) * 0.05

        Total_COGS = CIF + New_listing_SKU + Storage + Allocation_Fee + Administration + Receiving + Assembly + Barcode + Damage + GST_Service_AGLC

        # INVOICE PRICE and INVOICE CS Calculation
        INVOICE_PRICE = Total_COGS / (1 - expected_profit)
        INVOICE_CS = INVOICE_PRICE * BTL_PER_CS

        return INVOICE_PRICE, INVOICE_CS, CIF, TOTAL_Freight_CAD, Total_COGS
    except Exception as e:
        print(f"计算发票价格时发生错误：{e}")
        return None, None, None, None, None

def calculate_wholesale(order, INVOICE_CS):
    try:
        BTL_PER_CS = int(order.get('BTL PER CS', 0))
        SIZE = float(order.get('SIZE', 0))
        ALC = float(order.get('ALC.', 0))

        # WHOLESALE Calculation
        if SIZE > 1:
            DEPOSIT = 0.25
        else:
            DEPOSIT = 0.1

        # MARKUP RATE
        if ALC <= 16:
            MARKUP_RATE = 3.91
        else:
            MARKUP_RATE = 6.56

        # TOTAL COST CASE Calculation
        PLUS_MARKUP = SIZE * BTL_PER_CS * MARKUP_RATE
        PLUS_RECYCLE = math.floor(config_params['WHLSE']['RECYCLE RATE'] * BTL_PER_CS * 1000) / 1000
        PLUS_EXCISE = calculate_excise_rate(ALC) * SIZE * BTL_PER_CS

        TOTAL_COST_CASE = INVOICE_CS + PLUS_MARKUP + PLUS_RECYCLE + config_params['WHLSE']['PLUS DUTY'] + PLUS_EXCISE
        COST_UNIT = TOTAL_COST_CASE / BTL_PER_CS

        # WHOLESALE BTL Calculation
        ROUNDUP_UNIT = math.ceil(COST_UNIT * 100) / 100
        PLUS_GST = ROUNDUP_UNIT * 0.05
        SUB_TOTAL = PLUS_GST + ROUNDUP_UNIT
        ROUNDED = round(SUB_TOTAL, 2)
        WHOLESALE_BTL = ROUNDED + DEPOSIT
        WHOLESALE_CS = WHOLESALE_BTL * BTL_PER_CS

        return WHOLESALE_BTL, WHOLESALE_CS
    except Exception as e:
        print(f"计算批发价格时发生错误：{e}")
        return None, None

def calculate_excise_rate(ALC):
    if ALC <= 0.012:
        return 0.022
    elif 0.012 < ALC <= 0.07:
        return 0.337
    elif 0.07 < ALC <= 0.229:
        return 0.702
    else:
        QMessageBox.warning(None, "警告", "请确认酒精度是否正确")
        return 0
# inventory_management.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel,
    QLineEdit, QHBoxLayout, QPushButton, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from data import inventory, load_inventory_from_db, update_inventory_allocation
import datetime

class InventoryManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("库存管理")
        self.setGeometry(300, 300, 1000, 600)

        self.layout_main = QVBoxLayout()

        # 输入区域
        self.layout_inputs = QGridLayout()
        self.entries = {}

        label_order_nb = QLabel("订单号:")
        self.entry_order_nb = QLineEdit()
        self.entries['Order_Nb'] = self.entry_order_nb
        self.layout_inputs.addWidget(label_order_nb, 0, 0)
        self.layout_inputs.addWidget(self.entry_order_nb, 0, 1)

        label_allocation = QLabel("Allocation:")
        self.entry_allocation = QLineEdit()
        self.entries['Allocation'] = self.entry_allocation
        self.layout_inputs.addWidget(label_allocation, 1, 0)
        self.layout_inputs.addWidget(self.entry_allocation, 1, 1)

        label_sub_allocation = QLabel("Sub-allocation:")
        self.entry_sub_allocation = QLineEdit()
        self.entries['Sub_allocation'] = self.entry_sub_allocation
        self.layout_inputs.addWidget(label_sub_allocation, 2, 0)
        self.layout_inputs.addWidget(self.entry_sub_allocation, 2, 1)

        # 更新按钮
        self.button_update = QPushButton("更新")
        self.button_update.clicked.connect(self.update_inventory_record)
        self.layout_inputs.addWidget(self.button_update, 3, 0, 1, 2)

        self.layout_main.addLayout(self.layout_inputs)

        # 总览标题
        total_label = QLabel("库存总览")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_main.addWidget(total_label)

        # 总览库存列表
        self.total_inventory_table = QTableWidget()
        self.total_inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.total_inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.total_inventory_table.setColumnCount(5)
        self.total_inventory_table.setHorizontalHeaderLabels(['产品编号', 'SKU CLS', '产品名称', '库存-箱数', '库存-瓶数'])
        self.total_inventory_table.verticalHeader().setVisible(False)
        self.total_inventory_table.horizontalHeader().setStretchLastSection(True)
        self.total_inventory_table.setWordWrap(True)
        self.total_inventory_table.resizeColumnsToContents()

        self.layout_main.addWidget(self.total_inventory_table)

        # 明细标题
        detail_label = QLabel("库存明细")
        detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_main.addWidget(detail_label)

        # 明细库存列表
        self.detail_inventory_table = QTableWidget()
        self.detail_inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.detail_inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.detail_inventory_table.setColumnCount(11)
        self.detail_inventory_table.setHorizontalHeaderLabels([
            'Allocation', 'Sub-allocation', '订单号', '产品编号', 'SKU CLS', '产品名称',
            '库存-箱数', '库存-瓶数', '库存天数', '到仓库日期', '创建日期'
        ])
        self.detail_inventory_table.verticalHeader().setVisible(False)
        self.detail_inventory_table.horizontalHeader().setStretchLastSection(True)
        self.detail_inventory_table.setWordWrap(True)
        self.detail_inventory_table.resizeColumnsToContents()

        self.layout_main.addWidget(self.detail_inventory_table)

        self.setLayout(self.layout_main)

        # 连接选择信号到处理函数
        self.detail_inventory_table.selectionModel().selectionChanged.connect(self.on_order_selected)

        # 加载库存数据
        load_inventory_from_db()
        self.update_inventory_tables()

    def on_order_selected(self, selected, deselected):
        indexes = self.detail_inventory_table.selectionModel().selectedRows()
        if indexes:
            index = indexes[0]
            row = index.row()
            order_nb = self.detail_inventory_table.item(row, 2).text()
            self.entry_order_nb.setText(order_nb)
            allocation = self.detail_inventory_table.item(row, 0).text()
            sub_allocation = self.detail_inventory_table.item(row, 1).text()
            self.entry_allocation.setText(allocation)
            self.entry_sub_allocation.setText(sub_allocation)

    def update_inventory_record(self):
        order_nb = self.entry_order_nb.text().strip()
        allocation = self.entry_allocation.text().strip()
        sub_allocation = self.entry_sub_allocation.text().strip()

        if not order_nb:
            QMessageBox.warning(self, "更新错误", "请输入订单号！")
            return

        try:
            # 更新库存记录
            # 找到对应的库存记录
            inventory_record = next((item for item in inventory if item['Order_Nb'] == order_nb), None)
            if not inventory_record:
                QMessageBox.warning(self, "更新错误", "未找到对应的库存记录！")
                return

            # 更新数据库
            update_inventory_allocation(order_nb, allocation, sub_allocation)

            # 更新内存中的 inventory 列表
            load_inventory_from_db()

            # 更新表格显示
            self.update_inventory_tables()

            QMessageBox.information(self, "成功", "库存记录已更新！")
        except Exception as e:
            print(f"更新库存记录时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"更新库存记录时发生错误：{e}")

    def update_inventory_tables(self):
        # 更新总览表
        total_inventory = {}
        for product in inventory:
            product_id = product['Product_ID']
            sku_cls = product.get('SKU_CLS', '')
            key = (product_id, sku_cls)
            if key not in total_inventory:
                total_inventory[key] = {
                    'Product_ID': product_id,
                    'SKU_CLS': sku_cls,
                    'Product_Name': product['Product_Name'],
                    'Current_Stock_CS': int(product['Current_Stock_CS']),
                    'Current_Stock_BTL': int(product['Current_Stock_BTL'])
                }
            else:
                total_inventory[key]['Current_Stock_CS'] += int(product['Current_Stock_CS'])
                total_inventory[key]['Current_Stock_BTL'] += int(product['Current_Stock_BTL'])

        self.total_inventory_table.setRowCount(0)
        self.total_inventory_table.setRowCount(len(total_inventory))
        for row, product in enumerate(total_inventory.values()):
            self.total_inventory_table.setItem(row, 0, QTableWidgetItem(product['Product_ID']))
            self.total_inventory_table.setItem(row, 1, QTableWidgetItem(product.get('SKU_CLS', '')))
            self.total_inventory_table.setItem(row, 2, QTableWidgetItem(product['Product_Name']))
            self.total_inventory_table.setItem(row, 3, QTableWidgetItem(str(product['Current_Stock_CS'])))
            self.total_inventory_table.setItem(row, 4, QTableWidgetItem(str(product['Current_Stock_BTL'])))

        # 更新明细表
        self.detail_inventory_table.setRowCount(0)
        self.detail_inventory_table.setRowCount(len(inventory))
        for row, product in enumerate(inventory):
            self.detail_inventory_table.setItem(row, 0, QTableWidgetItem(product.get('Allocation', '')))
            self.detail_inventory_table.setItem(row, 1, QTableWidgetItem(product.get('Sub-allocation', '')))
            self.detail_inventory_table.setItem(row, 2, QTableWidgetItem(product['Order_Nb']))
            self.detail_inventory_table.setItem(row, 3, QTableWidgetItem(product['Product_ID']))
            self.detail_inventory_table.setItem(row, 4, QTableWidgetItem(product.get('SKU_CLS', '')))
            self.detail_inventory_table.setItem(row, 5, QTableWidgetItem(product['Product_Name']))
            self.detail_inventory_table.setItem(row, 6, QTableWidgetItem(str(product['Current_Stock_CS'])))
            self.detail_inventory_table.setItem(row, 7, QTableWidgetItem(str(product['Current_Stock_BTL'])))

            # 计算库存天数
            arrival_date_str = product.get('Arrival_Date', '')
            if arrival_date_str:
                arrival_date = datetime.datetime.strptime(arrival_date_str, "%Y-%m-%d")
                delta_days = (datetime.datetime.now() - arrival_date).days
                self.detail_inventory_table.setItem(row, 8, QTableWidgetItem(str(delta_days)))
            else:
                self.detail_inventory_table.setItem(row, 8, QTableWidgetItem("N/A"))

            self.detail_inventory_table.setItem(row, 9, QTableWidgetItem(product.get('Arrival_Date', '')))
            self.detail_inventory_table.setItem(row, 10, QTableWidgetItem(product.get('Creation_Date', '')))
