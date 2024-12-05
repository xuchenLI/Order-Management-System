# inventory_management.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel,
    QLineEdit, QHBoxLayout, QPushButton, QGridLayout, QMessageBox, QComboBox,
    QHeaderView, QFormLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from data import inventory, load_inventory_from_db, data_manager, save_inventory_to_db
import datetime
import re
from dateutil.parser import parse

class InventoryManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("库存管理")
        self.setGeometry(300, 300, 1000, 600)

        self.layout_main = QVBoxLayout()

        # 输入区域
        self.layout_inputs = QFormLayout()
        self.entries = {}

        # 调整间距
        self.layout_inputs.setSpacing(5)
        self.layout_inputs.setContentsMargins(0, 0, 0, 0)

        # 修改后的“到货日期”输入项
        label_arrival_date = QLabel("到货日期:")
        self.entry_arrival_date = QLineEdit()
        self.entry_arrival_date.setPlaceholderText("YYYY-MM-DD")
        self.entries['Arrival_Date'] = self.entry_arrival_date
        self.layout_inputs.addRow(label_arrival_date, self.entry_arrival_date)
        self.entry_arrival_date.setFixedWidth(120)

        # 新增的“提货日期”输入项
        label_pickup_date = QLabel("提货日期:")
        self.entry_pickup_date = QLineEdit()
        self.entry_pickup_date.setPlaceholderText("YYYY-MM-DD")
        self.entries['Pick_up_Date'] = self.entry_pickup_date
        self.layout_inputs.addRow(label_pickup_date, self.entry_pickup_date)
        self.entry_pickup_date.setFixedWidth(120)

        # 更新按钮
        self.button_update = QPushButton("更新")
        self.button_update.clicked.connect(self.update_inventory_record)
        # 将“更新”按钮添加到新的行
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.button_update)
        button_layout.addStretch(1)
        self.layout_inputs.addRow(button_layout)

        self.layout_main.addLayout(self.layout_inputs)

        # 明细标题和过滤选项
        detail_layout = QHBoxLayout()

        # 添加排序和过滤控件的布局
        control_layout = QHBoxLayout()

        # 添加排序选项
        sort_label = QLabel("排序规则:")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["按更新时间", "按采购订单号", "按销售订单", "按产品编号", "按库存-箱数"])
        self.sort_combo.currentIndexChanged.connect(self.update_inventory_tables)
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(self.sort_combo)
        sort_layout.setSpacing(5)
        sort_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.addLayout(sort_layout)

        # 添加过滤选项
        filter_field_label = QLabel("过滤条件:")
        self.filter_field_combo = QComboBox()
        self.filter_field_combo.addItems(["按产品编号", "按采购订单", "按Order Type", "按SKU CLS", "按产品名称"])
        self.filter_field_combo.currentIndexChanged.connect(self.update_inventory_tables)
        self.filter_field_input = QLineEdit()
        self.filter_field_input.setPlaceholderText("输入过滤内容")
        self.filter_field_input.textChanged.connect(self.update_inventory_tables)
        self.filter_field_input.setFixedWidth(150)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(filter_field_label)
        filter_layout.addWidget(self.filter_field_combo)
        filter_layout.addWidget(self.filter_field_input)
        filter_layout.setSpacing(5)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.addLayout(filter_layout)

        # 添加弹性空间，将控件靠左对齐
        control_layout.addStretch(1)

        # 添加“库存明细”标签并使其居中
        title_layout = QHBoxLayout()
        title_layout.addStretch(1)
        detail_label = QLabel("库存明细")
        detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(detail_label)
        title_layout.addStretch(1)

        # 将控件布局和标题布局添加到 detail_layout
        detail_layout.addLayout(control_layout)
        detail_layout.addLayout(title_layout)

        self.layout_main.addLayout(detail_layout)

        # 明细库存列表
        self.detail_inventory_table = QTableWidget()
        self.detail_inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.detail_inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.detail_inventory_table.setColumnCount(13)
        self.detail_inventory_table.setHorizontalHeaderLabels([
            'Order Type', '采购订单', '销售订单', '产品编号', 'SKU CLS', '产品名称',
            '库存-箱数', '总瓶数', '库存天数', '到货日期', '提货日期', '售空日期', '创建日期'
        ])
        self.detail_inventory_table.verticalHeader().setVisible(False)
        # 修改列宽调整模式
        header = self.detail_inventory_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # 平均分配列宽
        for i in range(self.detail_inventory_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        self.layout_main.addWidget(self.detail_inventory_table)

        # 总览标题
        total_label = QLabel("库存总览")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_main.addWidget(total_label)

        # 总览库存列表
        self.total_inventory_table = QTableWidget()
        self.total_inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.total_inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.total_inventory_table.setColumnCount(7)
        self.total_inventory_table.setHorizontalHeaderLabels(['产品编号', '采购订单', '销售订单', 'SKU CLS', '产品名称', '库存-箱数','库存-总瓶数'])
        self.total_inventory_table.verticalHeader().setVisible(False)
        # 修改列宽调整模式
        total_header = self.total_inventory_table.horizontalHeader()
        total_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # 平均分配列宽
        for i in range(self.total_inventory_table.columnCount()):
            total_header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        self.layout_main.addWidget(self.total_inventory_table)

        self.setLayout(self.layout_main)

        # 初始化变量
        self.selected_inventory_item = None

        # 连接选择信号到处理函数
        self.detail_inventory_table.selectionModel().selectionChanged.connect(self.on_order_selected)
        # 连接数据变化信号到更新方法
        data_manager.inventory_changed.connect(self.on_inventory_changed)
        # 加载库存数据
        load_inventory_from_db()
        self.update_inventory_tables()

    def on_inventory_changed(self):
        self.update_inventory_tables()

    def on_order_selected(self, selected, deselected):
        indexes = self.detail_inventory_table.selectionModel().selectedRows()
        if indexes:
            index = indexes[0]
            row = index.row()
            # 获取选中的库存记录
            product_id = self.detail_inventory_table.item(row, 3).text()
            order_nb = self.detail_inventory_table.item(row, 1).text()
            # 查找对应的库存项
            inventory_item = next((item for item in inventory if item['Product_ID'] == product_id and item['Order_Nb'] == order_nb), None)
            if inventory_item:
                self.selected_inventory_item = inventory_item
                # 填充输入框
                self.entry_arrival_date.setText(inventory_item.get('Arrival_Date', ''))
                self.entry_pickup_date.setText(inventory_item.get('Pick_up_Date', ''))
            else:
                self.selected_inventory_item = None
                self.entry_arrival_date.clear()
                self.entry_pickup_date.clear()
        else:
            self.selected_inventory_item = None
            self.entry_arrival_date.clear()
            self.entry_pickup_date.clear()

    def update_inventory_record(self):
        if not self.selected_inventory_item:
            QMessageBox.warning(self, "更新错误", "请先选择要更新的库存记录！")
            return
        # 获取输入的日期
        arrival_date_str = self.entry_arrival_date.text().strip()
        pickup_date_str = self.entry_pickup_date.text().strip()
        # 创建一个标志，检查是否有更新
        has_update = False
        # 验证并更新到货日期
        if arrival_date_str:
            try:
                arrival_date = datetime.datetime.strptime(arrival_date_str, '%Y-%m-%d')
                self.selected_inventory_item['Arrival_Date'] = arrival_date_str
                has_update = True
            except ValueError:
                QMessageBox.warning(self, "输入错误", "到货日期格式错误，请输入正确的日期格式：YYYY-MM-DD")
                return
        # 验证并更新提货日期
        if pickup_date_str:
            try:
                pickup_date = datetime.datetime.strptime(pickup_date_str, '%Y-%m-%d')
                self.selected_inventory_item['Pick_up_Date'] = pickup_date_str
                has_update = True
            except ValueError:
                QMessageBox.warning(self, "输入错误", "提货日期格式错误，请输入正确的日期格式：YYYY-MM-DD")
                return
        if has_update:
            # 在保存之前，创建一个副本并移除不属于数据库的字段
            inventory_item_to_save = self.selected_inventory_item.copy()
            inventory_item_to_save.pop('Order_Type', None)  # 移除 Order_Type 字段
            # 保存到数据库
            save_inventory_to_db(inventory_item_to_save)
            QMessageBox.information(self, "成功", "库存记录已更新。")
            # 更新表格
            self.update_inventory_tables()
        else:
            QMessageBox.warning(self, "更新错误", "没有可更新的日期，请输入至少一个日期。")

    def update_inventory_tables(self):
        # 获取当前选择的排序规则
        sort_option = self.sort_combo.currentText()

        # 获取额外的过滤条件
        filter_field = self.filter_field_combo.currentText()
        filter_value = self.filter_field_input.text().strip()

        # 复制库存数据以进行过滤和排序
        filtered_inventory = inventory.copy()

        # 处理过滤条件
        if filter_value:
            if filter_field == "按产品编号":
                filtered_inventory = [item for item in filtered_inventory if filter_value.lower() in item.get('Product_ID', '').lower()]
            elif filter_field == "按采购订单":
                filtered_inventory = [item for item in filtered_inventory if filter_value.lower() in item.get('Order_Nb', '').lower()]
            elif filter_field == "按Order Type":
                filtered_inventory = [item for item in filtered_inventory if filter_value.lower() in item.get('Order_Type', '').lower()]
            elif filter_field == "按SKU CLS":
                filtered_inventory = [item for item in filtered_inventory if filter_value.lower() in item.get('SKU_CLS', '').lower()]
            elif filter_field == "按产品名称":
                # 将用户输入的通配符模式转换为正则表达式
                pattern = re.escape(filter_value).replace(r'\*', '.*')
                regex = re.compile(pattern, re.IGNORECASE)
                filtered_inventory = [item for item in filtered_inventory if regex.search(item.get('Product_Name', ''))]

        # 根据排序规则对数据排序
        if sort_option == "按更新时间":
            sorted_inventory = sorted(filtered_inventory, key=lambda x: x.get('Last_Update', ''), reverse=True)
        elif sort_option == "按采购订单号":
            sorted_inventory = sorted(filtered_inventory, key=lambda x: x.get('Order_Nb', ''))
        elif sort_option == "按销售订单":
            sorted_inventory = sorted(filtered_inventory, key=lambda x: x.get('Sales_Orders', ''))
        elif sort_option == "按产品编号":
            sorted_inventory = sorted(filtered_inventory, key=lambda x: x.get('Product_ID', ''))
        elif sort_option == "按库存-箱数":
            sorted_inventory = sorted(filtered_inventory, key=lambda x: int(x.get('Current_Stock_CS', 0)), reverse=True)
        else:
            sorted_inventory = filtered_inventory

        # 建立订单号到销售订单的映射
        order_nb_to_sales_orders = {}
        for item in sorted_inventory:
            order_nb = item['Order_Nb']
            sales_order = item.get('Sales_Orders', '')
            if order_nb not in order_nb_to_sales_orders:
                order_nb_to_sales_orders[order_nb] = set()
            if sales_order:
                order_nb_to_sales_orders[order_nb].update(
                    [s.strip() for s in sales_order.split(',')]
                )

        # 更新明细表
        self.detail_inventory_table.setRowCount(0)
        self.detail_inventory_table.setRowCount(len(sorted_inventory))
        for row, product in enumerate(sorted_inventory):
            self.detail_inventory_table.setItem(row, 0, QTableWidgetItem(product.get('Order_Type', '')))
            self.detail_inventory_table.setItem(row, 1, QTableWidgetItem(product['Order_Nb']))
            self.detail_inventory_table.setItem(row, 3, QTableWidgetItem(product['Product_ID']))
            self.detail_inventory_table.setItem(row, 4, QTableWidgetItem(product.get('SKU_CLS', '')))
            self.detail_inventory_table.setItem(row, 5, QTableWidgetItem(product['Product_Name']))
            self.detail_inventory_table.setItem(row, 6, QTableWidgetItem(str(product['Current_Stock_CS'])))
            # 计算总瓶数
            btl_per_cs = int(product.get('BTL PER CS', 0))
            total_btl = int(product['Current_Stock_CS']) * btl_per_cs
            self.detail_inventory_table.setItem(row, 7, QTableWidgetItem(str(total_btl)))
            # 计算库存天数
            arrival_date_str = product.get('Arrival_Date', '')
            pickup_date_str = product.get('Pick_up_Date', '')
            if arrival_date_str:
                arrival_date = parse(arrival_date_str)
                if pickup_date_str:
                    pickup_date = parse(pickup_date_str)
                    delta_days = (pickup_date - arrival_date).days
                else:
                    delta_days = (datetime.datetime.now() - arrival_date).days

                self.detail_inventory_table.setItem(row, 8, QTableWidgetItem(str(delta_days)))
            else:
                self.detail_inventory_table.setItem(row, 8, QTableWidgetItem("N/A"))

            self.detail_inventory_table.setItem(row, 9, QTableWidgetItem(product.get('Arrival_Date', '')))
            self.detail_inventory_table.setItem(row, 12, QTableWidgetItem(product.get('Creation_Date', '')))
            self.detail_inventory_table.setItem(row, 10, QTableWidgetItem(product.get('Pick_up_Date', '')))
            self.detail_inventory_table.setItem(row, 11, QTableWidgetItem(product.get('Sale_Date', '')))

            # 获取对应订单号的销售订单
            sales_orders = order_nb_to_sales_orders.get(product['Order_Nb'], set())
            sales_order_str = ', '.join(sorted(sales_orders))
            self.detail_inventory_table.setItem(row, 2, QTableWidgetItem(sales_order_str))

        # 更新总览表，应用相同的排序和过滤规则
        total_inventory = {}
        for product in sorted_inventory:
            product_id = product['Product_ID']
            order_nb = product.get('Order_Nb', '')
            sales_order = product.get('Sales_Orders', '')
            sku_cls = product.get('SKU_CLS', '')
            product_name = product['Product_Name']
            current_stock_cs = int(product['Current_Stock_CS'])
            btl_per_cs = int(product.get('BTL PER CS', 0))
            current_stock_btl = current_stock_cs * btl_per_cs
            if product_id not in total_inventory:
                total_inventory[product_id] = {
                    'Product_ID': product_id,
                    'Order_Nb_Set': set([order_nb]),
                    'Sales_Order_Set': set(),
                    'SKU_CLS': sku_cls,
                    'Product_Name': product_name,
                    'Current_Stock_CS': current_stock_cs,
                    'Current_Stock_BTL': current_stock_btl
                }
            else:
                total_inventory[product_id]['Order_Nb_Set'].add(order_nb)
                total_inventory[product_id]['Current_Stock_CS'] += current_stock_cs
                total_inventory[product_id]['Current_Stock_BTL'] += current_stock_btl

            # 收集销售订单
            if sales_order:
                total_inventory[product_id]['Sales_Order_Set'].update(
                    [s.strip() for s in sales_order.split(',')]
                )

        # 将聚合后的数据转换为列表
        total_inventory_list = list(total_inventory.values())

        # 根据排序规则对总览表数据排序
        if sort_option == "按更新时间":
            # 总览表没有直接的更新时间字段，这里暂时不排序
            pass
        elif sort_option == "按采购订单号":
            total_inventory_list = sorted(total_inventory_list, key=lambda x: ','.join(sorted(x['Order_Nb_Set'])))
        elif sort_option == "按销售订单":
            total_inventory_list = sorted(total_inventory_list, key=lambda x: ','.join(sorted(x['Sales_Order_Set'])))
        elif sort_option == "按产品编号":
            total_inventory_list = sorted(total_inventory_list, key=lambda x: x.get('Product_ID', ''))
        elif sort_option == "按库存-箱数":
            total_inventory_list = sorted(total_inventory_list, key=lambda x: x.get('Current_Stock_CS', 0), reverse=True)

        # 更新总览表
        self.total_inventory_table.setRowCount(0)
        self.total_inventory_table.setRowCount(len(total_inventory_list))
        for row, product in enumerate(total_inventory_list):
            self.total_inventory_table.setItem(row, 0, QTableWidgetItem(product['Product_ID']))
            order_nb_str = ', '.join(sorted(product['Order_Nb_Set']))
            self.total_inventory_table.setItem(row, 1, QTableWidgetItem(order_nb_str))
            self.total_inventory_table.setItem(row, 3, QTableWidgetItem(product.get('SKU_CLS', '')))
            self.total_inventory_table.setItem(row, 4, QTableWidgetItem(product['Product_Name']))
            self.total_inventory_table.setItem(row, 5, QTableWidgetItem(str(product['Current_Stock_CS'])))
            self.total_inventory_table.setItem(row, 6, QTableWidgetItem(str(product['Current_Stock_BTL'])))

            # 展示销售订单
            sales_order_str = ', '.join(sorted(product['Sales_Order_Set']))
            self.total_inventory_table.setItem(row, 2, QTableWidgetItem(sales_order_str))
