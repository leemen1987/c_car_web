# 更新日志

## 2026-10-25~11-10（客户确认+企微消息+Excel导入+汇总页+性能优化）

### 功能新增
- **Excel 导入任务**：任务管理"导入"按钮，解析任务模板格式.xlsx（23列），可编辑预览表格（改/删行），确认导入
  - 列映射：用车方/出发/目的/出车回程时间/天数/租车费/车牌/司机/公司/收款/合同号等
  - 自动推断：自驾车（目的地=自驾）、内外部（车属公司）、状态（里程→已完成，车牌→已排班，无→待排班）
  - 中文日期格式兼容（cellDates+fmtDate），自动创建缺失车辆/司机
- **客户确认管理大改**：多维筛选（状态/日期/用车方/车属单位）+ 统一格式输出
  - 企微客户：选收件人发消息（内部 markdown，外部 add_msg_template 群发任务）
  - 导出 Excel / 生成图片 / 复制任务 / 复制链接
  - 统一格式：`月日-时分，出发--目的，安排X座车车牌，司机：姓名 电话（车费X元）`
- **汇总页 token 公开访问**：`/summary/:token` 无需登录，筛选条件存 token 绑定，篡改参数无效
- **历史操作页面**：登录/登出记录（LoginLog 模型），管理员可见
- **排班临时调用外部车辆**：排班行"外部"勾选，司机人工费按内部车辆数缩放，10%提成
- **租车天数新规则**：≤5小时=0.5天，>5小时=ceil(小时/24)整数天（历史数据已迁移）
- **自驾车外部提成固定¥50/天**（历史数据已迁移）
- **云之家ID绑定**：权限控制加云之家ID列，审批必须用发起人自己的openid
- **企微 sender 配置**：权限控制加企微UserID列，update_user 保存 wx_sender
- **报表按车辆查询**：车属单位筛选（多选）+ 顶部汇总统计（总任务/总租车费/总利润）
- **复制任务按钮**：统一格式文本复制到剪贴板

### 修复
- 外部联系人消息 API 端点（add_msg_template 替代 message/send）
- update_user 漏存 wx_sender / yunzhijia_openid
- 中文日期格式解析（cellDates）
- localStorage 旧列名导致导出/图片崩溃（白名单过滤+安全访问）
- 座字重复（49座座→49座）
- 汇总页日期格式（11月11日-15:00）
- 链接带筛选条件hash
- 复制链接 HTTP 兼容（三级 fallback）
- 图片截断（截图前展开表格）

### 提交记录
- `2811912` fix: 用车方第一列+修座字重复
- `e357cd7` feat: 企微客户/导出Excel/生成图片去掉列勾选，统一格式直出
- `239e350` fix: 导出Excel无响应+新增复制任务按钮
- `682e2ba` feat: 汇总页token公开访问
- `a1a84af` fix: 汇总页日期格式+座车重复
- `a111283` feat: 汇总页去编号列+统一格式
- `143bc09` fix: localStorage旧列名导致崩溃
- `dcf7c81` feat: 客户确认统一输出格式
- `e4269c0` feat: 权限控制加云之家ID列+审批用发起人openid
- `5847a8b` style: 发送表格按钮改名为企微客户
- `cb31d77` feat: 群发消息格式统一
- `0d641b3` fix: 外部联系人API端点修正
- `cf0d7a8` fix: 外部联系人字段名修正+链接带筛选hash
- `812da86` feat: 一期企微发送任务通知
- `4c1775c` feat: 生成图片预览弹窗
- `3028293` chore: 取消复制图片功能
- `86d68f0` fix: 复制图片修复+文件名统一
- `4b7cf46` fix: 图片复制HTTP兼容+截图展开
- `109a99b` feat: 汇总页显示数据+企微sender+图片复制
- `7cc973a` fix: 复制链接summary路由+外部link卡片
- `52db23f` fix: 日期宽度+链接CONFIRM_BASE_URL
- `f922342` fix: 日期CSS变量/复制fallback/外部全选bug
- `b719e59` fix: 确认页4项修复
- `4026b4b` fix: 确认页日期+复制链接fallback
- `f7a0150` feat: 客户确认页面大改
- `a3c22ff` fix: 导入中文日期格式解析
- `e47815f` revert: 回退日期对齐修改
- `b1357c3` feat: 任务管理Excel导入
- `a2732f1` feat: 报表按车辆查询汇总+车属单位多选
- `0498509` feat: 历史操作页面
- `f35bd74` feat: 自驾车外部提成¥50/天
- `794878e` feat: 报表车属单位筛选
- `0bea6d6` feat: 租车天数新规则
- `8a4dfc4` fix: 外部车辆需选司机+人工费缩放
- `aa79fa0` feat: 排班临时调用外部车辆
- `37b54de` fix: 排班出车时间显示return_time
- `5410cef` perf: 任务管理加载优化
- `6f21763` fix: 报表表格高度消除双滚动条
- `f1dca3f` feat: 表格高度自适应
- `3b84e2b` fix: 多车油电桥路费乘车辆数
- `39d6d95` feat: 对账Excel样式+外部用车对账
- `352e09a` fix: 客户对账公司名匹配
- `0139caa` feat: 客户对账下拉选择
- `3cfc174` feat: 客户对账栏

## 2026-10-22~24（多车混合 + 对账单 + 性能优化）

### 功能新增
- **多车混合任务**：一单多车，每车独立租车费，内外部车辆可混合录入
  - 车辆配置行：`[座位数▼]×[数量][单台租车费¥][删除][☑外部]`，外部勾选放行末
  - 差费不在配置行填写，由差费标准×内部车辆数自动计算
  - 利润公式：`内部租车 = 租车费−外部租车`；`利润 = 内部租车 + 外部租车×10% − 成本`
- **自驾车计费三模式**：包干总价 / 按天计费 / 按里程计费（fixed/daily/mileage），录入时可选
  - 按天：`租车费 = 日租金×租用天数`，回程后自动补算
  - 按里程：`租车费 = (止码−起码)×油费率`，完成后填止码自动算
- **已完成任务可修改**：需填写修改说明（edit_reason），操作栏显示"已修改"标签，变更记录完整留痕
- **客户对账 Tab**（报表管理）：
  - 筛选：用车单位（可搜索下拉+自由输入）+ 月份 + 日期区间
  - 数据源 `GET /api/reports/by-client`，公司名/联系人名双匹配
  - 导出 Excel 完整复刻 dzdz.xlsx 样式（xlsx-js-style：宋体26标题合并/边框/SUM公式/合计行/复核行）
- **外部用车对账 Tab**：按外部车属单位筛选，列出该单位车辆执行的任务明细
  - 数据源 `GET /api/reports/by-external-company`（TaskVehicle JOIN vehicles WHERE company=单位）
  - 导出格式同客户对账单
- **表格高度自适应**：任务管理/报表管理表格 `max-height` 实测表格顶部位置计算，最大化填满可视区域
  - 切换 Tab、收起/展开筛选栏自动重算，消除双滚动条

### 修复
- **多车油电/桥路费未乘车辆数**：`vehicle_count` 在配置行化后不再同步，改用 `totalVehicleCount` 汇总
- **外部车辆完成任务 500**：`end_mileage` UnboundLocalError，变量引用移入条件块
- **客户对账查不出数据**：`Task.client_name.like` 只匹配联系人名，增加 `Task.client.has(Client.name.like(...))` OR 查询
- **排班弹窗出车时间**：`return_time` 为空时不再显示推算假时间，改显示 `~ 待定`；后端优先用 `return_time` 计算 `task_end`

### 性能优化
- **任务管理加载提速**：
  - 默认只拉进行中任务（`?status=active`），已完成/已取消需切换筛选才加载
  - `to_dict` 不再携带 `change_log`（改 `has_change_log` 布尔），变更记录按需 fetch `/api/tasks/<id>/change-log`
  - `selectinload` 预加载 task_vehicles/vehicle/driver/client/contact 消除 N+1
  - 响应体积：全量 202KB → 默认 66KB（-67%）

### 提交记录
- `37b54de` fix: 排班弹窗出车时间优先显示return_time，为空时显示待定
- `5410cef` perf: 任务管理加载优化 — 默认只拉进行中任务，change_log按需加载
- `6f21763` fix: 报表表格高度按实际位置测量，消除双滚动条
- `f1dca3f` feat: 任务/报表表格高度自适应窗口，最大化时填满可视区域
- `3b84e2b` fix: 多车任务油电/桥路费按车辆配置行总台数计算
- `39d6d95` feat: 对账Excel样式复刻dzdz.xlsx + 外部用车对账Tab
- `352e09a` fix: 客户对账查询支持公司名匹配，下拉含个人客户
- `0139caa` feat: 客户对账用车单位支持下拉选择+自由输入
- `3cfc174` feat: 报表管理新增客户对账栏 - 筛选显示+对账单格式导出Excel
- `3ebd644` feat: 车辆配置行优化 - 外部勾选置末，差费自动计算
- `677509b` feat: 多车混合任务 - 按车配置租车费，内外部混合录入
- `2dd1572` feat: 自驾车增加按里程计费模式
- `a4aef3d` feat: 自驾车租车费支持按天计费
- `104c62c` feat: 已完成任务可修改，需填写修改说明
- `0e2d307` fix: 外部车辆完成任务500 - end_mileage未定义引用

## 2026-10（内部审批 + 任务录入增强）

### 功能新增（重点：内部审批流程，替代云之家）
- **外部车辆任务**：录入任务车辆配置区增加"外部车辆"勾选（10%提成）：
  - 勾选后隐藏任务里程/油电费/桥路费/差费标准/司机人工费/预计成本，预估利润=租车费×10%
  - 排班只需填外部车牌（可输入），不选内部司机
  - 完成任务可填其他费用，利润=租车费×10%−其他费用
- **内部审批流程**：三级审批（可自定义层级数量），按公司配置不同审批流程（默认/国顺司/国开司/外单位），企业微信卡片推送 + 免登录审批页 `/approval/:token`
  - 审批设置弹窗（管理员）：公司 Tab 配置层级、审批人（可多人），显示 UserID 绑定状态
  - 逐级推送：通过自动推进下一级并微信通知；拒绝立即终止
  - 同级多审批人先操作者生效
- **全局审批方式**：审批设置弹窗顶部切换（系统审批/云之家审批），仅超管可配置；发起审批弹窗只读显示当前方式
- **多座位数组合任务**：录入任务支持不同座位数的多台车（如49座×1、15座×1、31座×1），排班按座位数过滤匹配车辆
- **任务日期筛选**：任务管理增加出车日期区间筛选
- **编辑允许改过去时间**：录入仍禁选过去出车时间，编辑时可选

### 修复
- **预估利润不重算**：编辑任务费用后自动重算预估利润（修复存量数据）
- **云之家审批500**：多车任务属性引用错误 + venv 缺 cryptography 导致回调500（已安装并加固异常处理，同步卡住的审批状态）
- **审批设置**：添加按钮样式、公司 Tab 添加层级无反应

### 提交记录
- `615344c` feat: 外部车辆任务 - 录入标记+排班填外部车牌+利润10%提成
- `70a06ea` feat: 发起审批方式改为超管全局配置
- `0afed66` fix: 审批设置按钮样式与Tab无反应修复，发起审批增加内部/云之家方式切换
- `1519438` feat: 内部审批流程（替代云之家）- 按公司配置多级审批+企业微信推送+免登录审批页
- `30100af` fix: venv缺cryptography导致云之家回调500 - 安装依赖并加固异常处理
- `768a7df` feat: 编辑任务时出车时间允许选择过去的时间
- `32fe45b` fix: 编辑任务费用后重算预估利润，修复存量数据
- `b1995f5` fix: 云之家审批多车任务引用错误属性导致500
- `13ff9c3` feat: 任务管理增加按出车日期区间筛选

## 2026-10-04

### 功能新增
- **司机历史任务与结算查询**：司机管理操作列增加"历史"按钮，弹窗显示：
  - 按结算周期（每月26日–次月25日）分组汇总：任务数、总人工费、已收、未收
  - 结算月份下拉选择器，可筛选任意历史周期（默认当前结算月，支持"全部历史"）
  - 周期汇总表点击行可直接切换该周期的任务明细（分页）
- **依赖锁定**：新增 `backend/requirements-py312.txt`（升级 26.04 前兼容性验证）

### 环境准备
- **Python 3.14 兼容性验证通过**：后端已切换到 `.venv`（Python 3.14.8），前后端运行正常，为 Ubuntu 26.04 升级做准备

### 提交记录
- `64c24cb` feat: 司机历史查询增加结算月份选择
- `a7dc129` feat: 司机管理增加历史任务与结算查询
- `7bebd5b` chore: 锁定Python依赖版本（升级前兼容性验证准备）

## 2026-09

### 功能新增
- **报表只显示已完成任务**：三个查询tab仅统计 `status == 'completed'`
- **报表编辑增加里程**：编辑弹窗可修改起始/结束里程，结束里程同步更新车辆当前里程（取较大值）
- **排班记录起始里程**：排班时自动读取车辆当前里程作为任务起始里程，报表默认显示起始里程列

### 界面优化
- **报表列设置持久化**：列设置保存到 localStorage，刷新后保持
- **报表列设置**：增加起始/结束里程列选项
- **报表用车单位**：始终显示单位名称（自驾车不再显示"-"），状态列移除
- **自驾车完成任务**：可填写租车费
- **自驾车回程时间**：录入时非必填，完成任务时可补填（同时重算租用天数）

### 修复
- **报表列设置失效**：起始/结束里程列未在表格中定义，已补齐三张表格
- **报表编辑无法保存里程**：`update_task` 接口补充 `start_mileage`/`end_mileage` 字段处理

### 提交记录
- `82e2eae` fix: 报表编辑结束里程时同步更新车辆当前里程（取较大值）
- `7d18878` fix: 报表用车单位列移除自驾车标签（已有包车类型列）
- `a0d3fa9` fix: 报表编辑支持保存起始/结束里程
- `3e44de4` fix: 报表只显示已完成任务，编辑弹窗增加起始/结束里程
- `41528be` feat: 排班时自动记录车辆当前里程为起始里程，报表默认显示起始里程列
- `cd293e1` fix: 报表用车单位始终显示名称，移除状态列
- `d11a1f4` fix: 报表列设置保存到localStorage，刷新后不再丢失
- `9eb8d98` fix: 报表列设置增加起始/结束里程列显示
- `4b46a0a` feat: 自驾车完成任务时可填写租车费
- `57c5e11` feat: 自驾车任务回程时间改为非必填，完成时可补填

## 2026-08-30

### 功能新增
- **云之家审批多车支持**：审批单车牌号/司机按 `1.粤J576L5;2.粤J57K35` 格式分号分隔显示所有分配车辆
- **报表开票筛选**：包车类型下拉增加"自驾车"选项
- **客户确认删除**：确认记录支持删除（前端按钮 + 后端 DELETE 接口）
- **差费标准序号**：ID 列改为序号显示

### 提交记录
- `f361c45` fix: 客户确认记录可删除，差费标准ID改序号，报表增加自驾车筛选
- `444f947` fix: 云之家审批支持多车任务 - 车牌号和司机按1.2.3.格式分号分隔显示

## 2026-08-28

### 功能新增
- **自驾车任务类型**：用车类型新增"自驾车"复选框，可与个人/单位组合
- **多车排班**：用车数量大于1时，排班弹窗显示多个车辆/司机选择行
- **里程区间加成配置**：费率设置增加里程预估加成比例配置（按距离区间设置百分比）
- **报表开票筛选**：三个查询tab增加"是否开票"筛选
- **车辆里程管理**：车辆编辑增加当前里程数字段

### 界面优化
- **自驾车排班**：隐藏目的地、司机人工费、结算周期；显示车辆里程数；增加备注输入框
- **自驾车完成任务**：隐藏油电/桥路/人工费，起始里程只读自动带出
- **自驾车标识**：用车方列下方居中显示"自驾车"标签
- **驾驶司机列**：自驾车任务显示"自驾车"而非"未排班"
- **多车排班防重复**：车辆和司机下拉自动排除已选选项
- **用车数量**：变更时自动重算里程、桥路费、油电费、司机人工费

### 修复
- **车辆编辑里程不更新**：后端update_vehicle接口增加mileage字段处理
- **自驾车验证**：勾选自驾车后不再要求填写出发地和目的地

### 提交记录
- `db58e82` feat: 6项系统优化需求（自驾车/批量录入/单位搜索/合同编号/里程管理/报表列自定义）
- `4701437` fix: 用车数量列宽调整
- `58b0aa0` feat: 里程预估按区间配置加成比例
- `e12955e` fix: 用车数量大于1时司机人工费乘以倍数
- `64e5711` refactor: 用车数量改为单任务多车排班模式
- `3009087` fix: 多车排班过滤已选车辆和司机
- `4d6726f` feat: 报表管理增加是否开票筛选
- `71726cd` refactor: 自驾车改为复选模式
- `b6a1ebd` fix: 自驾车隐藏里程等费用字段
- `bbb7057` feat: 自驾车排班优化
- `711922b` fix: 自驾车排班弹窗美化
- `e381741` fix: 车辆编辑增加当前里程数
- `41defa7` fix: 车辆编辑接口增加mileage处理
- `9c598b8` fix: 自驾车完成任务简化
- `f5442c7` fix: 自驾车标识水平居中显示
- `9418286` fix: 自驾车标识居中，移除X台标签，驾驶司机列显示自驾车

## 2026-08-21

### 功能新增
- **司机结算周期统计**：排班选择司机显示结算周期内人工费（上月26日-本月25日）
- **司机管理结算明细**：可展开行查看结算周期内任务详情
- **报表编辑功能**：报表页面可直接编辑任务费用和收款状态（需report_edit权限）
- **报表筛选增强**：搜索栏可折叠，增加收款状态和收款方式筛选

### 界面优化
- **报表操作列**：移至最后列，按钮改为透明样式
- **报表筛选按钮**：移至卡片标题栏右侧，不占额外空间
- **报表状态显示**：修复已取消任务显示为待排班的问题
- **排班对话框**：司机下拉显示"本月结算"替代"已获人工费"

### 权限系统
- **新增report_edit权限**：超管可分配用户报表编辑权限
- **后端permission_required装饰器**：支持细粒度权限控制

### 提交记录
- `90d66b7` fix: 报表默认排除已取消任务，修复已取消任务显示为待排班的问题
- `47096cf` feat: 报表搜索栏可折叠，列顺序调整，增加收款列
- `e56cef4` feat: 报表筛选按钮优化至标题栏，明细按权限可编辑
- `d270503` feat: 报表编辑本页弹窗，操作列置末，新增报表编辑权限
- `7e169e6` fix: 报表操作列宽度从70改为80，修复编辑按钮文字截断
- `e1851cb` feat: 司机结算周期统计（上月26日-本月25日）

## 2026-08-19

### 功能新增
- **桥路费自动预估**：输入出发地/目的地后，调用高德地图API自动获取过路费和里程（来回×2，里程含配置百分比余量）
- **油电费自动计算**：根据核定载人数×里程×单价，自动带出油电费
- **核定载人数**：任务管理页面"车辆类型"改为"核定载人数"，下拉选项从车辆数据获取

### 界面优化
- **任务管理页头部**：筛选下拉框移至"任务管理"标题右侧
- **费率按钮**：仅管理员可见，弹窗只配置油电费费率
- **顶栏设置**：个人配置（OpenID、UserID），发送人账号标签改为UserID
- **完成任务**：油电费/桥路费改为只读显示（自动用预估值），不再手动输入
- **完成按钮**：回程时间前禁用，回程时间过后才可操作

### 数据与后端
- **报表收款方式筛选**：按单位/司机/车辆查询均支持按收款方式（转账/二维码/现金）筛选
- **报表收款状态筛选**：支持按已收款/未收款筛选
- **油电费费率可配置**：管理员可在任务管理设置弹窗中修改油电费单价规则
- **车辆管理扩展**：新增核定载人数、品牌型号、使用性质、注册日期、发证日期、检验有效期、保险到期日期、强制报废期等字段
- **高德地图集成**：新增 `/api/estimate-toll` 接口，支持地理编码+驾车路线规划获取过路费
- **个人设置**：设置页面新增"发送人账号"（企业微信UserID），联系人不再单独配置
- **OpenID配置**：用户可配置个人云之家OpenID，审批时使用
- **收款状态列**：任务管理表格新增收款状态显示
- **状态筛选**：默认隐藏已取消任务，支持按状态筛选
- **状态列移至第二列**
- **删除确认修复**：弹窗定位问题修复

### 提交记录
- `d94c3b4` feat: 功能增强 — OpenID配置、车辆管理扩展、桥路费自动预估
- `2c14ac7` fix: 里程和桥路费改为来回计算（×2），里程含10%余量
- `0ef699e` fix: 完成任务时油电费/桥路费用预估值，回程时间前禁用完成按钮
- `17cd41f` refactor: 发送人账号移至用户设置，联系人不再单独配置
- `e4a92e7` feat: 油电费单价支持前端配置，管理员可在设置中修改费率
- `043e8e0` fix: 设置按钮标签改为UserID，任务管理费率设置独立于个人设置
- `574745f` feat: 报表管理增加收款方式筛选（转账/二维码/现金）

---

## 附录：云之家审批模板控件 ID 对照表

### 审批模板 ID

| 所属公司 | formCodeId |
|---------|------------|
| 国顺司 | `0e1d321692a9441fa24db3bb3776a7d9` |
| 国开司 | `3d50bcac14d947a5a006d64187b8fa5b` |
| 外单位 | `134dc1d64c964b68870e5a2665baac0d` |

### 控件 ID 对照表

| 控件 ID | 含义 | 数据来源 | 备注 |
|---------|------|---------|------|
| `_S_TITLE` | 审批单标题 | `包车审批 - 出发地→目的地 日期` | 标题控件 |
| `Te_0` | 用车方 | client.name（公司）或 client_name（个人） | |
| `Te_1` | 联系人 | client_name + client_phone | 格式：姓名 电话 |
| `Te_2` | 出发地点 | task.departure | 自驾车时为空 |
| `Te_3` | 目的地 | task.destination | 自驾车时为空 |
| `Te_4` | 车牌号 | 多车：`1.粤J576L5;2.粤J57K35`；单车：主车牌 | 分号分隔 |
| `Te_5` | 驾驶司机 | 多车：`1.张师傅;2.李师傅`；单车：主司机 | 自驾车时为空 |
| `Te_6` | 出车时间 | departure_time → `YYYY-MM-DD HH:MM` | |
| `Te_7` | 回程时间 | return_time → `YYYY-MM-DD HH:MM` | |
| `Te_8` | 车辆类型 | vehicle_type（核定载人数） | 如"45座" |
| `Te_9` | 里程 | mileage | 单位：km |
| `Te_10` | 租车费 | rental_fee | 单位：元 |
| `Te_11` | 油电费 | fuel_fee | 自驾车时为0 |
| `Te_12` | 桥路费 | bridge_fee | 自驾车时为0 |
| `Te_13` | 司机人工费 | labor_fee | 自驾车时为0 |
| `Te_14` | 预计成本 | estimated_cost | |
| `Te_15` | 预估利润 | estimated_profit | |
| `Te_16` | 天数 | rental_days | |

### 相关代码
- 审批表单构建：`backend/app.py` — `build_yzj_approval_body`
- 审批提交：`backend/app.py` — `submit_approval`
- 前端审批弹窗：`frontend/src/views/TaskManagement.vue`

---

## 附录：安全漏洞修复报告（2026-07-15）

**日期**：2026年7月15日  
**事件来源**：CNCERT 漏洞利用事件报告（编号 CNCERT-NetMon-Exploit-00001855-000002-20260712-WA3）  
**涉事IP**：113.107.137.16（广东省江门市）  
**攻击者IP**：111.247.10.249、38.113.126.182 等

---

## 一、漏洞概述

2026年7月11日 12:01:47，攻击者利用 **CVE-2025-30208（Vite 任意文件读取漏洞）**，通过 `/_nuxt/@fs/` 路径读取服务器敏感文件。

**攻击载荷示例**：
```
GET /_nuxt/@fs/etc/passwd?vue&type=script&src=true&lang.js HTTP/1.1
```

**攻击路径**：
```
公网 113.107.137.16:8008 → 路由端口映射 → 内网 Nginx:80 → Vite dev server:5174
```

---

## 二、攻击影响评估

### 2.1 已确认泄露的文件

| 文件 | 响应码 | 内容风险 |
|---|---|---|
| `/etc/passwd` | 200 | 低 — 仅含系统用户名（root、xxb），不含密码哈希 |
| `/home/xxb/.bashrc` | 200 | 低 — 仅含 NVM/PATH 配置，无密钥 |
| `/home/xxb/.profile` | 200 | 低 — 标准默认配置，无敏感信息 |

### 2.2 攻击者尝试读取但未成功的文件

| 文件类别 | 响应码 | 说明 |
|---|---|---|
| `.aws/credentials`、`.aws/config` | 500 | 文件不存在 |
| 各种 `.env` 文件 | 500/377 | 文件不存在，377字节为 Vite SPA fallback 页面 |
| `terraform.tfstate`、`terraform.tfvars` | 377 | 文件不存在，返回 Vite 默认页面 |
| `docker-compose.yml` | 377 | 文件不存在，返回 Vite 默认页面 |
| `.bash_profile`、`.profile` | 500 | 路径解析失败 |

### 2.3 其他攻击者活动（同日）

| 攻击者IP | 时间 | 行为 |
|---|---|---|
| `38.113.126.182` | 7月10日 14:19 | CVE-2025-30208 扫描 |
| `5.187.35.26` | 7月11日 15:05 | 路径遍历攻击 `../../etc/passwd` |
| `66.132.224.79` | 7月11日 16:24 | Censys 安全扫描 |
| `79.124.40.174` 等 | 全天 | RDP 爆破尝试（`mstshash=Administr`） |

---

## 三、已采取的修复措施

### 3.1 Vite 漏洞修复（CVE-2025-30208）

- **漏洞版本**：< 5.4.18
- **当前版本**：5.4.21
- **修复状态**：✅ 已修复
- **操作**：`npm update` 更新前端依赖（21个包）

### 3.2 Nginx 安全升级

- **原版本**：1.24.0（18个已知CVE，含1个严重级别）
- **升级版本**：1.30.4（无已知CVE）
- **操作**：
  1. 添加 Nginx 官方源（`http://nginx.org/packages/ubuntu noble nginx`）
  2. 导入 Nginx 签名密钥
  3. `apt-get install -y nginx` 升级
  4. 修复配置文件加载问题（`conf.d/` 目录结构变更）

### 3.3 Nginx @fs 路径拦截

在 Nginx 配置中添加拦截规则，阻止含 `@fs` 的请求到达 Vite：

```nginx
# 拦截 Vite 任意文件读取攻击 (CVE-2025-30208)
location ~ @fs {
    return 403;
}
```

**验证**：`curl http://127.0.0.1:80/_nuxt/@fs/etc/passwd` → 返回 403

### 3.4 systemd 服务端口对齐

**问题**：`c-car-web-frontend.service` 使用 `--port 5173` 覆盖 Vite 配置，与 Nginx 代理的 5174 端口不匹配。

**修复**：
- `deploy/systemd/c-car-web-frontend.service` — 移除 `--port` 覆盖，使用 nvm node 路径
- `deploy/systemd/c-car-web-backend.service` — Description 加 `(Dev)` 后缀
- `deploy/start.sh` — 移除 `--port 5173` 覆盖

### 3.5 其他安全加固

| 措施 | 说明 |
|---|---|
| AGENTS.md 新增安全注意事项 | 记录 Vite 安全配置要求 |
| 大众司审批流程跳过 | 大众司车辆不走云之家审批 |
| 车辆管理添加大众司 | 所属公司下拉新增选项 |
| 司机ID显示修复 | 改为行号递增显示 |

---

## 四、Nginx 升级后配置修复

### 4.1 问题

Nginx 1.30.4 的 `nginx.conf` 仅包含 `conf.d/*.conf`，不包含 `sites-enabled/*`，导致 `c_car_web` 配置未加载。

### 4.2 修复

```bash
# 创建符号链接到 conf.d
ln -sf /etc/nginx/sites-available/c_car_web /etc/nginx/conf.d/c_car_web.conf

# 删除默认配置避免冲突
rm -f /etc/nginx/conf.d/default.conf
```

---

## 五、验证结果

```
✅ 前端 :5174        → 200 OK
✅ 后端 :5000        → 401（未登录，正常）
✅ Nginx :80         → 200 OK
✅ @fs 拦截          → 403 Forbidden
✅ 漏洞利用测试      → 403 Forbidden
```

---

## 六、建议后续操作

| 优先级 | 操作 | 说明 |
|---|---|---|
| 高 | 关闭 8008 端口映射 | 如不需要公网访问，从路由器删除端口映射 |
| 高 | 定期更新依赖 | `cd frontend && npm update` |
| 中 | 生产环境用静态构建 | `npm run build` + Nginx 直接服务静态文件 |
| 中 | 更换数据库凭据 | `config.py` 中的密码应改为环境变量 |
| 低 | 添加 fail2ban | 自动封禁多次攻击的 IP |

---

## 七、相关文件

- 漏洞报告：`bug1.docx`
- Nginx 配置：`deploy/nginx/c_car_web.conf`
- systemd 服务：`deploy/systemd/c-car-web-*.service`
- 前端配置：`frontend/vite.config.js`
- 项目指引：`AGENTS.md`

---

**报告生成时间**：2026-07-15  
**执行人**：MiMo Code Agent

---

## 附录：企业微信排班确认方案

## 一、项目概述

### 1.1 需求背景
车辆排班完成后，需要将排班信息发送给客户确认，客户在企业微信中点击确认链接完成确认操作，系统保留完整的确认证据链。

### 1.2 技术方案
- **推送渠道**：企业微信应用消息
- **确认方式**：H5确认页面
- **证据存储**：数据库记录 + 数据快照

### 1.3 业务流程
```
调度员排班完成 → 点击推送确认 → 系统生成确认链接 → 企业微信推送消息
    ↓
客户收到消息 → 点击确认链接 → 查看排班详情 → 点击确认/拒绝
    ↓
系统记录证据 → 更新任务状态 → 完成确认
```

---

## 二、数据库设计

### 2.1 新增表：排班确认记录表 (schedule_confirmations)

```sql
CREATE TABLE schedule_confirmations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         INTEGER NOT NULL,           -- 关联任务ID
    customer_id     INTEGER,                    -- 关联客户ID（单位客户）
    customer_name   VARCHAR(100),               -- 客户名称
    customer_phone  VARCHAR(20),                -- 客户电话
    contact_id      INTEGER,                    -- 关联联系人ID
    
    -- 企业微信相关
    wx_userid       VARCHAR(64),                -- 企业微信用户ID
    wx_corp_id      VARCHAR(64),                -- 企业微信企业ID
    
    -- 确认信息
    confirm_token   VARCHAR(64) UNIQUE NOT NULL, -- 确认Token（唯一）
    confirm_status  VARCHAR(20) DEFAULT 'pending', -- pending/confirmed/rejected
    confirm_time    DATETIME,                    -- 确认时间
    confirm_ip      VARCHAR(45),                 -- 客户端IP
    confirm_device  VARCHAR(500),                -- 设备信息（User-Agent）
    confirm_remark  TEXT,                        -- 确认备注/异议说明
    
    -- 消息推送记录
    msg_id          VARCHAR(64),                -- 企业微信消息ID
    push_time       DATETIME,                   -- 推送时间
    push_status     VARCHAR(20) DEFAULT 'pending', -- pending/success/failed
    push_error      TEXT,                       -- 推送失败原因
    
    -- 审计字段
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER,                    -- 发起人用户ID
    
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (customer_id) REFERENCES clients(id),
    FOREIGN KEY (contact_id) REFERENCES client_contacts(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

### 2.2 新增表：确认快照表 (confirmation_snapshots)

```sql
CREATE TABLE confirmation_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    confirmation_id INTEGER NOT NULL,           -- 关联确认记录ID
    snapshot_type   VARCHAR(20),                -- task/customer/vehicle/driver
    snapshot_data   TEXT NOT NULL,              -- JSON快照数据
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (confirmation_id) REFERENCES schedule_confirmations(id)
);
```

### 2.3 表结构说明

#### schedule_confirmations 表字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | INTEGER | 关联tasks表，必填 |
| customer_id | INTEGER | 关联clients表，单位客户时填写 |
| customer_name | VARCHAR | 客户名称（冗余字段，方便查询） |
| customer_phone | VARCHAR | 客户电话 |
| contact_id | INTEGER | 关联client_contacts表 |
| wx_userid | VARCHAR | 企业微信用户ID（@企业成员时使用） |
| wx_corp_id | VARCHAR | 企业微信企业ID |
| confirm_token | VARCHAR | 唯一确认令牌，用于生成确认链接 |
| confirm_status | VARCHAR | 确认状态：pending/confirmed/rejected |
| confirm_time | DATETIME | 客户确认时间 |
| confirm_ip | VARCHAR | 客户端IP地址 |
| confirm_device | VARCHAR | 客户端设备信息 |
| confirm_remark | TEXT | 客户填写的备注或异议说明 |
| msg_id | VARCHAR | 企业微信消息ID |
| push_time | DATETIME | 消息推送时间 |
| push_status | VARCHAR | 推送状态：pending/success/failed |
| push_error | TEXT | 推送失败的错误信息 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| created_by | INTEGER | 发起推送的用户ID |

#### confirmation_snapshots 表字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| confirmation_id | INTEGER | 关联schedule_confirmations表 |
| snapshot_type | VARCHAR | 快照类型：task/customer/vehicle/driver |
| snapshot_data | TEXT | JSON格式的快照数据 |
| created_at | DATETIME | 创建时间 |

---

## 三、后端API设计

### 3.1 推送确认消息

**接口**: `POST /api/task/{task_id}/push-confirm`

**请求参数**:
```json
{
    "contact_id": 123,           // 可选，指定联系人
    "wx_userid": "zhangsan",     // 可选，企业微信用户ID
    "custom_message": "请确认"   // 可选，自定义消息
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "推送成功",
    "data": {
        "confirmation_id": 1,
        "msg_id": "msg_xxx",
        "push_time": "2026-06-07 14:30:00",
        "confirm_url": "https://xxx.com/confirm/abc123"
    }
}
```

**业务逻辑**:
1. 校验任务存在且状态为scheduled
2. 生成唯一confirm_token
3. 创建确认记录
4. 保存任务、客户、车辆、司机快照
5. 调用企业微信API发送消息
6. 更新推送状态

---

### 3.2 获取确认页面数据

**接口**: `GET /api/confirm/{token}`

**响应**:
```json
{
    "code": 200,
    "data": {
        "task_info": {
            "task_no": "SQSYGKSCLCS-20260607-001",
            "departure": "公司",
            "destination": "机场",
            "departure_time": "2026-06-08 08:00",
            "return_time": "2026-06-08 18:00",
            "vehicle_type": "小巴(15座)",
            "vehicle_plate": "粤B12345",
            "driver_name": "张三",
            "driver_phone": "13800138000"
        },
        "confirm_status": "pending",
        "push_time": "2026-06-07 14:30:00",
        "created_by": "调度员李四"
    }
}
```

**业务逻辑**:
1. 根据token查询确认记录
2. 从快照中恢复任务信息
3. 返回确认状态和任务详情

---

### 3.3 提交确认

**接口**: `POST /api/confirm/{token}`

**请求参数**:
```json
{
    "action": "confirm",         // confirm 或 reject
    "remark": "同意，准时出发"   // 可选，备注
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "确认成功",
    "data": {
        "confirm_time": "2026-06-07 15:00:00",
        "confirm_status": "confirmed"
    }
}
```

**业务逻辑**:
1. 校验token有效且状态为pending
2. 记录确认信息（时间、IP、设备、备注）
3. 更新确认状态
4. 更新任务状态（confirmed/rejected）
5. 可选：通知调度员确认结果

---

### 3.4 查询确认记录

**接口**: `GET /api/task/{task_id}/confirmation`

**响应**:
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "task_id": 123,
        "customer_name": "某某公司",
        "confirm_status": "confirmed",
        "confirm_time": "2026-06-07 15:00:00",
        "confirm_ip": "120.36.xx.xx",
        "confirm_remark": "同意",
        "push_time": "2026-06-07 14:30:00",
        "push_status": "success",
        "created_by_name": "李四"
    }
}
```

---

### 3.5 获取确认列表

**接口**: `GET /api/confirmations`

**查询参数**:
- `status`: 筛选状态（pending/confirmed/rejected）
- `page`: 页码
- `per_page`: 每页数量

**响应**:
```json
{
    "code": 200,
    "data": {
        "total": 100,
        "items": [
            {
                "id": 1,
                "task_id": 123,
                "task_no": "SQSYGKSCLCS-20260607-001",
                "customer_name": "某某公司",
                "confirm_status": "confirmed",
                "confirm_time": "2026-06-07 15:00:00"
            }
        ]
    }
}
```

---

## 四、企业微信配置

### 4.1 企业微信接入准备

#### 4.1.1 注册企业微信
1. 访问 https://work.weixin.qq.com/
2. 注册企业微信账号
3. 完成企业认证

#### 4.1.2 创建应用
1. 登录企业微信管理后台
2. 进入"应用管理" → "自建"
3. 点击"创建应用"
4. 填写应用信息：
   - 应用名称：排班确认
   - 应用Logo：上传Logo
   - 应用介绍：车辆排班客户确认

#### 4.1.3 获取配置信息
```
CorpID: ww1234567890abcdef        # 企业ID
AgentID: 1000002                   # 应用AgentId
Secret: xxxxxxxxxxxxxxxxxxxxxxxx   # 应用Secret
```

#### 4.1.4 配置可信域名
1. 进入应用设置
2. 设置"网页授权及JS-SDK"
3. 添加可信域名：your-domain.com

### 4.2 配置文件

在 `backend/config.py` 中添加：

```python
# 企业微信配置
WX_WORK_CORP_ID = 'ww1234567890abcdef'
WX_WORK_AGENT_ID = '1000002'
WX_WORK_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxx'

# 确认页面域名
CONFIRM_BASE_URL = 'https://your-domain.com'
```

---

## 五、企业微信API集成

### 5.1 获取Access Token

```python
def get_wx_work_token():
    """获取企业微信access_token"""
    url = f'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
    params = {
        'corpid': Config.WX_WORK_CORP_ID,
        'corpsecret': Config.WX_WORK_SECRET
    }
    # 请求并缓存token（2小时有效）
    # ...
```

### 5.2 发送应用消息

```python
def send_wx_work_message(userid, title, content, confirm_url):
    """发送企业微信应用消息"""
    url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}'
    data = {
        "touser": userid,
        "msgtype": "textcard",
        "agentid": Config.WX_WORK_AGENT_ID,
        "textcard": {
            "title": title,
            "description": content,
            "url": confirm_url,
            "btntxt": "确认排班"
        }
    }
    # 发送请求
    # ...
```

### 5.3 发送消息到客户（非企业成员）

```python
def send_message_to_external_user(external_userid, content):
    """发送消息到外部联系人"""
    url = f'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/message/send?access_token={token}'
    data = {
        "chat_type": "single",
        "external_userid": [external_userid],
        "sender": "",
        "text": {
            "content": content
        },
        "msgtype": "text"
    }
    # 发送请求
    # ...
```

---

## 六、前端页面设计

### 6.1 H5确认页面

**文件**: `frontend/src/views/ConfirmSchedule.vue`

**功能**:
- 显示排班详情卡片
- 确认/拒绝按钮
- 备注输入框
- 确认成功/失败提示
- 响应式设计（适配手机）

**页面结构**:
```
┌─────────────────────────────────────┐
│         排班确认                     │
├─────────────────────────────────────┤
│  任务编号: SQSYGKSCLCS-20260607-001 │
│  出发时间: 2026-06-08 08:00         │
│  出发地点: 公司                      │
│  目的地: 机场                       │
│  车辆类型: 小巴(15座)               │
│  车牌号: 粤B12345                   │
│  驾驶员: 张三                       │
│  联系电话: 13800138000              │
├─────────────────────────────────────┤
│  备注: [________________]           │
│                                     │
│  [拒绝]           [确认]            │
└─────────────────────────────────────┘
```

### 6.2 管理后台确认记录页面

**文件**: `frontend/src/views/ConfirmationManagement.vue`

**功能**:
- 确认记录列表
- 筛选条件（状态、时间、客户）
- 查看详情
- 导出功能

---

## 七、开发步骤

### 阶段一：环境准备（1天）

#### 步骤1：注册企业微信
- [ ] 注册企业微信账号
- [ ] 完成企业认证
- [ ] 记录CorpID

#### 步骤2：创建应用
- [ ] 登录管理后台
- [ ] 创建自建应用
- [ ] 记录AgentID和Secret
- [ ] 配置可信域名

#### 步骤3：配置后端
- [ ] 修改config.py添加企业微信配置
- [ ] 安装依赖（如需要）

---

### 阶段二：数据库设计（0.5天）

#### 步骤4：创建数据表
- [ ] 修改models.py，添加ScheduleConfirmation模型
- [ ] 修改models.py，添加ConfirmationSnapshot模型
- [ ] 运行数据库迁移

---

### 阶段三：后端API开发（2天）

#### 步骤5：企业微信工具函数
- [ ] 创建utils/wx_work.py
- [ ] 实现get_wx_work_token()函数
- [ ] 实现send_wx_work_message()函数
- [ ] 实现token缓存机制

#### 步骤6：确认API开发
- [ ] 实现POST /api/task/{task_id}/push-confirm
- [ ] 实现GET /api/confirm/{token}
- [ ] 实现POST /api/confirm/{token}
- [ ] 实现GET /api/task/{task_id}/confirmation
- [ ] 实现GET /api/confirmations

#### 步骤7：快照功能
- [ ] 实现任务快照生成函数
- [ ] 实现快照保存功能
- [ ] 实现快照读取功能

---

### 阶段四：前端开发（2天）

#### 步骤8：H5确认页面
- [ ] 创建ConfirmSchedule.vue
- [ ] 实现响应式布局
- [ ] 实现确认/拒绝功能
- [ ] 实现备注输入
- [ ] 实现成功/失败提示

#### 步骤9：管理页面
- [ ] 创建ConfirmationManagement.vue
- [ ] 实现列表展示
- [ ] 实现筛选功能
- [ ] 实现详情查看

#### 步骤10：任务管理页面集成
- [ ] 在TaskManagement.vue添加"推送确认"按钮
- [ ] 实现推送功能调用
- [ ] 显示确认状态标签

---

### 阶段五：测试与优化（1天）

#### 步骤11：功能测试
- [ ] 测试消息推送
- [ ] 测试确认流程
- [ ] 测试证据记录
- [ ] 测试异常情况

#### 步骤12：优化完善
- [ ] 添加错误处理
- [ ] 优化用户体验
- [ ] 完善日志记录

---

## 八、代码结构

### 8.1 新增文件
```
backend/
├── models.py              # 添加新模型
├── config.py              # 添加配置项
├── utils/
│   └── wx_work.py         # 企业微信工具函数
└── api/
    └── confirmation.py    # 确认相关API

frontend/
└── src/
    └── views/
        ├── ConfirmSchedule.vue         # H5确认页面
        └── ConfirmationManagement.vue  # 管理页面
```

### 8.2 修改文件
```
backend/
└── app.py                 # 注册新路由

frontend/
└── src/
    ├── router/
    │   └── index.js       # 添加路由
    └── views/
        └── TaskManagement.vue  # 添加推送按钮
```

---

## 九、证据链说明

### 9.1 证据要素
| 证据 | 来源 | 说明 |
|------|------|------|
| 推送记录 | schedule_confirmations | 消息ID、推送时间、推送状态 |
| 确认时间 | confirm_time | 精确到秒 |
| 客户身份 | wx_userid + phone | 双重身份标识 |
| 操作记录 | confirm_status | 确认/拒绝操作 |
| 客户端信息 | confirm_ip + confirm_device | IP和设备信息 |
| 数据快照 | confirmation_snapshots | 确认时的完整任务信息 |

### 9.2 证据链完整性
```
排班完成 → 保存快照 → 推送消息 → 记录消息ID → 客户确认 → 记录时间/IP → 更新状态
     ↓           ↓           ↓           ↓           ↓           ↓
  任务数据     快照表      消息记录     推送状态     确认记录     审计日志
```

### 9.3 防篡改措施
1. **数据快照**：确认时保存完整的任务、客户、车辆、司机信息
2. **不可变记录**：确认记录只允许追加，不允许修改
3. **审计日志**：记录所有操作的时间和操作人
4. **Token安全**：使用随机Token，防止猜测和重放

---

## 十、注意事项

### 10.1 安全考虑
1. Token使用UUID或随机字符串，长度至少32位
2. Token设置有效期（如7天）
3. 确认页面使用HTTPS
4. 防止SQL注入和XSS攻击
5. 限制API调用频率

### 10.2 异常处理
1. 企业微信API调用失败
2. Token过期或无效
3. 网络超时
4. 重复确认

### 10.3 性能优化
1. Access Token缓存
2. 数据库索引优化
3. 静态资源CDN
4. 接口响应缓存

---

## 十一、测试用例

### 11.1 推送确认测试
- [ ] 正常推送成功
- [ ] 推送失败重试
- [ ] 无联系人时提示
- [ ] 重复推送处理

### 11.2 确认流程测试
- [ ] 正常确认成功
- [ ] 拒绝操作
- [ ] Token过期处理
- [ ] 重复确认处理

### 11.3 证据记录测试
- [ ] 快照数据完整性
- [ ] 确认记录准确性
- [ ] IP和设备记录

---

## 十二、后续扩展

### 12.1 可选功能
1. **模板消息**：使用更丰富的消息模板
2. **提醒功能**：超时未确认自动提醒
3. **批量推送**：多个任务批量推送确认
4. **统计报表**：确认率统计、响应时间分析
5. **消息撤回**：允许撤回已发送的确认

### 12.2 系统集成
1. **企业微信通讯录**：自动同步客户联系人
2. **企业微信审批**：集成审批流程
3. **企业微信日程**：创建排班日程

---

## 附录A：企业微信API参考

### A.1 获取access_token
```
GET https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=ID&corpsecret=SECRET
```

### A.2 发送应用消息
```
POST https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=ACCESS_TOKEN
```

### A.3 消息类型
- text: 文本消息
- textcard: 文本卡片消息（推荐）
- news: 图文消息
- markdown: Markdown消息

---

## 附录B：确认消息模板

### B.1 文本卡片消息示例
```json
{
    "touser": "UserID1|UserID2",
    "msgtype": "textcard",
    "agentid": 1000002,
    "textcard": {
        "title": "排班确认通知",
        "description": "<div class=\"gray\">2026年06月07日</div> <div class=\"normal\">任务编号：SQSYGKSCLCS-20260607-001</div><div class=\"highlight\">请于明日08:00准时出发</div>",
        "url": "https://xxx.com/confirm/abc123",
        "btntxt": "确认排班"
    }
}
```

---

**文档版本**: v1.0
**创建日期**: 2026-06-07
**最后更新**: 2026-06-07
**作者**: 开发团队

---

## 附录：用户操作指南

## 一、系统登录

1. 打开浏览器，输入系统地址
2. 输入用户名和密码，点击「登录」
3. 默认管理员账号：`admin` / `admin123`

---

## 二、任务管理

任务管理是系统的核心页面，用于录入、排班、完成包车任务以及发起云之家审批。

### 2.1 录入任务

1. 点击页面右上角「**录入任务**」按钮
2. 选择用车类型：
   - **个人**：填写姓名和手机号码
   - **单位**：从下拉列表选择用车单位和联系人
3. 填写以下信息：
   - 车辆类型（大巴/中巴/小巴/商务车）
   - 出发地点、目的地
   - 出车时间、回程时间（系统自动计算租用天数）
   - 任务里程、租车费
   - 油电费、桥路费（预估）
   - 差费标准（自动计算司机人工费）
4. 系统自动计算：预计成本 = 油电费 + 桥路费 + 人工费
5. 系统自动计算：预估利润 = 租车费 - 预计成本
6. 点击「确定」保存

### 2.2 排班分配

任务录入后状态为「**待排班**」，需要分配车辆和司机：

1. 在任务列表中找到待排班的任务，点击「**排班分配**」
2. 弹窗显示该时间段可用的车辆和司机
3. 选择车辆和司机后，点击「**确认排班**」
4. 任务状态变为「**已排班**」

> 系统会自动排除该时间段已被占用的车辆和司机。

### 2.3 完成任务

任务执行完毕后，录入实际费用：

1. 在已排班任务中点击「**完成任务**」
2. 填写实际费用：
   - 实际油电费、实际桥路费、实际司机人工费、其他费用
3. 系统自动计算：实际成本、最终利润
4. 点击「**确认完成**」
5. 任务状态变为「**已完成**」

### 2.4 编辑和删除

- 未完成的任务可以「**编辑**」修改信息
- 修改记录会自动保存到「**变更记录**」中
- 可以「**删除**」不需要的任务

### 2.5 任务状态说明

| 状态 | 颜色 | 说明 |
|------|------|------|
| 待排班 | 橙色 | 已录入但未分配车辆司机 |
| 已排班 | 蓝色 | 已分配车辆司机，可发起审批 |
| 已完成 | 绿色 | 已执行完毕并录入实际费用 |

---

## 三、发起云之家审批

### 3.1 操作步骤

1. 点击任务管理页面的「**发起审批**」按钮（绿色）
2. 弹窗中显示所有**已排班**的任务列表
3. 勾选需要发起审批的任务（只能选同一所属公司的车辆）
4. 底部显示已选任务数量和所属公司分布
5. 点击「**发起审批**」提交

### 3.2 审批规则

| 规则 | 说明 |
|------|------|
| 只能选已排班任务 | 待排班和已完成的任务无法勾选 |
| 已过期任务不能发起 | 出车时间已过的任务自动置灰 |
| 已发起的任务不能重复 | 已提交审批的任务显示「已发起」，无法再勾选 |
| 不能混合不同公司 | 国顺司、国开司、外单位的车辆必须分开发起 |

### 3.3 审批模板自动匹配

系统根据车辆的**所属公司**自动选择对应的审批模板：

| 车辆所属公司 | 审批模板 |
|------------|---------|
| 国顺司 | 申请使用国顺司车辆测试 |
| 国开司 | 申请使用国开司车辆测试 |
| 外单位 | 申请使用外单位司车辆测试 |

### 3.4 审批状态显示

任务管理页面的「审批」列显示：

| 状态 | 说明 |
|------|------|
| - | 未发起审批 |
| 已发起（绿色） | 审批已提交，等待审批人处理 |
| 已通过（蓝色） | 审批已通过 |
| 已拒绝（红色） | 审批被拒绝 |

下方还会显示审批流水号（如 `SQSYGSSCLCS-20260527-005`），可在云之家APP中通过该流水号搜索审批单。

---

## 四、车辆管理

管理公司所有车辆信息。

### 4.1 添加车辆

1. 点击「**添加车辆**」
2. 填写车牌号、选择车辆类型
3. **选择所属公司**（国顺司 / 国开司 / 外单位）
4. 选择状态（可用 / 忙碌 / 维修中）
5. 点击「确定」

> **重要：** 所属公司决定了该车辆发起审批时使用哪个模板，请务必正确选择。

### 4.2 编辑车辆

点击「编辑」可修改车辆信息，包括所属公司。

---

## 五、司机管理

管理司机信息（姓名、电话、状态）。

### 5.1 添加司机

1. 点击「添加司机」
2. 填写姓名和电话号码
3. 选择状态（可用 / 忙碌 / 离职）

---

## 六、客户管理

管理用车单位和联系人信息。

### 6.1 添加单位

1. 点击「添加单位」
2. 填写单位名称和地址

### 6.2 管理联系人

在单位列表中点击「联系人」，可为每个单位添加多个联系人。

---

## 七、差费标准

管理各目的地的司机差费标准。

### 7.1 添加标准

1. 点击「添加标准」
2. 填写目的地名称
3. 填写费用金额和对应天数
4. 系统在排班时自动计算人工费

---

## 八、报表管理

### 8.1 按客户统计

查看各客户的用车次数、费用汇总。

### 8.2 按司机统计

查看各司机的任务量、人工费汇总。

### 8.3 按车辆统计

查看各车辆的使用次数、收入汇总。

---

## 九、常见问题

### Q: 任务录入后看不到？

A: 检查任务状态筛选条件，确保显示了「待排班」状态的任务。

### Q: 排班时提示没有可用车辆？

A: 检查车辆状态是否为「可用」，以及该时间段是否与其他任务冲突。

### Q: 发起审批报错？

A: 确认以下几点：
- 车辆已设置所属公司
- 任务状态为「已排班」
- 出车时间未过期
- 所选任务为同一所属公司
- 云之家服务正常

### Q: 审批流水号在哪里查看？

A: 在任务管理页面的「审批」列中，已发起审批的任务会显示流水号。也可以在云之家APP中通过流水号搜索。

### Q: 审批被拒绝了怎么办？

A: 审批拒绝后，任务的审批状态会变为「已拒绝」，可以重新发起审批。

### Q: 页面长时间不操作后报错？

A: 这是正常的连接超时，刷新页面即可恢复。

---

## 十、数据流程图

```
录入任务 → 待排班
    ↓
排班分配 → 已排班
    ↓
发起审批 → 云之家审批流程
    ↓
审批通过 → 任务可执行
    ↓
完成任务 → 录入实际费用 → 已完成
```

---

## 附录：云之家审批集成说明

## 一、功能概述

任务管理页面支持将包车任务发起为云之家审批流程。系统按车辆所属公司自动匹配审批模板，多条任务可合并为一条审批，明细行自动填充。

## 二、云之家开发者配置

| 配置项 | 值 |
|--------|-----|
| 审批appId | SP11228529 |
| 工作圈eid | 11228529 |
| 开发者secret（team scope） | z69nc1A9qyCXGugKYV49vvzUMElCAK |
| 资源组密钥（resGroupSecret scope） | 2uTljIhad999kw1uXRDhdoH8NytDZP0f |
| 开发者key | FB5daoyipm49K58y |
| 发起人openid | `5b078855e4b098424c8c3f7f` |

### 审批模板（带"测试"后缀）

| 所属公司 | 模板名称 | formCodeId |
|---------|---------|-----------|
| 国顺司 | 申请使用国顺司车辆测试 | `0e1d321692a9441fa24db3bb3776a7d9` |
| 国开司 | 申请使用国开司车辆测试 | `3d50bcac14d947a5a006d64187b8fa5b` |
| 外单位 | 申请使用外单位司车辆测试 | `134dc1d64c964b68870e5a2665baac0d` |

## 三、获取 access_token

```
GET https://yunzhijia.com/gateway/oauth2/token/getAccessToken?appId=SP11228529&eid=11228529&secret=xxx&timestamp=毫秒时间戳&scope=team
```

> 必须用 GET + Query String。POST 会返回 secret出错。token 有效期约 5000-7200 秒。

## 四、创建审批流程（createInst）

```
POST https://www.yunzhijia.com/gateway/workflow/form/thirdpart/createInst?accessToken={token}
Content-Type: application/json
```

### 请求体结构

```json
{
    "formCodeId": "模板codeId",
    "creator": "发起人openid",
    "skipWidgetAuthorityCheck": true,
    "useAlias": false,
    "requestId": "UUID",
    "widgetValue": { "_S_TITLE": "审批标题" },
    "details": {
        "Dd_0": {
            "widgetValue": [
                { "_id_": "1", "Te_0": "用车方", "Te_1": "联系人", ... },
                { "_id_": "2", "Te_0": "用车方2", "Te_1": "联系人2", ... }
            ]
        }
    }
}
```

> **关键：** 明细数据放在 `details` 参数中（与 `widgetValue` 平级），不能放在 `widgetValue` 内部。

## 五、明细字段顺序（已通过 viewFormDef 接口确认）

> ⚠️ 注意：字段编号（Te_8 ~ Te_16）与表头显示顺序不一致，必须按 codeId 送数据，不能按表头顺序。
> 以下映射已通过 `viewFormDef` 接口验证，codeId 由云之家模板定义决定。

| codeId | 控件标题 | 对应任务字段 |
|--------|---------|------------|
| Te_0 | 用车方 | client_name / client_company |
| Te_1 | 联系人 | client_name + " " + client_phone |
| Te_2 | 出发地点 | departure |
| Te_3 | 目的地 | destination |
| Te_4 | 车牌号 | vehicle.plate_number |
| Te_5 | 驾驶司机 | driver.name |
| Te_6 | 出车时间 | departure_time（yyyy-MM-dd HH:mm） |
| Te_7 | 回程时间 | return_time（yyyy-MM-dd HH:mm） |
| Te_8 | 车辆类型 | vehicle_type |
| Te_9 | 里程(km) | mileage |
| Te_10 | 租车费 | rental_fee |
| Te_11 | 油电费 | fuel_fee |
| Te_12 | 桥路费 | bridge_fee |
| Te_13 | 司机人工费 | labor_fee |
| Te_14 | 预计成本 | estimated_cost |
| Te_15 | 预估利润 | estimated_profit |
| Te_16 | 天数 | rental_days |

### 验证字段映射的方法

如需确认模板字段定义，可调用 `viewFormDef` 接口：

```
POST https://www.yunzhijia.com/gateway/workflow/form/thirdpart/viewFormDef?accessToken={token}
Content-Type: application/json

{ "formCodeId": "模板codeId" }
```

返回的 `data.formInfo.detailMap.Dd_0.widgetVos` 中包含每个子字段的 codeId 和标题。

## 六、审批模板自动匹配规则

系统根据任务排班车辆的**所属公司**自动选择审批模板：

| 车辆所属公司 | 审批模板 |
|------------|---------|
| 国顺司 | 申请使用国顺司车辆测试 |
| 国开司 | 申请使用国开司车辆测试 |
| 外单位（或未设置） | 申请使用外单位司车辆测试 |

> 不同所属公司的车辆不能混合发起审批，系统会按公司分组分别提交。

## 七、获取审批流水号

```
POST https://www.yunzhijia.com/gateway/workflow/form/thirdpart/viewFormInst?accessToken={token}
```

请求体：`{ "formInstId": "createInst返回的formInstId", "formCodeId": "模板codeId" }`

流水号在 `data.formInfo.widgetMap._S_SERIAL.value` 中（如 `SQSYGSSCLCS-20260527-005`）。

## 八、审批回调

```
POST https://你的域名/api/yunzhijia/callback
```

### 8.1 回调配置

在云之家开发者后台配置回调地址（"大众回调"）：
- 回调URL: `http://你的域名:端口/api/yunzhijia/callback`
- 数据格式: 加密（AES/ECB模式）

### 8.2 回调解密

回调数据是 **AES/ECB/PKCS5Padding** 加密的 Base64 字符串。

| 配置项 | 说明 |
|--------|------|
| 加密算法 | AES/ECB/PKCS5Padding |
| 密钥来源 | 开发者key（16位字符） |
| 密钥编码 | UTF-8 |

**解密流程**：
1. Base64 解码回调数据
2. 使用开发者key的UTF-8字节作为AES密钥
3. AES/ECB模式解密
4. 去除PKCS7 padding
5. 解析JSON

### 8.3 回调数据结构

云之家"大众回调"发送的是**表单数据**，不是审批状态通知：

```json
{
  "data": {
    "formInfo": {
      "widgetMap": {
        "_S_SERIAL": { "value": "SQSYGSSCLCS-20260614-005" },
        "_S_DATE": { "value": 1781439780880 },
        ...
      }
    }
  },
  "success": true,
  "bizId": "cloudFlow",
  "errorCode": 0
}
```

### 8.4 审批状态查询

由于回调不包含审批状态，系统需要**主动查询**：

```
POST https://www.yunzhijia.com/gateway/workflow/form/thirdpart/getFlowStatus?accessToken={token}
Content-Type: application/json

{ "flowInstId": "流程实例ID" }
```

返回数据：
```json
{ "data": "FINISH", "errorCode": 0 }
```

| 返回值 | 含义 | 系统处理 |
|--------|------|---------|
| FINISH | 审批完成 | 任务标记「已通过」 |
| agree | 审批通过 | 任务标记「已通过」 |
| reject | 审批拒绝 | 任务标记「已拒绝」 |
| revoke | 撤销审批 | 清空状态，可重新发起 |

### 8.5 回调处理流程

1. 接收加密回调数据
2. AES/ECB解密（使用开发者key）
3. 从表单数据中提取流水号（`_S_SERIAL`）
4. 通过流水号匹配本地任务
5. 调用 `getFlowStatus` API 查询审批状态
6. 更新任务审批状态

## 九、车辆所属公司

车辆管理中每辆车需设置「所属公司」，选项为：国顺司、国开司、外单位。此字段决定审批时使用哪个模板。

## 十、注意事项

1. access_token 必须用 GET + Query String 获取
2. 明细数据放在 `details` 参数中（与 `widgetValue` 平级）
3. 已过出车时间的任务禁止发起审批
4. 已发起过审批的任务不能重复提交
5. 不同所属公司的车辆不能混合发起审批
6. token 有效期约 1.5-2 小时，过期自动刷新重试
7. 审批回调地址支持 HTTP（开发环境）或 HTTPS（生产环境）
8. 重启后端后需调用 `POST /api/init-db` 初始化数据库字段
9. **回调解密使用 AES/ECB 模式**，密钥是开发者key（16位），不是标准的43位 EncodingAESKey
10. **云之家"大众回调"只发送表单数据**，审批状态需要通过 `getFlowStatus` API 主动查询

---

## 附录：Nginx与代理配置说明

本文说明包车排班系统在开发环境下的网络架构、各服务端口、配置文件位置，以及如何修改访问端口。

---

## 一、整体架构

系统由三个进程组成：**Nginx（对外入口）**、**Vite 前端开发服务**、**Flask 后端 API 服务**。

```
局域网用户浏览器
        │
        │  http://192.168.1.3:80  （对外访问端口，可改）
        ▼
┌───────────────────────────────────────┐
│  Nginx  (:80)                         │
│  配置文件: deploy/nginx/c_car_web.conf │
│  系统路径: /etc/nginx/sites-enabled/   │
└───────────────┬───────────────────────┘
                │
     ┌──────────┴──────────┐
     │                     │
     │ /api/*              │  /* （页面、JS、CSS、热更新 WebSocket）
     ▼                     ▼
┌─────────────┐     ┌─────────────┐
│ Flask 后端   │     │ Vite 前端    │
│ 127.0.0.1   │     │ 127.0.0.1   │
│ :5000       │     │ :5173       │
└─────────────┘     └─────────────┘
 python3 app.py      npm run dev
```

**设计要点：**

- 前端和后端只监听 `127.0.0.1`（本机），**不直接暴露**给局域网，避免绕过 Nginx。
- 局域网用户统一通过 **Nginx 的对外端口** 访问。
- 前端代码里 API 地址写死为相对路径 `/api`（见 `frontend/src/utils/api.js`），浏览器会请求「当前访问域名 + /api」，因此只要走 Nginx 入口，无需改前端代码。

---

## 二、请求是如何转发的

### 2.1 打开页面（例如访问首页）

```
浏览器 GET http://192.168.1.3/
    → Nginx location /
    → 转发到 http://127.0.0.1:5173/
    → Vite 返回 index.html 及前端资源
```

### 2.2 登录、查询任务等 API 请求

```
浏览器 POST http://192.168.1.3/api/login
    → Nginx location /api/
    → 转发到 http://127.0.0.1:5000/api/login
    → Flask 处理并返回 JSON
```

### 2.3 前端热更新（开发模式）

Vite 通过 WebSocket 推送代码变更。Nginx 在 `location /` 中配置了：

```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

这样浏览器连 `ws://192.168.1.3/...` 时，Nginx 会把 WebSocket 转发到 Vite，热更新才能正常工作。

---

## 三、各服务端口与配置文件

| 组件 | 默认端口 | 监听地址 | 项目内配置文件 | 系统部署后位置 |
|------|---------|---------|---------------|---------------|
| **Nginx（对外入口）** | **80** | `0.0.0.0`（全网卡） | `deploy/nginx/c_car_web.conf` | `/etc/nginx/sites-enabled/c_car_web` |
| Flask 后端 | 5000 | `127.0.0.1` | `backend/app.py` 最后一行 | systemd: `c-car-web-backend.service` |
| Vite 前端 | 5173 | `127.0.0.1` | `frontend/vite.config.js` | systemd: `c-car-web-frontend.service` |

### 3.1 Nginx 配置（核心）

文件：`deploy/nginx/c_car_web.conf`

```nginx
listen 80;                          # ← 对外访问端口

location /api/ {
    proxy_pass http://127.0.0.1:5000;   # ← 后端地址
}

location / {
    proxy_pass http://127.0.0.1:5173;   # ← 前端地址
}
```

### 3.2 后端端口

文件：`backend/app.py`

```python
app.run(debug=True, host='127.0.0.1', port=5000)
```

### 3.3 前端端口

文件：`frontend/vite.config.js`

```javascript
server: {
  host: '127.0.0.1',
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:5000',   // 仅本地直连 Vite 时生效
      changeOrigin: true
    }
  }
}
```

> **说明：** 经 Nginx 访问时，API 由 Nginx 转发，不经过 Vite 的 `proxy`。Vite 的 proxy 只在「直接打开 `http://127.0.0.1:5173`」调试时有用。

### 3.4 systemd 服务（可选，用 install.sh 安装后生效）

| 服务名 | 启动命令 |
|--------|---------|
| `c-car-web-backend` | `python3 app.py` |
| `c-car-web-frontend` | `npm run dev -- --host 127.0.0.1 --port 5173` |

---

## 四、如何修改访问端口

下面分三种常见需求说明。**改完配置后都要重载/重启对应服务。**

---

### 4.1 修改对外访问端口（最常用）

例如：把局域网访问从 `http://192.168.1.3` 改为 `http://192.168.1.3:8080`。

**只需改 Nginx 的 `listen` 端口**，前后端内部端口（5000、5173）不用动。

**步骤：**

1. 编辑 `deploy/nginx/c_car_web.conf`：

```nginx
# 改前
listen 80;

# 改后（示例：8080）
listen 8080;
listen [::]:8080;
```

2. 同步到系统并重载 Nginx：

```bash
sudo cp deploy/nginx/c_car_web.conf /etc/nginx/sites-enabled/c_car_web
sudo nginx -t                    # 检查语法
sudo systemctl reload nginx      # 重载配置
```

3. 若启用了防火墙，放行新端口：

```bash
sudo ufw allow 8080/tcp
# 如不再使用 80 端口，可删除旧规则：sudo ufw delete allow 80/tcp
```

4. 局域网访问地址变为：

```
http://192.168.1.3:8080
```

**注意：** 1024 以下的端口（如 80）需要 root 权限，8080、8888 等高位端口普通配置即可。

---

### 4.2 修改后端内部端口（5000 → 其他）

例如改为 `5001`。需要改 **3 处**，并保持 Nginx 的 `proxy_pass` 与后端一致。

| 序号 | 文件 | 修改内容 |
|------|------|---------|
| 1 | `backend/app.py` | `port=5001` |
| 2 | `deploy/nginx/c_car_web.conf` | `proxy_pass http://127.0.0.1:5001;`（`/api/` 段） |
| 3 | `frontend/vite.config.js` | `target: 'http://127.0.0.1:5001'`（本地直连 Vite 调试用） |

若使用 systemd，还需改 `deploy/systemd/c-car-web-backend.service`（命令本身不变，端口在 app.py 里）。

**重启：**

```bash
sudo systemctl restart c-car-web-backend
sudo cp deploy/nginx/c_car_web.conf /etc/nginx/sites-enabled/c_car_web
sudo nginx -t && sudo systemctl reload nginx
```

对外访问端口（Nginx 的 80 或 8080）**不需要改**。

---

### 4.3 修改前端内部端口（5173 → 其他）

例如改为 `3000`。需要改 **3 处**：

| 序号 | 文件 | 修改内容 |
|------|------|---------|
| 1 | `frontend/vite.config.js` | `port: 3000` |
| 2 | `deploy/nginx/c_car_web.conf` | `proxy_pass http://127.0.0.1:3000;`（`location /` 段） |
| 3 | `deploy/systemd/c-car-web-frontend.service` | `--port 3000` |

**重启：**

```bash
sudo cp deploy/systemd/c-car-web-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart c-car-web-frontend
sudo cp deploy/nginx/c_car_web.conf /etc/nginx/sites-enabled/c_car_web
sudo nginx -t && sudo systemctl reload nginx
```

对外访问端口同样**不需要改**。

---

## 五、两种访问方式对比

| 访问方式 | 地址示例 | 适用场景 |
|---------|---------|---------|
| **经 Nginx（推荐，局域网用）** | `http://192.168.1.3:80` | 局域网其他电脑访问；与生产环境路径一致 |
| **直连 Vite（仅本机调试）** | `http://127.0.0.1:5173` | 本机开发；API 由 Vite proxy 转到 5000 |
| **直连 Flask（仅测 API）** | `http://127.0.0.1:5000/api/...` | 用 curl/Postman 测接口 |

---

## 六、部署与日常命令

### 首次部署（安装 Nginx + 注册 systemd 服务）

```bash
sudo bash deploy/install.sh
```

### 手动启动（不用 systemd）

```bash
bash deploy/start.sh
# 仍需单独配置 Nginx 才能局域网访问
```

### 修改 Nginx 配置后的标准流程

```bash
sudo cp deploy/nginx/c_car_web.conf /etc/nginx/sites-enabled/c_car_web
sudo nginx -t                 # 必须通过，否则不要 reload
sudo systemctl reload nginx
```

### 查看日志

```bash
# Nginx 访问/错误日志
sudo tail -f /var/log/nginx/c_car_web_access.log
sudo tail -f /var/log/nginx/c_car_web_error.log

# 后端 / 前端 systemd 日志
sudo journalctl -u c-car-web-backend -f
sudo journalctl -u c-car-web-frontend -f
```

### 检查端口占用

```bash
ss -tlnp | grep -E ':80|:5000|:5173'
```

---

## 七、常见问题

### Q1：改了 Nginx 端口，局域网还是访问不了？

1. 确认 Nginx 已重载：`sudo systemctl status nginx`
2. 确认防火墙已放行：`sudo ufw status`
3. 确认访问 URL 带上了新端口，例如 `http://192.168.1.3:8080`
4. 确认后端、前端服务在运行：`sudo systemctl status c-car-web-backend c-car-web-frontend`

### Q2：页面能打开，但登录/API 报错？

1. 检查后端是否在 5000 端口：`curl http://127.0.0.1:5000/api/init-db -X POST`
2. 检查 Nginx `/api/` 的 `proxy_pass` 是否指向正确后端端口
3. 查看 Nginx 错误日志

### Q3：本机 5173 正常，经 Nginx 访问没有热更新？

确认 `c_car_web.conf` 的 `location /` 中包含 WebSocket 相关 `Upgrade` / `Connection` 头（默认已配置）。

### Q4：云之家审批回调地址怎么填？

回调需从公网或内网可达的 **Nginx 对外地址**，例如：

```
http://192.168.1.3/api/yunzhijia/callback
```

若改了 Nginx 端口，需带上端口，例如：

```
http://192.168.1.3:8080/api/yunzhijia/callback
```

---

## 八、配置文件速查

```
c_car_web/
├── deploy/
│   ├── nginx/c_car_web.conf          # Nginx 反代规则（对外端口在这里改）
│   ├── systemd/
│   │   ├── c-car-web-backend.service # 后端 systemd
│   │   └── c-car-web-frontend.service# 前端 systemd
│   ├── install.sh                    # 一键部署脚本
│   └── start.sh                      # 手动启动脚本
├── backend/app.py                    # 后端端口 host/port
└── frontend/
    ├── vite.config.js                # 前端端口 + 本地调试 proxy
    └── src/utils/api.js              # API 基路径 /api（一般不用改）
```

---

## 九、端口修改速查表

| 想改什么 | 改哪些文件 | 局域网 URL 变化 |
|---------|-----------|----------------|
| 对外访问端口 80→8080 | 仅 `c_car_web.conf` 的 `listen` + 防火墙 | `http://IP:8080` |
| 后端 5000→5001 | `app.py` + `c_car_web.conf` + `vite.config.js` | 无变化（仍走 Nginx 对外端口） |
| 前端 5173→3000 | `vite.config.js` + `c_car_web.conf` + frontend systemd | 无变化 |

**原则：用户看到的端口 = Nginx 的 `listen`；5000 和 5173 是服务器内部端口，局域网用户通常无感知。**
