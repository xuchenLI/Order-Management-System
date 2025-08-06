# main.py
import os
import shutil
import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
import sys
import file_compare
from data import (
    initialize_database,
    load_purchase_orders_from_db,
    load_sales_orders_from_db,
    load_inventory_from_db,
    load_products_from_db
)
from order_details import OrderDetailsWindow
from inventory_management import InventoryManagementWindow
from sales_order import SalesOrderWindow
from product_management import ProductManagementWindow  
from purchase_order_dashboard import PurchaseOrderDashboardWindow
# from aglc_report_parser import open_aglc_parser  # 暂时注释掉，等待重新实现

# 配置数据库和备份文件夹路径
DB_PATH = r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\orders.db'
BACKUP_FOLDER = r'D:\00_Programming\98_Pycharm\00_Workplace\Order Manager\Official_Tool\01_Cursor_Code\01_Working\00_Main Branch\backups'
COUNTER_FILE = os.path.join(BACKUP_FOLDER, 'backup_counter.txt')
def backup_database(backup_type):
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)
    
    # 使用当天日期作为时间戳，确保一天内备份文件名固定
    date_stamp = datetime.datetime.now().strftime('%Y%m%d')
    if backup_type == "auto":
        backup_file = os.path.join(BACKUP_FOLDER, f"orders_backup_auto_{date_stamp}.db")
    elif backup_type == "periodic":
        backup_file = os.path.join(BACKUP_FOLDER, f"orders_backup_periodic_{date_stamp}.db")
    else:
        backup_file = os.path.join(BACKUP_FOLDER, f"orders_backup_{backup_type}_{date_stamp}.db")
    
    try:
        shutil.copy2(DB_PATH, backup_file)
        print(f"[{backup_type}备份成功] 数据库已备份至：{backup_file}")
    except Exception as e:
        print(f"[{backup_type}备份失败] 无法备份数据库：{e}")

def update_backup_counter():
    """
    更新备份计数器，每次启动程序调用此函数。
    如果计数器文件不存在，则创建并初始化为 1；否则累加 1 并写回文件。
    返回当前计数值。
    """
    # 如果备份目录不存在，则创建
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)
        
    count = 0
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, 'r', encoding='utf-8') as f:
                count = int(f.read().strip())
        except Exception as e:
            print(f"[计数器读取错误] {e}")
    count += 1  # 每次启动时加 1
    try:
        with open(COUNTER_FILE, 'w', encoding='utf-8') as f:
            f.write(str(count))
    except Exception as e:
        print(f"[计数器写入错误] {e}")
    return count

def perform_backup_on_startup():
    """
    在程序启动时执行两个备份：
    1. 每次启动均做自动备份（类型：auto）。
    2. 每打开五次程序时，再做一次周期备份（类型：periodic）。
    """
    # 自动备份
    backup_database("auto")
    # 更新计数器，并判断是否达到周期条件
    count = update_backup_counter()
    print(f"[启动计数] 当前启动次数：{count}")
    if count % 5 == 0:
        backup_database("periodic")

perform_backup_on_startup()
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
load_products_from_db()  # 新增

# 布局设置
layout_main = QVBoxLayout()

# 按钮区域
layout_buttons = QHBoxLayout()

button_order_dashboard = QPushButton("采购订单仪表盘")
button_order_dashboard.clicked.connect(lambda: open_purchase_order_dashboard_window())

# 移除采购订单管理按钮
# button_order_details = QPushButton("采购订单管理")
# button_order_details.clicked.connect(lambda: open_order_details_window())

button_sales_order = QPushButton("销售订单管理")
button_sales_order.clicked.connect(lambda: open_sales_order_window())

button_inventory_management = QPushButton("库存管理")
button_inventory_management.clicked.connect(lambda: open_inventory_management_window())

button_product_management = QPushButton("产品管理")  
button_product_management.clicked.connect(lambda: open_product_management_window())  

button_file_compare_tool = QPushButton("文件对比工具")
button_file_compare_tool.clicked.connect(lambda: file_compare.open_file_compare_tool())

# button_aglc_parser = QPushButton("AGLC报告解析")
# button_aglc_parser.clicked.connect(lambda: open_aglc_parser())

# 删除财务管理相关内容
# button_financial_management = QPushButton("财务管理")
# button_financial_management.clicked.connect(lambda: open_financial_management_window())

layout_buttons.addWidget(button_order_dashboard)
# layout_buttons.addWidget(button_order_details)
layout_buttons.addWidget(button_sales_order)
layout_buttons.addWidget(button_inventory_management)
layout_buttons.addWidget(button_product_management)
layout_buttons.addWidget(button_file_compare_tool)
# layout_buttons.addWidget(button_aglc_parser)
# layout_buttons.addWidget(button_financial_management)

layout_main.addLayout(layout_buttons)


# 定义窗口实例
order_details_window = None
sales_order_window = None
inventory_management_window = None
product_management_window = None  
financial_management_window = None
purchase_order_dashboard_window = None

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

# 打开产品管理窗口
def open_product_management_window():
    global product_management_window
    try:
        if product_management_window is None:
            product_management_window = ProductManagementWindow()
        else:
            product_management_window.update_product_table()
        product_management_window.show()
    except Exception as e:
        print(f"打开产品管理窗口时发生错误：{e}")
        QMessageBox.critical(None, "错误", f"打开产品管理窗口时发生错误：{e}")

def open_purchase_order_dashboard_window():
    global purchase_order_dashboard_window
    try:
        if purchase_order_dashboard_window is None:
            purchase_order_dashboard_window = PurchaseOrderDashboardWindow()
        else:
            purchase_order_dashboard_window.refresh_main_orders()
        purchase_order_dashboard_window.show()
    except Exception as e:
        print(f"打开采购订单仪表盘窗口时发生错误：{e}")
        QMessageBox.critical(None, "错误", f"打开采购订单仪表盘窗口时发生错误：{e}")

# 设置主布局
window.setLayout(layout_main)
window.show()

if __name__ == "__main__":
    sys.exit(app.exec())
