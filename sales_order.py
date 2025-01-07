# sales_order.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QGridLayout, QComboBox, QListWidget, QAbstractItemView, QListWidgetItem
)
from PyQt6.QtCore import Qt
import datetime
from data import (
    sales_orders, save_sales_order_to_db, delete_sales_order_from_db,
    load_sales_orders_from_db, get_btl_per_cs, restore_inventory, data_manager, inventory, update_inventory, get_inventory_info, purchase_orders
)
from data import get_purchase_order_by_product_id
import re

class SalesOrderWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("销售订单管理")
        self.setGeometry(200, 200, 1000, 600)

        self.layout_main = QVBoxLayout()

        self.layout_inputs = QGridLayout()
        self.entries = {}

        fields = [
            ('销售订单号', 'Sales_ID'),
            ('产品编号', 'Product_ID'),
            ('订单号','Order_Nb'),
            ('客户编号', 'Customer_ID'),
            ('销售箱数', 'Quantity_CS_Sold'),
            ('单瓶售价(€)', 'Price_per_bottle'),
        ]

        for row, (label_text, field_name) in enumerate(fields):
            label = QLabel(label_text + ":")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if field_name == 'Product_ID':
                entry = QComboBox()
                product_ids = self.get_all_product_ids()
                product_ids.insert(0, '')
                entry.addItems(product_ids)
                entry.currentIndexChanged.connect(self.on_product_id_changed)
            elif field_name == 'Order_Nb':
                entry = QListWidget()
                entry.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
                entry.setFixedHeight(100)
                entry.itemSelectionChanged.connect(self.update_available_stock)
            else:
                entry = QLineEdit()
            entry.setFixedWidth(300)
            entry.setStyleSheet("border: 1px solid lightgray;")
            self.entries[field_name] = entry
            self.layout_inputs.addWidget(label, row, 0)
            self.layout_inputs.addWidget(entry, row, 1)
            if field_name == 'Quantity_CS_Sold':
                self.available_cs_label = QLabel("可用箱数: 0")
                self.available_cs_label.setStyleSheet("color: gray; font-style: italic;")
                self.layout_inputs.addWidget(self.available_cs_label, row, 2)

        label_btl_per_cs = QLabel("每箱瓶数:")
        label_btl_per_cs.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.label_btl_per_cs_value = QLabel("0")
        self.layout_inputs.addWidget(label_btl_per_cs, len(fields), 0)
        self.layout_inputs.addWidget(self.label_btl_per_cs_value, len(fields), 1)

        self.layout_main.addLayout(self.layout_inputs)

        layout_buttons = QHBoxLayout()

        self.button_add = QPushButton("添加销售订单")
        self.button_add.clicked.connect(self.add_sales_order)
        self.button_update = QPushButton("更新销售订单")
        self.button_update.clicked.connect(self.update_sales_order)
        self.button_delete = QPushButton("删除销售订单")
        self.button_delete.clicked.connect(self.delete_sales_order)

        layout_buttons.addWidget(self.button_add)
        layout_buttons.addWidget(self.button_update)
        layout_buttons.addWidget(self.button_delete)
        self.layout_main.addLayout(layout_buttons)

        # 增加排序和过滤区域
        filter_sort_layout = QHBoxLayout()

        sort_label = QLabel("排序规则:")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["按订单日期", "按客户编号", "按销售订单号", "按采购订单号", "按产品编号", "按产品名称", "按总金额"])
        self.sort_combo.currentIndexChanged.connect(self.update_sales_order_table)
        filter_sort_layout.addWidget(sort_label)
        filter_sort_layout.addWidget(self.sort_combo)

        filter_field_label = QLabel("过滤条件:")
        self.filter_field_combo = QComboBox()
        self.filter_field_combo.addItems(["按订单日期", "按客户编号", "按采购订单号", "按产品编号", "按产品名称"])
        filter_sort_layout.addWidget(filter_field_label)
        filter_sort_layout.addWidget(self.filter_field_combo)

        self.filter_field_input = QLineEdit()
        self.filter_field_input.setPlaceholderText("输入过滤内容(支持*通配符)")
        self.filter_field_input.textChanged.connect(self.update_sales_order_table)
        filter_sort_layout.addWidget(self.filter_field_input)

        self.layout_main.addLayout(filter_sort_layout)

        self.table_fields = [
            ('客户编号', 'Customer_ID'),
            ('销售订单号', 'Sales_ID'),
            ('采购订单号', 'Order_Nb'),
            ('产品编号', 'Product_ID'),
            ('产品名称', 'Product_Name'),
            ('销售箱数', 'Quantity_CS_Sold'),
            ('BTL PER CS', 'BTL_PER_CS'),
            ('总销售瓶数', 'Total_Quantity_BTL_Sold'),
            ('单瓶售价(€)', 'Price_per_bottle'),
            ('总金额(€)', 'Total_Amount'),
            ('订单日期', 'Order_Date'),
            ('备注', 'Remarks')
        ]
        self.sales_order_table = QTableWidget()
        self.sales_order_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sales_order_table.setColumnCount(len(self.table_fields))
        self.sales_order_table.setHorizontalHeaderLabels([label_text for label_text, field_name in self.table_fields])
        self.sales_order_table.verticalHeader().setVisible(False)
        self.sales_order_table.horizontalHeader().setStretchLastSection(True)
        self.sales_order_table.setWordWrap(True)
        self.sales_order_table.resizeColumnsToContents()
        self.sales_order_table.itemChanged.connect(self.on_item_changed)

        self.sales_order_table.selectionModel().selectionChanged.connect(self.on_order_selected)
        self.layout_main.addWidget(self.sales_order_table)
        self.setLayout(self.layout_main)

        load_sales_orders_from_db()
        self.update_sales_order_table()
        data_manager.inventory_changed.connect(self.on_inventory_changed)

        # 初始化
        self.on_product_id_changed()

    def on_item_changed(self, item):
        column = item.column()
        remarks_col = self.field_index('Remarks')
        if column == remarks_col:
            new_remarks = item.text()
            sales_id_item = self.sales_order_table.item(item.row(), self.field_index('Sales_ID'))
            if sales_id_item:
                sales_id = sales_id_item.text()
                order = next((o for o in sales_orders if o['Sales_ID'] == sales_id), None)
                if order:
                    order['Remarks'] = new_remarks
                    save_sales_order_to_db(order)

    def field_index(self, field_name):
        for index, (label, field) in enumerate(self.table_fields):
            if field == field_name:
                return index
        return None

    def on_inventory_changed(self):
        self.update_product_ids()

    def update_product_ids(self):
        current_product_id = self.entries['Product_ID'].currentText()
        product_ids = self.get_all_product_ids()
        self.entries['Product_ID'].clear()
        for pid in product_ids:
            self.entries['Product_ID'].addItem(pid)

        if current_product_id in product_ids:
            idx = product_ids.index(current_product_id)
            self.entries['Product_ID'].setCurrentIndex(idx)
        else:
            self.entries['Product_ID'].setCurrentIndex(0)
        self.on_product_id_changed()

    def update_order_nb_list(self, product_id):
        self.entries['Order_Nb'].clear()
        order_nbs = self.get_order_nbs_by_product_id(product_id)
        for order_nb, arrival_date in order_nbs:
            display_text = f"{order_nb}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, order_nb)
            self.entries['Order_Nb'].addItem(item)

    def update_available_stock(self):
        selected_items = self.entries['Order_Nb'].selectedItems()
        selected_order_nbs = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

        total_available_cs = 0
        btl_per_cs_values = []

        for item in inventory:
            if item['Order_Nb'] in selected_order_nbs:
                current_stock_cs = int(item.get('Current_Stock_CS', 0))
                total_available_cs += current_stock_cs
                btl_val = int(item.get('BTL PER CS', 0))
                if btl_val not in btl_per_cs_values:
                    btl_per_cs_values.append(btl_val)

        self.available_cs_label.setText(f"可用箱数: {total_available_cs}")
        if btl_per_cs_values:
            self.label_btl_per_cs_value.setText(", ".join(map(str, sorted(btl_per_cs_values))))
        else:
            self.label_btl_per_cs_value.setText("0")

    def get_order_nbs_by_product_id(self, product_id):
        order_list = []
        for item_ in inventory:
            if item_['Product_ID'] == product_id:
                current_stock_cs = int(item_.get('Current_Stock_CS',0))
                if current_stock_cs > 0:
                    order_nb = item_['Order_Nb']
                    arrival_date = item_.get('Arrival_Date','')
                    order_list.append((order_nb, arrival_date))
        order_list.sort(key=lambda x: x[1])
        return order_list

    def get_all_product_ids(self):
        product_ids = set()
        for item_ in inventory:
            product_ids.add(item_['Product_ID'])
        return sorted(list(product_ids))

    def on_product_id_changed(self):
        product_id = self.entries['Product_ID'].currentText()
        btl_per_cs = get_btl_per_cs(product_id)
        self.label_btl_per_cs_value.setText(str(btl_per_cs))
        self.update_order_nb_list(product_id)
        self.update_available_stock()

    def on_order_selected(self, selected, deselected):
        indexes = self.sales_order_table.selectionModel().selectedRows()
        if indexes:
            index = indexes[0]
            row = index.row()
            fs_orders = self.get_filtered_and_sorted_sales_orders()
            order = fs_orders[row]
            for field_name, entry in self.entries.items():
                if field_name == 'Order_Nb':
                    order_nbs = order.get('Order_Nb','').split(',')
                    entry.clearSelection()
                    for i in range(entry.count()):
                        item = entry.item(i)
                        if item.data(Qt.ItemDataRole.UserRole) in order_nbs:
                            item.setSelected(True)
                elif field_name == 'Product_ID':
                    idx = entry.findText(order.get('Product_ID',''))
                    if idx >=0:
                        entry.setCurrentIndex(idx)
                else:
                    value = order.get(field_name, '')
                    entry.setText(str(value))
            self.update_available_stock()

    def add_sales_order(self):
        # 原有代码不变
        # ...
        try:
            new_order = {}
            for field_name, entry in self.entries.items():
                if isinstance(entry, QComboBox):
                    value = entry.currentText().strip()
                elif isinstance(entry, QListWidget):
                    selected_items = entry.selectedItems()
                    selected_order_nbs = [it.data(Qt.ItemDataRole.UserRole) for it in selected_items]
                    if not selected_order_nbs:
                        QMessageBox.warning(self, "添加失败", "请至少选择一个订单号！")
                        return
                    value = ','.join(selected_order_nbs)
                else:
                    value = entry.text().strip()
                new_order[field_name] = value

            new_order['Order_Date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_order['Shipped_Date'] = ''

            quantity_cs_sold = int(new_order['Quantity_CS_Sold']) if new_order['Quantity_CS_Sold'] else 0
            selected_order_nbs = new_order['Order_Nb'].split(',')
            product_id = new_order.get('Product_ID')
            if selected_order_nbs:
                product_name, btl_per_cs = get_inventory_info(product_id, selected_order_nbs[0])
            else:
                product_name, btl_per_cs = '', 0
            new_order['Product_Name'] = product_name
            new_order['BTL_PER_CS'] = btl_per_cs

            price_per_bottle = float(new_order['Price_per_bottle']) if new_order['Price_per_bottle'] else 0.0
            if price_per_bottle == 0.0:
                QMessageBox.warning(self, "添加失败", "单瓶售价不能为0！")
                return

            total_available_cs = 0
            for order_nb in selected_order_nbs:
                inventory_item = next((item for item in inventory if item['Order_Nb'] == order_nb), None)
                if inventory_item:
                    current_stock_cs = int(inventory_item.get('Current_Stock_CS', 0))
                    total_available_cs += current_stock_cs

            if total_available_cs < quantity_cs_sold:
                QMessageBox.warning(self, "库存不足", f"库存不足！可用: {total_available_cs}箱，需要: {quantity_cs_sold}箱")
                return

            deduction_details = []
            remaining_cs_to_sell = quantity_cs_sold
            total_amount = 0.0
            total_btl = 0

            for order_nb in selected_order_nbs:
                inventory_item = next((item for item in inventory if item['Order_Nb'] == order_nb), None)
                if not inventory_item:
                    continue
                btl_per_cs_order = int(inventory_item['BTL PER CS'])
                current_stock_cs = int(inventory_item['Current_Stock_CS'])

                if remaining_cs_to_sell <= current_stock_cs:
                    deduct_cs = remaining_cs_to_sell
                    update_inventory(
                        new_order['Product_ID'],
                        order_nb,
                        -deduct_cs,
                        inventory_item.get('Arrival_Date'),
                        inventory_item.get('Creation_Date'),
                        inventory_item.get('Product_Name'),
                        inventory_item.get('SKU_CLS'),
                        btl_per_cs_order,
                        operation_type='sales',
                        sale_date=new_order['Order_Date'],
                        sales_orders=new_order['Sales_ID']
                    )
                    deduction_details.append({'Order_Nb':order_nb,'Deduct_CS':deduct_cs})
                    total_amount += deduct_cs * btl_per_cs_order * price_per_bottle
                    total_btl += deduct_cs * btl_per_cs_order
                    remaining_cs_to_sell = 0
                    break
                else:
                    deduct_cs = current_stock_cs
                    update_inventory(
                        new_order['Product_ID'],
                        order_nb,
                        -deduct_cs,
                        inventory_item.get('Arrival_Date'),
                        inventory_item.get('Creation_Date'),
                        inventory_item.get('Product_Name'),
                        inventory_item.get('SKU_CLS'),
                        btl_per_cs_order,
                        operation_type='sales',
                        sale_date=new_order['Order_Date'],
                        sales_orders=new_order['Sales_ID']
                    )
                    deduction_details.append({'Order_Nb':order_nb,'Deduct_CS':deduct_cs})
                    total_amount += deduct_cs * btl_per_cs_order * price_per_bottle
                    total_btl += deduct_cs * btl_per_cs_order
                    remaining_cs_to_sell -= deduct_cs

            new_order['Deduction_Details'] = deduction_details
            new_order['Total_Amount'] = total_amount
            new_order['Total_Quantity_BTL_Sold'] = total_btl

            sales_orders.append(new_order)
            save_sales_order_to_db(new_order)
            self.update_sales_order_table()
            QMessageBox.information(self, "成功", f"销售订单 {new_order['Sales_ID']} 已添加，总金额：{total_amount:.2f} €")

        except Exception as e:
            print(f"添加销售订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"添加销售订单时发生错误：{e}")

    def update_sales_order(self):
        # 您可根据需要实现更新逻辑
        print("功能开发中")

    def delete_sales_order(self):
        try:
            selected_rows = self.sales_order_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "删除错误", "请先选择要删除的销售订单！")
                return

            for index in selected_rows:
                row = index.row()
                fs_orders = self.get_filtered_and_sorted_sales_orders()
                order = fs_orders[row]
                sales_id = order['Sales_ID']
                if order:
                    restore_inventory(order)
                    sales_orders.remove(order)
                    delete_sales_order_from_db(sales_id)

            self.update_sales_order_table()
            QMessageBox.information(self, "成功", "选中的销售订单已删除。")

        except Exception as e:
            print(f"删除销售订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"删除销售订单时发生错误：{e}")

    def get_filtered_and_sorted_sales_orders(self):
        filtered = sales_orders.copy()
        filter_field = self.filter_field_combo.currentText()
        filter_value = self.filter_field_input.text().strip()

        if filter_value:
            pattern = None
            if '*' in filter_value:
                pattern = re.escape(filter_value).replace(r'\*', '.*')
                regex = re.compile(pattern, re.IGNORECASE)
            def match_field(val):
                if pattern:
                    return bool(regex.search(str(val)))
                else:
                    return filter_value.lower() in str(val).lower()

            if filter_field == "按订单日期":
                filtered = [o for o in filtered if match_field(o.get('Order_Date',''))]
            elif filter_field == "按客户编号":
                filtered = [o for o in filtered if match_field(o.get('Customer_ID',''))]
            elif filter_field == "按采购订单号":
                filtered = [o for o in filtered if match_field(o.get('Order_Nb',''))]
            elif filter_field == "按产品编号":
                filtered = [o for o in filtered if match_field(o.get('Product_ID',''))]
            elif filter_field == "按产品名称":
                filtered = [o for o in filtered if match_field(o.get('Product_Name',''))]

        sort_option = self.sort_combo.currentText()
        def sort_key(o):
            if sort_option == "按订单日期":
                return o.get('Order_Date','')
            elif sort_option == "按客户编号":
                return o.get('Customer_ID','')
            elif sort_option == "按销售订单号":
                return o.get('Sales_ID','')
            elif sort_option == "按采购订单号":
                return o.get('Order_Nb','')
            elif sort_option == "按产品编号":
                return o.get('Product_ID','')
            elif sort_option == "按产品名称":
                return o.get('Product_Name','')
            elif sort_option == "按总金额":
                try:
                    return float(o.get('Total_Amount',0))
                except:
                    return 0
            return ''

        filtered = sorted(filtered, key=sort_key)
        return filtered

    def update_sales_order_table(self):
        self.sales_order_table.blockSignals(True)

        filtered_sorted_orders = self.get_filtered_and_sorted_sales_orders()
        self.sales_order_table.setRowCount(0)
        self.sales_order_table.setRowCount(len(filtered_sorted_orders))
        for row, order in enumerate(filtered_sorted_orders):
            for col, (label_text, field_name) in enumerate(self.table_fields):
                value = order.get(field_name, "")
                item = QTableWidgetItem(str(value))
                if field_name == 'Remarks':
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.sales_order_table.setItem(row, col, item)

        self.sales_order_table.blockSignals(False)
