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

if __name__ == "__main__":
    sys.exit(app.exec())
