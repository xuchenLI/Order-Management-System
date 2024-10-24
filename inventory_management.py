# inventory_management.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel,
    QLineEdit, QHBoxLayout, QPushButton, QGridLayout, QMessageBox, QComboBox
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

        # 明细标题和过滤选项
        detail_layout = QHBoxLayout()
        detail_label = QLabel("库存明细")
        detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail_layout.addWidget(detail_label)

        # 添加过滤选项到库存明细标题的右侧
        filter_label = QLabel("过滤库存类型:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "In Stock", "Allocation"])
        self.filter_combo.currentIndexChanged.connect(self.update_inventory_tables)
        detail_layout.addWidget(filter_label)
        detail_layout.addWidget(self.filter_combo)

        self.layout_main.addLayout(detail_layout)

        # 明细库存列表
        self.detail_inventory_table = QTableWidget()
        self.detail_inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.detail_inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.detail_inventory_table.setColumnCount(12)
        self.detail_inventory_table.setHorizontalHeaderLabels([
            'Order Type', 'Allocation', 'Sub-allocation', '订单号', '产品编号', 'SKU CLS', '产品名称',
            '库存-箱数', '库存-瓶数', '库存天数', '到仓库日期', '创建日期'
        ])
        self.detail_inventory_table.verticalHeader().setVisible(False)
        self.detail_inventory_table.horizontalHeader().setStretchLastSection(True)
        self.detail_inventory_table.setWordWrap(True)
        self.detail_inventory_table.resizeColumnsToContents()

        self.layout_main.addWidget(self.detail_inventory_table)

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
            order_nb = self.detail_inventory_table.item(row, 3).text()
            self.entry_order_nb.setText(order_nb)
            allocation = self.detail_inventory_table.item(row, 1).text()
            sub_allocation = self.detail_inventory_table.item(row, 2).text()
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
        # 获取当前选择的过滤类型
        selected_filter = self.filter_combo.currentText()
        # 筛选库存数据
        if selected_filter == "全部":
            filtered_inventory = inventory
        else:
            filtered_inventory = [item for item in inventory if item.get('Order_Type', '') == selected_filter]

        # 更新明细表
        self.detail_inventory_table.setRowCount(0)
        self.detail_inventory_table.setRowCount(len(filtered_inventory))
        for row, product in enumerate(filtered_inventory):
            self.detail_inventory_table.setItem(row, 0, QTableWidgetItem(product.get('Order_Type', '')))
            self.detail_inventory_table.setItem(row, 1, QTableWidgetItem(product.get('Allocation', '')))
            self.detail_inventory_table.setItem(row, 2, QTableWidgetItem(product.get('Sub-allocation', '')))
            self.detail_inventory_table.setItem(row, 3, QTableWidgetItem(product['Order_Nb']))
            self.detail_inventory_table.setItem(row, 4, QTableWidgetItem(product['Product_ID']))
            self.detail_inventory_table.setItem(row, 5, QTableWidgetItem(product.get('SKU_CLS', '')))
            self.detail_inventory_table.setItem(row, 6, QTableWidgetItem(product['Product_Name']))
            self.detail_inventory_table.setItem(row, 7, QTableWidgetItem(str(product['Current_Stock_CS'])))
            self.detail_inventory_table.setItem(row, 8, QTableWidgetItem(str(product['Current_Stock_BTL'])))

            # 计算库存天数
            arrival_date_str = product.get('Arrival_Date', '')
            if arrival_date_str:
                arrival_date = datetime.datetime.strptime(arrival_date_str, "%Y-%m-%d")
                delta_days = (datetime.datetime.now() - arrival_date).days
                self.detail_inventory_table.setItem(row, 9, QTableWidgetItem(str(delta_days)))
            else:
                self.detail_inventory_table.setItem(row, 9, QTableWidgetItem("N/A"))

            self.detail_inventory_table.setItem(row, 10, QTableWidgetItem(product.get('Arrival_Date', '')))
            self.detail_inventory_table.setItem(row, 11, QTableWidgetItem(product.get('Creation_Date', '')))

        # 更新总览表
        total_inventory = {}
        for product in filtered_inventory:
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
