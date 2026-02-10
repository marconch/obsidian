
     │ 销售出库单「单据联查」无法显示上游销售订单                                                        │
     │                                                                                                   │
     │ Context                                                                                           │
     │                                                                                                   │
     │ 用户反馈：销售出库单 SC202602090006 在"单据联查"弹窗中只能看到上游的销售合同，无法看到销售订单。  │
     │                                                                                                   │
     │ 根因分析：                                                                                        │
     │                                                                                                   │
     │ CommonService.querySalesTradeChain() 查找上游销售订单的逻辑是：                                   │
     │ 1. 查询 sales_trade_detail.source_id → 拿到销售订单 ID → 查询销售订单                             │
     │ 2. 若步骤1找不到，就没有 fallback 了                                                              │
     │                                                                                                   │
     │ 但 SalesTradeService.associateOrder() 的 detail 匹配逻辑依赖合同明细做 SKU 匹配（第 692-732       │
     │ 行）。如果合同不存在、合同无明细、或 SKU 不匹配，则 detail 的 sourceId 不会被写入。此时只有表头的 │
     │ sourceNo（销售订单号）被写入成功。                                                                │
     │                                                                                                   │
     │ 对比：销售合同的联查有一个 fallback 路径（第 935-941 行）：当 detail 链路查不到合同时，会通过     │
     │ salesTrade.salesContractNo 直接查合同。销售订单缺少同样的 fallback 机制。                         │
     │                                                                                                   │
     │ 修改方案                                                                                          │
     │                                                                                                   │
     │ 文件: leaping-server/ruoyi-modules/ruoyi-admin-erp/src/main/java/org/dromara/erp/base/service/Comm│
     │ onService.java                                                                                    │
     │                                                                                                   │
     │ 在 querySalesTradeChain() 方法中（约第 934 行之后），增加一个与合同联查相同模式的 fallback：当    │
     │ detail 链路未查到销售订单时，通过 salesTrade.sourceNo（存储的是销售订单号）直接查询。             │
     │                                                                                                   │
     │ 具体改动                                                                                          │
     │                                                                                                   │
     │ 在第 934 行（} 结束了 salesOrderList != null 的 if 块）之后、第 935 行（合同                      │
     │ fallback）之前，插入：                                                                            │
     │                                                                                                   │
     │             // 补充：通过 sourceNo 直接查找销售订单（关联订单但明细未匹配到的场景）               │
     │             if (CollUtil.isEmpty(vo.getSalesOrderList()) &&                                       │
     │ StringUtils.isNotBlank(salesTrade.getSourceNo())) {                                               │
     │                 LambdaQueryWrapper<SalesOrder> orderQw = new LambdaQueryWrapper<>();              │
     │                 orderQw.eq(SalesOrder::getDocNo, salesTrade.getSourceNo());                       │
     │                 SalesOrderVo directOrder = salesOrderMapper.selectVoOne(orderQw);                 │
     │                 if (directOrder != null) {                                                        │
     │                                                                                                   │
     │ directOrder.setDetails(salesOrderDetailService.queryBySid(directOrder.getId()));                  │
     │                     vo.setSalesOrderList(List.of(directOrder));                                   │
     │                     // 同时通过此订单查上游合同                                                   │
     │                     List<Long> orderIds = List.of(directOrder.getId());                           │
     │                     List<SalesContractVo> contractList =                                          │
     │ getSalesContractListBySalesOrderList(orderIds);                                                   │
     │                     if (contractList != null) {                                                   │
     │                         vo.setSalesContractList(contractList);                                    │
     │                     }                                                                             │
     │                 }                                                                                 │
     │             }                                                                                     │
     │                                                                                                   │
     │ 依赖说明：salesOrderMapper、salesOrderDetailService、SalesOrder 类均已在 CommonService            │
     │ 中注入/导入，无需新增依赖。                                                                       │
     │                                                                                                   │
     │ 模式完全复用已有的合同 fallback（第 935-941 行）的风格。                                          │
     │                                                                                                   │
     │ 验证                                                                                              │
     │                                                                                                   │
     │ 1. 找一个已关联订单但明细 source_id 为 NULL 的销售出库单                                          │
     │ 2. 点击"单据联查"→ 上游单据中应同时显示"销售订单"和"销售合同"                                     │
     │ 3. 对于明细 source_id 正常的出库单，联查行为不变（走正常 detail 链路）                            │
     │ 4. 检查数据库确认：SELECT source_no FROM sales_trade WHERE doc_no = 'SC202602090006' 应该有值     │

