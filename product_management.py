# product_management.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QGridLayout, QComboBox
)
from PyQt6.QtCore import Qt
import datetime
import re

from data import (
    products, save_product_to_db, delete_product_from_db,
    load_products_from_db, data_manager, get_product_by_sku
)

class ProductManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("产品管理")
        self.setGeometry(200, 200, 800, 600)

        self.layout_main = QVBoxLayout()

        # 输入区域
        self.layout_inputs = QGridLayout()
        self.entries = {}

        fields = [
            ('SKU CLS', 'SKU_CLS'),
            ('ITEM Name', 'ITEM_Name'),
            ('Category', 'Category'),
            ('Size', 'Size'),
            ('ALC.', 'ALC'),
            ('BTL PER CS', 'BTL_PER_CS'),
            ('Supplier', 'Supplier'),
        ]

        for row, (label_text, field_name) in enumerate(fields):
            label = QLabel(label_text + ":")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            entry = QLineEdit()
            entry.setFixedWidth(300)
            entry.setStyleSheet("border: 1px solid lightgray;")
            self.entries[field_name] = entry
            self.layout_inputs.addWidget(label, row, 0)
            self.layout_inputs.addWidget(entry, row, 1)

        self.layout_main.addLayout(self.layout_inputs)

        # 按钮区域
        layout_buttons = QHBoxLayout()

        self.button_add = QPushButton("添加产品")
        self.button_add.clicked.connect(self.add_product)
        self.button_update = QPushButton("更新产品")
        self.button_update.clicked.connect(self.update_product)
        self.button_delete = QPushButton("删除产品")
        self.button_delete.clicked.connect(self.delete_product)

        layout_buttons.addWidget(self.button_add)
        layout_buttons.addWidget(self.button_update)
        layout_buttons.addWidget(self.button_delete)

        self.layout_main.addLayout(layout_buttons)

        # 添加排序和过滤区域
        control_layout = QHBoxLayout()

        # 排序选项
        sort_label = QLabel("排序规则:")
        self.sort_combo = QComboBox()
        # 定义产品管理的排序选项
        self.sort_combo.addItems(["按SKU CLS", "按产品名称", "按Supplier", "按BTL PER CS", "按创建日期"])
        self.sort_combo.currentIndexChanged.connect(self.update_product_table)

        control_layout.addWidget(sort_label)
        control_layout.addWidget(self.sort_combo)

        # 过滤选项
        filter_field_label = QLabel("过滤条件:")
        self.filter_field_combo = QComboBox()
        self.filter_field_combo.addItems(["按SKU CLS", "按产品名称", "按Supplier"])
        self.filter_field_combo.currentIndexChanged.connect(self.update_product_table)

        self.filter_field_input = QLineEdit()
        self.filter_field_input.setPlaceholderText("输入过滤内容(支持*通配符)")
        self.filter_field_input.textChanged.connect(self.update_product_table)
        self.filter_field_input.setFixedWidth(200)

        control_layout.addWidget(filter_field_label)
        control_layout.addWidget(self.filter_field_combo)
        control_layout.addWidget(self.filter_field_input)

        control_layout.addStretch(1)

        self.layout_main.addLayout(control_layout)

        # 产品列表显示区域
        self.product_table = QTableWidget()
        self.product_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.product_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.product_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.product_table.setColumnCount(8)
        self.product_table.setHorizontalHeaderLabels([
            'SKU CLS', 'ITEM Name', 'Category', 'Size', 'ALC.', 'BTL PER CS', 'Supplier', '创建日期'
        ])
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.horizontalHeader().setStretchLastSection(True)
        self.product_table.setWordWrap(True)
        self.product_table.resizeColumnsToContents()

        # 连接产品表格的选择信号到处理函数
        self.product_table.selectionModel().selectionChanged.connect(self.on_product_selected)

        self.layout_main.addWidget(self.product_table)

        self.setLayout(self.layout_main)

        # 加载产品数据
        load_products_from_db()
        self.update_product_table()

        # 连接数据变化信号到更新方法
        data_manager.products_changed.connect(self.update_product_table)

    def on_product_selected(self, selected, deselected):
        try:
            indexes = self.product_table.selectionModel().selectedRows()
            if indexes:
                index = indexes[0]
                row = index.row()
                # 根据当前显示的产品列表获取产品
                # 因为update_product_table会根据过滤排序产生一个局部列表，所以需要在方法中保留这个列表
                # 在这里我们再次调用 get_filtered_and_sorted_products 获取当前显示的列表
                displayed_products = self.get_filtered_and_sorted_products()
                product = displayed_products[row]

                for field_name, entry in self.entries.items():
                    value = product.get(field_name, "")
                    entry.setText(str(value))
            else:
                for entry in self.entries.values():
                    entry.clear()
        except Exception as e:
            print(f"处理产品选择时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"处理产品选择时发生错误：{e}")

    def get_filtered_and_sorted_products(self):
        # 根据过滤和排序条件，返回处理后的产品列表
        filtered_products = products.copy()

        # 获取过滤条件
        filter_field = self.filter_field_combo.currentText()
        filter_value = self.filter_field_input.text().strip()

        # 执行过滤逻辑
        if filter_value:
            # 如果包含'*'，需要模糊匹配
            if '*' in filter_value:
                pattern = re.escape(filter_value).replace(r'\*', '.*')
                regex = re.compile(pattern, re.IGNORECASE)
            
            if filter_field == "按SKU CLS":
                if '*' in filter_value:
                    filtered_products = [p for p in filtered_products if regex.search(p.get('SKU_CLS', ''))]
                else:
                    filtered_products = [p for p in filtered_products if filter_value.lower() in p.get('SKU_CLS', '').lower()]
            elif filter_field == "按产品名称":
                # 产品名称对ITEM_Name字段过滤
                if '*' in filter_value:
                    filtered_products = [p for p in filtered_products if regex.search(p.get('ITEM_Name', ''))]
                else:
                    filtered_products = [p for p in filtered_products if filter_value.lower() in p.get('ITEM_Name', '').lower()]
            elif filter_field == "按Supplier":
                if '*' in filter_value:
                    filtered_products = [p for p in filtered_products if regex.search(p.get('Supplier', ''))]
                else:
                    filtered_products = [p for p in filtered_products if filter_value.lower() in p.get('Supplier', '').lower()]

        # 获取排序规则
        sort_option = self.sort_combo.currentText()
        if sort_option == "按SKU CLS":
            filtered_products = sorted(filtered_products, key=lambda x: x.get('SKU_CLS', ''))
        elif sort_option == "按产品名称":
            filtered_products = sorted(filtered_products, key=lambda x: x.get('ITEM_Name', ''))
        elif sort_option == "按Supplier":
            filtered_products = sorted(filtered_products, key=lambda x: x.get('Supplier', ''))
        elif sort_option == "按BTL PER CS":
            filtered_products = sorted(filtered_products, key=lambda x: int(x.get('BTL_PER_CS', 0)))
        elif sort_option == "按创建日期":
            # Creation_Date格式为 "YYYY-MM-DD HH:MM:SS"，字符串比较即可按时间顺序排序
            filtered_products = sorted(filtered_products, key=lambda x: x.get('Creation_Date', ''))

        return filtered_products

    def update_product_table(self):
        # 在更新表格显示前，获取过滤和排序后的产品列表
        displayed_products = self.get_filtered_and_sorted_products()

        self.product_table.setRowCount(0)
        self.product_table.setRowCount(len(displayed_products))
        for row, product in enumerate(displayed_products):
            self.product_table.setItem(row, 0, QTableWidgetItem(product.get('SKU_CLS', '')))
            self.product_table.setItem(row, 1, QTableWidgetItem(product.get('ITEM_Name', '')))
            self.product_table.setItem(row, 2, QTableWidgetItem(product.get('Category', '')))
            self.product_table.setItem(row, 3, QTableWidgetItem(str(product.get('Size', ''))))
            self.product_table.setItem(row, 4, QTableWidgetItem(str(product.get('ALC', ''))))
            self.product_table.setItem(row, 5, QTableWidgetItem(str(product.get('BTL_PER_CS', ''))))
            self.product_table.setItem(row, 6, QTableWidgetItem(product.get('Supplier', '')))
            self.product_table.setItem(row, 7, QTableWidgetItem(product.get('Creation_Date', '')))

    def add_product(self):
        try:
            new_product = {}
            for field_name, entry in self.entries.items():
                value = entry.text().strip()
                if not value:
                    QMessageBox.warning(self, "输入错误", f"{field_name} 不能为空！")
                    return
                new_product[field_name] = value

            # 检查 SKU_CLS 是否已存在
            sku_cls = new_product['SKU_CLS']
            if any(product['SKU_CLS'] == sku_cls for product in products):
                QMessageBox.warning(self, "添加失败", f"产品 {sku_cls} 已存在！")
                return

            # 转换数据类型
            try:
                new_product['Size'] = float(new_product['Size'])
                new_product['ALC'] = float(new_product['ALC'])
                new_product['BTL_PER_CS'] = int(new_product['BTL_PER_CS'])
            except ValueError:
                QMessageBox.warning(self, "输入错误", "Size、ALC.、BTL PER CS 必须是有效的数字！")
                return

            new_product['Creation_Date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            products.append(new_product)
            save_product_to_db(new_product)
            data_manager.products_changed.emit()

            self.update_product_table()
            QMessageBox.information(self, "成功", f"产品 {sku_cls} 已添加。")
        except Exception as e:
            print(f"添加产品时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"添加产品时发生错误：{e}")

    def update_product(self):
        try:
            sku_cls = self.entries['SKU_CLS'].text().strip()
            if not sku_cls:
                QMessageBox.warning(self, "更新失败", "请输入 SKU CLS！")
                return

            # 获取现有产品数据
            existing_product = get_product_by_sku(sku_cls)
            if not existing_product:
                QMessageBox.warning(self, "更新失败", f"产品 {sku_cls} 不存在！")
                return

            # 准备更新后的产品数据
            updated_product = {}
            for field_name, entry in self.entries.items():
                value = entry.text().strip()
                if not value:
                    QMessageBox.warning(self, "输入错误", f"{field_name} 不能为空！")
                    return
                updated_product[field_name] = value

            # 转换数据类型
            try:
                updated_product['Size'] = float(updated_product['Size'])
                updated_product['ALC'] = float(updated_product['ALC'])
                updated_product['BTL_PER_CS'] = int(updated_product['BTL_PER_CS'])
            except ValueError:
                QMessageBox.warning(self, "输入错误", "Size、ALC.、BTL PER CS 必须是有效的数字！")
                return

            # 保留创建日期
            updated_product['Creation_Date'] = existing_product['Creation_Date']

            # 更新产品列表和数据库
            index = products.index(existing_product)
            products[index] = updated_product
            save_product_to_db(updated_product)
            data_manager.products_changed.emit()

            self.update_product_table()
            QMessageBox.information(self, "成功", f"产品 {sku_cls} 已更新。")
        except Exception as e:
            print(f"更新产品时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"更新产品时发生错误：{e}")

    def delete_product(self):
        try:
            sku_cls = self.entries['SKU_CLS'].text().strip()
            if not sku_cls:
                QMessageBox.warning(self, "删除失败", "请输入 SKU CLS！")
                return

            product = get_product_by_sku(sku_cls)
            if product:
                # 从产品列表中删除
                products.remove(product)
                # 从数据库中删除
                delete_product_from_db(sku_cls)
                data_manager.products_changed.emit()

                self.update_product_table()
                QMessageBox.information(self, "成功", f"产品 {sku_cls} 已删除。")
            else:
                QMessageBox.information(self, "删除失败", f"未找到 SKU CLS 为 {sku_cls} 的产品。")
        except Exception as e:
            print(f"删除产品时发生错误：{e}")
            QMessageBox.critical(self, "错误", f"删除产品时发生错误：{e}")
