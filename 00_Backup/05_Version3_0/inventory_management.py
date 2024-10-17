# inventory_management.py
import sys
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QMessageBox, QInputDialog, QLineEdit
)
from PyQt6.QtCore import Qt
from data import orders, display_fields, data_manager

class InventoryManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("库存管理")
        self.setGeometry(300, 300, 1400, 800)

        # 首先初始化过滤条件
        self.filters = {
            'Supplier': None,
            'allocation': None,
            'ITEM Name': None,
        }

        # 记录被过滤的列
        self.filtered_columns = set()

        self.layout_main = QVBoxLayout()

        # 库存展示区域
        self.inventory_table = QTableWidget()
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.inventory_table.verticalHeader().setVisible(False)
        self.inventory_table.horizontalHeader().setStretchLastSection(True)
        self.inventory_table.setWordWrap(True)
        self.inventory_table.resizeColumnsToContents()

        # 添加过滤器
        self.add_filters_to_headers()

        self.layout_main.addWidget(self.inventory_table)

        # 显示方式下拉菜单
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["按单品", "按供应商", "按客户", "按时间"])

        # 加载上次选择的显示方式
        self.load_display_mode()

        # 在加载显示模式后再连接信号
        self.display_mode_combo.currentTextChanged.connect(self.update_inventory_table)

        # 添加“重置筛选”按钮
        layout_top = QHBoxLayout()
        layout_top.addWidget(QLabel("显示方式："))
        layout_top.addWidget(self.display_mode_combo)
        reset_filters_button = QPushButton("重置筛选")
        reset_filters_button.clicked.connect(self.reset_filters)
        layout_top.addWidget(reset_filters_button)
        self.layout_main.addLayout(layout_top)

        self.setLayout(self.layout_main)

        # 连接数据变化信号到更新方法
        data_manager.data_changed.connect(self.update_inventory_table)

        # 更新库存表格
        self.update_inventory_table()

    def add_filters_to_headers(self):
        header = self.inventory_table.horizontalHeader()
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.handle_header_clicked)

    def handle_header_clicked(self, index):
        field_name = display_fields[index][1]
        if field_name in ["Supplier", "allocation", "ITEM Name"]:
            self.show_filter_dialog(field_name)

    def show_filter_dialog(self, field_name):
        unique_values = set(order.get(field_name, "") for order in orders)
        if field_name == "ITEM Name":
            # 对于 ITEM Name，使用输入框
            text, ok = QInputDialog.getText(self, "筛选 ITEM Name", "请输入产品名称：", text=self.filters.get(field_name) or "")
            if ok:
                text = text.strip()
                if text:
                    self.filters[field_name] = text
                    self.filtered_columns.add(field_name)
                else:
                    self.filters[field_name] = None
                    self.filtered_columns.discard(field_name)
        else:
            # 对于 Supplier 和 allocation，使用单选列表
            items = ["（全部）"] + sorted(unique_values)
            current_value = self.filters.get(field_name) or "（全部）"
            index = items.index(current_value) if current_value in items else 0
            selected_item, ok = QInputDialog.getItem(
                self, f"筛选 {field_name}", f"请选择要显示的{field_name}：",
                items, index, False
            )
            if ok:
                if selected_item == "（全部）":
                    self.filters[field_name] = None
                    self.filtered_columns.discard(field_name)
                else:
                    self.filters[field_name] = selected_item
                    self.filtered_columns.add(field_name)
        self.update_inventory_table()

    def update_inventory_table(self):
        try:
            display_mode = self.display_mode_combo.currentText()

            # 根据显示方式分组订单数据
            if display_mode == "按单品":
                key_field = "ITEM Name"
            elif display_mode == "按供应商":
                key_field = "Supplier"
            elif display_mode == "按客户":
                key_field = "allocation"
            elif display_mode == "按时间":
                key_field = "date"
            else:
                key_field = None

            # 应用过滤条件
            filtered_orders = self.apply_filters(orders)
            grouped_orders = self.group_orders_by_field(filtered_orders, key_field)

            # 设置表格列
            self.inventory_table.clear()
            headers = []
            for label, field in display_fields:
                if field in ["Supplier", "allocation", "ITEM Name"]:
                    # 始终在可过滤列上添加过滤器图标
                    if field in self.filtered_columns:
                        # 当应用了过滤器时，添加指示
                        headers.append(f"{label} (🔍✔)")
                    else:
                        headers.append(f"{label} (🔍)")
                else:
                    headers.append(label)
            self.inventory_table.setColumnCount(len(headers))
            self.inventory_table.setHorizontalHeaderLabels(headers)

            # 填充表格数据
            self.inventory_table.setRowCount(0)
            for group in grouped_orders:
                for order in group:
                    row = self.inventory_table.rowCount()
                    self.inventory_table.insertRow(row)
                    for col, (label_text, field_name) in enumerate(display_fields):
                        value = order.get(field_name, "")
                        item = QTableWidgetItem(str(value))
                        self.inventory_table.setItem(row, col, item)

            # 保存当前显示方式
            self.save_display_mode()
        except Exception as e:
            print(f"更新库存表格时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"更新库存表格时发生错误：{e}")

    def apply_filters(self, orders_list):
        filtered = []
        for order in orders_list:
            match = True
            for field, value in self.filters.items():
                if value:
                    if field == "ITEM Name":
                        if value.lower() not in order.get(field, "").lower():
                            match = False
                            break
                    else:
                        if order.get(field, "") != value:
                            match = False
                            break
            if match:
                filtered.append(order)
        return filtered

    def group_orders_by_field(self, orders_list, field_name):
        if not field_name:
            return [orders_list]

        grouped = {}
        for order in orders_list:
            key = order.get(field_name, "未定义")
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(order)

        # 按日期从新到旧排序
        for group in grouped.values():
            group.sort(key=lambda x: x.get('date', ''), reverse=True)

        return grouped.values()

    def reset_filters(self):
        self.filters = {
            'Supplier': None,
            'allocation': None,
            'ITEM Name': None,
        }
        self.filtered_columns.clear()
        self.update_inventory_table()

    def save_display_mode(self):
        with open('display_mode.cfg', 'w') as f:
            f.write(self.display_mode_combo.currentText())

    def load_display_mode(self):
        try:
            with open('display_mode.cfg', 'r') as f:
                mode = f.read().strip()
                index = self.display_mode_combo.findText(mode)
                if index >= 0:
                    self.display_mode_combo.blockSignals(True)
                    self.display_mode_combo.setCurrentIndex(index)
                    self.display_mode_combo.blockSignals(False)
        except FileNotFoundError:
            pass  # 如果配置文件不存在，使用默认值

    def closeEvent(self, event):
        # 保存显示模式
        self.save_display_mode()
        super().closeEvent(event)
