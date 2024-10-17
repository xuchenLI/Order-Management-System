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
