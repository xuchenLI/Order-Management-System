# sales_order.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QGridLayout, QComboBox, QListWidget, QAbstractItemView, QListWidgetItem
)
from PyQt6.QtCore import Qt
import datetime
from data import (
    sales_orders, save_sales_order_to_db, delete_sales_order_from_db,
    load_sales_orders_from_db, get_total_stock, deduct_inventory,
    get_btl_per_cs, restore_inventory, get_WHOLESALE_BTL_price, data_manager, inventory, update_inventory
)
from data import get_purchase_order_by_product_id

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
            ('订单号','Order_Nb'),
            ('客户编号', 'Customer_ID'),
            ('销售箱数', 'Quantity_CS_Sold'),
            ('销售瓶数', 'Quantity_BTL_Sold'),
            ('单瓶售价(€)', 'Price_per_bottle'),
            ('备注', 'Remarks')
        ]

        for row, (label_text, field_name) in enumerate(fields):
            label = QLabel(label_text + ":")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if field_name == 'Product_ID':
                entry = QComboBox()
                product_ids = self.get_all_product_ids()
                # 在产品编号列表的开头插入一个空字符串，代表空选项
                product_ids.insert(0, '')
                entry.addItems(product_ids)
                entry.setCurrentIndex(0)  # 设置默认选中第一个空选项
                entry.currentIndexChanged.connect(self.on_product_id_changed)
            elif field_name == 'Order_Nb':
                entry = QListWidget()
                entry.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
                entry.setFixedHeight(100)
                entry.itemSelectionChanged.connect(self.update_available_stock)
            elif field_name == 'Quantity_CS_Sold':
                entry = QLineEdit()
                entry.setFixedWidth(300)
                entry.setStyleSheet("border: 1px solid lightgray;")
                self.entries[field_name] = entry
                self.layout_inputs.addWidget(label, row, 0)
                self.layout_inputs.addWidget(entry, row, 1)
                # 可用库存显示
                self.available_cs_label = QLabel("可用箱数: 0")
                self.available_cs_label.setStyleSheet("color: gray; font-style: italic;")
                self.layout_inputs.addWidget(self.available_cs_label, row, 2)
            elif field_name == 'Quantity_BTL_Sold':
                entry = QLineEdit()
                entry.setFixedWidth(300)
                entry.setStyleSheet("border: 1px solid lightgray;")
                self.entries[field_name] = entry
                self.layout_inputs.addWidget(label, row, 0)
                self.layout_inputs.addWidget(entry, row, 1)
                # 可用库存显示
                self.available_btl_label = QLabel("可用瓶数: 0")
                self.available_btl_label.setStyleSheet("color: gray; font-style: italic;")
                self.layout_inputs.addWidget(self.available_btl_label, row, 2)
            elif field_name == 'Price_per_bottle':
                entry = QLineEdit()
            else:
                entry = QLineEdit()
            entry.setFixedWidth(300)
            entry.setStyleSheet("border: 1px solid lightgray;")
            self.entries[field_name] = entry
            self.layout_inputs.addWidget(label, row, 0)
            self.layout_inputs.addWidget(entry, row, 1)

        # 显示 BTL_PER_CS
        label_btl_per_cs = QLabel("每箱瓶数:")
        label_btl_per_cs.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.label_btl_per_cs_value = QLabel("0")
        self.layout_inputs.addWidget(label_btl_per_cs, len(fields), 0)
        self.layout_inputs.addWidget(self.label_btl_per_cs_value, len(fields), 1)

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
        table_fields = [
            ('销售订单号', 'Sales_ID'),
            ('产品编号', 'Product_ID'),
            ('客户编号', 'Customer_ID'),
            ('销售箱数', 'Quantity_CS_Sold'),
            ('销售瓶数', 'Quantity_BTL_Sold'),
            ('总销售瓶数', 'Total_Quantity_BTL_Sold'),
            ('单瓶售价(€)', 'Price_per_bottle'),
            ('总金额(€)', 'Total_Amount'),
            ('订单日期', 'Order_Date'),
            ('备注', 'Remarks')
        ]
        self.sales_order_table.setColumnCount(len(table_fields))
        self.sales_order_table.setHorizontalHeaderLabels([label_text for label_text, field_name in table_fields])
        self.sales_order_table.verticalHeader().setVisible(False)
        self.sales_order_table.horizontalHeader().setStretchLastSection(True)
        self.sales_order_table.setWordWrap(True)
        self.sales_order_table.resizeColumnsToContents()

        self.layout_main.addWidget(self.sales_order_table)

        self.setLayout(self.layout_main)

        # 加载销售订单数据
        load_sales_orders_from_db()
        self.update_sales_order_table()

        # 连接数据变化信号到更新方法
        data_manager.inventory_changed.connect(self.on_inventory_changed)

        # 连接 Order_Nb 的选择变化信号到 update_available_stock 方法
        self.entries['Order_Nb'].itemSelectionChanged.connect(self.update_available_stock)
        # 在初始化完成后，手动调用 on_product_id_changed 方法
        self.on_product_id_changed()
    #手动选择订单填充到输入栏
    """
    def on_order_selected(self, selected, deselected):
            try:
                indexes = self.sales_order_table.selectionModel().selectedRows()
                if indexes:
                    index = indexes[0]
                    row = index.row()
                    order = sales_orders[row]
                    for field_name, entry in self.entries.items():
                        value = order.get(field_name, "")
                        if isinstance(entry, QComboBox):
                            combo_index = entry.findText(str(value))
                            if combo_index >= 0:
                                entry.setCurrentIndex(combo_index)
                            else:
                                entry.setCurrentText(str(value))
                        elif isinstance(entry, QListWidget):
                            entry.clearSelection()
                            order_nbs = value if isinstance(value, list) else [value]
                            for i in range(entry.count()):
                                item = entry.item(i)
                                if item.data(Qt.ItemDataRole.UserRole) in order_nbs:
                                    item.setSelected(True)
                        elif isinstance(entry, QLineEdit):
                            entry.setText(str(value))
                        else:
                            pass
                else:
                    for entry in self.entries.values():
                        if isinstance(entry, QComboBox):
                            entry.setCurrentIndex(-1)
                        elif isinstance(entry, QListWidget):
                            entry.clearSelection()
                        elif isinstance(entry, QLineEdit):
                            entry.clear()
                        else:
                            pass
            except Exception as e:
                print(f"处理订单选择时发生错误：{e}")
                QMessageBox.critical(self, "错误", f"处理订单选择时发生错误：{e}")
                """
    def on_inventory_changed(self):
        # 当库存数据发生变化时，更新产品编号列表和相关信息
        self.update_product_ids()
        # 如果有必要，清空或更新其他相关字段

    def update_product_ids(self):
        # 重新获取产品编号列表，并更新下拉框
        current_product_id = self.entries['Product_ID'].currentText()
        product_ids = self.get_all_product_ids()
        self.entries['Product_ID'].clear()
        self.entries['Product_ID'].addItems(product_ids)

        # 如果当前选择的产品编号仍然存在于新的列表中，保持选择，否则选择第一个
        if current_product_id in product_ids:
            index = product_ids.index(current_product_id)
            self.entries['Product_ID'].setCurrentIndex(index)
        else:
            self.entries['Product_ID'].setCurrentIndex(0)

        # 更新单瓶售价和每箱瓶数
        self.on_product_id_changed()

    def update_order_nb_list(self, product_id):
        self.entries['Order_Nb'].clear()
        order_nbs = self.get_order_nbs_by_product_id(product_id)
        for order_nb, arrival_date in order_nbs:
            display_text = f"{order_nb}" # - 到仓日期: {arrival_date}
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, order_nb)
            self.entries['Order_Nb'].addItem(item)

    def update_available_stock(self):
        selected_items = self.entries['Order_Nb'].selectedItems()
        selected_order_nbs = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

        total_available_cs = 0
        total_available_btl = 0
        btl_per_cs_values = []  # 用于存储所有选中的 BTL_PER_CS

        for item in inventory:
            if item['Order_Nb'] in selected_order_nbs:
                current_stock_cs = int(item.get('Current_Stock_CS', 0))
                current_stock_btl = int(item.get('Current_Stock_BTL', 0))
                btl_per_cs = int(item.get('BTL PER CS', 0))

                total_available_cs += current_stock_cs
                total_available_btl += current_stock_btl

                if btl_per_cs not in btl_per_cs_values:
                    btl_per_cs_values.append(btl_per_cs)

        # 更新可用库存显示
        self.available_cs_label.setText(f"可用箱数: {total_available_cs}")
        self.available_btl_label.setText(f"可用瓶数: {total_available_btl}")

        # 更新每箱瓶数显示（以逗号分隔显示所有值）
        if btl_per_cs_values:
            self.label_btl_per_cs_value.setText(", ".join(map(str, sorted(btl_per_cs_values))))
        else:
            self.label_btl_per_cs_value.setText("0")



    def get_order_nbs_by_product_id(self, product_id):
        # 获取库存中该产品的所有订单号，且总瓶数不为零
        order_list = []
        for item in inventory:
            if item['Product_ID'] == product_id:
                # 计算总瓶数
                current_stock_cs = int(item.get('Current_Stock_CS', 0))
                current_stock_btl = int(item.get('Current_Stock_BTL', 0))
                btl_per_cs = int(item.get('BTL PER CS', 0))
                total_btl = current_stock_cs * btl_per_cs + current_stock_btl
                if total_btl > 0:
                    order_nb = item['Order_Nb']
                    arrival_date = item.get('Arrival_Date', '')
                    order_list.append((order_nb, arrival_date))
        # 按照到仓库日期从远到近排序
        order_list.sort(key=lambda x: x[1])
        return order_list

    def get_all_product_ids(self):
        product_ids = set()
        for item in inventory:
            product_ids.add(item['Product_ID'])
        return sorted(list(product_ids))

    def on_product_id_changed(self):
        product_id = self.entries['Product_ID'].currentText()
        # 获取 WHOLESALE BTL 和 BTL_PER_CS
        who_btl_price = get_WHOLESALE_BTL_price(product_id)
        btl_per_cs = get_btl_per_cs(product_id)
        # 更新单瓶售价和每箱瓶数
        self.entries['Price_per_bottle'].setText(str(who_btl_price))
        self.label_btl_per_cs_value.setText(str(btl_per_cs))
        # 更新订单号列表
        self.update_order_nb_list(product_id)
        # 更新可用库存显示
        self.update_available_stock()

    def add_sales_order(self):
        try:
            new_order = {}
            for field_name, entry in self.entries.items():
                if isinstance(entry, QComboBox):
                    value = entry.currentText().strip()
                elif isinstance(entry, QListWidget):
                    # 获取选中的订单号列表
                    selected_items = entry.selectedItems()
                    selected_order_nbs = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
                    if not selected_order_nbs:
                        QMessageBox.warning(self, "添加失败", "请至少选择一个订单号！")
                        return
                    value = ','.join(selected_order_nbs)
                elif isinstance(entry, QLineEdit):
                    value = entry.text().strip()
                else:
                    value = ''
                new_order[field_name] = value

            # 自动添加订单日期
            new_order['Order_Date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_order['Shipped_Date'] = ''

            # 检查必要字段
            if not new_order['Sales_ID']:
                QMessageBox.warning(self, "添加失败", "销售订单号不能为空！")
                return

            # 获取销售数量
            quantity_cs_sold = int(new_order['Quantity_CS_Sold']) if new_order['Quantity_CS_Sold'] else 0
            quantity_btl_sold = int(new_order['Quantity_BTL_Sold']) if new_order['Quantity_BTL_Sold'] else 0
            selected_order_nbs = new_order['Order_Nb'].split(',')

            # 计算所需的总瓶数
            btl_per_cs = get_btl_per_cs(new_order['Product_ID'])
            total_quantity_btl_sold = quantity_cs_sold * btl_per_cs + quantity_btl_sold
            new_order['Total_Quantity_BTL_Sold'] = total_quantity_btl_sold

            # 获取单瓶售价
            price_per_bottle = float(new_order['Price_per_bottle']) if new_order['Price_per_bottle'] else 0.0
            if price_per_bottle == 0.0:
                QMessageBox.warning(self, "添加失败", "单瓶售价不能为 0！")
                return

            # **检查所选订单的库存是否足够**
            total_available_bottles = 0
            for order_nb in selected_order_nbs:
                inventory_item = next((item for item in inventory if item['Order_Nb'] == order_nb), None)
                if inventory_item:
                    current_stock_cs = int(inventory_item.get('Current_Stock_CS', 0))
                    current_stock_btl = int(inventory_item.get('Current_Stock_BTL', 0))
                    btl_per_cs_order = int(inventory_item.get('BTL PER CS', 0))
                    total_available_bottles += current_stock_cs * btl_per_cs_order + current_stock_btl

            if total_available_bottles < total_quantity_btl_sold:
                QMessageBox.warning(self, "库存不足", f"所选订单的库存不足，无法完成销售！\n可用库存：{total_available_bottles} 瓶\n需要库存：{total_quantity_btl_sold} 瓶")
                return

            # 开始扣减库存
            deduction_details = []
            remaining_bottles_to_sell = total_quantity_btl_sold
            total_amount = 0.0

            for order_nb in selected_order_nbs:
                inventory_item = next((item for item in inventory if item['Order_Nb'] == order_nb), None)
                if not inventory_item:
                    continue

                btl_per_cs_order = int(inventory_item['BTL PER CS'])
                current_stock_cs = int(inventory_item['Current_Stock_CS'])
                current_stock_btl = int(inventory_item['Current_Stock_BTL'])

                total_bottles_in_stock = current_stock_cs * btl_per_cs_order + current_stock_btl

                if remaining_bottles_to_sell <= total_bottles_in_stock:
                    deduct_btl = remaining_bottles_to_sell
                    deduct_cs = deduct_btl // btl_per_cs_order
                    deduct_btl = deduct_btl % btl_per_cs_order

                    # 扣减库存
                    update_inventory(
                        new_order['Product_ID'],
                        order_nb,
                        -deduct_cs,
                        -deduct_btl,
                        inventory_item.get('Arrival_Date'),
                        inventory_item.get('Creation_Date'),
                        inventory_item.get('Product_Name'),
                        inventory_item.get('SKU_CLS'),
                        btl_per_cs_order,
                        operation_type='sales'
                    )

                    deduction_details.append({
                        'Order_Nb': order_nb,
                        'Deduct_CS': deduct_cs,
                        'Deduct_BTL': deduct_btl,
                    })

                    total_amount += (deduct_cs * btl_per_cs_order + deduct_btl) * price_per_bottle
                    remaining_bottles_to_sell = 0
                    break
                else:
                    # 当前订单库存不足，扣减所有库存
                    deduct_cs = current_stock_cs
                    deduct_btl = current_stock_btl

                    update_inventory(
                        new_order['Product_ID'],
                        order_nb,
                        -deduct_cs,
                        -deduct_btl,
                        inventory_item.get('Arrival_Date'),
                        inventory_item.get('Creation_Date'),
                        inventory_item.get('Product_Name'),
                        inventory_item.get('SKU_CLS'),
                        btl_per_cs_order,
                        operation_type='sales'
                    )

                    deduction_details.append({
                        'Order_Nb': order_nb,
                        'Deduct_CS': deduct_cs,
                        'Deduct_BTL': deduct_btl,
                    })

                    total_amount += (deduct_cs * btl_per_cs_order + deduct_btl) * price_per_bottle
                    remaining_bottles_to_sell -= total_bottles_in_stock

            new_order['Deduction_Details'] = deduction_details
            new_order['Total_Amount'] = total_amount

            # 保存销售订单
            sales_orders.append(new_order)
            save_sales_order_to_db(new_order)
            self.update_sales_order_table()

            QMessageBox.information(self, "成功", f"销售订单 {new_order['Sales_ID']} 已添加，总金额：{total_amount:.2f} €")

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
                # 获取销售订单对象
                order = next((o for o in sales_orders if o['Sales_ID'] == sales_id), None)
                if order:
                    # 恢复库存
                    restore_inventory(order)

                    # 从列表和数据库中删除
                    sales_orders.remove(order)
                    delete_sales_order_from_db(sales_id)

            self.update_sales_order_table()

            QMessageBox.information(self, "成功", "选中的销售订单已删除。")

        except Exception as e:
            print(f"删除销售订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"删除销售订单时发生错误：{e}")

    def update_sales_order_table(self):
        table_fields = [
            ('销售订单号', 'Sales_ID'),
            ('产品编号', 'Product_ID'),
            ('客户编号', 'Customer_ID'),
            ('销售箱数', 'Quantity_CS_Sold'),
            ('销售瓶数', 'Quantity_BTL_Sold'),
            ('总销售瓶数', 'Total_Quantity_BTL_Sold'),
            ('单瓶售价(€)', 'Price_per_bottle'),
            ('总金额(€)', 'Total_Amount'),
            ('订单日期', 'Order_Date'),
            ('备注', 'Remarks')
        ]
        self.sales_order_table.setRowCount(0)
        self.sales_order_table.setRowCount(len(sales_orders))
        for row, order in enumerate(sales_orders):
            for col, (label_text, field_name) in enumerate(table_fields):
                value = order.get(field_name, "")
                item = QTableWidgetItem(str(value))
                self.sales_order_table.setItem(row, col, item)
