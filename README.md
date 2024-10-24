2024-10-22
1. 决定：不修复采购订单中，更新采购订单后，价格计算的内容消失的问题。目的，避免修改内容后，没有及时更新计算价格导致的错误。

2. 采购订单中，添加显示页面的排序分类，按时间从旧到新和从新到旧，按供应商，按产品编号，按订单号由小到大和由大到小。

3. 采购订单中，显示页面的每个title上增加一个filter按钮，点击后，可以按照该title进行筛选。

5. 采购订单中，显示界面删除最后两列的Allocation和Sub-allocation

6. 库存管理中，库存明细旁有一个选项，选项分为全部、In Stock和Allocation，它们来自采购订单中，订单的 Order Type。当用户选择In Stock时，库存明细只显示In Stock的库存，选择Allocation则只显示Allocation的库存。

7. 库存管理中，库存明细的Allocation界面，在title，到仓库日期，后面增加两列，名称为：提货日期，提货数量。数据库中，将这两项从最后列添加。
7.1 库存管理中，库存明细的Allocation界面，提货数量为负数，表示退货数量。
7.2 库存管理中，输入界面增加提货日期和提货数量的输入框。

8. 库存管理中，库存明细的Allocation界面，在最后一列增加，名称为：Remark。数据库中，Remark添加到最后一列。
9. 库存管理中，库存明细的Allocation界面，在第一列增加，名称为Order Type。数据库中，Order Type添加到最后一列。
10. 库存管理中，库存明细的Allocation界面，右上角增加一个按钮，名称为：Export。点击后，可以导出当前显示的所有数据。
11. 库存管理中，库存明细的Allocation界面，每个title上增加一个filter按钮，点击后，可以按照该title进行筛选。
12. 在库存管理中，库存明细的In Stock界面，删除Allocation和Sub-allocation。无需更改数据库。
13. 在库存管理中，库存明细的In Stock界面，在第一列增加，名称为Order Type。
14. 在库存管理中，库存明细的In Stock界面，删除库存天数，增加库存详情。
14.1 库存详情中，存在sub-title，分别是：提货日期，提货数量，库存天数。提货日期和提货数量的输入框同7.2中定义的。库存天数由sub-title中的提货日期与title中的到仓库日期计算得出。
14.2 库存详情中，根据提货日期，从旧到新排列。
14.3 库存详情中，提货数量为负数，表示退货数量。
15. 在库存管理中，库存明细的In Stock界面，右上角增加一个按钮，名称为：Export。点击后，可以导出当前显示的所有数据。
16. 在库存管理中，库存明细的In Stock界面，每个title上增加一个filter按钮，点击后，可以按照该title进行筛选。
17. 在销售订单管理中，增加一个输入框，名称为：订单编号。
18. 在销售订单管理中，增加一个输入框，名称为：销售数量（BTL）。
19. 在销售订单管理中，数量输入框，改为销售数量（CS）。
20. 在销售订单管理中，销售订单售出的产品数量可以按照箱数或者瓶数进行输入。分别对应的是输入框的销售数量（CS）和销售数量（BTL）。
20.1 当销售数量（CS）为空时，销售数量（BTL）不为空，则按照销售数量（BTL）作为销售数量。
20.2 当销售数量（BTL）为空时，销售数量（CS）不为空，则按照销售数量（CS）作为销售数量。
20.3 当销售数量（CS）和销售数量（BTL）都为空时，销售数量为0。
20.4 当销售数量（CS）和销售数量（BTL）都不为空时，销售数量为两者之和。
20.5 销售订单中，销售数量（CS）和销售数量（BTL）的输入框，只能输入数字。
20.6 销售订单中，销售数量（CS）和销售数量（BTL）的输入框，输入的数字只能为整数。
20.7 销售订单中，销售数量（CS）和销售数量（BTL）的输入框，输入的数字为负数时，代表退货。
20.8 销售订单中，销售数量应从库存中减去。
20.9 根据输入的产品编号和订单编号，从库存中减去对应的产品数量。
20.10 若库存订单的Order Type为allocation，则允许只输入订单编号。
20.11 若库存订单的Order Type为in stock，则允许只输入产品编号。备注：此处与编程无关，仅仅做开发记录用，产品编号应该根据packing的不同而重新编号。因为28中需要根据产品编号找到对应的BTL PER CS用于计算总销售瓶数。
20.12 若输入的订单编号不存在，则提示错误信息。
21. 在销售订单管理中，单价输入框，改为销售单价（CAD/BTL）。
22. 在销售订单管理中，销售订单显示页面，无法显示添加的订单信息。
23. 在销售订单管理中，输入框客户编号改为客户名称。
24. 在销售订单管理中，显示区域的title应该跟输入区域保持一致。
25. 在销售订单管理中，显示区域，每个title上增加一个filter按钮，点击后，可以按照该title进行筛选。
26. 在销售订单管理中，显示区域，右上角增加一个按钮，名称为：Export。点击后，可以导出当前显示的所有数据。
27. 在销售订单管理中，显示区域，右上角增加一个按钮，名称为：Refresh。点击后，可以刷新当前显示的所有数据。
28. 在销售订单管理中，显示区域，增加一列，名称为：总价。总价的计算公式为，总价 = 销售单价*销售数量（BTL）。若，用户输入的为销售数量（CS），系统应通过匹配对应的产品或者订单，找到每箱（CS）对应的瓶数（BTL），BTL PER CS。例如销售数量（BTL）= BTL PER CS * 销售数量（CS）。
