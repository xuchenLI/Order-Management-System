# financial_management.py
import re
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QComboBox, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from data import (
    purchase_orders, sales_orders, save_purchase_order_to_db,
    save_sales_order_to_db, get_purchase_order_by_product_id
)

class FinancialManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("财务管理系统")
        self.setGeometry(150, 150, 900, 600)
        self.layout_main = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_receivables_payables_tab(), "应收应付")
        self.tab_widget.addTab(self.create_profit_analysis_tab(), "利润分析")
        self.tab_widget.addTab(self.create_overview_tab(), "总览")
        
        self.layout_main.addWidget(self.tab_widget)
        self.setLayout(self.layout_main)
    
    # ---------- 应收应付标签页 -----------
    def create_receivables_payables_tab(self):
        widget = QWidget()
        main_layout = QHBoxLayout()
        
        # 左侧：销售订单（应收）
        sales_layout = QVBoxLayout()
        # 过滤控件：销售订单部分
        sales_filter_layout = QHBoxLayout()
        self.sales_filter_combo = QComboBox()
        self.sales_filter_combo.addItems(["订单号", "产品编号", "SKU CLS", "销售日期"])
        self.sales_filter_input = QLineEdit()
        self.sales_filter_input.setPlaceholderText("销售订单过滤")
        sales_filter_btn = QPushButton("过滤")
        sales_filter_btn.clicked.connect(self.refresh_sales_table)
        sales_filter_layout.addWidget(self.sales_filter_combo)
        sales_filter_layout.addWidget(self.sales_filter_input)
        sales_filter_layout.addWidget(sales_filter_btn)
        sales_layout.addLayout(sales_filter_layout)
        
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(5)
        self.sales_table.setHorizontalHeaderLabels(["销售订单号", "产品编号", "SKU CLS", "销售日期", "销售金额(€)"])
        self.sales_table.verticalHeader().setVisible(False)
        self.sales_table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed
        )
        self.sales_table.cellChanged.connect(self.on_sales_cell_changed)
        sales_layout.addWidget(self.sales_table)
        
        self.label_sales_total = QLabel("当前销售总金额: 0.00 €")
        sales_layout.addWidget(self.label_sales_total)
        
        # 右侧：采购订单（应付）
        purchase_layout = QVBoxLayout()
        purchase_filter_layout = QHBoxLayout()
        self.purchase_filter_combo = QComboBox()
        self.purchase_filter_combo.addItems(["订单号", "产品编号", "SKU CLS", "采购日期"])
        self.purchase_filter_input = QLineEdit()
        self.purchase_filter_input.setPlaceholderText("采购订单过滤")
        purchase_filter_btn = QPushButton("过滤")
        purchase_filter_btn.clicked.connect(self.refresh_purchase_table)
        purchase_filter_layout.addWidget(self.purchase_filter_combo)
        purchase_filter_layout.addWidget(self.purchase_filter_input)
        purchase_filter_layout.addWidget(purchase_filter_btn)
        purchase_layout.addLayout(purchase_filter_layout)
        
        self.purchase_table = QTableWidget()
        self.purchase_table.setColumnCount(5)
        self.purchase_table.setHorizontalHeaderLabels(["采购订单号", "产品编号", "SKU CLS", "采购日期", "采购成本(€)"])
        self.purchase_table.verticalHeader().setVisible(False)
        self.purchase_table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed
        )
        self.purchase_table.cellChanged.connect(self.on_purchase_cell_changed)
        purchase_layout.addWidget(self.purchase_table)
        
        self.label_purchase_total = QLabel("当前采购总成本: 0.00 €")
        purchase_layout.addWidget(self.label_purchase_total)
        
        main_layout.addLayout(sales_layout)
        main_layout.addLayout(purchase_layout)
        widget.setLayout(main_layout)
        
        self.refresh_sales_table()
        self.refresh_purchase_table()
        return widget
    
    def refresh_sales_table(self):
        # 获取销售订单过滤条件
        filter_field = self.sales_filter_combo.currentText()
        filter_text = self.sales_filter_input.text().strip()
        field_map = {"订单号": "Sales_ID", "产品编号": "Product_ID", "SKU CLS": "SKU CLS", "销售日期": "Order_Date"}
        pattern = re.escape(filter_text).replace(r'\*', '.*') if filter_text else None
        
        filtered_sales = []
        total_sales_amount = 0.0
        for order in sales_orders:
            # 对SKU CLS字段，取对应采购订单的 SKU CLS
            if filter_field == "SKU CLS":
                purchase_order = get_purchase_order_by_product_id(order.get("Product_ID", ""))
                value = purchase_order.get("SKU CLS", "") if purchase_order else ""
            else:
                value = str(order.get(field_map.get(filter_field, ""), ""))
            if pattern:
                if not re.search(pattern, value, re.IGNORECASE):
                    continue
            filtered_sales.append(order)
        
        self.sales_table.blockSignals(True)
        self.sales_table.setRowCount(len(filtered_sales))
        for row, order in enumerate(filtered_sales):
            self.sales_table.setItem(row, 0, QTableWidgetItem(str(order.get("Sales_ID", ""))))
            self.sales_table.setItem(row, 1, QTableWidgetItem(str(order.get("Product_ID", ""))))
            # 获取SKU CLS：从对应采购订单中提取
            purchase_order = get_purchase_order_by_product_id(order.get("Product_ID", ""))
            sku_cls = purchase_order.get("SKU CLS", "") if purchase_order else ""
            self.sales_table.setItem(row, 2, QTableWidgetItem(sku_cls))
            date_item = QTableWidgetItem(str(order.get("Order_Date", "")))
            date_item.setFlags(date_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.sales_table.setItem(row, 3, date_item)
            try:
                amount = float(order.get("Total_Amount", 0))
            except ValueError:
                amount = 0.0
            self.sales_table.setItem(row, 4, QTableWidgetItem(f"{amount:.2f}"))
            total_sales_amount += amount
        self.sales_table.blockSignals(False)
        self.label_sales_total.setText(f"当前销售总金额: {total_sales_amount:.2f} €")
    
    def refresh_purchase_table(self):
        # 获取采购订单过滤条件
        filter_field = self.purchase_filter_combo.currentText()
        filter_text = self.purchase_filter_input.text().strip()
        field_map = {"订单号": "Order Nb", "产品编号": "Product_ID", "SKU CLS": "SKU CLS", "采购日期": "date"}
        pattern = re.escape(filter_text).replace(r'\*', '.*') if filter_text else None
        
        filtered_purchase = []
        total_purchase_cost = 0.0
        for order in purchase_orders:
            value = str(order.get(field_map.get(filter_field, ""), ""))
            if pattern:
                if not re.search(pattern, value, re.IGNORECASE):
                    continue
            filtered_purchase.append(order)
        self.purchase_table.blockSignals(True)
        self.purchase_table.setRowCount(len(filtered_purchase))
        for row, order in enumerate(filtered_purchase):
            self.purchase_table.setItem(row, 0, QTableWidgetItem(str(order.get("Order Nb", ""))))
            self.purchase_table.setItem(row, 1, QTableWidgetItem(str(order.get("Product_ID", ""))))
            self.purchase_table.setItem(row, 2, QTableWidgetItem(str(order.get("SKU CLS", ""))))
            date_item = QTableWidgetItem(str(order.get("date", "")))
            date_item.setFlags(date_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.purchase_table.setItem(row, 3, date_item)
            try:
                qty = float(order.get("QUANTITY CS", 0))
            except ValueError:
                qty = 0.0
            try:
                btl = float(order.get("BTL PER CS", 0))
            except ValueError:
                btl = 0.0
            try:
                price = float(order.get("EXW EURO", 0))
            except ValueError:
                price = 0.0
            cost = qty * btl * price
            self.purchase_table.setItem(row, 4, QTableWidgetItem(f"{cost:.2f}"))
            total_purchase_cost += cost
        self.purchase_table.blockSignals(False)
        self.label_purchase_total.setText(f"当前采购总成本: {total_purchase_cost:.2f} €")
    
    def on_sales_cell_changed(self, row, column):
        # 仅处理销售日期列（第4列）
        if column != 3:
            return
        new_date = self.sales_table.item(row, column).text().strip()
        sales_id_item = self.sales_table.item(row, 0)
        if sales_id_item is None:
            return
        sales_id = sales_id_item.text().strip()
        for order in sales_orders:
            if str(order.get("Sales_ID", "")).strip() == sales_id:
                order["Order_Date"] = new_date
                save_sales_order_to_db(order)
                break
    
    def on_purchase_cell_changed(self, row, column):
        # 仅处理采购日期列（第4列）
        if column != 3:
            return
        new_date = self.purchase_table.item(row, column).text().strip()
        order_nb_item = self.purchase_table.item(row, 0)
        if order_nb_item is None:
            return
        order_nb = order_nb_item.text().strip()
        for order in purchase_orders:
            if str(order.get("Order Nb", "")).strip() == order_nb:
                order["date"] = new_date
                save_purchase_order_to_db(order)
                break
    
    # ---------- 利润分析标签页 ----------
    def create_profit_analysis_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.label_sales_revenue = QLabel("销售收入: 0.00 €")
        self.label_purchase_cost = QLabel("采购成本: 0.00 €")
        self.label_gross_profit = QLabel("毛利: 0.00 €")
        
        refresh_btn = QPushButton("刷新利润数据")
        refresh_btn.clicked.connect(self.calculate_profit_metrics)
        
        layout.addWidget(self.label_sales_revenue)
        layout.addWidget(self.label_purchase_cost)
        layout.addWidget(self.label_gross_profit)
        layout.addWidget(refresh_btn)
        widget.setLayout(layout)
        
        self.calculate_profit_metrics()
        return widget
    
    def calculate_profit_metrics(self):
        total_sales_revenue = 0.0
        for order in sales_orders:
            try:
                total_sales_revenue += float(order.get("Total_Amount", 0))
            except ValueError:
                pass
        total_purchase_cost = 0.0
        for order in purchase_orders:
            try:
                qty = float(order.get("QUANTITY CS", 0))
                btl = float(order.get("BTL PER CS", 0))
                price = float(order.get("EXW EURO", 0))
                total_purchase_cost += qty * btl * price
            except ValueError:
                pass
        gross_profit = total_sales_revenue - total_purchase_cost
        
        self.label_sales_revenue.setText(f"销售收入: {total_sales_revenue:.2f} €")
        self.label_purchase_cost.setText(f"采购成本: {total_purchase_cost:.2f} €")
        self.label_gross_profit.setText(f"毛利: {gross_profit:.2f} €")
    
    # ---------- 总览标签页 ----------
    def create_overview_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.label_total_sales_orders = QLabel("销售订单总数: 0")
        self.label_total_sales_amount = QLabel("销售总金额: 0.00 €")
        self.label_total_purchase_orders = QLabel("采购订单总数: 0")
        self.label_total_purchase_amount = QLabel("采购总金额: 0.00 €")
        
        refresh_btn = QPushButton("刷新总览")
        refresh_btn.clicked.connect(self.calculate_overview)
        
        layout.addWidget(self.label_total_sales_orders)
        layout.addWidget(self.label_total_sales_amount)
        layout.addWidget(self.label_total_purchase_orders)
        layout.addWidget(self.label_total_purchase_amount)
        layout.addWidget(refresh_btn)
        widget.setLayout(layout)
        
        self.calculate_overview()
        return widget
    
    def calculate_overview(self):
        total_sales_orders = len(sales_orders)
        total_purchase_orders = len(purchase_orders)
        total_sales_amount = 0.0
        for order in sales_orders:
            try:
                total_sales_amount += float(order.get("Total_Amount", 0))
            except ValueError:
                pass
        total_purchase_amount = 0.0
        for order in purchase_orders:
            try:
                qty = float(order.get("QUANTITY CS", 0))
                btl = float(order.get("BTL PER CS", 0))
                price = float(order.get("EXW EURO", 0))
                total_purchase_amount += qty * btl * price
            except ValueError:
                pass
        
        self.label_total_sales_orders.setText(f"销售订单总数: {total_sales_orders}")
        self.label_total_sales_amount.setText(f"销售总金额: {total_sales_amount:.2f} €")
        self.label_total_purchase_orders.setText(f"采购订单总数: {total_purchase_orders}")
        self.label_total_purchase_amount.setText(f"采购总金额: {total_purchase_amount:.2f} €")
