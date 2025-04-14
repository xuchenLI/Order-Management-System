# sales_order.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QGridLayout, QComboBox, QListWidget, QAbstractItemView, QListWidgetItem, QApplication
)
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QInputDialog
import datetime
from data import (
    sales_orders, save_sales_order_to_db, delete_sales_order_from_db,
    load_sales_orders_from_db, get_btl_per_cs, restore_inventory, data_manager, inventory, update_inventory, get_inventory_info, purchase_orders, get_purchase_order_by_nb, get_po_guid_for_inventory
)
from data import get_purchase_order_by_product_id
import re
from data import get_inventory_item
from data import load_sales_orders_from_db, data_manager
import uuid

class SalesOrderWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("销售订单管理")
        self.setGeometry(200, 200, 1000, 600)
        self.last_deleted_order = None  # 用于保存上次删除的订单
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
                entry.setEditable(True)  # 设置为可编辑
                # 获取完整的产品编号列表，并保存为成员变量
                self.full_product_ids = self.get_all_product_ids()
                # 添加空项以及全部产品编号
                entry.addItem('')
                entry.addItems(self.full_product_ids)
                # 连接下拉框文本变化信号，进行模糊搜索过滤
                entry.lineEdit().textChanged.connect(self.filter_product_ids)
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
        self.button_undo_delete = QPushButton("撤销删除")
        self.button_undo_delete.clicked.connect(self.undo_last_deletion)

        layout_buttons.addWidget(self.button_add)
        layout_buttons.addWidget(self.button_update)
        layout_buttons.addWidget(self.button_delete)
        layout_buttons.addWidget(self.button_undo_delete)
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
            ('SKU CLS', 'SKU_CLS'),
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
        # 设置表格为单元格选择并允许拖动选择多个单元格
        self.sales_order_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.sales_order_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.sales_order_table.setColumnCount(len(self.table_fields))
        self.sales_order_table.setHorizontalHeaderLabels([label_text for label_text, field_name in self.table_fields])
        self.sales_order_table.verticalHeader().setVisible(False)
        self.sales_order_table.horizontalHeader().setStretchLastSection(True)
        self.sales_order_table.setWordWrap(True)
        self.sales_order_table.resizeColumnsToContents()
        self.sales_order_table.itemChanged.connect(self.on_item_changed)
        self.sales_order_table.selectionModel().selectionChanged.connect(self.on_order_selected)
        self.layout_main.addWidget(self.sales_order_table)

        # 添加复制快捷键：在表格初始化完成之后
        self.copy_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Copy), self.sales_order_table)
        self.copy_shortcut.activated.connect(self.copySelectedCells)
        self.clear_selection_shortcut = QShortcut(QKeySequence("Escape"), self.sales_order_table)
        self.clear_selection_shortcut.activated.connect(lambda: self.sales_order_table.clearSelection())


        self.setLayout(self.layout_main)

        # 加载订单数据并更新表格
        load_sales_orders_from_db()
        self.update_sales_order_table()
        data_manager.inventory_changed.connect(self.on_inventory_changed)

        # 初始化产品编号相关操作
        self.on_product_id_changed()

    # 实现复制选中单元格内容到剪贴板的函数
    def copySelectedCells(self):
        selected_ranges = self.sales_order_table.selectedRanges()
        if not selected_ranges:
            return
        copied_text = ""
        for selection in selected_ranges:
            for row in range(selection.topRow(), selection.bottomRow() + 1):
                row_data = []
                for col in range(selection.leftColumn(), selection.rightColumn() + 1):
                    item = self.sales_order_table.item(row, col)
                    row_data.append(item.text() if item else "")
                copied_text += "\t".join(row_data) + "\n"
        clipboard = QApplication.clipboard()
        clipboard.setText(copied_text)


    def filter_product_ids(self, text):
        """
        根据用户输入的 text 对产品编号进行模糊匹配，并更新下拉列表显示的内容，
        支持使用 '*' 作为通配符进行匹配。匹配方式为只要产品编号中含有符合模式的子串即可匹配。
        """
        product_combo: QComboBox = self.entries['Product_ID']
        # 阻塞 QLineEdit 信号，避免递归触发
        product_combo.lineEdit().blockSignals(True)
        
        current_text = text
        product_combo.clear()
        product_combo.addItem('')  # 保留空选项

        if '*' in current_text:
            # 将输入文本转换为正则表达式模式
            # 使用 re.escape 对普通字符进行转义，然后将转义后的 '*' 替换为 '.*'
            # 不加锚点，这样只匹配产品编号中任意位置的匹配项
            pattern = re.escape(current_text).replace(r'\*', '.*')
            regex = re.compile(pattern, re.IGNORECASE)
            filtered_ids = [pid for pid in self.full_product_ids if regex.search(pid)]
        else:
            # 普通的包含匹配（忽略大小写）
            filtered_ids = [pid for pid in self.full_product_ids if current_text.lower() in pid.lower()]

        product_combo.addItems(filtered_ids)
        
        # 恢复用户输入的文本和光标位置
        product_combo.lineEdit().setText(current_text)
        product_combo.lineEdit().setCursorPosition(len(current_text))
        
        # 恢复 QLineEdit 信号
        product_combo.lineEdit().blockSignals(False)
        
        # 更新产品编号变更后的相关逻辑
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
        product_dict = {}
        for item in inventory:
            pid = item['Product_ID']
            key = pid.lower()  # 归一化为小写作为键
            if key not in product_dict:
                product_dict[key] = pid  # 保留原始形式（或你想显示的格式）
        # 返回时按照小写排序
        return sorted(list(product_dict.values()), key=lambda x: x.lower())

    def on_product_id_changed(self):
        product_id = self.entries['Product_ID'].currentText()
        btl_per_cs = get_btl_per_cs(product_id)
        self.label_btl_per_cs_value.setText(str(btl_per_cs))
        self.update_order_nb_list(product_id)
        self.update_available_stock()

    def on_order_selected(self, selected, deselected):
        indexes = self.sales_order_table.selectionModel().selectedIndexes()
        if indexes:
            # 取第一个选中单元格所在的行
            row = indexes[0].row()
            fs_orders = self.get_filtered_and_sorted_sales_orders()
            order = fs_orders[row]
            for field_name, entry in self.entries.items():
                if field_name == 'Order_Nb':
                    order_nbs = order.get('Order_Nb', '').split(',')
                    entry.clearSelection()
                    for i in range(entry.count()):
                        item = entry.item(i)
                        if item.data(Qt.ItemDataRole.UserRole) in order_nbs:
                            item.setSelected(True)
                elif field_name == 'Product_ID':
                    idx = entry.findText(order.get('Product_ID', ''))
                    if idx >= 0:
                        entry.setCurrentIndex(idx)
                else:
                    value = order.get(field_name, '')
                    entry.setText(str(value))
            self.update_available_stock()


    def add_sales_order(self):

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

            # 检查销售订单号是否重复
            sales_id = new_order.get('Sales_ID', '')
            if any(o['Sales_ID'] == sales_id for o in sales_orders):
                QMessageBox.warning(self, "添加失败", f"销售订单号 {sales_id} 已存在！")
                return

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
                po_guid = get_po_guid_for_inventory(product_id, order_nb)
                if remaining_cs_to_sell <= current_stock_cs:
                    deduct_cs = remaining_cs_to_sell
                    update_inventory(
                        po_guid,
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
                    deduction_details.append({'Order_Nb': order_nb, 'Deduct_CS': deduct_cs})
                    total_amount += deduct_cs * btl_per_cs_order * price_per_bottle
                    total_btl += deduct_cs * btl_per_cs_order
                    remaining_cs_to_sell = 0
                    break
                else:
                    deduct_cs = current_stock_cs
                    update_inventory(
                        po_guid,
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
                    deduction_details.append({'Order_Nb': order_nb, 'Deduct_CS': deduct_cs})
                    total_amount += deduct_cs * btl_per_cs_order * price_per_bottle
                    total_btl += deduct_cs * btl_per_cs_order
                    remaining_cs_to_sell -= deduct_cs

            new_order['Deduction_Details'] = deduction_details
            new_order['Total_Amount'] = total_amount
            new_order['Total_Quantity_BTL_Sold'] = total_btl
            # ======= 新增 GUID 生成逻辑 =======
            # 为销售订单生成自己的唯一标识 SO_GUID
            new_order['SO_GUID'] = str(uuid.uuid4())
            # 根据销售订单中的多个 Order_Nb 查找对应的采购订单记录，
            # 并把所有采购订单的 PO_GUID 合并成逗号分隔的字符串
            po_guid_list = []
            for order_nb in selected_order_nbs:
                associated_po = get_purchase_order_by_nb(order_nb)
                if associated_po:
                    po_guid = associated_po.get('PO_GUID', '')
                    if po_guid:
                        po_guid_list.append(po_guid)
            # 将多个 PO_GUID 用逗号分隔保存
            new_order['PO_GUID'] = ','.join(po_guid_list)
            # =====================================
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
        """
        通过输入销售订单号删除订单，一次只能输入一个。
        删除时调用 restore_inventory 将扣减的库存恢复，
        并将删除的订单保存到 self.last_deleted_order 中，便于撤销删除。
        """
        order_id, ok = QInputDialog.getText(self, "删除销售订单", "请输入要删除的销售订单号：")
        if not ok or not order_id.strip():
            return

        order_id = order_id.strip()
        # 如果输入中包含逗号或者空格，认为用户输入了多个订单号
        if ',' in order_id or ' ' in order_id:
            QMessageBox.warning(self, "删除错误", "一次只能输入一个销售订单号！")
            return

        # 在销售订单列表中查找对应订单
        order = next((o for o in sales_orders if o['Sales_ID'] == order_id), None)
        if not order:
            QMessageBox.warning(self, "删除错误", f"找不到销售订单号：{order_id}")
            return

        try:
            # 先恢复库存，即将订单中扣减的库存返还
            restore_inventory(order)
            # 删除订单：从内存和数据库中移除
            sales_orders.remove(order)
            delete_sales_order_from_db(order_id)
            # 保存删除的订单信息，便于撤销删除
            self.last_deleted_order = order.copy()
            self.update_sales_order_table()
            QMessageBox.information(self, "成功", f"销售订单 {order_id} 已删除。")
        except Exception as e:
            print(f"删除销售订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"删除销售订单时发生错误：{e}")

    def reapply_inventory_deduction(self, order):
        """
        根据订单中的扣减详情，重新扣减库存，
        实现撤销删除后恢复销售订单时的库存扣减操作。
        """
        product_id = order.get('Product_ID')
        order_date = order.get('Order_Date')
        sales_id = order.get('Sales_ID')
        deduction_details = order.get('Deduction_Details', [])
        if not deduction_details:
            # 如果订单中没有扣减详情，不做处理
            return

        for deduction in deduction_details:
            order_nb = deduction.get('Order_Nb')
            deduct_cs = deduction.get('Deduct_CS', 0)
            # 查找对应的库存记录
            inventory_item = get_inventory_item(product_id, order_nb)
            if not inventory_item:
                # 如果找不到库存记录，则提示或跳过
                print(f"找不到库存记录，产品ID: {product_id}, 订单号: {order_nb}")
                continue
            btl_per_cs = int(inventory_item.get('BTL PER CS', 0))
            arrival_date = inventory_item.get('Arrival_Date')
            creation_date = inventory_item.get('Creation_Date')
            product_name = inventory_item.get('Product_Name')
            sku_cls = inventory_item.get('SKU_CLS')
            po_guid = get_po_guid_for_inventory(product_id, order_nb)
            # 重新扣减库存，即库存变化量为负的扣减数量
            update_inventory(
                po_guid,
                product_id,
                order_nb,
                -deduct_cs,  # 负数表示扣减库存
                arrival_date,
                creation_date,
                product_name,
                sku_cls,
                btl_per_cs,
                operation_type='sales',
                sale_date=order_date,
                sales_orders=sales_id
            )

    def undo_last_deletion(self):
        """
        撤销上一次删除的销售订单：
        1. 将订单恢复到内存和数据库中。
        2. 根据订单的扣减详情重新扣减库存（撤销恢复库存）。
        """
        if not self.last_deleted_order:
            QMessageBox.warning(self, "撤销错误", "没有可撤销的删除操作。")
            return
        try:
            order = self.last_deleted_order
            # 将订单恢复到内存中，并保存到数据库
            sales_orders.append(order)
            save_sales_order_to_db(order)
            # 重新扣减库存：撤销删除时，需要重新扣减与该订单对应的库存
            self.reapply_inventory_deduction(order)
            self.last_deleted_order = None  # 清除上次删除记录
            self.update_sales_order_table()
            QMessageBox.information(self, "成功", f"销售订单 {order['Sales_ID']} 已恢复，库存已更新。")
        except Exception as e:
            print(f"恢复销售订单时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"恢复销售订单时发生错误：{e}")

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
                return o.get('Order_Date','') or ''
            elif sort_option == "按客户编号":
                return o.get('Customer_ID','') or ''
            elif sort_option == "按销售订单号":
                return o.get('Sales_ID','') or ''
            elif sort_option == "按采购订单号":
                return o.get('Order_Nb','') or ''
            elif sort_option == "按产品编号":
                return o.get('Product_ID','') or ''
            elif sort_option == "按产品名称":
                return o.get('Product_Name','') or ''
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
                if field_name == 'SKU_CLS':
                    # 根据订单中的产品编号，从对应的采购订单中提取 SKU CLS
                    purchase_order = get_purchase_order_by_product_id(order.get("Product_ID", ""))
                    value = purchase_order.get("SKU CLS", "") if purchase_order else ""
                else:
                    value = order.get(field_name, "")
                item = QTableWidgetItem(str(value))
                if field_name == 'Remarks':
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.sales_order_table.setItem(row, col, item)


        self.sales_order_table.blockSignals(False)
