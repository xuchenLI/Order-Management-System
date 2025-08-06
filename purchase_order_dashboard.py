from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QSplitter, QMessageBox, QComboBox, QDialog, QHeaderView, QDialogButtonBox, QTabWidget,
    QDoubleSpinBox, QScrollArea, QSizePolicy, QLineEdit, QInputDialog, QListWidget, QListWidgetItem, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtCore import QEvent
from data import purchase_orders, save_purchase_order_to_db, get_freight_by_main_order, set_freight_for_main_order
import datetime
import os
import json
from order_details import OrderDetailsWindow
import matplotlib
matplotlib.use('QtAgg')
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
matplotlib.rcParams['axes.unicode_minus'] = False
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import numpy as np

ORDER_STATUS_LIST = ["未下单", "已下单", "已发货", "已到货", "已完成", "退货"]
MAIN_ORDER_STATUS_LIST = [
    "未下单", "部分下单", "已下单", "部分发货", "已发货", "部分到货", "已到货", "部分完成", "已完成", "部分退货", "已退货"
]
MATERIAL_REVIEW_ITEMS = ["sticker", "发票", "照片"]
MATERIAL_REVIEW_STATUS = ["", "Yes", "No"]
CONFIG_FILE = r"C:\Users\mosho\OneDrive\Order_Management_Tool\order_dashboard_config.json"
SPLITTER_CONFIG_FILE = r"C:\Users\mosho\OneDrive\Order_Management_Tool\order_dashboard_config.json"

class StatusHistoryDialog(QDialog):
    def __init__(self, status_history, parent=None):
        super().__init__(parent)
        self.setWindowTitle("状态变更追踪")
        self.setGeometry(300, 300, 500, 300)
        layout = QVBoxLayout()
        self.setLayout(layout)
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["变更前", "变更后", "时间", "操作人"])
        table.verticalHeader().setVisible(False)
        table.setRowCount(len(status_history))
        for row, record in enumerate(status_history):
            table.setItem(row, 0, QTableWidgetItem(record.get("from", "")))
            table.setItem(row, 1, QTableWidgetItem(record.get("to", "")))
            table.setItem(row, 2, QTableWidgetItem(record.get("time", "")))
            table.setItem(row, 3, QTableWidgetItem(record.get("user", "")))
        table.resizeColumnsToContents()
        layout.addWidget(table)

class BatchStatusDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量修改状态")
        self.setGeometry(400, 400, 300, 100)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.combo = QComboBox()
        self.combo.addItems(ORDER_STATUS_LIST)
        layout.addWidget(QLabel("选择要设置的新状态："))
        layout.addWidget(self.combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
    def get_status(self):
        return self.combo.currentText()

class OrderStatisticsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("订单统计")
        self.setGeometry(300, 200, 900, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)
        self.setMinimumSize(800, 500)
        layout = QVBoxLayout()
        self.setLayout(layout)
        from data import purchase_orders
        status_list = ["未下单", "已下单", "已发货", "已到货", "已完成", "退货"]
        # --- 数据准备 ---
        df = pd.DataFrame(purchase_orders)
        # 合并供应商名称
        def calc_amount(row):
            try:
                return float(row.get("QUANTITY CS", 0)) * float(row.get("BTL PER CS", 0)) * float(row.get("EXW EURO", 0))
            except Exception:
                return 0.0
        df["金额"] = df.apply(calc_amount, axis=1)
        df["date"] = pd.to_datetime(df.get("date", pd.NaT), errors='coerce')
        total_orders = len(df)
        total_amount = df["金额"].sum()
        label_total = QLabel(f"采购订单总数：{total_orders}    总金额：{total_amount:.2f} €")
        layout.addWidget(label_total)
        tabs = QTabWidget()
        layout.addWidget(tabs)
        # --- 1. 状态分布 ---
        tab_status = QWidget()
        tab_status_layout = QVBoxLayout()
        tab_status.setLayout(tab_status_layout)
        status_count = df["Order Step"].value_counts().reindex(status_list, fill_value=0)
        status_amount = df.groupby("Order Step")["金额"].sum().reindex(status_list, fill_value=0)
        table_status = QTableWidget()
        table_status.setColumnCount(3)
        table_status.setRowCount(len(status_list))
        table_status.setHorizontalHeaderLabels(["订单状态", "订单数", "订单金额(€)"])
        for i, s in enumerate(status_list):
            table_status.setItem(i, 0, QTableWidgetItem(s))
            table_status.setItem(i, 1, QTableWidgetItem(str(status_count[s])))
            table_status.setItem(i, 2, QTableWidgetItem(f"{status_amount[s]:.2f}"))
        table_status.resizeColumnsToContents()
        tab_status_layout.addWidget(QLabel("各状态订单数与金额："))
        tab_status_layout.addWidget(table_status)
        # 饼图自适应
        self.fig1 = Figure()
        self.ax1 = self.fig1.add_subplot(111)
        self.pie_canvas = FigureCanvas(self.fig1)
        self._draw_pie(status_count, status_list)
        tab_status_layout.addWidget(self.pie_canvas)
        tabs.addTab(tab_status, "状态分布")
        # --- 2. 供应商统计 ---
        tab_supplier = QWidget()
        tab_supplier_layout = QVBoxLayout()
        tab_supplier.setLayout(tab_supplier_layout)
        supplier_group = df.groupby("Supplier")["金额"].agg(['count','sum']).sort_values("sum", ascending=False)
        table_supplier = QTableWidget()
        table_supplier.setColumnCount(3)
        table_supplier.setRowCount(len(supplier_group))
        table_supplier.setHorizontalHeaderLabels(["供应商", "订单数", "订单金额(€)"])
        for i, (supplier, row) in enumerate(supplier_group.iterrows()):
            table_supplier.setItem(i, 0, QTableWidgetItem(str(supplier)))
            table_supplier.setItem(i, 1, QTableWidgetItem(str(int(row['count']))))
            table_supplier.setItem(i, 2, QTableWidgetItem(f"{row['sum']:.2f}"))
        table_supplier.resizeColumnsToContents()
        tab_supplier_layout.addWidget(QLabel("各供应商订单统计："))
        tab_supplier_layout.addWidget(table_supplier)
        # 柱状图自适应
        self.fig2 = Figure()
        self.ax2 = self.fig2.add_subplot(111)
        self.bar_canvas = FigureCanvas(self.fig2)
        self._draw_bar(supplier_group)
        tab_supplier_layout.addWidget(self.bar_canvas)
        tabs.addTab(tab_supplier, "供应商统计")
        # --- 3. 酒品排行 ---
        tab_product = QWidget()
        tab_product_layout = QVBoxLayout()
        tab_product.setLayout(tab_product_layout)
        product_group = df.groupby("ITEM Name")["金额"].agg(['count','sum']).sort_values("sum", ascending=False)
        table_product = QTableWidget()
        table_product.setColumnCount(3)
        table_product.setRowCount(len(product_group))
        table_product.setHorizontalHeaderLabels(["酒品名称", "订单数", "订单金额(€)"])
        for i, (name, row) in enumerate(product_group.iterrows()):
            table_product.setItem(i, 0, QTableWidgetItem(str(name)))
            table_product.setItem(i, 1, QTableWidgetItem(str(int(row['count']))))
            table_product.setItem(i, 2, QTableWidgetItem(f"{row['sum']:.2f}"))
        table_product.resizeColumnsToContents()
        tab_product_layout.addWidget(QLabel("酒品采购排行："))
        tab_product_layout.addWidget(table_product)
        tabs.addTab(tab_product, "酒品排行")
        # --- 4. 材料审查 ---
        tab_material = QWidget()
        tab_material_layout = QVBoxLayout()
        tab_material.setLayout(tab_material_layout)
        def count_review(item):
            yes = 0
            total = 0
            material_review = load_material_review()
            for po in purchase_orders:
                order_nb = po.get("Order Nb", "")
                review = material_review.get(order_nb, {k: "" for k in MATERIAL_REVIEW_ITEMS})
                if item in review:
                    total += 1
                    if review[item] == "Yes":
                        yes += 1
            return yes, total
        review_items = ["sticker", "发票", "照片"]
        table_review = QTableWidget()
        table_review.setColumnCount(3)
        table_review.setRowCount(len(review_items))
        table_review.setHorizontalHeaderLabels(["材料项", "通过数/总数", "通过率"])
        for i, item in enumerate(review_items):
            yes, total = count_review(item)
            rate = f"{(yes/total*100):.1f}%" if total else "-"
            table_review.setItem(i, 0, QTableWidgetItem(item))
            table_review.setItem(i, 1, QTableWidgetItem(f"{yes}/{total}"))
            table_review.setItem(i, 2, QTableWidgetItem(rate))
        table_review.resizeColumnsToContents()
        tab_material_layout.addWidget(QLabel("材料审查通过率："))
        tab_material_layout.addWidget(table_review)
        table_unpass = QTableWidget()
        failed = [(po.get("Order Nb", ""), item)
                  for po in purchase_orders
                  for item in review_items
                  if load_material_review().get(po.get("Order Nb", ""), {}).get(item, "") == "No"]
        table_unpass.setColumnCount(2)
        table_unpass.setRowCount(len(failed))
        table_unpass.setHorizontalHeaderLabels(["订单号", "未通过项"])
        for i, (order_nb, item) in enumerate(failed):
            table_unpass.setItem(i, 0, QTableWidgetItem(order_nb))
            table_unpass.setItem(i, 1, QTableWidgetItem(item))
        table_unpass.resizeColumnsToContents()
        tab_material_layout.addWidget(QLabel("未通过材料明细："))
        tab_material_layout.addWidget(table_unpass)
        tabs.addTab(tab_material, "材料审查")
        # --- 5. 趋势分析 ---
        tab_trend = QWidget()
        tab_trend_layout = QVBoxLayout()
        tab_trend.setLayout(tab_trend_layout)
        # 以主订单号为横坐标
        df['main_order'] = df['Order Nb'].astype(str).str.split('_').str[0]
        # 彻底过滤TEST主订单
        df = df[df['main_order'] != 'TEST']
        # 主订单号按自然顺序（年4位、月2位、日/序号2位分段）排序
        import re
        def extract_order_tuple(nb):
            m = re.match(r'AVN(\d{4})(\d{2})(\d{2})?$', nb)
            if m:
                year = int(m.group(1))
                month = int(m.group(2))
                day = int(m.group(3)) if m.group(3) else 0
                return (year, month, day)
            return (float('inf'), float('inf'), float('inf'))
        main_order_sorted = sorted([x for x in df['main_order'].unique() if x != 'TEST'], key=extract_order_tuple)
        # 金额趋势
        main_order_amount = df.groupby('main_order')['金额'].sum().reindex(main_order_sorted, fill_value=0)
        self.fig3 = Figure()
        self.ax3 = self.fig3.add_subplot(111)
        self.line_canvas1 = FigureCanvas(self.fig3)
        self._draw_line(self.ax3, main_order_amount, "主订单金额趋势", "主订单号", "金额(€)")
        tab_trend_layout.addWidget(self.line_canvas1)
        # 瓶数趋势（主订单）
        def calc_bt(row):
            try:
                return float(row.get("QUANTITY CS", 0)) * float(row.get("BTL PER CS", 0))
            except Exception:
                return 0.0
        df['瓶数'] = df.apply(calc_bt, axis=1)
        main_order_bt = df.groupby('main_order')['瓶数'].sum().reindex(main_order_sorted, fill_value=0)
        self.fig4 = Figure()
        self.ax4 = self.fig4.add_subplot(111)
        self.line_canvas2 = FigureCanvas(self.fig4)
        self._draw_line(self.ax4, main_order_bt, "主订单采购瓶数趋势", "主订单号", "瓶数", color='orange')
        tab_trend_layout.addWidget(self.line_canvas2)
        # 供应商分线图
        supplier_bt = df.groupby(['main_order', 'Supplier'])['瓶数'].sum().unstack(fill_value=0).reindex(main_order_sorted, fill_value=0)
        self.fig5 = Figure()
        self.ax5 = self.fig5.add_subplot(111)
        self.line_canvas3 = FigureCanvas(self.fig5)
        self._draw_multi_line(self.ax5, supplier_bt, "各供应商采购瓶数趋势", "主订单号", "瓶数")
        tab_trend_layout.addWidget(self.line_canvas3)
        tabs.addTab(tab_trend, "趋势分析")
        # --- 6. 异常订单 ---
        tab_abnormal = QWidget()
        tab_abnormal_layout = QVBoxLayout()
        tab_abnormal.setLayout(tab_abnormal_layout)
        abnormal_status = ["未下单", "已下单", "已发货", "退货"]
        df_abnormal = df[df["Order Step"].isin(abnormal_status)]
        table_abnormal = QTableWidget()
        table_abnormal.setColumnCount(4)
        table_abnormal.setRowCount(len(df_abnormal))
        table_abnormal.setHorizontalHeaderLabels(["订单号", "状态", "金额(€)", "供应商"])
        for i, row in df_abnormal.iterrows():
            table_abnormal.setItem(i, 0, QTableWidgetItem(str(row.get("Order Nb", ""))))
            table_abnormal.setItem(i, 1, QTableWidgetItem(str(row.get("Order Step", ""))))
            table_abnormal.setItem(i, 2, QTableWidgetItem(f"{row.get('金额', 0):.2f}"))
            table_abnormal.setItem(i, 3, QTableWidgetItem(str(row.get("Supplier", ""))))
        table_abnormal.resizeColumnsToContents()
        tab_abnormal_layout.addWidget(QLabel("未到货/未完成/退货订单明细："))
        tab_abnormal_layout.addWidget(table_abnormal)
        tabs.addTab(tab_abnormal, "异常订单")
        # --- 新增 7. 主订单统计 ---
        tab_main_order = QWidget()
        tab_main_order_layout = QVBoxLayout()
        tab_main_order.setLayout(tab_main_order_layout)
        # 主订单号下拉框（必须先于布局创建）
        main_orders = sorted(set([str(nb).split('_')[0] for nb in df['Order Nb'].dropna().unique() if str(nb).split('_')[0] != 'TEST']))
        self.combo_main_order = QComboBox()
        self.combo_main_order.addItems(main_orders)
        # 主体分割区
        splitter = QSplitter(Qt.Orientation.Horizontal)
        tab_main_order_layout.addWidget(splitter)
        # 左侧主订单统计（1/3）
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        left_layout.addWidget(QLabel("选择主订单号："))
        left_layout.addWidget(self.combo_main_order)
        # 运费输入框改为QLineEdit
        freight_layout = QHBoxLayout()
        freight_layout.addWidget(QLabel("Air Freight:"))
        self.input_air = QLineEdit(); self.input_air.setPlaceholderText("€")
        self.input_air.setReadOnly(True)
        self.input_air.setStyleSheet("background-color: #f0f0f0;")
        freight_layout.addWidget(self.input_air)
        freight_layout.addWidget(QLabel("Airport Fees:"))
        self.input_airport = QLineEdit(); self.input_airport.setPlaceholderText("€")
        self.input_airport.setReadOnly(True)
        self.input_airport.setStyleSheet("background-color: #f0f0f0;")
        freight_layout.addWidget(self.input_airport)
        freight_layout.addWidget(QLabel("In bond Freight:"))
        self.input_inbond = QLineEdit(); self.input_inbond.setPlaceholderText("€")
        self.input_inbond.setReadOnly(True)
        self.input_inbond.setStyleSheet("background-color: #f0f0f0;")
        freight_layout.addWidget(self.input_inbond)
        # 新增按钮
        self.btn_edit_freight = QPushButton("修改")
        self.btn_save_freight = QPushButton("保存")
        self.btn_save_freight.setEnabled(False)
        freight_layout.addWidget(self.btn_edit_freight)
        freight_layout.addWidget(self.btn_save_freight)
        freight_layout.addStretch()
        left_layout.addLayout(freight_layout)
        # 绑定按钮事件
        self.btn_edit_freight.clicked.connect(self.enable_freight_edit)
        self.btn_save_freight.clicked.connect(self.save_freight)
        # 供应商统计表格
        self.table_main_supplier = QTableWidget()
        self.table_main_supplier.setColumnCount(6)
        self.table_main_supplier.setHorizontalHeaderLabels(["供应商", "EXW总价(€)", "数量(CS)", "数量(BT)", "已售出瓶数", "销售金额(€)"])
        left_layout.addWidget(self.table_main_supplier)
        # 主订单总价和TOTAL
        self.label_main_total = QLabel()
        self.label_total = QLabel()
        left_layout.addWidget(self.label_main_total)
        left_layout.addWidget(self.label_total)
        left_layout.addStretch()
        splitter.addWidget(left_widget)
        # 右侧趋势分析（2/3）
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        # 滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_content.setLayout(scroll_layout)
        # 趋势分析按钮放到右侧scroll区左上
        btn_trend = QPushButton("趋势分析")
        btn_trend.setFixedWidth(100)
        btn_trend.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        btn_trend.clicked.connect(self.open_trend_analysis_window)
        btn_trend_layout = QHBoxLayout()
        btn_trend_layout.addWidget(btn_trend)
        btn_trend_layout.addStretch()
        scroll_layout.addLayout(btn_trend_layout)
        # 重新生成趋势分析图表
        # 金额趋势
        self.fig3 = Figure(figsize=(max(8, len(main_order_sorted)*0.8), 3))
        self.ax3 = self.fig3.add_subplot(111)
        self.line_canvas1 = FigureCanvas(self.fig3)
        self._draw_line(self.ax3, main_order_amount, "主订单金额趋势", "主订单号", "金额(€)")
        scroll_layout.addWidget(self.line_canvas1)
        # 瓶数趋势
        self.fig4 = Figure(figsize=(max(8, len(main_order_sorted)*0.8), 3))
        self.ax4 = self.fig4.add_subplot(111)
        self.line_canvas2 = FigureCanvas(self.fig4)
        self._draw_line(self.ax4, main_order_bt, "主订单采购瓶数趋势", "主订单号", "瓶数", color='orange')
        scroll_layout.addWidget(self.line_canvas2)
        # 供应商分线图
        self.fig5 = Figure(figsize=(max(8, len(main_order_sorted)*0.8), 3))
        self.ax5 = self.fig5.add_subplot(111)
        self.line_canvas3 = FigureCanvas(self.fig5)
        self._draw_multi_line(self.ax5, supplier_bt, "各供应商采购瓶数趋势", "主订单号", "瓶数")
        scroll_layout.addWidget(self.line_canvas3)
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)
        splitter.addWidget(right_widget)
        splitter.setSizes([int(self.width()*0.33), int(self.width()*0.67)])
        tabs.addTab(tab_main_order, "主订单统计")
        # 趋势分析弹窗
        self.trend_analysis_window = None
        # 运费数据存储（可扩展为持久化）
        self._main_order_freight = {}
        # 信号连接
        self.combo_main_order.currentIndexChanged.connect(self.load_freight_for_main_order)
        self.input_air.textChanged.connect(self.update_main_order_stats)
        self.input_airport.textChanged.connect(self.update_main_order_stats)
        self.input_inbond.textChanged.connect(self.update_main_order_stats)
        # 初始化
        if main_orders:
            self.combo_main_order.setCurrentIndex(0)
            self.load_freight_for_main_order()
            self.update_main_order_stats()
        layout.addStretch()

    def enable_freight_edit(self):
        self.input_air.setReadOnly(False)
        self.input_air.setStyleSheet("background-color: #ffffff;")
        self.input_airport.setReadOnly(False)
        self.input_airport.setStyleSheet("background-color: #ffffff;")
        self.input_inbond.setReadOnly(False)
        self.input_inbond.setStyleSheet("background-color: #ffffff;")
        self.btn_save_freight.setEnabled(True)
        self.btn_edit_freight.setEnabled(False)

    def save_freight(self):
        main_nb = self.combo_main_order.currentText()
        def safe_float(val):
            try:
                return float(val)
            except Exception:
                return 0.0
        air = safe_float(self.input_air.text())
        airport = safe_float(self.input_airport.text())
        inbond = safe_float(self.input_inbond.text())
        set_freight_for_main_order(main_nb, air, airport, inbond)
        self.input_air.setReadOnly(True)
        self.input_air.setStyleSheet("background-color: #f0f0f0;")
        self.input_airport.setReadOnly(True)
        self.input_airport.setStyleSheet("background-color: #f0f0f0;")
        self.input_inbond.setReadOnly(True)
        self.input_inbond.setStyleSheet("background-color: #f0f0f0;")
        self.btn_save_freight.setEnabled(False)
        self.btn_edit_freight.setEnabled(True)
        self.update_main_order_stats()

    def load_freight_for_main_order(self):
        main_nb = self.combo_main_order.currentText()
        freight = get_freight_by_main_order(main_nb)
        self.input_air.setText(str(freight.get("air", "")))
        self.input_air.setReadOnly(True)
        self.input_air.setStyleSheet("background-color: #f0f0f0;")
        self.input_airport.setText(str(freight.get("airport", "")))
        self.input_airport.setReadOnly(True)
        self.input_airport.setStyleSheet("background-color: #f0f0f0;")
        self.input_inbond.setText(str(freight.get("inbond", "")))
        self.input_inbond.setReadOnly(True)
        self.input_inbond.setStyleSheet("background-color: #f0f0f0;")
        self.btn_save_freight.setEnabled(False)
        self.btn_edit_freight.setEnabled(True)
        self.update_main_order_stats()

    def resizeEvent(self, event):
        # 图表自适应窗口大小
        w = max(self.width() // 2, 300)
        h = max(self.height() // 3, 200)
        self.fig1.set_size_inches(w/100, h/100, forward=True)
        self.pie_canvas.draw()
        self.fig2.set_size_inches(w/100, h/100, forward=True)
        self.bar_canvas.draw()
        if hasattr(self, 'fig3'):
            self.fig3.set_size_inches(w/100, h/100, forward=True)
            self.line_canvas1.draw()
        if hasattr(self, 'fig4'):
            self.fig4.set_size_inches(w/100, h/100, forward=True)
            self.line_canvas2.draw()
        if hasattr(self, 'fig5'):
            self.fig5.set_size_inches(w/100, h/100, forward=True)
            self.line_canvas3.draw()
        return super().resizeEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.type() == QEvent.Type.MouseButtonDblClick:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        super().mouseDoubleClickEvent(event)

    def _draw_pie(self, status_count, status_list):
        self.ax1.clear()
        self.ax1.pie(status_count, labels=status_list, autopct='%1.1f%%', startangle=90)
        self.ax1.set_title("订单状态分布")
        self.fig1.tight_layout()
        self.pie_canvas.draw()

    def _draw_bar(self, supplier_group):
        self.ax2.clear()
        top_suppliers = supplier_group.head(10)
        self.ax2.bar(range(len(top_suppliers.index)), top_suppliers['sum'])
        self.ax2.set_xticks(range(len(top_suppliers.index)))
        self.ax2.set_xticklabels(list(top_suppliers.index), rotation=45, ha='right')
        self.ax2.set_ylabel("金额(€)")
        self.ax2.set_title("供应商订单金额TOP10")
        self.fig2.tight_layout()
        self.bar_canvas.draw()

    def _draw_line(self, ax, series, title, xlabel, ylabel, color=None):
        ax.clear()
        ax.plot(series.index, series.values, marker='o', color=color if color else None)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis='x', rotation=45)
        ax.figure.tight_layout()
        ax.figure.canvas.draw()

    def _draw_multi_line(self, ax, df, title, xlabel, ylabel):
        ax.clear()
        for col in df.columns:
            ax.plot(df.index, df[col], marker='o', label=str(col))
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis='x', rotation=45)
        ax.legend()
        ax.figure.tight_layout()
        ax.figure.canvas.draw()

    def update_main_order_stats(self):
        main_nb = self.combo_main_order.currentText()
        if not main_nb:
            self.table_main_supplier.setRowCount(0)
            self.label_main_total.setText("")
            self.label_total.setText("")
            return
        from data import purchase_orders
        # 过滤该主订单下所有子订单
        sub_orders = [po for po in purchase_orders if str(po.get("Order Nb", "")).startswith(main_nb + "_") and main_nb != "TEST"]
        # 按供应商分组统计
        supplier_stats = {}
        main_total_exw = 0.0
        main_total_wholesale = 0.0
        main_total_profit = 0.0
        
        for po in sub_orders:
            supplier = po.get("Supplier", "")
            try:
                qty_cs = float(po.get("QUANTITY CS", 0))
            except Exception:
                qty_cs = 0.0
            try:
                btl_per_cs = float(po.get("BTL PER CS", 0))
            except Exception:
                btl_per_cs = 0.0
            try:
                exw = float(po.get("EXW EURO", 0))
            except Exception:
                exw = 0.0
            try:
                wholesale_btl = float(po.get("WHOLESALE BTL", 0))
            except Exception:
                wholesale_btl = 0.0
            try:
                profit_total = float(po.get("PROFIT TOTAL", 0))
            except Exception:
                profit_total = 0.0
                
            exw_total = qty_cs * btl_per_cs * exw
            wholesale_total = qty_cs * btl_per_cs * wholesale_btl
            
            main_total_exw += exw_total
            main_total_wholesale += wholesale_total
            main_total_profit += profit_total  # 这里直接累加每个子订单的PROFIT TOTAL
            
            if supplier not in supplier_stats:
                supplier_stats[supplier] = {"exw": 0.0, "cs": 0.0, "bt": 0.0, "sold_bt": 0.0, "sold_amount": 0.0}
            supplier_stats[supplier]["exw"] += exw_total
            supplier_stats[supplier]["cs"] += qty_cs
            supplier_stats[supplier]["bt"] += qty_cs * btl_per_cs
            
        # 计算销售信息
        self.calculate_sales_info(main_nb, supplier_stats)
        
        # 填充表格
        self.table_main_supplier.setRowCount(len(supplier_stats))
        for row, (supplier, stat) in enumerate(supplier_stats.items()):
            self.table_main_supplier.setItem(row, 0, QTableWidgetItem(str(supplier)))
            self.table_main_supplier.setItem(row, 1, QTableWidgetItem(f"{stat['exw']:.2f}"))
            self.table_main_supplier.setItem(row, 2, QTableWidgetItem(f"{stat['cs']:.2f}"))
            self.table_main_supplier.setItem(row, 3, QTableWidgetItem(f"{stat['bt']:.2f}"))
            self.table_main_supplier.setItem(row, 4, QTableWidgetItem(f"{stat['sold_bt']:.0f}"))
            self.table_main_supplier.setItem(row, 5, QTableWidgetItem(f"{stat['sold_amount']:.2f}"))
        self.table_main_supplier.resizeColumnsToContents()
        self.label_main_total.setText(f"本主订单EXW总价：{main_total_exw:.2f} €    总批发价：{main_total_wholesale:.2f} €    总利润：{main_total_profit:.2f} €")
        # 运费
        def safe_float(val):
            try:
                return float(val)
            except Exception:
                return 0.0
        air = safe_float(self.input_air.text())
        airport = safe_float(self.input_airport.text())
        inbond = safe_float(self.input_inbond.text())
        total = main_total_exw + air + airport + inbond
        self.label_total.setText(f"TOTAL（含运费）：{total:.2f} €")
        # 可扩展：保存运费数据
        self._main_order_freight[main_nb] = {"air": air, "airport": airport, "inbond": inbond}

    def calculate_sales_info(self, main_nb, supplier_stats):
        """计算销售信息"""
        from data import purchase_orders
        
        # 查找该主订单相关的售出订单
        sale_orders = [po for po in purchase_orders if po.get('Original Order Nb', '').startswith(main_nb + '_')]
        
        for sale_order in sale_orders:
            supplier = sale_order.get('Supplier', '')
            if supplier in supplier_stats:
                try:
                    sold_bt = float(sale_order.get('QUANTITY BTL', 0))
                    sold_amount = float(sale_order.get('TOTAL AMOUNT EURO', 0))
                    
                    supplier_stats[supplier]['sold_bt'] += sold_bt
                    supplier_stats[supplier]['sold_amount'] += sold_amount
                except (ValueError, TypeError):
                    continue

    def open_trend_analysis_window(self):
        if self.trend_analysis_window is None:
            self.trend_analysis_window = TrendAnalysisWindow(self)
        self.trend_analysis_window.show()

class PurchaseOrderDashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("采购订单仪表盘")
        self.setGeometry(150, 150, 1200, 700)
        self.order_details_window = None
        self.order_statistics_window = None
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(splitter)
        # 左侧主订单表格
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        btn_layout = QHBoxLayout()
        self.btn_order_details = QPushButton("采购订单管理")
        self.btn_order_details.clicked.connect(self.open_order_details_window)
        btn_layout.addWidget(self.btn_order_details)
        self.btn_order_statistics = QPushButton("订单统计")
        self.btn_order_statistics.clicked.connect(self.open_order_statistics_window)
        btn_layout.addWidget(self.btn_order_statistics)
        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)
        self.table_main_orders = QTableWidget()
        self.table_main_orders.setColumnCount(3)
        self.table_main_orders.setHorizontalHeaderLabels(["主订单号", "订单状态", "订单总货值(€)"])
        self.table_main_orders.verticalHeader().setVisible(False)
        self.table_main_orders.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_main_orders.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_main_orders.itemSelectionChanged.connect(self.on_main_order_selected)
        self.table_main_orders.horizontalHeader().sectionResized.connect(self.save_main_orders_col_widths)
        left_layout.addWidget(self.table_main_orders)
        splitter.addWidget(left_widget)
        # 右侧整体widget
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        sub_btn_layout = QHBoxLayout()
        self.btn_batch_status = QPushButton("订单状态批量修改")
        self.btn_batch_status.clicked.connect(self.batch_update_status)
        sub_btn_layout.addWidget(self.btn_batch_status)
        self.btn_material_review = QPushButton("材料审核")
        self.btn_material_review.clicked.connect(self.open_material_review_dialog)
        sub_btn_layout.addWidget(self.btn_material_review)
        sub_btn_layout.addStretch()
        right_layout.addLayout(sub_btn_layout)
        self.table_sub_orders = QTableWidget()
        self.table_sub_orders.setColumnCount(7)
        self.table_sub_orders.setHorizontalHeaderLabels(["子订单号", "酒品名称", "数量", "订单状态", "小计(€)", "审核状态", "追踪"])
        self.table_sub_orders.verticalHeader().setVisible(False)
        self.table_sub_orders.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_sub_orders.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_sub_orders.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_sub_orders.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table_sub_orders.horizontalHeader().sectionResized.connect(self.save_sub_orders_col_widths)
        self.table_sub_orders.installEventFilter(self)
        right_layout.addWidget(self.table_sub_orders)
        self.label_stats = QLabel()
        right_layout.addWidget(self.label_stats)
        splitter.addWidget(right_widget)
        self._splitter = splitter
        self._load_splitter_ratio()
        splitter.splitterMoved.connect(self._save_splitter_ratio)
        self.refresh_main_orders()
        # 恢复主订单表格列宽
        self.restore_main_orders_col_widths()

    def showEvent(self, event):
        super().showEvent(event)
        # 恢复窗口大小和位置
        config = load_dashboard_config()
        geo = config.get('dashboard_geometry', None)
        if geo:
            try:
                self.setGeometry(*geo)
            except Exception:
                pass

    def closeEvent(self, event):
        # 保存窗口大小和位置
        config = load_dashboard_config()
        rect = self.geometry()
        config['dashboard_geometry'] = [rect.x(), rect.y(), rect.width(), rect.height()]
        save_dashboard_config(config)
        super().closeEvent(event)

    def save_main_orders_col_widths(self):
        config = load_dashboard_config()
        widths = [self.table_main_orders.columnWidth(i) for i in range(self.table_main_orders.columnCount())]
        config['main_orders_col_widths'] = widths
        save_dashboard_config(config)
    def restore_main_orders_col_widths(self):
        config = load_dashboard_config()
        widths = config.get('main_orders_col_widths', None)
        if widths:
            for i, w in enumerate(widths):
                if i < self.table_main_orders.columnCount():
                    self.table_main_orders.setColumnWidth(i, w)
    def save_sub_orders_col_widths(self):
        config = load_dashboard_config()
        main_nb = self.get_current_main_order_nb()
        if not main_nb:
            return
        widths = [self.table_sub_orders.columnWidth(i) for i in range(self.table_sub_orders.columnCount())]
        sub_orders_col_widths = config.get('sub_orders_col_widths', {})
        # 兼容旧数据：如果是list，自动迁移为dict
        if isinstance(sub_orders_col_widths, list):
            sub_orders_col_widths = {}
        sub_orders_col_widths[main_nb] = widths
        config['sub_orders_col_widths'] = sub_orders_col_widths
        save_dashboard_config(config)
    def restore_sub_orders_col_widths(self, main_nb):
        config = load_dashboard_config()
        sub_orders_col_widths = config.get('sub_orders_col_widths', {})
        # 兼容旧数据：如果是list，自动迁移为dict
        if isinstance(sub_orders_col_widths, list):
            sub_orders_col_widths = {}
        widths = sub_orders_col_widths.get(main_nb, None)
        if widths:
            for i, w in enumerate(widths):
                if i < self.table_sub_orders.columnCount():
                    self.table_sub_orders.setColumnWidth(i, w)
    def get_current_main_order_nb(self):
        row = self.table_main_orders.currentRow()
        if row < 0:
            return None
        item = self.table_main_orders.item(row, 0)
        if not item:
            return None
        return item.text()
    def open_order_details_window(self):
        if self.order_details_window is None:
            self.order_details_window = OrderDetailsWindow()
        else:
            self.order_details_window.update_order_table()
        self.order_details_window.show()

    def open_order_statistics_window(self):
        if self.order_statistics_window is None:
            self.order_statistics_window = OrderStatisticsWindow(self)
        self.order_statistics_window.show()

    def open_material_review_dialog(self):
        # 只对当前主订单号下的子订单进行材料审查
        if not hasattr(self, '_current_sub_orders') or not self._current_sub_orders:
            QMessageBox.information(self, "提示", "请先选择主订单号。")
            return
        dlg = MaterialReviewDialog(self._current_sub_orders, self)
        dlg.exec()
        # 审核内容变更后，关闭弹窗时刷新子订单表格
        self.on_main_order_selected()

    def _load_column_widths(self):
        import json
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            widths = config.get("sub_orders_col_widths", None)
            if widths:
                for i, w in enumerate(widths):
                    self.table_sub_orders.setColumnWidth(i, w)
        except Exception:
            pass

    def on_section_resized(self, idx, oldw, neww):
        import json
        widths = [self.table_sub_orders.columnWidth(i) for i in range(self.table_sub_orders.columnCount())]
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}
        config["sub_orders_col_widths"] = widths
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f)

    def refresh_main_orders(self):
        # 统计所有主订单号（如 AVN202412）
        main_orders = {}
        for po in purchase_orders:
            order_nb = po.get("Order Nb", "")
            if not order_nb:
                continue
            main_nb = order_nb.split("_")[0]
            if main_nb == "TEST":
                continue  # 彻底过滤TEST主订单
            if main_nb not in main_orders:
                main_orders[main_nb] = []
            main_orders[main_nb].append(po)
        self._main_orders = main_orders
        main_order_status = load_main_order_status()
        self.table_main_orders.setRowCount(len(main_orders))
        for row, (main_nb, sub_orders) in enumerate(main_orders.items()):
            # 订单总货值：所有子订单的金额合计
            total_value = 0.0
            for po in sub_orders:
                try:
                    qty = float(po.get("QUANTITY CS", 0))
                except Exception:
                    qty = 0.0
                try:
                    btl = float(po.get("BTL PER CS", 0))
                except Exception:
                    btl = 0.0
                try:
                    price = float(po.get("EXW EURO", 0))
                except Exception:
                    price = 0.0
                total_value += qty * btl * price
            # 主订单状态从 JSON 读取
            main_status = main_order_status.get(main_nb, "未下单")
            self.table_main_orders.setItem(row, 0, QTableWidgetItem(main_nb))
            self.table_main_orders.setItem(row, 1, QTableWidgetItem(main_status))
            self.table_main_orders.setItem(row, 2, QTableWidgetItem(f"{total_value:.2f}"))
        self.table_main_orders.resizeColumnsToContents()

    def _calc_main_order_status(self, status_count, total):
        # 优先级从高到低
        if status_count["未下单"] == total:
            return "未下单"
        if status_count["退货"] == total:
            return "已退货"
        if 0 < status_count["退货"] < total:
            return "部分退货"
        if status_count["已完成"] == total:
            return "已完成"
        if 0 < status_count["已完成"] < total:
            return "部分完成"
        if status_count["已到货"] == total:
            return "已到货"
        if 0 < status_count["已到货"] < total:
            return "部分到货"
        if status_count["已发货"] == total:
            return "已发货"
        if 0 < status_count["已发货"] < total:
            return "部分发货"
        if status_count["已下单"] == total:
            return "已下单"
        if 0 < status_count["已下单"] < total:
            return "部分下单"
        return "未下单"

    def on_main_order_selected(self):
        selected = self.table_main_orders.selectedItems()
        if not selected:
            self.table_sub_orders.setRowCount(0)
            self.label_stats.setText("")
            return
        main_nb = self.table_main_orders.item(self.table_main_orders.currentRow(), 0).text()
        # 找到所有属于该主订单的子订单
        sub_orders = [po for po in purchase_orders if po.get("Order Nb", "").startswith(main_nb + "_") and main_nb != "TEST"]
        self._current_sub_orders = sub_orders
        # 读取材料审查项目和数据
        config = load_dashboard_config()
        review_items = config.get('material_review_items', ["Sticker", "发票", "照片", "详细信息"])
        material_review = config.get('material_review', {})
        # 统计每个项目的审查情况
        status_summary = []
        for item in review_items:
            vals = [material_review.get(po.get("Order Nb", ""), {}).get(item, "否") for po in sub_orders]
            if all(v == "已审查" for v in vals) and vals:
                status_summary.append(item)
            elif any(v == "已审查" for v in vals) and any(v == "否" for v in vals):
                status_summary.append(f"部分审查（{item}）")
        status_str = ", ".join(status_summary) if status_summary else "未审查"
        # 设置表格列数和表头
        self.table_sub_orders.setColumnCount(7)
        self.table_sub_orders.setHorizontalHeaderLabels(["子订单号", "酒品名称", "数量", "订单状态", "小计(€)", "审核状态", "追踪"])
        self.table_sub_orders.setRowCount(len(sub_orders))
        for row, po in enumerate(sub_orders):
            # 子订单号
            item_order_nb = QTableWidgetItem(po.get("Order Nb", ""))
            item_order_nb.setFlags(item_order_nb.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_sub_orders.setItem(row, 0, item_order_nb)
            # 酒品名称
            item_name = QTableWidgetItem(po.get("ITEM Name", ""))
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_sub_orders.setItem(row, 1, item_name)
            # 数量
            qty = po.get("QUANTITY CS", 0)
            item_qty = QTableWidgetItem(str(qty))
            item_qty.setFlags(item_qty.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_sub_orders.setItem(row, 2, item_qty)
            # 状态下拉
            combo = QComboBox()
            combo.addItems(ORDER_STATUS_LIST)
            current_status = po.get("Order Step", ORDER_STATUS_LIST[0])
            idx = combo.findText(current_status)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            combo.currentIndexChanged.connect(lambda idx, r=row, po=po, cb=combo: self.on_status_changed(r, po, cb))
            combo.installEventFilter(self)
            self.table_sub_orders.setCellWidget(row, 3, combo)
            # 小计
            try:
                qtyf = float(po.get("QUANTITY CS", 0))
            except Exception:
                qtyf = 0.0
            try:
                btl = float(po.get("BTL PER CS", 0))
            except Exception:
                btl = 0.0
            try:
                price = float(po.get("EXW EURO", 0))
            except Exception:
                price = 0.0
            subtotal = qtyf * btl * price
            item_subtotal = QTableWidgetItem(f"{subtotal:.2f}")
            item_subtotal.setFlags(item_subtotal.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_sub_orders.setItem(row, 4, item_subtotal)
            # 审核状态（只显示该子订单自己的材料审查状态，去掉部分审查逻辑）
            review_data = material_review.get(po.get("Order Nb", ""), {})
            checked_items = [item for item in review_items if review_data.get(item, "否") == "已审查"]
            if checked_items:
                status_str = ", ".join(checked_items)
            else:
                status_str = "未审查"
            item_review = QTableWidgetItem(status_str)
            item_review.setFlags(item_review.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_sub_orders.setItem(row, 5, item_review)
            # 追踪按钮
            btn = QPushButton("追踪")
            btn.clicked.connect(lambda _, po=po: self.show_status_history(po))
            self.table_sub_orders.setCellWidget(row, 6, btn)
        # 统计信息
        status_count = {s: 0 for s in ORDER_STATUS_LIST}
        total_value = 0.0
        total_qty = 0
        arrived_qty = 0
        for po in sub_orders:
            status = po.get("Order Step", ORDER_STATUS_LIST[0])
            if status in status_count:
                status_count[status] += 1
            try:
                qtyf = float(po.get("QUANTITY CS", 0))
                if status == "已到货":
                    arrived_qty += int(qtyf)
                total_qty += int(qtyf)
            except Exception:
                pass
            try:
                btl = float(po.get("BTL PER CS", 0))
            except Exception:
                btl = 0.0
            try:
                price = float(po.get("EXW EURO", 0))
            except Exception:
                price = 0.0
            total_value += float(po.get("QUANTITY CS", 0)) * btl * price
        total = len(sub_orders)
        arrived = status_count.get("已到货", 0)
        finished = status_count.get("已完成", 0)
        rate = f"{(arrived+finished)/total*100:.1f}%" if total else "0%"
        self.label_stats.setText(f"子订单数: {total}，已到货/完成: {arrived+finished}，到货率: {rate}，总金额: {total_value:.2f} €")
        # 最后恢复列宽
        self.restore_sub_orders_col_widths(main_nb)

    def update_main_order_status(self, main_nb):
        # 统计该主订单下所有子订单的状态，计算主订单状态
        sub_orders = [po for po in purchase_orders if str(po.get("Order Nb", "")).startswith(main_nb + "_") and main_nb != "TEST"]
        status_count = {s: 0 for s in ORDER_STATUS_LIST}
        total = len(sub_orders)
        for po in sub_orders:
            status = po.get("Order Step", ORDER_STATUS_LIST[0])
            if status in status_count:
                status_count[status] += 1
        # 复用原有主订单状态联动逻辑
        main_status = self._calc_main_order_status(status_count, total)
        # 写入 JSON
        main_order_status = load_main_order_status()
        main_order_status[main_nb] = main_status
        save_main_order_status(main_order_status)

    def on_status_changed(self, row, po, combo):
        old_status = po.get("Order Step", ORDER_STATUS_LIST[0])
        new_status = combo.currentText()
        if old_status == new_status:
            return
        # 记录历史
        if "status_history" not in po or not isinstance(po["status_history"], list):
            po["status_history"] = []
        po["status_history"].append({
            "from": old_status,
            "to": new_status,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": os.getenv("USERNAME") or "系统"
        })
        po["Order Step"] = new_status
        if "material_review" in po:
            del po["material_review"]
        if "status_history" in po:
            del po["status_history"]
        save_purchase_order_to_db(po)
        # 自动更新主订单状态到 JSON
        main_nb = po.get("Order Nb", "").split("_")[0]
        self.update_main_order_status(main_nb)
        self.on_main_order_selected()  # 刷新子订单明细
        self.refresh_main_orders()     # 新增，刷新主订单表格

    def on_material_review_changed(self, order_nb, item, combo):
        material_review = load_material_review()
        if order_nb not in material_review:
            material_review[order_nb] = {k: "" for k in MATERIAL_REVIEW_ITEMS}
        material_review[order_nb][item] = combo.currentText()
        save_material_review(material_review)

    def show_status_history(self, po):
        history = po.get("status_history", [])
        dlg = StatusHistoryDialog(history, self)
        dlg.exec()

    def batch_update_status(self):
        selected_rows = set(idx.row() for idx in self.table_sub_orders.selectionModel().selectedRows())
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先在子订单表格中选择要批量修改的行。")
            return
        dlg = BatchStatusDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_status = dlg.get_status()
            for row in selected_rows:
                if row < 0 or row >= len(self._current_sub_orders):
                    continue
                po = self._current_sub_orders[row]
                old_status = po.get("Order Step", ORDER_STATUS_LIST[0])
                if old_status == new_status:
                    continue
                # 记录历史
                if "status_history" not in po or not isinstance(po["status_history"], list):
                    po["status_history"] = []
                po["status_history"].append({
                    "from": old_status,
                    "to": new_status,
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user": os.getenv("USERNAME") or "系统"
                })
                po["Order Step"] = new_status
                if "material_review" in po:
                    del po["material_review"]
                if "status_history" in po:
                    del po["status_history"]
                save_purchase_order_to_db(po)
                # 自动更新主订单状态到 JSON
                main_nb = po.get("Order Nb", "").split("_")[0]
                self.update_main_order_status(main_nb)
            self.on_main_order_selected()
            self.refresh_main_orders()

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent, Qt
        if obj == self.table_sub_orders:
            # 1. 屏蔽订单状态列滚轮导致的整行选中
            if event.type() == QEvent.Type.Wheel:
                index = self.table_sub_orders.indexAt(event.position().toPoint())
                if index.isValid() and index.column() == 3:
                    return True  # 屏蔽订单状态列的滚轮
            # 2. 多行选中时鼠标左键点击单元格只选中当前行
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self.table_sub_orders.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                self.table_sub_orders.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
                index = self.table_sub_orders.indexAt(event.position().toPoint())
                if index.isValid():
                    selected_rows = self.table_sub_orders.selectionModel().selectedRows()
                    if len(selected_rows) > 1:
                        self.table_sub_orders.clearSelection()
                        self.table_sub_orders.selectRow(index.row())
                        return True  # 阻止后续事件，防止再次多选
            # 3. 双击非下拉/按钮单元格时只选中该单元格且支持复制
            if event.type() == QEvent.Type.MouseButtonDblClick and event.button() == Qt.MouseButton.LeftButton:
                index = self.table_sub_orders.indexAt(event.position().toPoint())
                if index.isValid() and index.column() in [0,1,2,4]:
                    self.table_sub_orders.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
                    self.table_sub_orders.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
                    self.table_sub_orders.clearSelection()
                    self.table_sub_orders.setCurrentCell(index.row(), index.column())
                    self.table_sub_orders.item(index.row(), index.column()).setSelected(True)
                    self.table_sub_orders.viewport().update()
                    return True  # 不再自动恢复
        # QComboBox滚轮屏蔽
        if event.type() == QEvent.Type.Wheel and isinstance(obj, QComboBox):
            return True
        return super().eventFilter(obj, event)

    def _load_splitter_ratio(self):
        try:
            with open(SPLITTER_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            ratio = config.get("splitter_ratio", [400, 800])
            self._splitter.setSizes(ratio)
        except Exception:
            self._splitter.setSizes([400, 800])

    def _save_splitter_ratio(self, pos, index):
        sizes = self._splitter.sizes()
        try:
            with open(SPLITTER_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}
        config["splitter_ratio"] = sizes
        with open(SPLITTER_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f) 

# 新增趋势分析弹窗类
class TrendAnalysisWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("趋势分析")
        self.setGeometry(350, 220, 1200, 800)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)
        self.setMinimumSize(800, 500)
        layout = QVBoxLayout()
        self.setLayout(layout)
        from data import purchase_orders
        df = pd.DataFrame(purchase_orders)
        df['main_order'] = df['Order Nb'].astype(str).str.split('_').str[0]
        df = df[df['main_order'] != 'TEST']  # 彻底过滤TEST主订单
        df['date'] = pd.to_datetime(df.get('date', pd.NaT), errors='coerce')
        main_order_dates = df.groupby('main_order')['date'].min().sort_values()
        main_order_sorted = main_order_dates.index.tolist()
        def calc_amount(row):
            try:
                return float(row.get("QUANTITY CS", 0)) * float(row.get("BTL PER CS", 0)) * float(row.get("EXW EURO", 0))
            except Exception:
                return 0.0
        df["金额"] = df.apply(calc_amount, axis=1)
        def calc_bt(row):
            try:
                return float(row.get("QUANTITY CS", 0)) * float(row.get("BTL PER CS", 0))
            except Exception:
                return 0.0
        df['瓶数'] = df.apply(calc_bt, axis=1)
        main_order_amount = df.groupby('main_order')['金额'].sum().reindex(main_order_sorted, fill_value=0)
        main_order_bt = df.groupby('main_order')['瓶数'].sum().reindex(main_order_sorted, fill_value=0)
        supplier_bt = df.groupby(['main_order', 'Supplier'])['瓶数'].sum().unstack(fill_value=0).reindex(main_order_sorted, fill_value=0)
        # 滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_content.setLayout(scroll_layout)
        # 金额趋势
        self.fig3 = Figure(figsize=(max(8, len(main_order_sorted)*0.8), 3))
        self.ax3 = self.fig3.add_subplot(111)
        self.line_canvas1 = FigureCanvas(self.fig3)
        self._draw_line(self.ax3, main_order_amount, "主订单金额趋势", "主订单号", "金额(€)")
        scroll_layout.addWidget(self.line_canvas1)
        # 瓶数趋势
        self.fig4 = Figure(figsize=(max(8, len(main_order_sorted)*0.8), 3))
        self.ax4 = self.fig4.add_subplot(111)
        self.line_canvas2 = FigureCanvas(self.fig4)
        self._draw_line(self.ax4, main_order_bt, "主订单采购瓶数趋势", "主订单号", "瓶数", color='orange')
        scroll_layout.addWidget(self.line_canvas2)
        # 供应商分线图
        self.fig5 = Figure(figsize=(max(8, len(main_order_sorted)*0.8), 3))
        self.ax5 = self.fig5.add_subplot(111)
        self.line_canvas3 = FigureCanvas(self.fig5)
        self._draw_multi_line(self.ax5, supplier_bt, "各供应商采购瓶数趋势", "主订单号", "瓶数")
        scroll_layout.addWidget(self.line_canvas3)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    def mouseDoubleClickEvent(self, event):
        if event.type() == QEvent.Type.MouseButtonDblClick:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        super().mouseDoubleClickEvent(event)
    def _draw_line(self, ax, series, title, xlabel, ylabel, color=None):
        ax.clear()
        ax.plot(series.index, series.values, marker='o', color=color if color else None)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis='x', rotation=45)
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
    def _draw_multi_line(self, ax, df, title, xlabel, ylabel):
        ax.clear()
        for col in df.columns:
            ax.plot(df.index, df[col], marker='o', label=str(col))
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis='x', rotation=45)
        ax.legend()
        ax.figure.tight_layout()
        ax.figure.canvas.draw() 

# 新增材料审查弹窗类
class MaterialReviewDialog(QDialog):
    def __init__(self, sub_orders, parent=None):
        super().__init__(parent)
        self.setWindowTitle("材料审核")
        self.setGeometry(400, 200, 900, 600)
        layout = QVBoxLayout()
        self.setLayout(layout)
        # 读取审查项目
        self.config = load_dashboard_config()
        self.review_items = self.config.get('material_review_items', ["Sticker", "发票", "照片", "详细信息"])
        # 只显示传入的子订单号
        self.sub_order_nbs = [po.get("Order Nb", "") for po in sub_orders]
        # 读取材料审查数据
        self.material_review = self.config.get('material_review', {})
        # 批量修改区域
        batch_layout = QHBoxLayout()
        self.combo_batch_item = QComboBox()
        self.combo_batch_item.addItems(self.review_items)
        batch_layout.addWidget(QLabel("批量修改项目："))
        batch_layout.addWidget(self.combo_batch_item)
        self.combo_batch_status = QComboBox()
        self.combo_batch_status.addItems(["否", "已审查"])
        batch_layout.addWidget(QLabel("目标状态："))
        batch_layout.addWidget(self.combo_batch_status)
        btn_batch_apply = QPushButton("批量修改")
        btn_batch_apply.clicked.connect(self.apply_batch_update)
        batch_layout.addWidget(btn_batch_apply)
        # 修改审查项目按钮（小号，放右侧）
        btn_modify_items = QPushButton("修改审查项目")
        btn_modify_items.setFixedWidth(80)
        btn_modify_items.clicked.connect(self.modify_review_items)
        batch_layout.addWidget(btn_modify_items)
        batch_layout.addStretch()
        layout.addLayout(batch_layout)
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.review_items) + 1)
        self.table.setRowCount(len(self.sub_order_nbs))
        self.table.setHorizontalHeaderLabels(["子订单号"] + self.review_items)
        self._refresh_table()
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)
        # 关闭按钮
        btns = QHBoxLayout()
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(btn_close)
        layout.addLayout(btns)
    def _refresh_table(self):
        self.table.setColumnCount(len(self.review_items) + 1)
        self.table.setHorizontalHeaderLabels(["子订单号"] + self.review_items)
        for row, order_nb in enumerate(self.sub_order_nbs):
            item_nb = QTableWidgetItem(order_nb)
            item_nb.setFlags(item_nb.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item_nb)
            review_data = self.material_review.get(order_nb, {k: "否" for k in self.review_items})
            for col, item in enumerate(self.review_items):
                combo = QComboBox()
                combo.addItems(["否", "已审查"])
                val = review_data.get(item, "否")
                idx = combo.findText(val)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                combo.currentIndexChanged.connect(lambda idx, order_nb=order_nb, item=item, cb=combo: self.on_review_changed(order_nb, item, cb))
                self.table.setCellWidget(row, col + 1, combo)
    def on_review_changed(self, order_nb, item, combo):
        config = load_dashboard_config()
        material_review = config.get('material_review', {})
        if order_nb not in material_review:
            material_review[order_nb] = {}
        material_review[order_nb][item] = combo.currentText()
        config['material_review'] = material_review
        save_dashboard_config(config)
        self.material_review = material_review
    def apply_batch_update(self):
        item = self.combo_batch_item.currentText()
        status = self.combo_batch_status.currentText()
        config = load_dashboard_config()
        material_review = config.get('material_review', {})
        for order_nb in self.sub_order_nbs:
            if order_nb not in material_review:
                material_review[order_nb] = {}
            material_review[order_nb][item] = status
        config['material_review'] = material_review
        save_dashboard_config(config)
        self.material_review = material_review
        self._refresh_table()
    def modify_review_items(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("修改审查项目")
        dlg.setGeometry(500, 300, 400, 350)
        vbox = QVBoxLayout()
        dlg.setLayout(vbox)
        # 当前项目列表
        list_widget = QListWidget()
        for item in self.review_items:
            lw_item = QListWidgetItem(item)
            lw_item.setFlags(lw_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            lw_item.setCheckState(Qt.CheckState.Unchecked)
            list_widget.addItem(lw_item)
        vbox.addWidget(QLabel("勾选要删除的项目："))
        vbox.addWidget(list_widget)
        # 添加新项目
        hbox_add = QHBoxLayout()
        input_new = QLineEdit()
        input_new.setPlaceholderText("新项目名称")
        btn_add = QPushButton("添加")
        hbox_add.addWidget(input_new)
        hbox_add.addWidget(btn_add)
        vbox.addLayout(hbox_add)
        # 按钮区
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        vbox.addWidget(btn_box)
        # 添加新项目逻辑
        def add_new_item():
            new_item = input_new.text().strip()
            if new_item and new_item not in self.review_items:
                lw_item = QListWidgetItem(new_item)
                lw_item.setFlags(lw_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                lw_item.setCheckState(Qt.CheckState.Unchecked)
                list_widget.addItem(lw_item)
                self.review_items.append(new_item)
                input_new.clear()
        btn_add.clicked.connect(add_new_item)
        # 确认/取消逻辑
        def on_accept():
            # 删除勾选的项目
            to_delete = [list_widget.item(i).text() for i in range(list_widget.count()) if list_widget.item(i).checkState() == Qt.CheckState.Checked]
            new_items = [list_widget.item(i).text() for i in range(list_widget.count()) if list_widget.item(i).checkState() == Qt.CheckState.Unchecked]
            if not new_items:
                QMessageBox.warning(dlg, "操作无效", "至少保留一个审查项目！")
                return
            # 更新 config
            config = load_dashboard_config()
            config['material_review_items'] = new_items
            # 更新所有子订单的材料审查数据结构
            material_review = config.get('material_review', {})
            for order_nb in material_review:
                # 删除被移除的项目
                for d in to_delete:
                    if d in material_review[order_nb]:
                        del material_review[order_nb][d]
                # 新增的项目补“否”
                for ni in new_items:
                    if ni not in material_review[order_nb]:
                        material_review[order_nb][ni] = "否"
            config['material_review'] = material_review
            save_dashboard_config(config)
            self.review_items = new_items
            self.material_review = material_review
            self.combo_batch_item.clear()
            self.combo_batch_item.addItems(self.review_items)
            self._refresh_table()
            dlg.accept()
        btn_box.accepted.connect(on_accept)
        btn_box.rejected.connect(dlg.reject)
        dlg.exec()

# 工具函数：加载和保存材料审查信息、主订单状态

def load_dashboard_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception:
        return {}

def save_dashboard_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'保存 order_dashboard_config.json 失败: {e}')

def load_main_order_status():
    config = load_dashboard_config()
    return config.get('main_order_status', {})

def save_main_order_status(main_order_status):
    config = load_dashboard_config()
    config['main_order_status'] = main_order_status
    save_dashboard_config(config)

def load_material_review():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('material_review', {})
    except Exception:
        return {}

def save_material_review(material_review):
    try:
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            config = {}
        config['material_review'] = material_review
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'保存材料审查信息失败: {e}') 