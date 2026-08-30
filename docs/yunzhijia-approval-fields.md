# 云之家审批模板控件 ID 对照表

## 审批模板 ID

| 所属公司 | formCodeId |
|---------|------------|
| 国顺司 | `0e1d321692a9441fa24db3bb3776a7d9` |
| 国开司 | `3d50bcac14d947a5a006d64187b8fa5b` |
| 外单位 | `134dc1d64c964b68870e5a2665baac0d` |

## 控件 ID 对照表

| 控件 ID | 含义 | 数据类型 | 数据来源 | 备注 |
|---------|------|---------|---------|------|
| `_S_TITLE` | 审批单标题 | 文本 | `包车审批 - 出发地→目的地 日期` | 标题控件 |
| `Te_0` | 用车方 | 文本 | client.name（公司）或 client_name（个人） | |
| `Te_1` | 联系人 | 文本 | client_name + client_phone | 格式：姓名 电话 |
| `Te_2` | 出发地点 | 文本 | task.departure | 自驾车时为空 |
| `Te_3` | 目的地 | 文本 | task.destination | 自驾车时为空 |
| `Te_4` | 车牌号 | 文本 | 多车：`1.粤J576L5;2.粤J57K35`；单车：主车牌 | 分号分隔 |
| `Te_5` | 驾驶司机 | 文本 | 多车：`1.张师傅;2.李师傅`；单车：主司机 | 自驾车时为空 |
| `Te_6` | 出车时间 | 文本 | departure_time → `YYYY-MM-DD HH:MM` | |
| `Te_7` | 回程时间 | 文本 | return_time → `YYYY-MM-DD HH:MM` | |
| `Te_8` | 车辆类型 | 文本 | vehicle_type（核定载人数） | 如"45座" |
| `Te_9` | 里程 | 文本 | mileage | 单位：km |
| `Te_10` | 租车费 | 文本 | rental_fee | 单位：元 |
| `Te_11` | 油电费 | 文本 | fuel_fee | 自驾车时为0 |
| `Te_12` | 桥路费 | 文本 | bridge_fee | 自驾车时为0 |
| `Te_13` | 司机人工费 | 文本 | labor_fee | 自驾车时为0 |
| `Te_14` | 预计成本 | 文本 | estimated_cost | |
| `Te_15` | 预估利润 | 文本 | estimated_profit | |
| `Te_16` | 天数 | 文本 | rental_days | |

## 多车任务格式

当任务有多个车辆分配时（task_vehicles），Te_4 和 Te_5 使用以下格式：

- **车牌号**：`1.粤J576L5;2.粤J57K35;3.粤J57M01`
- **司机**：`1.张师傅;2.李师傅;3.王师傅`

每辆车/司机前加序号（1. 2. 3.），用分号分隔。

## 自驾车任务

自驾车任务发起审批时：
- `Te_2`（出发地点）：空
- `Te_3`（目的地）：空
- `Te_5`（司机）：空
- 其他字段正常填写

## 相关代码

- 审批表单构建函数：`backend/app.py` — `build_yzj_approval_body`
- 审批提交函数：`backend/app.py` — `submit_approval`
- 前端审批弹窗：`frontend/src/views/TaskManagement.vue`
