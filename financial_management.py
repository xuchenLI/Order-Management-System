# financial_management.py
import re
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QComboBox, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from data import purchase_orders, sales_orders, save_purchase_order_to_db, save_sales_order_to_db

class FinancialManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("财务管理 - 订单数据")
        self.setGeometry(150, 150, 800, 600)
        
        self.tab_widget = QTabWidget()
        self.purchase_tab = QWidget()
        self.sales_tab = QWidget()
        self.tab_widget.addTab(self.purchase_tab, "采购订单")
        self.tab_widget.addTab(self.sales_tab, "销售订单")
        
        self.setup_purchase_tab()
        self.setup_sales_tab()
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
        
        self.update_purchase_table()
        self.update_sales_table()
    
    def setup_purchase_tab(self):
        layout = QVBoxLayout()
        # 过滤和排序控件
        control_layout = QHBoxLayout()
        self.purchase_filter_combo = QComboBox()
        self.purchase_filter_combo.addItems(["订单号", "产品编号", "SKU CLS", "采购日期"])
        self.purchase_filter_input = QLineEdit()
        self.purchase_filter_input.setPlaceholderText("过滤条件")
        self.purchase_filter_input.textChanged.connect(self.update_purchase_table)
        
        self.purchase_sort_combo = QComboBox()
        self.purchase_sort_combo.addItems(["默认排序", "订单号", "产品编号", "SKU CLS", "采购日期"])
        self.purchase_sort_combo.currentIndexChanged.connect(self.update_purchase_table)
        
        control_layout.addWidget(self.purchase_filter_combo)
        control_layout.addWidget(self.purchase_filter_input)
        control_layout.addWidget(self.purchase_sort_combo)
        layout.addLayout(control_layout)
        
        # 订单数据表格
        self.purchase_table = QTableWidget()
        self.purchase_table.setColumnCount(4)
        self.purchase_table.setHorizontalHeaderLabels(["订单号", "产品编号", "SKU CLS", "采购日期"])
        self.purchase_table.verticalHeader().setVisible(False)
        # 允许双击编辑日期
        self.purchase_table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed
        )
        self.purchase_table.cellChanged.connect(self.on_purchase_cell_changed)
        layout.addWidget(self.purchase_table)
        
        self.purchase_tab.setLayout(layout)
    
    def setup_sales_tab(self):
        layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        self.sales_filter_combo = QComboBox()
        self.sales_filter_combo.addItems(["销售订单号", "产品编号", "SKU CLS", "销售日期"])
        self.sales_filter_input = QLineEdit()
        self.sales_filter_input.setPlaceholderText("过滤条件")
        self.sales_filter_input.textChanged.connect(self.update_sales_table)
        
        self.sales_sort_combo = QComboBox()
        self.sales_sort_combo.addItems(["默认排序", "销售订单号", "产品编号", "SKU CLS", "销售日期"])
        self.sales_sort_combo.currentIndexChanged.connect(self.update_sales_table)
        
        control_layout.addWidget(self.sales_filter_combo)
        control_layout.addWidget(self.sales_filter_input)
        control_layout.addWidget(self.sales_sort_combo)
        layout.addLayout(control_layout)
        
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(4)
        self.sales_table.setHorizontalHeaderLabels(["销售订单号", "产品编号", "SKU CLS", "销售日期"])
        self.sales_table.verticalHeader().setVisible(False)
        self.sales_table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed
        )
        self.sales_table.cellChanged.connect(self.on_sales_cell_changed)
        layout.addWidget(self.sales_table)
        
        self.sales_tab.setLayout(layout)
    
    def update_purchase_table(self):
        # 获取过滤和排序条件
        filter_field = self.purchase_filter_combo.currentText()
        filter_text = self.purchase_filter_input.text().strip()
        sort_field = self.purchase_sort_combo.currentText()
        
        # 映射采购订单中相关字段
        field_map = {"订单号": "Order Nb", "产品编号": "Product_ID", "SKU CLS": "SKU CLS", "采购日期": "date"}
        
        def filter_func(order):
            if not filter_text:
                return True
            value = str(order.get(field_map.get(filter_field, ""), ""))
            pattern = re.escape(filter_text).replace(r'\*', '.*')
            return re.search(pattern, value, re.IGNORECASE) is not None
        
        filtered_orders = list(filter(filter_func, purchase_orders))
        if sort_field != "默认排序":
            key = field_map.get(sort_field, "Order Nb")
            filtered_orders.sort(key=lambda o: o.get(key, ""))
        
        self.purchase_table.blockSignals(True)
        self.purchase_table.setRowCount(len(filtered_orders))
        for row, order in enumerate(filtered_orders):
            self.purchase_table.setItem(row, 0, QTableWidgetItem(str(order.get("Order Nb", ""))))
            self.purchase_table.setItem(row, 1, QTableWidgetItem(str(order.get("Product_ID", ""))))
            self.purchase_table.setItem(row, 2, QTableWidgetItem(str(order.get("SKU CLS", ""))))
            # 采购日期列可编辑
            date_item = QTableWidgetItem(str(order.get("date", "")))
            date_item.setFlags(date_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.purchase_table.setItem(row, 3, date_item)
        self.purchase_table.blockSignals(False)
    
    def update_sales_table(self):
        filter_field = self.sales_filter_combo.currentText()
        filter_text = self.sales_filter_input.text().strip()
        sort_field = self.sales_sort_combo.currentText()
        
        field_map = {"销售订单号": "Sales_ID", "产品编号": "Product_ID", "SKU CLS": "SKU CLS", "销售日期": "Order_Date"}
        
        def filter_func(order):
            if not filter_text:
                return True
            value = str(order.get(field_map.get(filter_field, ""), ""))
            pattern = re.escape(filter_text).replace(r'\*', '.*')
            return re.search(pattern, value, re.IGNORECASE) is not None
        
        filtered_orders = list(filter(filter_func, sales_orders))
        if sort_field != "默认排序":
            key = field_map.get(sort_field, "Sales_ID")
            filtered_orders.sort(key=lambda o: o.get(key, ""))
        
        self.sales_table.blockSignals(True)
        self.sales_table.setRowCount(len(filtered_orders))
        for row, order in enumerate(filtered_orders):
            self.sales_table.setItem(row, 0, QTableWidgetItem(str(order.get("Sales_ID", ""))))
            self.sales_table.setItem(row, 1, QTableWidgetItem(str(order.get("Product_ID", ""))))
            self.sales_table.setItem(row, 2, QTableWidgetItem(str(order.get("SKU CLS", ""))))
            date_item = QTableWidgetItem(str(order.get("Order_Date", "")))
            date_item.setFlags(date_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.sales_table.setItem(row, 3, date_item)
        self.sales_table.blockSignals(False)
    
    def on_purchase_cell_changed(self, row, column):
        # 仅处理采购日期列（第 3 列）
        if column != 3:
            return
        new_date = self.purchase_table.item(row, column).text().strip()
        # 根据表格第一列的订单号找到对应采购订单记录
        order_nb_item = self.purchase_table.item(row, 0)
        if order_nb_item is None:
            return
        order_nb = order_nb_item.text().strip()
        for order in purchase_orders:
            if str(order.get("Order Nb", "")).strip() == order_nb:
                order["date"] = new_date
                save_purchase_order_to_db(order)
                break
    
    def on_sales_cell_changed(self, row, column):
        # 仅处理销售日期列（第 3 列）
        if column != 3:
            return
        new_date = self.sales_table.item(row, column).text().strip()
        order_id_item = self.sales_table.item(row, 0)
        if order_id_item is None:
            return
        sales_id = order_id_item.text().strip()
        for order in sales_orders:
            if str(order.get("Sales_ID", "")).strip() == sales_id:
                order["Order_Date"] = new_date
                save_sales_order_to_db(order)
                break
