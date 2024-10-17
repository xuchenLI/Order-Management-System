# order_details.py
import re
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QGridLayout, QComboBox
)
from PyQt6.QtCore import Qt
import pandas as pd

from data import orders, deleted_orders, db_fields, display_fields, delete_order_from_db, save_order_to_db, data_manager
from price_calculator import open_price_calculator

class OrderDetailsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("订单管理")
        self.setGeometry(200, 200, 1400, 700)

        self.layout_main = QVBoxLayout()

        # 输入区域
        self.layout_inputs = QGridLayout()
        self.layout_inputs.setHorizontalSpacing(10)  # 设置水平间距为 10
        self.entries = {}

        # 左侧字段
        left_fields = [
            ('订单号', 'Order Nb'),
            ('Order Type', 'Order Type'),
            ('Order Step', 'Order Step'),
            ('期望利润', "Expected Profit"),
            ('境内运费', 'Domestic Freight (CAD)'),
            ('国际运费', 'International Freight(€)'),
            ('EXW 汇率', 'EXW Exchange Rate'),
            ('国际运费汇率', 'International Freight Exchange Rate')
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

        # 新增字段
        new_fields = [
            ("销售对象", "allocation"),
            ("下游客户", "Sub-allocation"),
            #("日期", "date"),  # 日期自动生成，不需要手动输入
            ("状态", "status"),
        ]

        # 左侧字段放在布局的左列
        for row, (label_text, field_name) in enumerate(left_fields):
            label = QLabel(label_text + ":")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)  # 标签右对齐
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
            else:
                entry = QLineEdit()
            entry.setFixedWidth(500)
            entry.setStyleSheet("border: 1px solid lightgray;")
            self.entries[field_name] = entry
            self.layout_inputs.addWidget(label, row, 0)  # 左列
            self.layout_inputs.addWidget(entry, row, 1)  # 左列输入框

        # 右侧字段放在布局的右列
        for row, (label_text, field_name) in enumerate(right_fields):
            label = QLabel(label_text + ":")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)  # 标签右对齐
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
            self.layout_inputs.addWidget(label, row, 2)  # 右列
            self.layout_inputs.addWidget(entry, row, 3)  # 右列输入框

        # 新增字段放在左列
        for row, (label_text, field_name) in enumerate(new_fields, start=len(left_fields)):
            label = QLabel(label_text + ":")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            entry = QLineEdit()
            entry.setFixedWidth(500)
            entry.setStyleSheet("border: 1px solid lightgray;")
            self.entries[field_name] = entry
            self.layout_inputs.addWidget(label, row, 0)
            self.layout_inputs.addWidget(entry, row, 1)

        self.layout_main.addLayout(self.layout_inputs)
        # 按钮区域
        layout_buttons = QHBoxLayout()

        self.button_add = QPushButton("添加订单")
        self.button_add.clicked.connect(self.add_order)

        self.button_update = QPushButton("更新订单")
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

        # 创建主表格和按钮布局
        layout_table_with_button = QHBoxLayout()
        # 创建排序按钮并设置其宽度
        self.button_sort = QPushButton("排序订单号")
        self.button_sort.setFixedWidth(100)  # 可以根据需要调整宽度
        self.button_sort.clicked.connect(self.sort_orders_by_order_nb)
        # 将排序按钮添加到表格的左侧
        layout_table_with_button.addWidget(self.button_sort)
        # 创建一个空白标签用于填充，确保排序按钮在表格左侧
        spacer = QLabel(" ")
        layout_table_with_button.addWidget(spacer)

        # 订单列表显示区域
        self.order_table = QTableWidget()
        self.order_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # 修改选择模式为扩展选择模式，支持使用 Ctrl 和 Shift 进行多选
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
        self.layout_main.addLayout(layout_table_with_button)

        self.setLayout(self.layout_main)

        self.update_order_table()

    def on_order_selected(self, selected, deselected):
        try:
            indexes = self.order_table.selectionModel().selectedRows()
            if indexes:
                # 假设只允许单行选择
                index = indexes[0]
                row = index.row()
                # 从订单列表中获取对应的订单数据
                order = orders[row]
                # 将订单数据填充到输入框中
                for field_name, entry in self.entries.items():
                    value = order.get(field_name, "")
                    if isinstance(entry, QComboBox):
                        # 如果是下拉框，设置对应的选项
                        combo_index = entry.findText(value)
                        if combo_index >= 0:
                            entry.setCurrentIndex(combo_index)
                        else:
                            entry.setCurrentText(value)
                    else:
                        # 如果是文本输入框，设置文本
                        entry.setText(str(value))
            else:
                # 如果没有选择任何行，清空输入框
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
                # 检查是否为 QComboBox
                if isinstance(entry, QComboBox):
                    value = entry.currentText().strip()
                else:
                    value = entry.text().strip()
                new_order[field_name] = value

            # 自动添加日期和状态
            new_order['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_order['status'] = 'new'

            # 检查订单号是否为空
            if not new_order['Order Nb']:
                QMessageBox.warning(self, "添加失败", "订单号不能为空！")
                return

            # 检查订单号是否已存在
            if any(order['Order Nb'] == new_order['Order Nb'] for order in orders):
                QMessageBox.warning(self, "添加失败", "该订单号已存在！")
                return

            orders.append(new_order)
            save_order_to_db(new_order)
            # 发射数据变化信号
            data_manager.data_changed.emit()

            self.update_order_table()

            QMessageBox.information(self, "成功", f"订单 {new_order['Order Nb']} 已添加。")
        except Exception as e:
            print(f"添加订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"添加订单时发生错误：{e}")

    def update_order(self):
        try:
            order_nb = self.entries['Order Nb'].text().strip()  # 获取订单号
            if not order_nb:
                QMessageBox.warning(self, "更新失败", "请输入订单号！")
                return

            # 查找订单
            order = next((o for o in orders if o['Order Nb'] == order_nb), None)
            if not order:
                QMessageBox.warning(self, "更新失败", "订单号不存在！")
                return

            # 更新订单信息
            for field_name, entry in self.entries.items():
                if field_name == 'Order Nb':  # 跳过订单号字段
                    continue
                if isinstance(entry, QComboBox):
                    value = entry.currentText().strip()
                else:
                    value = entry.text().strip()
                order[field_name] = value  # 无论是否为空，都更新

            # 更新日期和状态
            order['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            order['status'] = 'update'

            # 保存更新后的订单到数据库
            save_order_to_db(order)
            # 发射数据变化信号
            data_manager.data_changed.emit()

            self.update_order_table()  # 更新表格显示
            QMessageBox.information(self, "成功", f"订单 {order_nb} 已更新。")
        except Exception as e:
            print(f"更新订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"更新订单时发生错误：{e}")

    def open_price_calculator(self):
        open_price_calculator(self)  # 传递当前窗口实例以刷新表格

    def find_order(self):
        try:
            search_order_nb = self.entry_search.text().strip()
            if not search_order_nb:
                QMessageBox.warning(self, "输入错误", "请输入订单号！")
                return

            order_nb_col = next((i for i, (label, field) in enumerate(display_fields) if field == "Order Nb"), None)
            if order_nb_col is None:
                QMessageBox.critical(self, "错误", "订单号字段未找到！")
                return

            for row in range(self.order_table.rowCount()):
                if self.order_table.item(row, order_nb_col).text().strip() == search_order_nb:
                    self.order_table.selectRow(row)
                    return

            QMessageBox.information(self, "查找结果", "无此订单。")
        except Exception as e:
            print(f"查找订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"查找订单时发生错误：{e}")

    def delete_order(self):
        try:
            delete_order_nb = self.entry_delete.text().strip()
            if not delete_order_nb:
                QMessageBox.warning(self, "输入错误", "请输入要删除的订单号！")
                return

            for index, order in enumerate(orders):
                if str(order['Order Nb']).strip() == delete_order_nb:
                    deleted_orders.append(order)
                    del orders[index]
                    delete_order_from_db(delete_order_nb)
                    # 发射数据变化信号
                    data_manager.data_changed.emit()

                    self.update_order_table()
                    QMessageBox.information(self, "成功", f"订单 {delete_order_nb} 已删除。")
                    return

            QMessageBox.information(self, "删除结果", "无此订单。")
        except Exception as e:
            print(f"删除订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"删除订单时发生错误：{e}")

    def undo_delete_order(self):
        try:
            if not deleted_orders:
                QMessageBox.information(self, "撤销无效", "没有可撤销的删除操作。")
                return

            last_deleted_order = deleted_orders.pop()

            reply = QMessageBox.question(
                self,
                '撤销删除',
                f"你确定要撤销删除订单 {last_deleted_order['Order Nb']} 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                orders.append(last_deleted_order)
                save_order_to_db(last_deleted_order)
                # 发射数据变化信号
                data_manager.data_changed.emit()

                self.update_order_table()
                QMessageBox.information(self, "成功", f"订单 {last_deleted_order['Order Nb']} 已恢复。")
            else:
                deleted_orders.append(last_deleted_order)
        except Exception as e:
            print(f"撤销删除订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"撤销删除订单时发生错误：{e}")

    def export_orders(self):
        try:
            selected_rows = self.order_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "导出错误", "请先选择要导出的订单！")
                return

            selected_orders = []
            for index in selected_rows:
                row = index.row()
                order = {field_name: self.order_table.item(row, col).text()
                         for col, (label_text, field_name) in enumerate(display_fields)}
                selected_orders.append(order)

            df = pd.DataFrame(selected_orders)
            export_filename = 'exported_orders.xlsx'
            try:
                df.to_excel(export_filename, index=False)
                QMessageBox.information(self, "导出成功", f"已成功导出到 {export_filename}")
            except Exception as e:
                QMessageBox.critical(self, "导出错误", f"导出失败: {e}")
        except Exception as e:
            print(f"导出订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"导出订单时发生错误：{e}")

    def update_order_table(self):
        #orders.sort(key=lambda order: order.get('Order Nb'))  # 按订单号排序
        self.order_table.setRowCount(0)
        self.order_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            for col, (label_text, field_name) in enumerate(display_fields):
                value = order.get(field_name, "")
                item = QTableWidgetItem(str(value))
                self.order_table.setItem(row, col, item)

    # 排序订单号的函数
    def sort_orders_by_order_nb(self):
        orders.sort(key=lambda order: order.get('Order Nb'))  # 按订单号排序
        self.update_order_table()  # 刷新表格显示

    def showEvent(self, event):
        super().showEvent(event)
        self.update_order_table()
