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
        try:
            search_order_nb = self.entry_search.text().strip()
            if not search_order_nb:
                QMessageBox.warning(self, "查找失败", "请输入要查找的订单号！")
                return
            order = get_purchase_order_by_nb(search_order_nb)
            if order:
                # 在表格中定位并选中该订单
                for row in range(self.order_table.rowCount()):
                    if self.order_table.item(row, 0).text() == search_order_nb:
                        self.order_table.selectRow(row)
                        # 滚动到该行
                        self.order_table.scrollToItem(self.order_table.item(row, 0))
                        break
            else:
                QMessageBox.information(self, "查找结果", f"未找到订单号为 {search_order_nb} 的订单。")
        except Exception as e:
            print(f"查找订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"查找订单时发生错误：{e}")


    def delete_order(self):
        try:
            order_nb = self.entry_delete.text().strip()
            if not order_nb:
                QMessageBox.warning(self, "删除失败", "请输入要删除的订单号！")
                return
            order = get_purchase_order_by_nb(order_nb)
            if order:
                # 从采购订单列表中删除
                purchase_orders.remove(order)
                # 添加到已删除订单列表，用于撤销删除
                deleted_orders.append(order)
                # 从数据库中删除
                delete_purchase_order_from_db(order_nb)
                # 更新库存
                quantity_cs = int(order.get('QUANTITY CS', 0))
                btl_per_cs = int(order.get('BTL PER CS', 0))
                quantity_btl = quantity_cs * btl_per_cs
                # 减少库存
                update_inventory(
                    order.get('Product_ID', ''),
                    order_nb,
                    -quantity_cs,
                    -quantity_btl,
                    order.get('Arrival_Date', ''),
                    order.get('date', ''),
                    order.get('ITEM Name', ''),
                    order.get('SKU CLS', ''),
                    btl_per_cs
                )
                self.update_order_table()
                QMessageBox.information(self, "成功", f"订单 {order_nb} 已删除。")
            else:
                QMessageBox.information(self, "删除失败", f"未找到订单号为 {order_nb} 的订单。")
        except Exception as e:
            print(f"删除订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"删除订单时发生错误：{e}")


    def undo_delete_order(self):
        try:
            if not deleted_orders:
                QMessageBox.information(self, "撤销删除", "没有可撤销的删除操作。")
                return
            # 取出最后一个被删除的订单
            order = deleted_orders.pop()
            # 添加回采购订单列表
            purchase_orders.append(order)
            # 保存到数据库
            save_purchase_order_to_db(order)
            # 更新库存
            quantity_cs = int(order.get('QUANTITY CS', 0))
            btl_per_cs = int(order.get('BTL PER CS', 0))
            quantity_btl = quantity_cs * btl_per_cs
            # 增加库存
            update_inventory(
                order.get('Product_ID', ''),
                order['Order Nb'],
                quantity_cs,
                quantity_btl,
                order.get('Arrival_Date', ''),
                order.get('date', ''),
                order.get('ITEM Name', ''),
                order.get('SKU CLS', ''),
                btl_per_cs
            )
            self.update_order_table()
            QMessageBox.information(self, "成功", f"订单 {order['Order Nb']} 已恢复。")
        except Exception as e:
            print(f"撤销删除时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"撤销删除时发生错误：{e}")


    def export_orders(self):
        try:
            import pandas as pd
            from PyQt6.QtWidgets import QFileDialog
            # 将采购订单转换为 DataFrame
            df = pd.DataFrame(purchase_orders)
            if df.empty:
                QMessageBox.information(self, "导出", "没有可导出的订单数据。")
                return
            # 指定导出的字段顺序
            field_order = [field_name for label_text, field_name in db_fields]
            df = df[field_order]
            # 弹出文件保存对话框
            options = QFileDialog.Option.DontUseNativeDialog  # 根据需要选择选项
            file_name, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "Excel Files (*.xlsx);;All Files (*)", options=options)

            if file_name:
                if not file_name.endswith('.xlsx'):
                    file_name += '.xlsx'
                df.to_excel(file_name, index=False)
                QMessageBox.information(self, "导出成功", f"采购订单已导出到文件 {file_name}")
        except Exception as e:
            print(f"导出订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"导出订单时发生错误：{e}")


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
