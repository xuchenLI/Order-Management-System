# price_calculator.py

from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QDialog, QMessageBox
)
from data import purchase_orders, save_purchase_order_to_db
import math

# 默认配置参数
config_params = {
    'Total COGS': {
        'New_listing_SKU_cfg': 84,
        'Storage_cfg': 0.47,
        'Predict_Storage_Days': 100,
        'Allocation_Fee_cfg': 0.16,
        'Administration_cfg': 0.24,
        'Receiving_cfg': 0.46,
        'Assembly_cfg': 1.14,
        'Barcode_cfg': 0.44,
        'Damage_And_Retention_Sample_cfg': 0
    },
    'CIF': {
        'Strip Label Cost EURO': 0.37,
        'Total Freight CAD': 35
    },
    'WHLSE': {
        'RECYCLE RATE': 0.07,
        'PLUS DUTY': 0
    }
}

def open_price_calculator(order_details_window):
    calculator_window = QDialog()
    calculator_window.setWindowTitle("价格计算器")
    layout = QVBoxLayout()

    # 订单号输入字段
    layout.addWidget(QLabel("单个订单计算:"))
    order_nb_entry = QLineEdit()
    layout.addWidget(QLabel("订单号:"))
    layout.addWidget(order_nb_entry)

    # 主订单号输入字段
    layout.addWidget(QLabel("批量计算:"))
    main_order_nb_entry = QLineEdit()
    layout.addWidget(QLabel("主订单号:"))
    layout.addWidget(main_order_nb_entry)

    # 显示计算结果的字段
    results_labels = {
        'INVOICE PRICE': QLineEdit(),
        'INVOICE CS': QLineEdit(),
        'WHOLESALE BTL': QLineEdit(),
        'WHOLESALE CS': QLineEdit(),
        'TOTAL Freight CAD': QLineEdit(),
        'PROFIT PER BT': QLineEdit(),
        'PROFIT PER CS': QLineEdit(),
        'PROFIT TOTAL': QLineEdit(),
        'QUANTITY BTL': QLineEdit(),
        'TOTAL AMOUNT': QLineEdit()
    }

    # 设置这些字段为只读
    for key, entry in results_labels.items():
        entry.setReadOnly(True)
        layout.addWidget(QLabel(f"{key}:"))
        layout.addWidget(entry)

    # 计算和配置按钮
    calc_button = QPushButton("计算单个订单")
    calc_button.clicked.connect(lambda: calculate_and_display(order_nb_entry.text(), results_labels))
    layout.addWidget(calc_button)

    batch_calc_button = QPushButton("批量计算主订单")
    batch_calc_button.clicked.connect(lambda: batch_calculate_main_order(main_order_nb_entry.text(), order_details_window))
    layout.addWidget(batch_calc_button)

    update_button = QPushButton("更新单个订单")
    update_button.clicked.connect(lambda: update_order(order_nb_entry.text(), results_labels, order_details_window))
    layout.addWidget(update_button)

    calculator_window.setLayout(layout)
    calculator_window.exec()

def calculate_and_display(order_nb, results_labels):
    try:
        # 根据订单号获取订单
        order = next((o for o in purchase_orders if o['Order Nb'] == order_nb), None)
        if not order:
            QMessageBox.warning(None, "错误", "订单号不存在")
            return
        # 检查 EXW 汇率是否为 0
        EXW_rate = float(order.get('EXW Exchange Rate', 0))
        if EXW_rate == 0:
            QMessageBox.warning(None, "错误", "EXW 汇率不能为 0，请检查订单信息")
            return  # 如果汇率为 0，则终止计算
        # 计算 QUANTITY BTL 和 TOTAL AMOUNT
        QUANTITY_CS = int(order.get('QUANTITY CS', 0))
        BTL_PER_CS = int(order.get('BTL PER CS', 0))
        EXW = float(order.get('EXW EURO', 0))

        QUANTITY_BTL = QUANTITY_CS * BTL_PER_CS
        TOTAL_AMOUNT = EXW * QUANTITY_BTL

        # 计算其他价格
        INVOICE_PRICE, INVOICE_CS, CIF, TOTAL_Freight_CAD, Total_COGS = calculate_invoice_price(order)
        WHOLESALE_BTL, WHOLESALE_CS = calculate_wholesale(order, INVOICE_CS)

        # 计算 PROFIT PER BT、PROFIT PER CS 和 PROFIT TOTAL
        expected_profit = float(order.get('Expected Profit', 0))
        PROFIT_PER_BT = INVOICE_PRICE - Total_COGS
        PROFIT_PER_CS = PROFIT_PER_BT * BTL_PER_CS
        PROFIT_TOTAL = PROFIT_PER_CS * QUANTITY_CS

        # 显示结果
        results_labels['INVOICE PRICE'].setText(str(round(INVOICE_PRICE, 2)))
        results_labels['INVOICE CS'].setText(str(round(INVOICE_CS, 2)))
        results_labels['WHOLESALE BTL'].setText(str(round(WHOLESALE_BTL, 2)))
        results_labels['WHOLESALE CS'].setText(str(round(WHOLESALE_CS, 2)))
        results_labels['TOTAL Freight CAD'].setText(str(round(TOTAL_Freight_CAD, 2)))
        results_labels['PROFIT PER BT'].setText(str(round(PROFIT_PER_BT, 2)))
        results_labels['PROFIT PER CS'].setText(str(round(PROFIT_PER_CS, 2)))
        results_labels['PROFIT TOTAL'].setText(str(round(PROFIT_TOTAL, 2)))
        results_labels['QUANTITY BTL'].setText(str(QUANTITY_BTL))
        results_labels['TOTAL AMOUNT'].setText(str(round(TOTAL_AMOUNT, 2)))

        QMessageBox.information(None, "计算成功", "价格计算完成")
    except Exception as e:
        print(f"计算时发生错误：{e}")
        QMessageBox.critical(None, "计算错误", f"计算时发生错误：{e}")

def update_order(order_nb, results_labels, order_details_window):
    if not order_nb:
        QMessageBox.warning(None, "更新错误", "订单号为空")
        return

    try:
        # 获取订单对象
        order = next((o for o in purchase_orders if o['Order Nb'] == order_nb), None)
        if not order:
            QMessageBox.warning(None, "更新错误", "订单不存在")
            return

        # 更新订单的数据
        updated_fields = {}
        for key in ['INVOICE PRICE', 'INVOICE CS', 'WHOLESALE BTL', 'WHOLESALE CS', 'TOTAL Freight CAD',
                    'PROFIT PER BT', 'PROFIT PER CS', 'PROFIT TOTAL', 'QUANTITY BTL', 'TOTAL AMOUNT']:
            value = results_labels[key].text().strip()
            if value:
                if key == 'TOTAL Freight CAD':
                    order['TOTAL Freight'] = value
                elif key == 'TOTAL AMOUNT':
                    order['TOTAL AMOUNT EURO'] = value
                else:
                    order[key] = value
                updated_fields[key] = value

        # 将更新后的订单保存到数据库
        save_purchase_order_to_db(order)

        # 更新表格显示
        if order_details_window:
            order_details_window.update_order_table()

        QMessageBox.information(None, "更新成功", f"订单 {order_nb} 已成功更新")
    except Exception as e:
        print(f"更新订单时发生错误：{e}")
        QMessageBox.critical(None, "更新错误", f"更新订单时发生错误：{e}")

def batch_calculate_main_order(main_order_nb, order_details_window):
    """批量计算主订单下所有子订单的价格"""
    if not main_order_nb:
        QMessageBox.warning(None, "批量计算错误", "主订单号为空")
        return

    try:
        # 过滤该主订单下所有子订单
        sub_orders = [po for po in purchase_orders if str(po.get("Order Nb", "")).startswith(main_order_nb + "_")]
        
        if not sub_orders:
            QMessageBox.warning(None, "批量计算错误", f"未找到主订单 {main_order_nb} 下的子订单")
            return

        success_count = 0
        error_count = 0
        error_messages = []

        for order in sub_orders:
            try:
                order_nb = order.get('Order Nb', '')
                
                # 检查 EXW 汇率是否为 0
                EXW_rate = float(order.get('EXW Exchange Rate', 0))
                if EXW_rate == 0:
                    error_messages.append(f"订单 {order_nb}: EXW 汇率为 0")
                    error_count += 1
                    continue

                # 计算 QUANTITY BTL 和 TOTAL AMOUNT
                QUANTITY_CS = int(order.get('QUANTITY CS', 0))
                BTL_PER_CS = int(order.get('BTL PER CS', 0))
                EXW = float(order.get('EXW EURO', 0))

                QUANTITY_BTL = QUANTITY_CS * BTL_PER_CS
                TOTAL_AMOUNT = EXW * QUANTITY_BTL

                # 计算其他价格
                INVOICE_PRICE, INVOICE_CS, CIF, TOTAL_Freight_CAD, Total_COGS = calculate_invoice_price(order)
                WHOLESALE_BTL, WHOLESALE_CS = calculate_wholesale(order, INVOICE_CS)

                # 计算 PROFIT PER BT、PROFIT PER CS 和 PROFIT TOTAL
                expected_profit = float(order.get('Expected Profit', 0))
                PROFIT_PER_BT = INVOICE_PRICE - Total_COGS
                PROFIT_PER_CS = PROFIT_PER_BT * BTL_PER_CS
                PROFIT_TOTAL = PROFIT_PER_CS * QUANTITY_CS

                # 更新订单数据
                order['INVOICE PRICE'] = str(round(INVOICE_PRICE, 2))
                order['INVOICE CS'] = str(round(INVOICE_CS, 2))
                order['WHOLESALE BTL'] = str(round(WHOLESALE_BTL, 2))
                order['WHOLESALE CS'] = str(round(WHOLESALE_CS, 2))
                order['TOTAL Freight'] = str(round(TOTAL_Freight_CAD, 2))
                order['PROFIT PER BT'] = str(round(PROFIT_PER_BT, 2))
                order['PROFIT PER CS'] = str(round(PROFIT_PER_CS, 2))
                order['PROFIT TOTAL'] = str(round(PROFIT_TOTAL, 2))
                order['QUANTITY BTL'] = str(QUANTITY_BTL)
                order['TOTAL AMOUNT EURO'] = str(round(TOTAL_AMOUNT, 2))

                # 保存到数据库
                save_purchase_order_to_db(order)
                success_count += 1

            except Exception as e:
                error_messages.append(f"订单 {order.get('Order Nb', '')}: {str(e)}")
                error_count += 1

        # 更新表格显示
        if order_details_window:
            order_details_window.update_order_table()

        # 显示结果
        result_message = f"批量计算完成\n成功: {success_count} 个订单\n失败: {error_count} 个订单"
        if error_messages:
            result_message += f"\n\n错误详情:\n" + "\n".join(error_messages[:5])  # 只显示前5个错误
            if len(error_messages) > 5:
                result_message += f"\n... 还有 {len(error_messages) - 5} 个错误"

        if error_count == 0:
            QMessageBox.information(None, "批量计算成功", result_message)
        else:
            QMessageBox.warning(None, "批量计算完成", result_message)

    except Exception as e:
        print(f"批量计算时发生错误：{e}")
        QMessageBox.critical(None, "批量计算错误", f"批量计算时发生错误：{e}")

def calculate_invoice_price(order):
    try:
        # 验证并提取数据
        EXW = float(order.get('EXW EURO', 0))
        EXW_rate = float(order.get('EXW Exchange Rate', 0))
        BTL_PER_CS = int(order.get('BTL PER CS', 0))
        QUANTITY_CS = int(order.get('QUANTITY CS', 0))
        expected_profit = float(order.get('Expected Profit', 0))
        domestic_freight = float(order.get('Domestic Freight CAD', 0))
        international_freight = float(order.get('International Freight EURO', 0))
        international_freight_rate = float(order.get('International Freight Exchange Rate', 0))

        # CIF Calculation
        Strip_Label_Cost_CAD = config_params['CIF']['Strip Label Cost EURO'] * EXW_rate
        TOTAL_Freight_CAD = domestic_freight + international_freight * international_freight_rate
        EXW_CAD = EXW * EXW_rate
        CIF = EXW_CAD + Strip_Label_Cost_CAD + TOTAL_Freight_CAD

        # Total COGS Calculation
        New_listing_SKU = config_params['Total COGS']['New_listing_SKU_cfg'] / (BTL_PER_CS * QUANTITY_CS)
        Storage = config_params['Total COGS']['Storage_cfg'] / 30 / BTL_PER_CS * config_params['Total COGS']['Predict_Storage_Days']
        Allocation_Fee = config_params['Total COGS']['Allocation_Fee_cfg'] / BTL_PER_CS
        Administration = config_params['Total COGS']['Administration_cfg'] / BTL_PER_CS
        Receiving = config_params['Total COGS']['Receiving_cfg'] / BTL_PER_CS
        Assembly = config_params['Total COGS']['Assembly_cfg'] / BTL_PER_CS
        Barcode = config_params['Total COGS']['Barcode_cfg'] / BTL_PER_CS
        Damage = config_params['Total COGS']['Damage_And_Retention_Sample_cfg']
        GST_Service_AGLC = (
            New_listing_SKU + Storage + Allocation_Fee + Administration + Receiving + Assembly + Barcode) * 0.05

        Total_COGS = CIF + New_listing_SKU + Storage + Allocation_Fee + Administration + Receiving + Assembly + Barcode + Damage + GST_Service_AGLC

        # INVOICE PRICE and INVOICE CS Calculation
        INVOICE_PRICE = Total_COGS / (1 - expected_profit)
        INVOICE_CS = INVOICE_PRICE * BTL_PER_CS

        return INVOICE_PRICE, INVOICE_CS, CIF, TOTAL_Freight_CAD, Total_COGS
    except Exception as e:
        print(f"计算发票价格时发生错误：{e}")
        return None, None, None, None, None

def calculate_wholesale(order, INVOICE_CS):
    try:
        BTL_PER_CS = int(order.get('BTL PER CS', 0))
        SIZE = float(order.get('SIZE', 0))
        ALC = float(order.get('ALC.', 0))

        # WHOLESALE Calculation
        if SIZE > 1:
            DEPOSIT = 0.25
        else:
            DEPOSIT = 0.1

        # MARKUP RATE
        if ALC <= 16:
            MARKUP_RATE = 4.11
        else:
            MARKUP_RATE = 6.88
        # 计算markup加价部分
        Value_per_Litre = INVOICE_CS / (SIZE * BTL_PER_CS)
        Ad_Valorem_per_Litre = calculate_ad_valorem_per_litre(Value_per_Litre)
        Total_Additional_Markup_on_High_Value_Wine = SIZE * BTL_PER_CS * Ad_Valorem_per_Litre
        # TOTAL COST CASE Calculation
        PLUS_MARKUP = (SIZE * BTL_PER_CS * MARKUP_RATE) + Total_Additional_Markup_on_High_Value_Wine
        PLUS_RECYCLE = math.floor(config_params['WHLSE']['RECYCLE RATE'] * BTL_PER_CS * 1000) / 1000
        PLUS_EXCISE = calculate_excise_rate(ALC) * SIZE * BTL_PER_CS

        TOTAL_COST_CASE = INVOICE_CS + PLUS_MARKUP + PLUS_RECYCLE + config_params['WHLSE']['PLUS DUTY'] + PLUS_EXCISE
        COST_UNIT = TOTAL_COST_CASE / BTL_PER_CS

        # WHOLESALE BTL Calculation
        ROUNDUP_UNIT = math.ceil(COST_UNIT * 100) / 100
        PLUS_GST = ROUNDUP_UNIT * 0.05
        SUB_TOTAL = PLUS_GST + ROUNDUP_UNIT
        ROUNDED = round(SUB_TOTAL, 2)
        WHOLESALE_BTL = ROUNDED + DEPOSIT
        WHOLESALE_CS = WHOLESALE_BTL * BTL_PER_CS

        return WHOLESALE_BTL, WHOLESALE_CS
    except Exception as e:
        print(f"计算批发价格时发生错误：{e}")
        return None, None

def calculate_ad_valorem_per_litre(value_per_litre):
    if value_per_litre <= 15:
        return 0
    elif value_per_litre <= 20:
        return (value_per_litre * 0.05) - 0.75
    elif value_per_litre <= 25:
        return (value_per_litre * 0.1) - 1.75
    else:
        return (value_per_litre * 0.15) - 3

def calculate_excise_rate(ALC):
    if ALC <= 0.012:
        return 0.022
    elif 0.012 < ALC <= 0.07:
        return 0.351
    elif 0.07 < ALC <= 0.229:
        return 0.73
    else:
        QMessageBox.warning(None, "警告", "请确认酒精度是否正确")
        return 0
