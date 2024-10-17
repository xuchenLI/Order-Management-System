# main.py

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
import sys

from data import load_orders_from_db, order_details_window
from order_details import OrderDetailsWindow  # 删除了 price_calculator 导入

# 创建主窗口
app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("订单管理系统")
window.setGeometry(100, 100, 800, 600)  # 调整窗口大小

# 程序启动时加载订单数据
load_orders_from_db()

# 布局设置
layout_main = QVBoxLayout()

# 订单按钮区域
layout_buttons = QHBoxLayout()

button_order_details = QPushButton("订单管理")  # 修改按钮名称
button_order_details.clicked.connect(lambda: open_order_details_window())

# 移除价格计算器按钮部分
# button_price_calculator = QPushButton("价格计算器")
# button_price_calculator.clicked.connect(lambda: open_price_calculator())

layout_buttons.addWidget(button_order_details)
# 不再添加价格计算器按钮到布局
# layout_buttons.addWidget(button_price_calculator)

layout_main.addLayout(layout_buttons)

# 定义订单详情窗口的实例
order_details_window = None


# 打开订单详情窗口
def open_order_details_window():
    global order_details_window
    try:
        if order_details_window is None:
            order_details_window = OrderDetailsWindow()
        else:
            order_details_window.update_order_table()
        order_details_window.show()
    except Exception as e:
        print(f"打开订单详情窗口时发生错误：{e}")
        QMessageBox.critical(None, "错误", f"打开订单详情窗口时发生错误：{e}")

    # 设置主布局


window.setLayout(layout_main)
window.show()

sys.exit(app.exec())
