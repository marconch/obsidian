
› 生产执行管理功能开发规划

   一、现有系统现状分析

   1.1 功能完整性评估
   ┌──────────┬────────┬─────────────────────────────────┐
   │   模块   │ 完整度 │              现状               │
   ├──────────┼────────┼─────────────────────────────────┤
   │ 生产工单 │ 90%    │ ✅ 完整，支持从销售订单推送     │
   ├──────────┼────────┼─────────────────────────────────┤
   │ 工艺路线 │ 85%    │ ✅ 完整，支持版本、工序时间定义 │
   ├──────────┼────────┼─────────────────────────────────┤
   │ BOM管理  │ 85%    │ ✅ 完整，支持多层级、替代料     │
   ├──────────┼────────┼─────────────────────────────────┤
   │ 领料管理 │ 85%    │ ✅ 完整，自动推送领料单         │
   ├──────────┼────────┼─────────────────────────────────┤
   │ 验收记录 │ 50%    │ ⚠️ 仅基础数量验收，无质检流程   │
   ├──────────┼────────┼─────────────────────────────────┤
   │ 完工入库 │ 75%    │ ✅ 基本完整，可从工单推送       │
   ├──────────┼────────┼─────────────────────────────────┤
   │ 工序派工 │ 0%     │ ❌ 完全缺失                     │
   ├──────────┼────────┼─────────────────────────────────┤
   │ 质检管理 │ 30%    │ ❌ 严重缺失                     │
   ├──────────┼────────┼─────────────────────────────────┤
   │ 进度跟踪 │ 30%    │ ⚠️ 无实时工序进度               │
   └──────────┴────────┴─────────────────────────────────┘
   1.2 现有数据流

   销售订单 ──pushProductWorkOrder()──▶ 生产工单
                                           │
       ┌───────────────────────────────────┼───────────────────────────────────┐
       │                                   │                                   │
       ▼                                   ▼                                   ▼
   所需物料 ──pushTaskByCollection()──▶ 领料单 ──▶ 材料出库
   (WorkMaterial)                    (WorkCollection)
                                           │
                                           ▼
                                      生产工序 ◀─────────────────── [缺少派工功能]
                                     (WorkProcess)
                                           │
                                           ▼
                                      生产验收 ◀─────────────────── [缺少质检流程]
                                     (WorkAccept)
                                           │
                                           ▼
                                      产成品入库
                                     (ProductTrade)

   ---
   二、目标流程设计

   用户期望的完整流程：

   ┌─────────────────────────────────────────────────────────────────────────────────┐
   │                              生产执行完整流程                                    │
   └─────────────────────────────────────────────────────────────────────────────────┘

   [计划层]                    [执行层]                           [完工层]
       │                           │                                  │
       ▼                           ▼                                  ▼
   ┌─────────┐              ┌─────────────┐                    ┌──────────┐
   │ 销售订单 │              │   生产工单   │                    │ 完工入库  │
   │         │──────────────▶│  工序计划   │──────────────────▶│  产品验收 │
   │(可选:MRP │              │   工序派工   │                    │          │
   │ 任务管理)│              │  生产过程管理│                    │          │
   └─────────┘              └─────────────┘                    └──────────┘
                                  │
                                  ├── 首检 ──┐
                                  ├── 过程检 ├── 检验管理
                                  └── 末检 ──┘

   ---
   三、实施路径规划

   方案A：增量增强（推荐）

   在现有生产工单基础上增强，不引入新的计划层。

   第1阶段：工序派工（核心缺失）
       └── 新建 product_work_dispatch 表
       └── 增强 work/task.vue 页面

   第2阶段：检验管理
       └── 新建 product_inspect 检验单表
       └── 新建 product_inspect_item 检验项表
       └── 增强验收流程

   第3阶段：生产过程管理
       └── 工序开工/完工时间记录
       └── 工时记录
       └── 进度看板

   第4阶段：完工入库增强
       └── 入库前置条件检查
       └── 批次管理

   方案B：引入任务管理层

   在销售订单和生产工单之间增加任务管理层。

   第0阶段：MRP任务管理
       └── manufacture_task 任务管理
       └── 任务合并、分配
       └── 任务下发生成工单

   第1-4阶段：同方案A

   ---
   四、技术设计补充

   4.0 状态机与字段规范

   4.0.1 派工状态机

   ┌────────────────────────────────────────────────────────────────────────┐
   │                          班组派工单状态                                 │
   └────────────────────────────────────────────────────────────────────────┘

       ┌────────┐   分派工人    ┌────────┐   全部完成    ┌────────┐
       │ 待分派  │─────────────▶│ 进行中  │─────────────▶│ 已完成  │
       │  (0)   │              │  (1)   │              │  (2)   │
       └────────┘              └────────┘              └────────┘
           │                       │
           └───────取消────────────┴──────────────▶ ┌────────┐
                                                    │ 已取消  │
                                                    │  (9)   │
                                                    └────────┘

   ┌────────────────────────────────────────────────────────────────────────┐
   │                          工人任务单状态                                 │
   └────────────────────────────────────────────────────────────────────────┘

       ┌────────┐   开工      ┌────────┐   完工报数    ┌────────┐
       │ 待开工  │───────────▶│ 进行中  │─────────────▶│ 已完成  │
       │  (0)   │            │  (1)   │              │  (2)   │
       └────────┘            └────────┘              └────────┘
           │                     │
           │                     ▼
           │                ┌────────┐
           │                │ 已暂停  │◀──────暂停
           │                │  (3)   │───────恢复───▶ 进行中
           │                └────────┘
           │
           └───────取消───────────────────────────▶ ┌────────┐
                                                    │ 已取消  │
                                                    │  (9)   │
                                                    └────────┘

   4.0.2 检验状态机

       ┌────────┐   开始检验   ┌────────┐   提交结果   ┌────────┐
       │ 待检验  │────────────▶│ 检验中  │────────────▶│ 已完成  │
       │  (0)   │             │  (1)   │             │  (2)   │
       └────────┘             └────────┘             └────────┘
                                                          │
                                    ┌─────────────────────┼─────────────────────┐
                                    ▼                     ▼                     ▼
                               result=pass          result=fail
  result=conditional
                               (合格)               (不合格)              (让步接收)
                                    │                     │                     │
                                    ▼                     ▼                     ▼
                               允许入库/             生成处理单:            人工确认后
                               继续生产             返工/报废/退货          允许继续

   4.0.3 工序进度状态

   product_work_process.status:
       0 = 待开工（未派工或派工单未开工）
       1 = 进行中（有工人任务在执行）
       2 = 已完成（所有工人任务完成且检验合格）
       3 = 已暂停（所有工人任务暂停）

   4.0.4 字典数据新增

   -- 派工单状态
   INSERT INTO sys_dict_type VALUES (nextval('seq'), '派工单状态',
  'product_dispatch_status', '0', ...);
   INSERT INTO sys_dict_data VALUES
       (nextval('seq'), 1, '待分派', '0', 'product_dispatch_status', NULL, 'info', ...),
       (nextval('seq'), 2, '进行中', '1', 'product_dispatch_status', NULL,
  'primary', ...),
       (nextval('seq'), 3, '已完成', '2', 'product_dispatch_status', NULL,
  'success', ...),
       (nextval('seq'), 4, '已取消', '9', 'product_dispatch_status', NULL,
  'danger', ...);

   -- 工人任务状态
   INSERT INTO sys_dict_type VALUES (nextval('seq'), '工人任务状态',
  'product_task_status', '0', ...);
   INSERT INTO sys_dict_data VALUES
       (nextval('seq'), 1, '待开工', '0', 'product_task_status', NULL, 'info', ...),
       (nextval('seq'), 2, '进行中', '1', 'product_task_status', NULL, 'primary', ...),
       (nextval('seq'), 3, '已完成', '2', 'product_task_status', NULL, 'success', ...),
       (nextval('seq'), 4, '已暂停', '3', 'product_task_status', NULL, 'warning', ...),
       (nextval('seq'), 5, '已取消', '9', 'product_task_status', NULL, 'danger', ...);

   -- 检验类型
   INSERT INTO sys_dict_type VALUES (nextval('seq'), '检验类型', 'product_inspect_type',
  '0', ...);
   INSERT INTO sys_dict_data VALUES
       (nextval('seq'), 1, '首件检验', 'first', 'product_inspect_type', NULL,
  'primary', ...),
       (nextval('seq'), 2, '过程检验', 'process', 'product_inspect_type', NULL,
  'warning', ...),
       (nextval('seq'), 3, '完工检验', 'final', 'product_inspect_type', NULL,
  'success', ...),
       (nextval('seq'), 4, '来料检验', 'incoming', 'product_inspect_type', NULL,
  'info', ...);

   -- 检验结果
   INSERT INTO sys_dict_type VALUES (nextval('seq'), '检验结果',
  'product_inspect_result', '0', ...);
   INSERT INTO sys_dict_data VALUES
       (nextval('seq'), 1, '合格', 'pass', 'product_inspect_result', NULL,
  'success', ...),
       (nextval('seq'), 2, '不合格', 'fail', 'product_inspect_result', NULL,
  'danger', ...),
       (nextval('seq'), 3, '让步接收', 'conditional', 'product_inspect_result', NULL,
  'warning', ...);

   -- 缺陷类型（复用现有码表或新建）
   INSERT INTO sys_dict_type VALUES (nextval('seq'), '缺陷类型', 'product_defect_type',
  '0', ...);
   INSERT INTO sys_dict_data VALUES
       (nextval('seq'), 1, '外观缺陷', 'appearance', 'product_defect_type', ...),
       (nextval('seq'), 2, '尺寸超差', 'dimension', 'product_defect_type', ...),
       (nextval('seq'), 3, '功能异常', 'function', 'product_defect_type', ...),
       (nextval('seq'), 4, '材料问题', 'material', 'product_defect_type', ...),
       (nextval('seq'), 5, '其他', 'other', 'product_defect_type', ...);

   ---
   五、方案A详细设计（推荐）

   4.1 第1阶段：工序派工

   目标：实现两级派工（班组长 → 工人）和进度跟踪

   派工流程：
   工单工序 ──派给班组长──▶ 班组派工单 ──分派给工人──▶ 工人任务单
                              │                         │
                              ▼                         ▼
                        班组长汇总进度              工人报工/完工

   新增数据表（完整定义含约束与索引）：

   -- =============================================
   -- 班组派工单（一级派工：工序→班组长）
   -- =============================================
   CREATE TABLE product_work_dispatch (
       id BIGSERIAL PRIMARY KEY,
       dispatch_no VARCHAR(50) NOT NULL,       -- 派工单号（唯一）
       work_order_id BIGINT NOT NULL,          -- 生产工单ID（FK →
  product_work_order.id）
       work_order_no VARCHAR(50),              -- 生产工单号（冗余，便于查询）
       process_id BIGINT NOT NULL,             -- 工序ID（FK → product_work_process.id）
       process_name VARCHAR(200),              -- 工序名称（冗余）
       process_seq INT,                        -- 工序顺序（冗余）
       route_id BIGINT,                        -- 工艺路线ID（FK →
  product_process_route.id）
       route_detail_id BIGINT,                 -- 工艺路线明细ID（FK →
  product_process_route_detail.id）
       sku_id BIGINT NOT NULL,                 -- 产品SKU ID
       bom_id BIGINT,                          -- BOM ID
       bom_version VARCHAR(50),                -- BOM版本号（冗余）
       team_id BIGINT,                         -- 班组ID（FK → sys_dept.dept_id，部门类型
  =班组）
       team_name VARCHAR(100),                 -- 班组名称（冗余）
       team_leader_id BIGINT,                  -- 班组长ID（FK → sys_user.user_id）
       team_leader_name VARCHAR(100),          -- 班组长姓名（冗余）
       work_center_id BIGINT,                  -- 工作中心ID
       production_line_id BIGINT,              -- 生产线ID
       plan_qty DECIMAL(20,3) NOT NULL,        -- 派工数量
       dispatched_qty DECIMAL(20,3) DEFAULT 0, -- 已分派给工人数量
       finish_qty DECIMAL(20,3) DEFAULT 0,     -- 完成数量（汇总自工人任务）
       qualified_qty DECIMAL(20,3) DEFAULT 0,  -- 合格数量（汇总自检验结果）
       unqualified_qty DECIMAL(20,3) DEFAULT 0,-- 不合格数量
       scrap_qty DECIMAL(20,3) DEFAULT 0,      -- 报废数量
       rework_qty DECIMAL(20,3) DEFAULT 0,     -- 返工数量
       status VARCHAR(10) DEFAULT '0',         -- 状态：0=待分派,1=进行中,2=已完成,9=已取
  消
       plan_start_time TIMESTAMP,              -- 计划开工时间
       plan_end_time TIMESTAMP,                -- 计划完工时间
       actual_start_time TIMESTAMP,            -- 实际开工时间（首个工人开工时更新）
       actual_end_time TIMESTAMP,              -- 实际完工时间（最后一个工人完工时更新）
       total_work_hours DECIMAL(10,2),         -- 累计工时（汇总自工人任务）
       remark VARCHAR(500),
       -- 标准字段
       create_dept BIGINT,
       create_by BIGINT,
       create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       update_by BIGINT,
       update_time TIMESTAMP,
       tenant_id VARCHAR(20) DEFAULT '000000',
       del_flag CHAR(1) DEFAULT '0'
   );

   -- 唯一约束：同一工单+工序只能有一张有效派工单（未取消）
   CREATE UNIQUE INDEX uk_dispatch_order_process ON product_work_dispatch(work_order_id,
  process_id)
       WHERE del_flag = '0' AND status != '9';

   -- 索引
   CREATE INDEX idx_dispatch_work_order ON product_work_dispatch(work_order_id);
   CREATE INDEX idx_dispatch_process ON product_work_dispatch(process_id);
   CREATE INDEX idx_dispatch_team ON product_work_dispatch(team_id);
   CREATE INDEX idx_dispatch_leader ON product_work_dispatch(team_leader_id);
   CREATE INDEX idx_dispatch_status ON product_work_dispatch(status);
   CREATE INDEX idx_dispatch_tenant ON product_work_dispatch(tenant_id);
   CREATE INDEX idx_dispatch_no ON product_work_dispatch(dispatch_no);

   COMMENT ON TABLE product_work_dispatch IS '班组派工单';
   COMMENT ON COLUMN product_work_dispatch.dispatch_no IS '派工单号，格式：PG+年月日+序
  号';

   -- =============================================
   -- 工人任务单（二级派工：班组长→工人）
   -- =============================================
   CREATE TABLE product_work_dispatch_detail (
       id BIGSERIAL PRIMARY KEY,
       task_no VARCHAR(50) NOT NULL,           -- 任务单号（唯一）
       dispatch_id BIGINT NOT NULL,            -- 班组派工单ID（FK →
  product_work_dispatch.id）
       dispatch_no VARCHAR(50),                -- 派工单号（冗余）
       work_order_id BIGINT NOT NULL,          -- 生产工单ID（冗余，便于查询）
       process_id BIGINT NOT NULL,             -- 工序ID（冗余）
       worker_id BIGINT NOT NULL,              -- 工人ID（FK → sys_user.user_id）
       worker_name VARCHAR(100),               -- 工人姓名（冗余）
       station_id BIGINT,                      -- 工位ID（FK → product_station.id）
       station_name VARCHAR(100),              -- 工位名称（冗余）
       equipment_id BIGINT,                    -- 设备ID（可选扩展）
       plan_qty DECIMAL(20,3) NOT NULL,        -- 分配数量
       finish_qty DECIMAL(20,3) DEFAULT 0,     -- 完成数量
       qualified_qty DECIMAL(20,3) DEFAULT 0,  -- 合格数量
       unqualified_qty DECIMAL(20,3) DEFAULT 0,-- 不合格数量
       scrap_qty DECIMAL(20,3) DEFAULT 0,      -- 报废数量
       rework_qty DECIMAL(20,3) DEFAULT 0,     -- 返工数量
       status VARCHAR(10) DEFAULT '0',         -- 状态：0=待开工,1=进行中,2=已完成,3=已暂
  停,9=已取消
       plan_start_time TIMESTAMP,              -- 计划开工时间
       plan_end_time TIMESTAMP,                -- 计划完工时间
       actual_start_time TIMESTAMP,            -- 实际开工时间
       actual_end_time TIMESTAMP,              -- 实际完工时间
       work_hours DECIMAL(10,2),               -- 工时（小时）= end_time - start_time
       break_hours DECIMAL(10,2) DEFAULT 0,    -- 休息时间（小时）
       effective_hours DECIMAL(10,2),          -- 有效工时 = work_hours - break_hours
       first_inspect_passed CHAR(1) DEFAULT 'N', -- 首检是否通过：Y/N
       remark VARCHAR(500),
       -- 标准字段
       create_dept BIGINT,
       create_by BIGINT,
       create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       update_by BIGINT,
       update_time TIMESTAMP,
       tenant_id VARCHAR(20) DEFAULT '000000',
       del_flag CHAR(1) DEFAULT '0'
   );

   -- 索引
   CREATE INDEX idx_task_dispatch ON product_work_dispatch_detail(dispatch_id);
   CREATE INDEX idx_task_worker ON product_work_dispatch_detail(worker_id);
   CREATE INDEX idx_task_station ON product_work_dispatch_detail(station_id);
   CREATE INDEX idx_task_work_order ON product_work_dispatch_detail(work_order_id);
   CREATE INDEX idx_task_status ON product_work_dispatch_detail(status);
   CREATE INDEX idx_task_tenant ON product_work_dispatch_detail(tenant_id);
   CREATE INDEX idx_task_no ON product_work_dispatch_detail(task_no);

   COMMENT ON TABLE product_work_dispatch_detail IS '工人任务单';
   COMMENT ON COLUMN product_work_dispatch_detail.task_no IS '任务单号，格式：RW+年月日
  +序号';

   业务规则：
   ┌──────────────┬──────────────────────────────────────────────┐
   │     规则     │                     说明                     │
   ├──────────────┼──────────────────────────────────────────────┤
   │ 派工数量约束 │ 派工数量 ≤ 工序计划数量                      │
   ├──────────────┼──────────────────────────────────────────────┤
   │ 分派数量约束 │ 已分派数量 ≤ 派工数量                        │
   ├──────────────┼──────────────────────────────────────────────┤
   │ 完成数量汇总 │ 派工单完成数量 = SUM(工人任务.完成数量)      │
   ├──────────────┼──────────────────────────────────────────────┤
   │ 工时汇总     │ 派工单累计工时 = SUM(工人任务.有效工时)      │
   ├──────────────┼──────────────────────────────────────────────┤
   │ 状态联动     │ 首个工人开工 → 派工单状态变为进行中          │
   ├──────────────┼──────────────────────────────────────────────┤
   │ 状态联动     │ 所有工人完成 → 派工单状态变为已完成          │
   ├──────────────┼──────────────────────────────────────────────┤
   │ 取消约束     │ 进行中的派工单不可取消，需先暂停所有工人任务 │
   └──────────────┴──────────────────────────────────────────────┘
   功能清单：
   - 工序派给班组长（一级派工）
   - 班组长分派给工人（二级派工）
   - 工人开工/报工/完工
   - 班组长汇总进度
   - 工时统计

   前端页面：
   - 工单工序tab → 增加"派工"按钮
   - 班组派工弹窗（选班组、班组长）
   - 班组长工作台页面（分派工人、查看进度）
   - 工人报工页面/弹窗

   4.2 第2阶段：检验管理

   目标：实现生产过程检验 + 来料检验

   检验类型：
   ┌──────────┬────────────────┬────────────┐
   │   类型   │    触发时机    │  关联单据  │
   ├──────────┼────────────────┼────────────┤
   │ 首件检验 │ 派工开工后首件 │ 派工单     │
   ├──────────┼────────────────┼────────────┤
   │ 过程检验 │ 生产过程中抽检 │ 派工单     │
   ├──────────┼────────────────┼────────────┤
   │ 完工检验 │ 工序完成时     │ 派工单     │
   ├──────────┼────────────────┼────────────┤
   │ 来料检验 │ 采购入库时     │ 采购到货单 │
   └──────────┴────────────────┴────────────┘
   新增数据表（完整定义含约束与索引）：

   -- =============================================
   -- 检验单主表
   -- =============================================
   CREATE TABLE product_inspect (
       id BIGSERIAL PRIMARY KEY,
       inspect_no VARCHAR(50) NOT NULL,        -- 检验单号（唯一）
       inspect_type VARCHAR(20) NOT NULL,      -- 检验类型：first/process/final/incoming
       source_type VARCHAR(20),                -- 来源类型：work_dispatch(派工单)/
  purchase_arrival(采购到货)
       source_id BIGINT,                       -- 来源单据ID
       source_no VARCHAR(100),                 -- 来源单据号（冗余）
       -- 生产检验关联
       work_order_id BIGINT,                   -- 生产工单ID
       work_order_no VARCHAR(50),              -- 工单号（冗余）
       dispatch_id BIGINT,                     -- 派工单ID
       task_id BIGINT,                         -- 工人任务单ID
       process_id BIGINT,                      -- 工序ID
       process_name VARCHAR(200),              -- 工序名称（冗余）
       route_id BIGINT,                        -- 工艺路线ID
       route_version VARCHAR(50),              -- 工艺版本（冗余）
       -- 来料检验关联
       arrival_id BIGINT,                      -- 采购到货单ID
       arrival_detail_id BIGINT,               -- 到货明细ID
       merchant_id BIGINT,                     -- 供应商ID
       merchant_name VARCHAR(200),             -- 供应商名称（冗余）
       -- 产品/物料信息
       sku_id BIGINT NOT NULL,                 -- SKU ID
       goods_id BIGINT,                        -- 商品ID
       goods_name VARCHAR(200),                -- 商品名称（冗余）
       sku_name VARCHAR(200),                  -- 规格名称（冗余）
       batch_no VARCHAR(100),                  -- 批次号
       bom_id BIGINT,                          -- BOM ID（生产检验时）
       bom_version VARCHAR(50),                -- BOM版本（冗余）
       unit_id BIGINT,                         -- 单位ID
       -- 检验数量
       inspect_qty DECIMAL(20,3) NOT NULL,     -- 送检数量
       sample_qty DECIMAL(20,3),               -- 抽样数量（根据抽样规则计算）
       sample_rule VARCHAR(50),                -- 使用的抽样规则
       qualified_qty DECIMAL(20,3) DEFAULT 0,  -- 合格数量
       unqualified_qty DECIMAL(20,3) DEFAULT 0,-- 不合格数量
       scrap_qty DECIMAL(20,3) DEFAULT 0,      -- 报废数量
       rework_qty DECIMAL(20,3) DEFAULT 0,     -- 返工数量
       return_qty DECIMAL(20,3) DEFAULT 0,     -- 退货数量（来料检验）
       -- 状态与结论
       status VARCHAR(10) DEFAULT '0',         -- 状态：0=待检,1=检验中,2=已完成
       result VARCHAR(20),                     -- 检验结论：pass/fail/conditional
       result_desc VARCHAR(500),               -- 结论说明
       handle_type VARCHAR(20),                -- 处理方式：accept(接收)/rework(返工)/
  scrap(报废)/return(退货)
       handle_id BIGINT,                       -- 处理单ID（返工单/报废单/退货单）
       -- 检验人员
       inspector_id BIGINT,                    -- 检验员ID
       inspector_name VARCHAR(100),            -- 检验员姓名
       inspect_time TIMESTAMP,                 -- 检验完成时间
       submit_time TIMESTAMP,                  -- 提交时间
       -- 标准来源
       standard_id BIGINT,                     -- 使用的检验标准ID
       remark VARCHAR(500),
       -- 标准字段
       create_dept BIGINT,
       create_by BIGINT,
       create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       update_by BIGINT,
       update_time TIMESTAMP,
       tenant_id VARCHAR(20) DEFAULT '000000',
       del_flag CHAR(1) DEFAULT '0'
   );

   -- 唯一约束：首检单每个工人任务只能有一张
   CREATE UNIQUE INDEX uk_inspect_first ON product_inspect(task_id, inspect_type)
       WHERE del_flag = '0' AND inspect_type = 'first';

   -- 索引
   CREATE INDEX idx_inspect_no ON product_inspect(inspect_no);
   CREATE INDEX idx_inspect_type ON product_inspect(inspect_type);
   CREATE INDEX idx_inspect_work_order ON product_inspect(work_order_id);
   CREATE INDEX idx_inspect_dispatch ON product_inspect(dispatch_id);
   CREATE INDEX idx_inspect_task ON product_inspect(task_id);
   CREATE INDEX idx_inspect_arrival ON product_inspect(arrival_id);
   CREATE INDEX idx_inspect_sku ON product_inspect(sku_id);
   CREATE INDEX idx_inspect_status ON product_inspect(status);
   CREATE INDEX idx_inspect_result ON product_inspect(result);
   CREATE INDEX idx_inspect_tenant ON product_inspect(tenant_id);

   -- =============================================
   -- 检验项明细
   -- =============================================
   CREATE TABLE product_inspect_item (
       id BIGSERIAL PRIMARY KEY,
       inspect_id BIGINT NOT NULL,             -- 检验单ID（FK）
       standard_item_id BIGINT,                -- 检验标准项ID（来源）
       item_no INT,                            -- 检验项序号
       item_code VARCHAR(50),                  -- 检验项编码
       item_name VARCHAR(200) NOT NULL,        -- 检验项名称
       item_category VARCHAR(50),              -- 检验项分类（外观/尺寸/功能/性能）
       inspect_method VARCHAR(200),            -- 检验方法
       inspect_tool VARCHAR(100),              -- 检验工具/仪器
       standard_value VARCHAR(100),            -- 标准值（定性）
       upper_limit DECIMAL(15,4),              -- 上限（定量）
       lower_limit DECIMAL(15,4),              -- 下限（定量）
       target_value DECIMAL(15,4),             -- 目标值
       actual_value VARCHAR(100),              -- 实测值
       unit VARCHAR(20),                       -- 单位
       is_qualified CHAR(1),                   -- 是否合格：Y/N
       is_critical CHAR(1) DEFAULT 'N',        -- 是否关键项：Y/N
       defect_type VARCHAR(50),                -- 缺陷类型编码（不合格时）
       defect_desc VARCHAR(500),               -- 缺陷描述
       remark VARCHAR(500),
       -- 标准字段
       create_dept BIGINT,
       create_by BIGINT,
       create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       update_by BIGINT,
       update_time TIMESTAMP,
       tenant_id VARCHAR(20) DEFAULT '000000',
       del_flag CHAR(1) DEFAULT '0'
   );

   CREATE INDEX idx_inspect_item_inspect ON product_inspect_item(inspect_id);
   CREATE INDEX idx_inspect_item_qualified ON product_inspect_item(is_qualified);

   -- =============================================
   -- 检验标准库（标准主表）
   -- =============================================
   CREATE TABLE product_inspect_standard (
       id BIGSERIAL PRIMARY KEY,
       standard_no VARCHAR(50) NOT NULL,       -- 标准编号（唯一）
       standard_name VARCHAR(200) NOT NULL,    -- 标准名称
       standard_type VARCHAR(20),              --
   标准类型：sku(产品级)/category(分类级)/process(工序级)/global(全局)
       inspect_type VARCHAR(20),               -- 适用检验类型：first/process/final/
  incoming/all
       -- 适用范围（按优先级匹配）
       sku_id BIGINT,                          -- 产品SKU ID（最高优先级）
       goods_id BIGINT,                        -- 商品ID
       category_id BIGINT,                     -- 产品分类ID
       process_id BIGINT,                      -- 工序ID（生产检验）
       process_code VARCHAR(50),               -- 工序编码
       merchant_id BIGINT,                     -- 供应商ID（来料检验）
       -- 抽样规则
       sample_method VARCHAR(50),              -- 抽样方法：full(全检)/ratio(比例)/
  aql(AQL抽样)
       sample_ratio DECIMAL(5,2),              -- 抽样比例（%）
       sample_size INT,                        -- 固定抽样数量
       aql_level VARCHAR(20),                  -- AQL水平
       -- 状态
       status VARCHAR(10) DEFAULT '1',         -- 状态：0=禁用,1=启用
       version INT DEFAULT 1,                  -- 版本号
       effective_date DATE,                    -- 生效日期
       expiry_date DATE,                       -- 失效日期
       remark VARCHAR(500),
       -- 标准字段
       create_dept BIGINT,
       create_by BIGINT,
       create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       update_by BIGINT,
       update_time TIMESTAMP,
       tenant_id VARCHAR(20) DEFAULT '000000',
       del_flag CHAR(1) DEFAULT '0'
   );

   CREATE UNIQUE INDEX uk_standard_no ON product_inspect_standard(standard_no, tenant_id)
  WHERE del_flag = '0';
   CREATE INDEX idx_standard_sku ON product_inspect_standard(sku_id);
   CREATE INDEX idx_standard_category ON product_inspect_standard(category_id);
   CREATE INDEX idx_standard_process ON product_inspect_standard(process_id);
   CREATE INDEX idx_standard_type ON product_inspect_standard(inspect_type);

   -- =============================================
   -- 检验标准项（标准明细）
   -- =============================================
   CREATE TABLE product_inspect_standard_item (
       id BIGSERIAL PRIMARY KEY,
       standard_id BIGINT NOT NULL,            -- 检验标准ID（FK）
       item_no INT,                            -- 检验项序号
       item_code VARCHAR(50),                  -- 检验项编码
       item_name VARCHAR(200) NOT NULL,        -- 检验项名称
       item_category VARCHAR(50),              -- 检验项分类
       inspect_method VARCHAR(200),            -- 检验方法
       inspect_tool VARCHAR(100),              -- 检验工具
       value_type VARCHAR(20) DEFAULT 'range', -- 值类型：range(范围)/enum(枚举)/text(文
  本)
       standard_value VARCHAR(100),            -- 标准值（枚举/文本）
       upper_limit DECIMAL(15,4),              -- 上限（范围）
       lower_limit DECIMAL(15,4),              -- 下限（范围）
       target_value DECIMAL(15,4),             -- 目标值
       unit VARCHAR(20),                       -- 单位
       is_required CHAR(1) DEFAULT 'Y',        -- 是否必检：Y/N
       is_critical CHAR(1) DEFAULT 'N',        -- 是否关键项：Y/N
       sort_order INT DEFAULT 0,               -- 排序
       remark VARCHAR(500),
       -- 标准字段
       create_dept BIGINT,
       create_by BIGINT,
       create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       update_by BIGINT,
       update_time TIMESTAMP,
       tenant_id VARCHAR(20) DEFAULT '000000',
       del_flag CHAR(1) DEFAULT '0'
   );

   CREATE INDEX idx_standard_item_standard ON product_inspect_standard_item(standard_id);

   ---
   5.2.2 检验标准选取策略

   匹配优先级（从高到低）：

   1. SKU + 工序 + 检验类型（精确匹配）
      WHERE sku_id = ? AND process_id = ? AND inspect_type = ?

   2. SKU + 检验类型（产品级）
      WHERE sku_id = ? AND process_id IS NULL AND inspect_type = ?

   3. 商品 + 工序 + 检验类型
      WHERE goods_id = ? AND process_id = ? AND inspect_type = ?

   4. 分类 + 工序 + 检验类型
      WHERE category_id = ? AND process_id = ? AND inspect_type = ?

   5. 分类 + 检验类型
      WHERE category_id = ? AND process_id IS NULL AND inspect_type = ?

   6. 全局 + 工序 + 检验类型
      WHERE sku_id IS NULL AND category_id IS NULL AND process_id = ? AND inspect_type
  = ?

   7. 全局 + 检验类型
      WHERE sku_id IS NULL AND category_id IS NULL AND process_id IS NULL AND
  inspect_type IN (?, 'all')

   Java实现示例：

   public List<InspectStandardItem> matchStandard(Long skuId, Long goodsId, Long
  categoryId,
                                                   Long processId, String inspectType) {
       // 按优先级依次匹配
       List<InspectStandard> standards = standardMapper.selectByPriority(
           skuId, goodsId, categoryId, processId, inspectType
       );

       if (standards.isEmpty()) {
           return Collections.emptyList();
       }

       // 返回第一个匹配的标准的检验项
       return standardItemMapper.selectByStandardId(standards.get(0).getId());
   }

   ---
   5.2.3 抽样规则计算

   public int calculateSampleSize(String sampleMethod, BigDecimal sampleRatio,
                                   Integer sampleSize, BigDecimal inspectQty) {
       switch (sampleMethod) {
           case "full":
               // 全检
               return inspectQty.intValue();

           case "ratio":
               // 按比例抽样
               return inspectQty.multiply(sampleRatio).divide(new BigDecimal(100))
                   .setScale(0, RoundingMode.CEILING).intValue();

           case "fixed":
               // 固定数量
               return Math.min(sampleSize, inspectQty.intValue());

           case "aql":
               // AQL抽样表（简化版）
               return getAqlSampleSize(inspectQty.intValue(), aqlLevel);

           default:
               return inspectQty.intValue(); // 默认全检
       }
   }

   // AQL抽样表（GB/T 2828.1-2012 简化版）
   private int getAqlSampleSize(int lotSize, String aqlLevel) {
       // 批量范围 → 样本量
       if (lotSize <= 8) return lotSize;
       if (lotSize <= 15) return 3;
       if (lotSize <= 25) return 5;
       if (lotSize <= 50) return 8;
       if (lotSize <= 90) return 13;
       if (lotSize <= 150) return 20;
       if (lotSize <= 280) return 32;
       if (lotSize <= 500) return 50;
       if (lotSize <= 1200) return 80;
       return 125;
   }

   ---
   5.2.4 检验结果回写规则

   检验完成后触发回写：

   ┌─────────────────────────────────────────────────────────────────────────────┐
   │ 生产检验（首检/过程检/完工检）                                               │
   ├─────────────────────────────────────────────────────────────────────────────┤
   │                                                                             │
   │  检验单.result = 'pass'                                                     │
   │      │                                                                      │
   │      ├──▶ 工人任务单.qualified_qty += 检验单.qualified_qty                  │
   │      ├──▶ 工人任务单.first_inspect_passed = 'Y'（首检时）                   │
   │      └──▶ 派工单.qualified_qty = SUM(工人任务.qualified_qty)                │
   │                                                                             │
   │  检验单.result = 'fail'                                                     │
   │      │                                                                      │
   │      ├──▶ 工人任务单.unqualified_qty += 检验单.unqualified_qty              │
   │      ├──▶ 派工单.unqualified_qty = SUM(工人任务.unqualified_qty)            │
   │      │                                                                      │
   │      └──▶ 根据 handle_type 处理：                                           │
   │           ├── rework → 生成返工任务，工人任务.rework_qty += 数量            │
   │           ├── scrap  → 生成报废单，工人任务.scrap_qty += 数量               │
   │           └── conditional → 人工确认后继续                                  │
   │                                                                             │
   └─────────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────────────────┐
   │ 来料检验                                                                    │
   ├─────────────────────────────────────────────────────────────────────────────┤
   │                                                                             │
   │  检验单.result = 'pass'                                                     │
   │      │                                                                      │
   │      └──▶ 到货明细.inspect_status = 'pass'，允许入库                        │
   │                                                                             │
   │  检验单.result = 'fail'                                                     │
   │      │                                                                      │
   │      └──▶ 根据 handle_type 处理：                                           │
   │           ├── return → 生成退货单，到货明细.return_qty += 数量              │
   │           ├── scrap  → 生成报废单，到货明细.scrap_qty += 数量               │
   │           └── conditional → 人工确认后允许入库                              │
   │                                                                             │
   └─────────────────────────────────────────────────────────────────────────────┘

   功能清单：

   生产过程检验：
   - 首件检验：工人报工时触发
   - 过程检验：按抽检规则触发
   - 完工检验：工序完成时触发
   - 检验结果录入 → 更新派工单合格/不合格数量

   来料检验：
   - 采购到货时自动/手动生成检验单
   - 检验合格 → 允许入库
   - 检验不合格 → 退货/让步接收

   不合格品处理：
   - 返工处理
   - 报废处理
   - 退货处理（来料）

   前端页面：
   - 检验单列表页
   - 检验录入页面
   - 检验标准库管理页面
   - 采购到货页面增加"送检"按钮

   4.3 第3阶段：生产过程管理

   目标：实时跟踪生产进度，与派工系统联动

   工序与派工的耦合关系

   product_work_process.status 更新规则：

     派工单创建成功 → process.dispatch_status = '1'（已派工）
     首个工人任务开工 → process.status = '1'（进行中）
     所有工人任务完成 → process.status = '2'（已完成）
     所有工人任务暂停 → process.status = '3'（已暂停）

   数量与工时累加口径

   【按工人任务单累加到派工单】
   工人任务.finish_qty      ─汇总─▶ 派工单.finish_qty
   工人任务.qualified_qty   ─汇总─▶ 派工单.qualified_qty
   工人任务.effective_hours ─汇总─▶ 派工单.total_work_hours

   【派工单回写到工序】
   派工单.finish_qty        ─回写─▶ 工序.finish_qty
   派工单.qualified_qty     ─回写─▶ 工序.qualified_qty
   派工单.total_work_hours  ─回写─▶ 工序.work_hours

   【触发时机】
   - 工人报工时（增量更新）
   - 工人完工时（最终确认）
   - 检验结果提交时（更新合格/不合格数量）

   进度百分比计算

   // 工序进度 = 完成数量 / 计划数量 * 100
   int progress = finishQty.divide(planQty).multiply(100).intValue();
   // 最大100%

   // 工单整体进度 = 已完成工序数 / 总工序数 * 100
   int orderProgress = completedProcessCount * 100 / totalProcessCount;

   增强现有表：

   ALTER TABLE product_work_process ADD COLUMN IF NOT EXISTS dispatch_status VARCHAR(10);
  -- 派工状态
   ALTER TABLE product_work_process ADD COLUMN IF NOT EXISTS dispatch_id BIGINT;
  -- 派工单ID
   ALTER TABLE product_work_process ADD COLUMN IF NOT EXISTS actual_start_time TIMESTAMP;
  -- 实际开工
   ALTER TABLE product_work_process ADD COLUMN IF NOT EXISTS actual_end_time TIMESTAMP;
  -- 实际完工
   ALTER TABLE product_work_process ADD COLUMN IF NOT EXISTS finish_qty DECIMAL(20,3);
  -- 完成数量
   ALTER TABLE product_work_process ADD COLUMN IF NOT EXISTS qualified_qty DECIMAL(20,3);
  -- 合格数量
   ALTER TABLE product_work_process ADD COLUMN IF NOT EXISTS progress INT DEFAULT 0;
  -- 进度百分比
   ALTER TABLE product_work_process ADD COLUMN IF NOT EXISTS work_hours DECIMAL(10,2);
  -- 累计工时

   CREATE INDEX IF NOT EXISTS idx_process_dispatch ON product_work_process(dispatch_id);

   功能清单：
   - 工序状态自动联动（由派工任务驱动）
   - 进度百分比实时更新
   - 工时自动汇总（按工人任务累加）
   - 数量回写保证一致性（事务控制）
   - 生产看板（甘特图/进度条）

   4.4 第4阶段：工艺过程卡管理

   目标：完善工艺路线，支持完整的工艺过程卡管理

   现有基础

   现有 product_process_route 和 product_process_route_detail 表已支持：
   - ✅ 工艺路线版本管理（version, versionType, isDefault）
   - ✅ 工序基本信息（seqNo, processCode, processName, processDesc）
   - ✅ 5大时间参数（waitTime, setupTime, processTime, teardownTime, transferTime）
   - ✅ 资源配置（workCenterId, productionLineId, workstationType）
   - ✅ 质量标记（isInspection, isHandover, isReport, isBackflush）
   - ✅ 审批流程（checkedStatus）

   需要扩展的表结构

   -- =============================================
   -- 工艺路线工具配置表（刀具/夹具/量具）
   -- =============================================
   CREATE TABLE product_process_route_tool (
       id BIGSERIAL PRIMARY KEY,
       route_detail_id BIGINT NOT NULL,        -- 工序明细ID（FK →
  product_process_route_detail.id）
       tool_type VARCHAR(20) NOT NULL,         --
   工具类型：cutting(刀具)/fixture(夹具)/gauge(量具)/auxiliary(辅具)
       tool_code VARCHAR(50),                  -- 工具编码
       tool_name VARCHAR(200) NOT NULL,        -- 工具名称
       specification VARCHAR(200),             -- 规格型号
       quantity INT DEFAULT 1,                 -- 数量
       is_required CHAR(1) DEFAULT 'Y',        -- 是否必须：Y/N
       usage_desc VARCHAR(500),                -- 使用说明
       remark VARCHAR(500),
       -- 标准字段
       create_dept BIGINT, create_by BIGINT, create_time TIMESTAMP DEFAULT
  CURRENT_TIMESTAMP,
       update_by BIGINT, update_time TIMESTAMP, tenant_id VARCHAR(20) DEFAULT '000000',
  del_flag CHAR(1) DEFAULT
   '0'
   );

   CREATE INDEX idx_route_tool_detail ON product_process_route_tool(route_detail_id);
   COMMENT ON TABLE product_process_route_tool IS '工艺路线工具配置表';

   -- =============================================
   -- 工艺路线质量标准表
   -- =============================================
   CREATE TABLE product_process_route_quality (
       id BIGSERIAL PRIMARY KEY,
       route_detail_id BIGINT NOT NULL,        -- 工序明细ID
       item_no INT,                            -- 检验项序号
       item_code VARCHAR(50),                  -- 检验项编码
       item_name VARCHAR(200) NOT NULL,        -- 检验项名称
       item_category VARCHAR(50),              --
   分类：dimension(尺寸)/appearance(外观)/function(功能)/performance(性能)
       standard_value VARCHAR(100),            -- 标准值（定性）
       target_value DECIMAL(15,4),             -- 目标值（定量）
       upper_limit DECIMAL(15,4),              -- 上限
       lower_limit DECIMAL(15,4),              -- 下限
       unit VARCHAR(20),                       -- 单位
       inspect_method VARCHAR(200),            -- 检验方法
       inspect_tool VARCHAR(100),              -- 检验工具
       is_critical CHAR(1) DEFAULT 'N',        -- 是否关键项：Y/N
       sample_rule VARCHAR(50),                -- 抽样规则
       remark VARCHAR(500),
       -- 标准字段
       create_dept BIGINT, create_by BIGINT, create_time TIMESTAMP DEFAULT
  CURRENT_TIMESTAMP,
       update_by BIGINT, update_time TIMESTAMP, tenant_id VARCHAR(20) DEFAULT '000000',
  del_flag CHAR(1) DEFAULT
   '0'
   );

   CREATE INDEX idx_route_quality_detail ON
  product_process_route_quality(route_detail_id);
   COMMENT ON TABLE product_process_route_quality IS '工艺路线质量标准表';

   -- =============================================
   -- 工艺路线操作规范表（详细操作步骤）
   -- =============================================
   CREATE TABLE product_process_route_operation (
       id BIGSERIAL PRIMARY KEY,
       route_detail_id BIGINT NOT NULL,        -- 工序明细ID
       step_no INT NOT NULL,                   -- 步骤序号
       step_title VARCHAR(200) NOT NULL,       -- 步骤标题
       step_content TEXT,                      -- 步骤内容（详细描述）
       step_image VARCHAR(500),                -- 步骤示意图（OSS路径）
       duration_minutes INT,                   -- 预计耗时（分钟）
       key_points VARCHAR(500),                -- 操作要点
       safety_note VARCHAR(500),               -- 安全注意事项
       quality_note VARCHAR(500),              -- 质量注意事项
       remark VARCHAR(500),
       -- 标准字段
       create_dept BIGINT, create_by BIGINT, create_time TIMESTAMP DEFAULT
  CURRENT_TIMESTAMP,
       update_by BIGINT, update_time TIMESTAMP, tenant_id VARCHAR(20) DEFAULT '000000',
  del_flag CHAR(1) DEFAULT
   '0'
   );

   CREATE INDEX idx_route_operation_detail ON
  product_process_route_operation(route_detail_id);
   COMMENT ON TABLE product_process_route_operation IS '工艺路线操作规范表';

   -- =============================================
   -- 工艺路线设备配置表
   -- =============================================
   CREATE TABLE product_process_route_equipment (
       id BIGSERIAL PRIMARY KEY,
       route_detail_id BIGINT NOT NULL,        -- 工序明细ID
       equipment_id BIGINT,                    -- 设备ID（关联设备台账）
       equipment_code VARCHAR(50),             -- 设备编码
       equipment_name VARCHAR(200) NOT NULL,   -- 设备名称
       equipment_type VARCHAR(50),             -- 设备类型
       is_required CHAR(1) DEFAULT 'Y',        -- 是否必须：Y/N
       usage_desc VARCHAR(500),                -- 使用说明
       param_settings VARCHAR(1000),           -- 设备参数设置（JSON格式）
       remark VARCHAR(500),
       -- 标准字段
       create_dept BIGINT, create_by BIGINT, create_time TIMESTAMP DEFAULT
  CURRENT_TIMESTAMP,
       update_by BIGINT, update_time TIMESTAMP, tenant_id VARCHAR(20) DEFAULT '000000',
  del_flag CHAR(1) DEFAULT
   '0'
   );

   CREATE INDEX idx_route_equipment_detail ON
  product_process_route_equipment(route_detail_id);
   COMMENT ON TABLE product_process_route_equipment IS '工艺路线设备配置表';

   -- =============================================
   -- 工艺路线物料配置表（工序级物料消耗）
   -- =============================================
   CREATE TABLE product_process_route_material (
       id BIGSERIAL PRIMARY KEY,
       route_detail_id BIGINT NOT NULL,        -- 工序明细ID
       sku_id BIGINT NOT NULL,                 -- 物料SKU ID
       goods_id BIGINT,                        -- 商品ID
       goods_name VARCHAR(200),                -- 商品名称（冗余）
       sku_name VARCHAR(200),                  -- 规格名称（冗余）
       unit_id BIGINT,                         -- 单位ID
       consume_qty DECIMAL(20,6) NOT NULL,     -- 消耗数量（单件产品）
       loss_rate DECIMAL(5,2) DEFAULT 0,       -- 损耗率（%）
       is_backflush CHAR(1) DEFAULT 'N',       -- 是否倒冲：Y/N
       remark VARCHAR(500),
       -- 标准字段
       create_dept BIGINT, create_by BIGINT, create_time TIMESTAMP DEFAULT
  CURRENT_TIMESTAMP,
       update_by BIGINT, update_time TIMESTAMP, tenant_id VARCHAR(20) DEFAULT '000000',
  del_flag CHAR(1) DEFAULT
   '0'
   );

   CREATE INDEX idx_route_material_detail ON
  product_process_route_material(route_detail_id);
   CREATE INDEX idx_route_material_sku ON product_process_route_material(sku_id);
   COMMENT ON TABLE product_process_route_material IS '工艺路线物料配置表';

   -- =============================================
   -- 工艺路线明细表增加卡粒度配置字段
   -- =============================================
   ALTER TABLE product_process_route_detail
       ADD COLUMN IF NOT EXISTS card_granularity VARCHAR(20) DEFAULT 'per_batch';
       -- per_item = 一物一卡（每个产品个体独立卡）
       -- per_batch = 一批一卡（一批产品共用一张卡，默认）

   COMMENT ON COLUMN product_process_route_detail.card_granularity IS
   '过程卡粒度：per_item=一物一卡,per_batch=一批一卡';

   -- =============================================
   -- 工艺过程卡实例表（工单下达时自动生成）
   -- =============================================
   CREATE TABLE product_process_card (
       id BIGSERIAL PRIMARY KEY,
       card_no VARCHAR(50) NOT NULL,           -- 过程卡编号（唯一）
       card_granularity VARCHAR(20) NOT NULL,  -- 卡粒度：per_item/per_batch
       -- 工单关联
       work_order_id BIGINT NOT NULL,          -- 生产工单ID（FK →
  product_work_order.id）
       work_order_no VARCHAR(50),              -- 工单号（冗余）
       process_id BIGINT NOT NULL,             -- 工单工序ID（FK →
  product_work_process.id）
       -- 产品信息
       sku_id BIGINT NOT NULL,                 -- 产品SKU ID
       goods_name VARCHAR(200),                -- 商品名称（冗余）
       sku_name VARCHAR(200),                  -- 规格名称（冗余）
       batch_no VARCHAR(100),                  -- 批次号（一批一卡时填写）
       serial_no VARCHAR(100),                 -- 序列号（一物一卡时填写）
       -- 工艺来源
       route_id BIGINT,                        -- 工艺路线ID
       route_version VARCHAR(50),              -- 工艺版本
       route_detail_id BIGINT,                 -- 工艺路线明细ID（模板来源）
       -- 工序信息（从模板复制，允许现场调整）
       process_seq INT,                        -- 工序顺序
       process_code VARCHAR(50),               -- 工序编码
       process_name VARCHAR(200),              -- 工序名称
       process_desc TEXT,                      -- 工序描述
       -- 生产数量
       plan_qty DECIMAL(20,3),                 -- 计划数量
       finish_qty DECIMAL(20,3) DEFAULT 0,     -- 完成数量
       qualified_qty DECIMAL(20,3) DEFAULT 0,  -- 合格数量
       -- 状态
       status VARCHAR(10) DEFAULT '0',         -- 状态：0=待生产,1=生产中,2=已完成,9=已作
  废
       -- 关联派工
       dispatch_id BIGINT,                     -- 派工单ID
       -- 标准字段
       create_dept BIGINT, create_by BIGINT, create_time TIMESTAMP DEFAULT
  CURRENT_TIMESTAMP,
       update_by BIGINT, update_time TIMESTAMP, tenant_id VARCHAR(20) DEFAULT '000000',
  del_flag CHAR(1) DEFAULT
   '0'
   );

   CREATE UNIQUE INDEX uk_card_no ON product_process_card(card_no, tenant_id) WHERE
  del_flag = '0';
   CREATE INDEX idx_card_work_order ON product_process_card(work_order_id);
   CREATE INDEX idx_card_process ON product_process_card(process_id);
   CREATE INDEX idx_card_batch ON product_process_card(batch_no);
   CREATE INDEX idx_card_serial ON product_process_card(serial_no);
   CREATE INDEX idx_card_dispatch ON product_process_card(dispatch_id);
   COMMENT ON TABLE product_process_card IS '工艺过程卡实例表';
   COMMENT ON COLUMN product_process_card.card_no IS '过程卡编号，格式：PC+年月日+序号';

   -- =============================================
   -- 工艺过程卡明细表（工具/质量/操作等关联到实例）
   -- =============================================
   CREATE TABLE product_process_card_detail (
       id BIGSERIAL PRIMARY KEY,
       card_id BIGINT NOT NULL,                -- 过程卡ID（FK →
  product_process_card.id）
       detail_type VARCHAR(20) NOT NULL,       -- 明细类型：tool/quality/operation/
  equipment/material
       source_id BIGINT,                       -- 来源ID（模板明细ID）
       -- 通用字段（根据类型使用）
       item_no INT,                            -- 序号
       item_code VARCHAR(50),                  -- 编码
       item_name VARCHAR(200),                 -- 名称
       item_content TEXT,                      -- 内容（JSON格式，根据类型不同存储不同数
  据）
       -- 执行记录（生产现场填写）
       actual_value VARCHAR(200),              -- 实际值（质量检验用）
       is_qualified CHAR(1),                   -- 是否合格（质量检验用）
       execute_time TIMESTAMP,                 -- 执行时间
       executor_id BIGINT,                     -- 执行人ID
       executor_name VARCHAR(100),             -- 执行人姓名
       remark VARCHAR(500),
       -- 标准字段
       create_dept BIGINT, create_by BIGINT, create_time TIMESTAMP DEFAULT
  CURRENT_TIMESTAMP,
       update_by BIGINT, update_time TIMESTAMP, tenant_id VARCHAR(20) DEFAULT '000000',
  del_flag CHAR(1) DEFAULT
   '0'
   );

   CREATE INDEX idx_card_detail_card ON product_process_card_detail(card_id);
   CREATE INDEX idx_card_detail_type ON product_process_card_detail(detail_type);
   COMMENT ON TABLE product_process_card_detail IS '工艺过程卡明细表';

   过程卡生成规则

   工单下达（审批通过）时触发过程卡生成：

   ┌─────────────────────────────────────────────────────────────────────────────┐
   │ 工单下达 → 遍历工单工序                                                      │
   │     │                                                                       │
   │     └── 获取工艺路线明细配置的 card_granularity                              │
   │             │                                                               │
   │             ├── per_batch（一批一卡）                                       │
   │             │       └── 生成 1 张过程卡（card_no = PC + 日期 + 序号）        │
   │             │           └── 关联批次号 = 工单批次号                          │
   │             │                                                               │
   │             └── per_item（一物一卡）                                        │
   │                     └── 生成 N 张过程卡（N = 工序计划数量）                   │
   │                         └── 每张卡分配唯一序列号                             │
   │                                                                             │
   │ 过程卡明细：从工艺路线模板复制 tool/quality/operation/equipment/material      │
   └─────────────────────────────────────────────────────────────────────────────┘

   一物一卡 vs 一批一卡
   ┌────────────┬──────────────────────────────┬──────────────────────┐
   │    维度    │     一物一卡 (per_item)      │ 一批一卡 (per_batch) │
   ├────────────┼──────────────────────────────┼──────────────────────┤
   │ 适用场景   │ 航空航天、医疗器械、高端装备 │ 批量制造、通用件生产 │
   ├────────────┼──────────────────────────────┼──────────────────────┤
   │ 追溯粒度   │ 单件追溯（序列号）           │ 批次追溯（批次号）   │
   ├────────────┼──────────────────────────────┼──────────────────────┤
   │ 过程卡数量 │ 计划数量 张                  │ 1 张/工序            │
   ├────────────┼──────────────────────────────┼──────────────────────┤
   │ 质量记录   │ 每件独立记录                 │ 按批次抽检记录       │
   ├────────────┼──────────────────────────────┼──────────────────────┤
   │ 打印需求   │ 随工单流转                   │ 车间看板/电子显示    │
   ├────────────┼──────────────────────────────┼──────────────────────┤
   │ 数据量     │ 大                           │ 小                   │
   └────────────┴──────────────────────────────┴──────────────────────┘
   工艺过程卡完整内容

   ┌─────────────────────────────────────────────────────────────────────────────┐
   │                              工艺过程卡                                      │
   ├─────────────────────────────────────────────────────────────────────────────┤
   │ 产品编码: XXX-001          产品名称: 某产品                                  │
   │ 工艺版本: V1.0            BOM版本: B1.0           图纸号: DWG-001            │
   ├─────────────────────────────────────────────────────────────────────────────┤
   │ 工序号: 10                工序名称: 下料                                     │
   │ 工作中心: WC-001          生产线: L-001                                      │
   ├────────────────────────────────┬────────────────────────────────────────────┤
   │ 工艺参数                       │ 资源配置                                    │
   │ ├─ 准备时间: 15 min           │ ├─ 设备: 数控切割机 CNC-001                 │
   │ ├─ 加工时间: 30 min           │ ├─ 刀具: 合金切割刀 TL-001                  │
   │ ├─ 传输时间: 5 min            │ ├─ 夹具: 板材定位夹具 FX-001                │
   │ └─ 单位产量: 10 件/周期        │ └─ 量具: 卡尺 GA-001                        │
   ├────────────────────────────────┼────────────────────────────────────────────┤
   │ 操作步骤                       │ 质量标准                                    │
   │ 1. 确认板材规格，核对图纸      │ ├─ 尺寸公差: ±0.5mm                        │
   │ 2. 设置切割参数               │ ├─ 表面粗糙度: Ra3.2                         │
   │ 3. 装夹定位板材               │ ├─ 直线度: ≤0.1mm/m                         │
   │ 4. 执行切割程序               │ └─ 检验方法: 卡尺测量                        │
   │ 5. 检验尺寸，记录数据         │                                              │
   ├────────────────────────────────┴────────────────────────────────────────────┤
   │ 物料消耗                                                                     │
   │ ├─ 钢板 Q235 (1.5m²/件，损耗率 3%)                                          │
   │ └─ 切割液 (0.1L/件)                                                         │
   ├─────────────────────────────────────────────────────────────────────────────┤
   │ 安全注意事项                                                                 │
   │ ├─ 穿戴防护眼镜和手套                                                        │
   │ └─ 设备运行时禁止靠近切割区域                                                │
   └─────────────────────────────────────────────────────────────────────────────┘

   功能清单

   工艺过程卡模板编辑（工艺路线层面）：
   - 增强现有工艺路线编辑页面
   - 工序明细增加多个Tab页：工具配置、质量标准、操作步骤、设备配置、物料消耗
   - 新增：工序明细增加"过程卡粒度"配置（一物一卡/一批一卡）

   工艺过程卡实例化（工单层面）：
   - 工单下达（审批通过）时自动生成过程卡实例
   - 根据工艺路线配置的卡粒度决定生成数量
   - 一批一卡：每工序生成1张，关联批次号
   - 一物一卡：每工序按计划数量生成N张，分配序列号
   - 过程卡明细从模板复制（支持现场微调）

   工艺过程卡查看/打印：
   - 工艺过程卡预览页面
   - 支持导出PDF/Excel格式
   - 支持打印（A4纸张格式化）
   - 一物一卡支持批量打印

   工艺过程卡与派工关联：
   - 派工时关联过程卡实例
   - 工人任务页面展示操作步骤和质量标准
   - 生产现场可填写实际执行记录

   过程卡执行记录：
   - 质量检验项录入实测值
   - 操作步骤执行确认
   - 执行人、执行时间记录
   - 支持电子签名（可选扩展）

   API接口

   模板接口（工艺路线层面）：
   ┌──────┬─────────────────────────────────────────────────┬──────────────────┐
   │ 方法 │                      路径                       │       说明       │
   ├──────┼─────────────────────────────────────────────────┼──────────────────┤
   │ GET  │ /product/processRoute/tool/list/{detailId}      │ 工具配置列表     │
   ├──────┼─────────────────────────────────────────────────┼──────────────────┤
   │ POST │ /product/processRoute/tool/batch                │ 批量保存工具     │
   ├──────┼─────────────────────────────────────────────────┼──────────────────┤
   │ GET  │ /product/processRoute/quality/list/{detailId}   │ 质量标准列表     │
   ├──────┼─────────────────────────────────────────────────┼──────────────────┤
   │ POST │ /product/processRoute/quality/batch             │ 批量保存质量标准 │
   ├──────┼─────────────────────────────────────────────────┼──────────────────┤
   │ GET  │ /product/processRoute/operation/list/{detailId} │ 操作步骤列表     │
   ├──────┼─────────────────────────────────────────────────┼──────────────────┤
   │ POST │ /product/processRoute/operation/batch           │ 批量保存操作步骤 │
   ├──────┼─────────────────────────────────────────────────┼──────────────────┤
   │ GET  │ /product/processRoute/equipment/list/{detailId} │ 设备配置列表     │
   ├──────┼─────────────────────────────────────────────────┼──────────────────┤
   │ GET  │ /product/processRoute/material/list/{detailId}  │ 物料消耗列表     │
   ├──────┼─────────────────────────────────────────────────┼──────────────────┤
   │ PUT  │ /product/processRoute/detail/granularity        │ 设置过程卡粒度   │
   └──────┴─────────────────────────────────────────────────┴──────────────────┘
   实例接口（工单层面）：
   ┌──────┬────────────────────────────────────────────────┬──────────────────────────┐
   │ 方法 │                      路径                      │           说明           │
   ├──────┼────────────────────────────────────────────────┼──────────────────────────┤
   │ GET  │ /product/processCard/list                      │ 过程卡实例列表           │
   ├──────┼────────────────────────────────────────────────┼──────────────────────────┤
   │ GET  │ /product/processCard/{id}                      │ 过程卡详情（含明细）     │
   ├──────┼────────────────────────────────────────────────┼──────────────────────────┤
   │ GET  │ /product/processCard/byWorkOrder/{workOrderId} │ 按工单查询过程卡         │
   ├──────┼────────────────────────────────────────────────┼──────────────────────────┤
   │ GET  │ /product/processCard/byProcess/{processId}     │ 按工序查询过程卡         │
   ├──────┼────────────────────────────────────────────────┼──────────────────────────┤
   │ POST │ /product/processCard/generate/{workOrderId}    │ 手动触发生成过程卡       │
   ├──────┼────────────────────────────────────────────────┼──────────────────────────┤
   │ PUT  │ /product/processCard/detail/execute            │ 录入执行记录             │
   ├──────┼────────────────────────────────────────────────┼──────────────────────────┤
   │ POST │ /product/processCard/void/{id}                 │ 作废过程卡               │
   ├──────┼────────────────────────────────────────────────┼──────────────────────────┤
   │ GET  │ /product/processCard/export/{id}               │ 导出过程卡PDF            │
   ├──────┼────────────────────────────────────────────────┼──────────────────────────┤
   │ GET  │ /product/processCard/export/batch              │ 批量导出（一物一卡场景） │
   ├──────┼────────────────────────────────────────────────┼──────────────────────────┤
   │ GET  │ /product/processCard/print/{id}                │ 打印过程卡               │
   └──────┴────────────────────────────────────────────────┴──────────────────────────┘
   ---
   4.5 第5阶段：完工入库增强

   目标：完善入库流程

   增强功能：
   - 入库前检查：验收是否完成、合格数量是否足够
   - 批次管理：生成批次号
   - 库位分配：指定入库库位

   ---
   五、关于任务管理(manufacture_task)的建议

   5.1 是否需要任务管理？
   ┌──────────────────────┬───────────┬──────────────────────────┐
   │         场景         │ 是否需要  │           说明           │
   ├──────────────────────┼───────────┼──────────────────────────┤
   │ 销售订单直接生成工单 │ ❌ 不需要 │ 现有流程已支持           │
   ├──────────────────────┼───────────┼──────────────────────────┤
   │ 多订单合并生产       │ ⚠️ 可选   │ 可在工单层面合并         │
   ├──────────────────────┼───────────┼──────────────────────────┤
   │ MRP运算结果管理      │ ✅ 需要   │ 需要计划层管理           │
   ├──────────────────────┼───────────┼──────────────────────────┤
   │ 多类型任务统一管理   │ ✅ 需要   │ 生产/采购/外协需统一视图 │
   └──────────────────────┴───────────┴──────────────────────────┘
   5.2 建议

   如果暂不实现MRP运算，可以先不开发任务管理模块：
   - 销售订单 → 直接生成生产工单
   - 采购需求 → 直接生成采购订单

   如果后续需要MRP，再补充任务管理层：
   - MRP运算 → 生成任务 → 审批 → 下发工单/订单

   ---
   六、API接口与权限设计

   6.1 新增API接口清单

   6.1.1 派工管理接口
   方法: GET
   路径: /product/dispatch/list
   权限标识: product:dispatch:list
   说明: 班组派工单列表
   ────────────────────────────────────────
   方法: GET
   路径: /product/dispatch/{id}
   权限标识: product:dispatch:query
   说明: 派工单详情
   ────────────────────────────────────────
   方法: POST
   路径: /product/dispatch
   权限标识: product:dispatch:add
   说明: 创建派工单（工序→班组长）
   ────────────────────────────────────────
   方法: PUT
   路径: /product/dispatch
   权限标识: product:dispatch:edit
   说明: 修改派工单
   ────────────────────────────────────────
   方法: DELETE
   路径: /product/dispatch/{ids}
   权限标识: product:dispatch:remove
   说明: 删除派工单
   ────────────────────────────────────────
   方法: POST
   路径: /product/dispatch/cancel/{id}
   权限标识: product:dispatch:cancel
   说明: 取消派工单
   ────────────────────────────────────────
   方法: POST
   路径: /product/dispatch/assign
   权限标识: product:dispatch:assign
   说明: 分派给工人（班组长操作）
   ────────────────────────────────────────
   方法: GET
   路径: /product/dispatch/task/list
   权限标识: product:dispatch:task:list
   说明: 工人任务列表
   ────────────────────────────────────────
   方法: GET
   路径: /product/dispatch/task/{id}
   权限标识: product:dispatch:task:query
   说明: 工人任务详情
   ────────────────────────────────────────
   方法: POST
   路径: /product/dispatch/task/start/{id}
   权限标识: product:dispatch:task:start
   说明: 工人开工
   ────────────────────────────────────────
   方法: POST
   路径: /product/dispatch/task/pause/{id}
   权限标识: product:dispatch:task:pause
   说明: 工人暂停
   ────────────────────────────────────────
   方法: POST
   路径: /product/dispatch/task/resume/{id}
   权限标识: product:dispatch:task:resume
   说明: 工人恢复
   ────────────────────────────────────────
   方法: POST
   路径: /product/dispatch/task/report
   权限标识: product:dispatch:task:report
   说明: 工人报工
   ────────────────────────────────────────
   方法: POST
   路径: /product/dispatch/task/complete/{id}
   权限标识: product:dispatch:task:complete
   说明: 工人完工
   ────────────────────────────────────────
   方法: GET
   路径: /product/dispatch/progress/{workOrderId}
   权限标识: product:dispatch:progress
   说明: 工单派工进度
   ────────────────────────────────────────
   方法: POST
   路径: /product/dispatch/export
   权限标识: product:dispatch:export
   说明: 导出派工单
   6.1.2 检验管理接口

  ┌────────┬─────────────────────────────────┬─────────────────────────────────┬─────────
  ─────┐
   │  方法  │              路径               │            权限标识             │     说
  明     │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ GET    │ /product/inspect/list           │ product:inspect:list            │ 检验单
  列表   │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ GET    │ /product/inspect/{id}           │ product:inspect:query           │ 检验单
  详情   │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ POST   │ /product/inspect                │ product:inspect:add             │ 创建检
  验单   │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ PUT    │ /product/inspect                │ product:inspect:edit            │ 修改检
  验单   │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ DELETE │ /product/inspect/{ids}          │ product:inspect:remove          │ 删除检
  验单   │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ POST   │ /product/inspect/submit/{id}    │ product:inspect:submit          │ 提交检
  验结果 │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ POST   │ /product/inspect/handle         │ product:inspect:handle          │ 不合格
  品处理 │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ GET    │ /product/inspect/standard/list  │ product:inspect:standard:list   │ 检验标
  准列表 │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ GET    │ /product/inspect/standard/{id}  │ product:inspect:standard:query  │ 检验标
  准详情 │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ POST   │ /product/inspect/standard       │ product:inspect:standard:add    │ 创建检
  验标准 │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ PUT    │ /product/inspect/standard       │ product:inspect:standard:edit   │ 修改检
  验标准 │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ DELETE │ /product/inspect/standard/{ids} │ product:inspect:standard:remove │ 删除检
  验标准 │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ GET    │ /product/inspect/standard/match │ product:inspect:standard:match  │ 匹配检
  验标准 │

  ├────────┼─────────────────────────────────┼─────────────────────────────────┼─────────
  ─────┤
   │ POST   │ /product/inspect/export         │ product:inspect:export          │ 导出检
  验单   │

  └────────┴─────────────────────────────────┴─────────────────────────────────┴─────────
  ─────┘
   6.1.3 现有接口变更

  ┌────────────────────────────────┬────────────────────────────────────────────┬────────
  ──┐
   │              接口              │                  变更内容                  │ 影响范
  围 │

  ├────────────────────────────────┼────────────────────────────────────────────┼────────
  ──┤
   │ GET /product/work/process/list │ 增加返回字段：dispatch_status, dispatch_id │ 工序列
  表 │

  ├────────────────────────────────┼────────────────────────────────────────────┼────────
  ──┤
   │ POST /product/work/accept      │ 增加参数：inspect_id，关联检验单           │ 验收提
  交 │

  ├────────────────────────────────┼────────────────────────────────────────────┼────────
  ──┤
   │ GET /purchase/arrival/{id}     │ 增加返回字段：inspect_status               │ 到货详
  情 │

  ├────────────────────────────────┼────────────────────────────────────────────┼────────
  ──┤
   │ POST /purchase/arrival/stock   │ 增加前置校验：来料检验状态                 │ 到货入
  库 │

  └────────────────────────────────┴────────────────────────────────────────────┴────────
  ──┘
   6.2 权限菜单配置

   -- 派工管理菜单
   INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component,
  perms, menu_type, ...) VALUES
   -- 一级菜单
   (nextval('seq'), '派工管理', [生产执行父菜单ID], 1, 'dispatch', 'product/dispatch/
  index',
   'product:dispatch:list', 'C', ...),
   -- 班组长工作台
   (nextval('seq'), '班组工作台', [生产执行父菜单ID], 2, 'teamWorkbench', 'product/
  dispatch/teamWorkbench',
   'product:dispatch:assign', 'C', ...),
   -- 工人任务
   (nextval('seq'), '我的任务', [生产执行父菜单ID], 3, 'myTask', 'product/dispatch/
  myTask',
   'product:dispatch:task:list', 'C', ...),
   -- 按钮权限
   (nextval('seq'), '派工查询', [派工管理ID], 1, '#', '', 'product:dispatch:query',
  'F', ...),
   (nextval('seq'), '派工新增', [派工管理ID], 2, '#', '', 'product:dispatch:add',
  'F', ...),
   (nextval('seq'), '分派工人', [派工管理ID], 3, '#', '', 'product:dispatch:assign',
  'F', ...),
   (nextval('seq'), '开工操作', [派工管理ID], 4, '#', '', 'product:dispatch:task:start',
  'F', ...),
   (nextval('seq'), '报工操作', [派工管理ID], 5, '#', '', 'product:dispatch:task:report',
  'F', ...),
   (nextval('seq'), '完工操作', [派工管理ID], 6, '#', '',
  'product:dispatch:task:complete', 'F', ...);

   -- 检验管理菜单
   INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component,
  perms, menu_type, ...) VALUES
   (nextval('seq'), '检验管理', [质量管理父菜单ID], 1, 'inspect', 'product/inspect/
  index', 'product:inspect:list',
    'C', ...),
   (nextval('seq'), '检验标准', [质量管理父菜单ID], 2, 'inspectStandard', 'product/
  inspect/standard/index',
   'product:inspect:standard:list', 'C', ...),
   -- 按钮权限
   (nextval('seq'), '检验提交', [检验管理ID], 1, '#', '', 'product:inspect:submit',
  'F', ...),
   (nextval('seq'), '不合格处理', [检验管理ID], 2, '#', '', 'product:inspect:handle',
  'F', ...);

   6.3 前端按钮显示策略

   // 工序列表操作列按钮
   const processActions = computed(() => {
     const actions = [];

     // 派工按钮：工序未派工 + 工单已审批
     if (!row.dispatchId && workOrder.checkedStatus === 1) {
       if (hasPermi('product:dispatch:add')) {
         actions.push({ label: '派工', action: 'dispatch', type: 'primary' });
       }
     }

     // 查看派工：已有派工单
     if (row.dispatchId) {
       if (hasPermi('product:dispatch:query')) {
         actions.push({ label: '查看派工', action: 'viewDispatch' });
       }
     }

     return actions;
   });

   // 工人任务操作按钮
   const taskActions = computed(() => {
     const actions = [];
     const { status, firstInspectPassed } = row;

     // 开工：待开工状态
     if (status === '0' && hasPermi('product:dispatch:task:start')) {
       actions.push({ label: '开工', action: 'start', type: 'success' });
     }

     // 首检：开工后未通过首检
     if (status === '1' && firstInspectPassed === 'N' && hasPermi('product:inspect:add'))
  {
       actions.push({ label: '首检', action: 'firstInspect', type: 'warning' });
     }

     // 报工：进行中 + 首检通过
     if (status === '1' && firstInspectPassed === 'Y' &&
  hasPermi('product:dispatch:task:report')) {
       actions.push({ label: '报工', action: 'report', type: 'primary' });
     }

     // 暂停/恢复
     if (status === '1' && hasPermi('product:dispatch:task:pause')) {
       actions.push({ label: '暂停', action: 'pause', type: 'warning' });
     }
     if (status === '3' && hasPermi('product:dispatch:task:resume')) {
       actions.push({ label: '恢复', action: 'resume', type: 'success' });
     }

     // 完工：进行中
     if (status === '1' && hasPermi('product:dispatch:task:complete')) {
       actions.push({ label: '完工', action: 'complete', type: 'success' });
     }

     return actions;
   });

   ---
   七、前端改造范围

   7.1 现有页面改造
   ┌────────────────────────────┬───────────────────────────────────┬────────┐
   │            页面            │             改造内容              │ 工作量 │
   ├────────────────────────────┼───────────────────────────────────┼────────┤
   │ product/work/task.vue      │ 工序tab增加"派工"按钮和派工状态列 │ 小     │
   ├────────────────────────────┼───────────────────────────────────┼────────┤
   │ product/work/task.vue      │ 增加"派工进度"展示区域            │ 中     │
   ├────────────────────────────┼───────────────────────────────────┼────────┤
   │ purchase/arrival/edit.vue  │ 增加"送检"按钮，检验状态列        │ 小     │
   ├────────────────────────────┼───────────────────────────────────┼────────┤
   │ purchase/arrival/index.vue │ 增加"检验状态"筛选和列            │ 小     │
   └────────────────────────────┴───────────────────────────────────┴────────┘
   7.2 新增页面
   ┌─────────────────────────────────────┬──────────────────────┬─────────────────────┐
   │                页面                 │         功能         │       复杂度        │
   ├─────────────────────────────────────┼──────────────────────┼─────────────────────┤
   │ product/dispatch/index.vue          │ 派工单列表           │ 中（参考order列表） │
   ├─────────────────────────────────────┼──────────────────────┼─────────────────────┤
   │ product/dispatch/teamWorkbench.vue  │ 班组长工作台         │ 高（新设计）        │
   ├─────────────────────────────────────┼──────────────────────┼─────────────────────┤
   │ product/dispatch/myTask.vue         │ 工人任务列表         │ 中                  │
   ├─────────────────────────────────────┼──────────────────────┼─────────────────────┤
   │ product/dispatch/DispatchDialog.vue │ 派工弹窗（选班组长） │ 小                  │
   ├─────────────────────────────────────┼──────────────────────┼─────────────────────┤
   │ product/dispatch/AssignDialog.vue   │ 分派工人弹窗         │ 中                  │
   ├─────────────────────────────────────┼──────────────────────┼─────────────────────┤
   │ product/dispatch/ReportDialog.vue   │ 报工弹窗             │ 中                  │
   ├─────────────────────────────────────┼──────────────────────┼─────────────────────┤
   │ product/inspect/index.vue           │ 检验单列表           │ 中                  │
   ├─────────────────────────────────────┼──────────────────────┼─────────────────────┤
   │ product/inspect/edit.vue            │ 检验录入页面         │ 高                  │
   ├─────────────────────────────────────┼──────────────────────┼─────────────────────┤
   │ product/inspect/standard/index.vue  │ 检验标准列表         │ 中                  │
   ├─────────────────────────────────────┼──────────────────────┼─────────────────────┤
   │ product/inspect/standard/edit.vue   │ 检验标准编辑         │ 中                  │
   ├─────────────────────────────────────┼──────────────────────┼─────────────────────┤
   │ product/inspect/InspectDialog.vue   │ 送检弹窗             │ 小                  │
   ├─────────────────────────────────────┼──────────────────────┼─────────────────────┤
   │ product/inspect/HandleDialog.vue    │ 不合格品处理弹窗     │ 中                  │
   └─────────────────────────────────────┴──────────────────────┴─────────────────────┘
   7.3 新增API文件

   leaping-ui/src/api/supplychain/product/
   ├── dispatch.ts              # 派工管理API
   ├── dispatchTask.ts          # 工人任务API
   ├── inspect.ts               # 检验管理API
   └── inspectStandard.ts       # 检验标准API

   7.4 表单验证规则

   // 派工弹窗验证
   const dispatchRules = {
     teamId: [{ required: true, message: '请选择班组', trigger: 'change' }],
     teamLeaderId: [{ required: true, message: '请选择班组长', trigger: 'change' }],
     planQty: [
       { required: true, message: '请输入派工数量', trigger: 'blur' },
       { type: 'number', min: 0.001, message: '数量必须大于0', trigger: 'blur' }
     ]
   };

   // 分派工人验证
   const assignRules = {
     workerId: [{ required: true, message: '请选择工人', trigger: 'change' }],
     planQty: [
       { required: true, message: '请输入分配数量', trigger: 'blur' },
       {
         validator: (rule, value, callback) => {
           if (value > remainingQty.value) {
             callback(new Error(`分配数量不能超过剩余可分配数量 ${remainingQty.value}`));
           } else {
             callback();
           }
         },
         trigger: 'blur'
       }
     ]
   };

   // 报工验证
   const reportRules = {
     finishQty: [
       { required: true, message: '请输入完成数量', trigger: 'blur' },
       { type: 'number', min: 0, message: '数量不能为负', trigger: 'blur' }
     ]
   };

   // 检验录入验证
   const inspectRules = {
     inspectQty: [{ required: true, message: '请输入送检数量', trigger: 'blur' }],
     inspectorId: [{ required: true, message: '请选择检验员', trigger: 'change' }],
     items: [
       {
         validator: (rule, value, callback) => {
           const requiredItems = value.filter(item => item.isRequired === 'Y');
           const incomplete = requiredItems.filter(item => !item.actualValue);
           if (incomplete.length > 0) {
             callback(new Error(`必检项"${incomplete[0].itemName}"未填写`));
           } else {
             callback();
           }
         }
       }
     ]
   };

   ---
   八、数据迁移与兼容策略

   8.1 历史数据兼容

   原则： 新功能仅影响新创建的工单，历史工单保持原有流程。

   -- 为现有工序表增加派工状态字段（兼容历史数据）
   ALTER TABLE product_work_process
       ADD COLUMN IF NOT EXISTS dispatch_status VARCHAR(10) DEFAULT NULL;
   -- NULL = 未使用派工（历史数据）
   -- 0 = 未派工
   -- 1 = 已派工

   COMMENT ON COLUMN product_work_process.dispatch_status IS '派工状态：NULL=未使用派
  工,0=未派工,1=已派工';

   -- 为采购到货表增加检验状态字段
   ALTER TABLE purchase_arrival_detail
       ADD COLUMN IF NOT EXISTS inspect_status VARCHAR(10) DEFAULT NULL;
   -- NULL = 未使用来料检验（历史数据）
   -- 0 = 待检验
   -- 1 = 检验中
   -- 2 = 合格
   -- 3 = 不合格
   -- 9 = 免检

   COMMENT ON COLUMN purchase_arrival_detail.inspect_status IS '检验状态';

   8.2 功能开关配置

   # application.yml
   product:
     dispatch:
       enabled: true           # 是否启用派工功能
       require-first-inspect: true  # 是否强制首检
     inspect:
       incoming-enabled: true  # 是否启用来料检验
       incoming-required: false # 是否强制来料检验（false=可免检）

   // 控制器中使用
   @Value("${product.dispatch.enabled:true}")
   private boolean dispatchEnabled;

   @GetMapping("/product/work/process/list")
   public R<List<WorkProcessVo>> listProcess(Long workOrderId) {
       List<WorkProcessVo> list = processService.selectList(workOrderId);

       // 如果未启用派工，不返回派工相关字段
       if (!dispatchEnabled) {
           list.forEach(p -> {
               p.setDispatchStatus(null);
               p.setDispatchId(null);
           });
       }

       return R.ok(list);
   }

   8.3 数据初始化脚本

   -- 初始化班组数据（如果使用部门表管理班组）
   -- 假设部门类型 dept_type = 'team' 表示班组
   UPDATE sys_dept SET dept_type = 'team' WHERE dept_name LIKE '%班组%' OR dept_name LIKE
  '%班%';

   -- 初始化工人角色
   INSERT INTO sys_role (role_id, role_name, role_key, role_sort, ...) VALUES
   (nextval('seq'), '生产工人', 'worker', 100, ...),
   (nextval('seq'), '班组长', 'team_leader', 99, ...),
   (nextval('seq'), '检验员', 'inspector', 98, ...);

   -- 初始化默认检验标准（示例）
   INSERT INTO product_inspect_standard (standard_no, standard_name, standard_type,
  inspect_type, sample_method,
   ...) VALUES
   ('QC-INCOMING-001', '来料检验通用标准', 'global', 'incoming', 'ratio', ...),
   ('QC-PROCESS-001', '过程检验通用标准', 'global', 'process', 'ratio', ...),
   ('QC-FIRST-001', '首件检验通用标准', 'global', 'first', 'full', ...);

   8.4 回滚策略

   -- 如果需要回滚，执行以下脚本

   -- 1. 删除新增表（按依赖顺序）
   DROP TABLE IF EXISTS product_inspect_item;
   DROP TABLE IF EXISTS product_inspect;
   DROP TABLE IF EXISTS product_inspect_standard_item;
   DROP TABLE IF EXISTS product_inspect_standard;
   DROP TABLE IF EXISTS product_work_dispatch_detail;
   DROP TABLE IF EXISTS product_work_dispatch;

   -- 2. 删除新增字段
   ALTER TABLE product_work_process DROP COLUMN IF EXISTS dispatch_status;
   ALTER TABLE purchase_arrival_detail DROP COLUMN IF EXISTS inspect_status;

   -- 3. 删除菜单（根据实际ID）
   DELETE FROM sys_menu WHERE perms LIKE 'product:dispatch:%';
   DELETE FROM sys_menu WHERE perms LIKE 'product:inspect:%';

   -- 4. 删除字典
   DELETE FROM sys_dict_data WHERE dict_type IN ('product_dispatch_status',
  'product_task_status',
       'product_inspect_type', 'product_inspect_result', 'product_defect_type');
   DELETE FROM sys_dict_type WHERE dict_type IN ('product_dispatch_status',
  'product_task_status',
       'product_inspect_type', 'product_inspect_result', 'product_defect_type');

   8.5 灰度策略

   阶段1：开发环境验证
       └── 完整功能测试

   阶段2：测试环境验证
       └── 业务场景测试
       └── 性能测试
       └── 兼容性测试（历史数据）

   阶段3：生产灰度
       └── 选择1-2个班组试点
       └── 功能开关控制（仅试点班组可见派工菜单）
       └── 监控异常日志

   阶段4：全量发布
       └── 开放所有班组
       └── 关闭历史工单的派工入口

   ---
   九、推荐实施顺序

   第1阶段：工序派工（两级派工）
       ├── 数据表：product_work_dispatch（班组派工）、product_work_dispatch_detail（工人
  任务）
       ├── 后端：DispatchController/Service/Mapper
       ├── 前端：
       │   ├── 工单工序tab增加派工按钮
       │   ├── 班组派工弹窗
       │   ├── 班组长工作台（分派工人、查看进度）
       │   └── 工人报工页面
       └── 验证：派给班组长→分派工人→开工→报工→完工

   第2阶段：检验管理
       ├── 数据表：product_inspect, product_inspect_item, product_inspect_standard
       ├── 后端：InspectController/Service
       ├── 前端：
       │   ├── 检验单列表页
       │   ├── 检验录入页面
       │   ├── 检验标准库管理
       │   └── 采购到货页面增加"送检"按钮
       └── 验证：
           ├── 生产检验：首检→过程检→完工检
           └── 来料检验：到货→送检→检验→入库/退货

   第3阶段：生产过程管理增强
       ├── 增强：product_work_process 表（开工时间、完工时间、进度）
       ├── 后端：工序开工/完工API
       ├── 前端：进度展示、工时统计、生产看板
       └── 验证：完整生产流程

   第4阶段：工艺过程卡管理
       ├── 数据表：
       │   ├── 模板表（工艺路线层面）：
       │   │   ├── product_process_route_tool（工具配置）
       │   │   ├── product_process_route_quality（质量标准）
       │   │   ├── product_process_route_operation（操作步骤）
       │   │   ├── product_process_route_equipment（设备配置）
       │   │   └── product_process_route_material（物料消耗）
       │   ├── 实例表（工单层面）：
       │   │   ├── product_process_card（过程卡实例）
       │   │   └── product_process_card_detail（过程卡明细）
       │   └── 字段扩展：
       │       └── product_process_route_detail.card_granularity（卡粒度配置）
       ├── 后端：
       │   ├── 扩展ProcessRouteController（模板接口）
       │   ├── 新增ProcessCardController（实例接口）
       │   └── 工单下达时自动生成过程卡（WorkOrderService增强）
       ├── 前端：
       │   ├── 工艺路线编辑页面增加多Tab（工具/质量/操作/设备/物料）
       │   ├── 工艺路线工序明细增加卡粒度选择
       │   ├── 工艺过程卡实例列表页面
       │   ├── 工艺过程卡预览/详情页面
       │   ├── 工艺过程卡执行记录填写
       │   └── 工艺过程卡导出/打印
       └── 验证：
           ├── 模板配置→工单下达→自动生成实例
           ├── 一物一卡→批量生成+序列号
           ├── 一批一卡→单张生成+批次号
           └── 执行记录→打印/导出

   第5阶段：完工入库增强
       ├── 增强：入库前检查（检验是否完成、合格数量）
       ├── 后端：批次生成、库位分配
       └── 验证：端到端流程

   ---
   七、关键参考文件
   ┌──────────────────────────────────────────┬──────────────────────────────┐
   │                   文件                   │             用途             │
   ├──────────────────────────────────────────┼──────────────────────────────┤
   │ views/supplychain/product/work/index.vue │ 工单列表页                   │
   ├──────────────────────────────────────────┼──────────────────────────────┤
   │ views/supplychain/product/work/edit.vue  │ 工单编辑页                   │
   ├──────────────────────────────────────────┼──────────────────────────────┤
   │ views/supplychain/product/work/task.vue  │ 工单任务页（工序/物料/验收） │
   ├──────────────────────────────────────────┼──────────────────────────────┤
   │ api/supplychain/product/workOrder.ts     │ 工单API                      │
   ├──────────────────────────────────────────┼──────────────────────────────┤
   │ api/supplychain/product/workProcess.ts   │ 工序API                      │
   └──────────────────────────────────────────┴──────────────────────────────┘
   ---
   八、已确认需求
   ┌──────────────┬─────────────────────────────────────────┐
   │     问题     │                确认结果                 │
   ├──────────────┼─────────────────────────────────────────┤
   │ 工序派工粒度 │ ✅ 两级派工：先派给班组长，再分派给工人 │
   ├──────────────┼─────────────────────────────────────────┤
   │ 检验类型     │ ✅ 首件检验 + 过程检验 + 来料检验       │
   ├──────────────┼─────────────────────────────────────────┤
   │ 任务管理     │ ✅ 暂不实现，后续MRP需要时再补充        │
   ├──────────────┼─────────────────────────────────────────┤
   │ 外协订单     │ ✅ 暂不实现，后期迭代                   │
   └──────────────┴─────────────────────────────────────────┘
   ---
   九、验证方案

   端到端流程测试

   1. 销售订单 → 推送生产工单
   2. 工单审批 → 状态变更
   3. 领料管理 → 物料出库
   4. 工序派工 → 班组长接收
   5. 班组长分派 → 工人接收任务
   6. 工人开工 → 首件检验
   7. 生产过程 → 过程检验（抽检）
   8. 工人完工 → 完工检验
   9. 验收入库 → 产成品入库

   来料检验流程测试

   10. 采购订单 → 采购到货
   11. 到货送检 → 生成来料检验单
   12. 检验录入 → 合格/不合格判定
   13. 合格入库 / 不合格退货

   工艺过程卡管理流程测试

   模板配置测试：
   14. 工艺路线编辑 → 选择工序明细
   15. 配置工具 → 添加刀具/夹具/量具/辅具
   16. 配置质量标准 → 定义检验项和公差范围
   17. 配置操作步骤 → 编写详细操作规范
   18. 配置设备 → 关联设备和参数设置
   19. 配置物料消耗 → 定义工序级物料需求
   20. 配置卡粒度 → 选择一物一卡或一批一卡

   过程卡实例化测试（一批一卡）：
   21. 创建工单 → 关联已配置的工艺路线（卡粒度=per_batch）
   22. 工单审批通过 → 系统自动生成过程卡实例
   23. 验证：每个工序生成1张过程卡
   24. 验证：过程卡关联工单批次号
   25. 验证：过程卡明细从模板正确复制

   过程卡实例化测试（一物一卡）：
   26. 创建工单 → 计划数量=100，关联工艺路线（卡粒度=per_item）
   27. 工单审批通过 → 系统自动生成过程卡实例
   28. 验证：每个工序生成100张过程卡
   29. 验证：每张卡分配唯一序列号（格式：工单号-工序号-001~100）
   30. 验证：支持批量打印

   过程卡执行记录测试：
   31. 派工时关联过程卡 → 工人任务展示过程卡内容
   32. 工人生产时 → 录入质量检验实测值
   33. 工人完工时 → 确认操作步骤执行
   34. 验证：执行记录正确保存（执行人、时间、实际值）
   35. 验证：过程卡状态自动更新

   过程卡打印/导出测试：
   36. 单张过程卡预览 → 完整格式化展示
   37. 单张过程卡导出 → PDF/Excel格式
   38. 批量导出（一物一卡） → ZIP打包多张PDF
   39. 打印测试 → A4纸张格式化

   数据一致性测试

   40. 派工数量约束 → 派工数量 ≤ 工序计划数量
   41. 分派数量约束 → 已分派数量 ≤ 派工数量
   42. 完成数量汇总 → 派工单.完成数量 = SUM(工人任务.完成数量)
   43. 工时汇总 → 派工单.累计工时 = SUM(工人任务.有效工时)
   44. 状态联动 → 工人开工/完工自动更新派工单和工序状态
   45. 检验结果回写 → 合格/不合格数量正确更新

   边界场景测试

   46. 历史工单兼容 → 无派工字段的工单正常使用
   47. 功能开关验证 → 关闭派工/检验功能后UI隐藏
   48. 权限控制 → 班组长/工人/检验员权限隔离
   49. 并发操作 → 多工人同时报工数据一致性
   50. 取消/暂停恢复 → 状态流转正确
