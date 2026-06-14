<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:18px;font-weight:bold">任务管理</span>
          <div style="display:flex;gap:8px">
            <el-button type="success" @click="showApprovalDialog">发起审批</el-button>
            <el-button type="primary" @click="showAddDialog">录入任务</el-button>
          </div>
        </div>
      </template>

      <!-- Desktop table -->
      <el-table v-if="!isMobile" :data="tasks" border stripe style="width:100%" max-height="600" :header-cell-style="{ whiteSpace: 'nowrap' }">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column label="用车方" min-width="120">
          <template #default="{ row }">
            <span v-if="row.client_type === 'company'" style="font-weight:600">{{ row.client_company }}</span>
            <span v-else>{{ row.client_name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="联系人" min-width="120">
          <template #default="{ row }">
            <div v-if="row.client_type === 'company'">
              <div>{{ row.client_name }}</div>
              <div style="color:#909399;font-size:12px">{{ row.client_phone }}</div>
            </div>
            <span v-else>{{ row.client_phone }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="departure" label="出发地点" min-width="100" />
        <el-table-column prop="destination" label="目的地" min-width="100" />
        <el-table-column label="车牌号" min-width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.vehicle_plate">{{ row.vehicle_plate }}</span>
            <span v-else style="color:#909399">未排班</span>
          </template>
        </el-table-column>
        <el-table-column label="驾驶司机" min-width="120">
          <template #default="{ row }">
            <div v-if="row.driver_name">
              <div>{{ row.driver_name }}</div>
              <div style="color:#909399;font-size:12px">{{ row.driver_phone }}</div>
            </div>
            <span v-else style="color:#909399">未排班</span>
          </template>
        </el-table-column>
        <el-table-column prop="departure_time" label="出车时间" min-width="140" />
        <el-table-column prop="return_time" label="回程时间" min-width="140" />
        <el-table-column prop="rental_days" label="天数" width="70" align="center" />
        <el-table-column prop="vehicle_type" label="车辆类型" min-width="100" />
        <el-table-column prop="mileage" label="里程(km)" width="90" align="right" />
        <el-table-column prop="rental_fee" label="租车费(元)" width="100" align="right" />
        <el-table-column prop="fuel_fee" label="油电费" width="110" align="right" />
        <el-table-column prop="bridge_fee" label="桥路费" width="110" align="right" />
        <el-table-column prop="labor_fee" label="司机人工费" width="130" align="right" />
        <el-table-column prop="estimated_cost" label="预计成本" width="120" align="right" />
        <el-table-column prop="estimated_profit" label="预估利润" width="120" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.estimated_profit >= 0 ? '#67c23a' : '#f56c6c' }">{{ row.estimated_profit }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="actual_fuel_fee" label="实际油电费" width="100" align="right" />
        <el-table-column prop="actual_bridge_fee" label="实际桥路费" width="100" align="right" />
        <el-table-column prop="actual_labor_fee" label="实际人工费" width="100" align="right" />
        <el-table-column prop="other_fee" label="其他费用" width="90" align="right" />
        <el-table-column prop="actual_cost" label="实际成本" width="100" align="right" />
        <el-table-column prop="final_profit" label="最终利润" width="100" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.final_profit >= 0 ? '#67c23a' : '#f56c6c' }">{{ row.final_profit }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'pending'" type="warning">待排班</el-tag>
            <el-tag v-else-if="row.status === 'scheduled'" type="primary">已排班</el-tag>
            <el-tag v-else-if="row.status === 'completed'" type="success">已完成</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审批" width="160" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.yzj_approval_status === 'submitted'" type="success" size="small">已发起</el-tag>
            <el-tag v-else-if="row.yzj_approval_status === 'approved'" type="primary" size="small">已通过</el-tag>
            <el-tag v-else-if="row.yzj_approval_status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
            <span v-else style="color:#c0c4cc">-</span>
            <div v-if="row.yzj_serial" style="font-size:11px;color:#909399;margin-top:2px">{{ row.yzj_serial }}</div>
          </template>
        </el-table-column>
        <el-table-column label="客户确认" width="120" align="center">
          <template #default="{ row }">
            <div v-if="row.schedule_confirm_status">
              <el-tag v-if="row.schedule_confirm_status === 'pending'" type="warning" size="small">待确认</el-tag>
              <el-tag v-else-if="row.schedule_confirm_status === 'confirmed'" type="success" size="small">已确认</el-tag>
              <el-tag v-else-if="row.schedule_confirm_status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
            </div>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="480" fixed="right">
          <template #default="{ row }">
            <div style="display:flex;flex-wrap:nowrap;gap:4px;justify-content:center">
              <el-button v-if="row.status === 'pending'" type="primary" size="small" @click="showScheduleDialog(row)">排班分配</el-button>
              <el-button v-if="row.status === 'scheduled'" type="warning" size="small" @click="showScheduleDialog(row)">重新排班</el-button>
              <el-button v-if="row.status === 'scheduled'" type="success" size="small" @click="showCompleteDialog(row)">完成任务</el-button>
              <el-button v-if="row.status === 'scheduled' && !row.schedule_confirm_status" type="primary" size="small" @click="pushConfirm(row)">推送确认</el-button>
              <el-button v-if="row.schedule_confirm_status" type="success" size="small" @click="showConfirmDetail(row)">确认详情</el-button>
              <el-button v-if="row.change_log && row.change_log.length" type="info" size="small" @click="showChangeLog(row)">变更记录</el-button>
              <el-button v-if="row.status !== 'completed'" type="warning" size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-popconfirm title="确认删除?" @confirm="deleteTask(row.id)">
                <template #reference>
                  <el-button type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Mobile card list -->
      <div v-else class="mobile-task-list">
        <div v-for="row in tasks" :key="row.id" class="mobile-task-card">
          <div class="card-header">
            <span class="card-client">
              <template v-if="row.client_type === 'company'">{{ row.client_company }} ({{ row.client_name }} {{ row.client_phone }})</template>
              <template v-else>{{ row.client_name }}<span v-if="row.client_phone" style="font-size:12px;color:#909399;font-weight:normal;margin-left:6px">{{ row.client_phone }}</span></template>
            </span>
            <el-tag v-if="row.status === 'pending'" type="warning" size="small">待排班</el-tag>
            <el-tag v-else-if="row.status === 'scheduled'" type="primary" size="small">已排班</el-tag>
            <el-tag v-else-if="row.status === 'completed'" type="success" size="small">已完成</el-tag>
            <el-tag v-if="row.yzj_approval_status === 'submitted'" type="success" size="small" style="margin-left:4px">已发起</el-tag>
            <el-tag v-else-if="row.yzj_approval_status === 'approved'" type="primary" size="small" style="margin-left:4px">已通过</el-tag>
            <el-tag v-else-if="row.yzj_approval_status === 'rejected'" type="danger" size="small" style="margin-left:4px">已拒绝</el-tag>
          </div>
          <div class="card-body">
            <div class="card-row">
              <span class="card-label">出发</span>
              <span>{{ row.departure }} → {{ row.destination }}</span>
            </div>
            <div class="card-row">
              <span class="card-label">出车</span>
              <span>{{ row.departure_time }}</span>
            </div>
            <div class="card-row">
              <span class="card-label">回程</span>
              <span>{{ row.return_time || '未设置' }}</span>
            </div>
            <div class="card-row">
              <span class="card-label">天数</span>
              <span>{{ row.rental_days }} 天</span>
            </div>
            <div class="card-row">
              <span class="card-label">司机</span>
              <span v-if="row.driver_name">{{ row.driver_name }} ({{ row.driver_phone }})</span>
              <span v-else style="color:#909399">未排班</span>
            </div>
            <div class="card-row">
              <span class="card-label">车牌</span>
              <span v-if="row.vehicle_plate">{{ row.vehicle_plate }}</span>
              <span v-else style="color:#909399">未排班</span>
            </div>
            <div class="card-row">
              <span class="card-label">租车费</span>
              <span>¥{{ row.rental_fee }}</span>
            </div>
            <div class="card-row" v-if="row.yzj_serial">
              <span class="card-label">审批</span>
              <span style="font-size:12px;color:#909399">{{ row.yzj_serial }}</span>
            </div>
            <div class="card-row" v-if="row.schedule_confirm_status">
              <span class="card-label">客户确认</span>
              <el-tag v-if="row.schedule_confirm_status === 'pending'" type="warning" size="small">待确认</el-tag>
              <el-tag v-else-if="row.schedule_confirm_status === 'confirmed'" type="success" size="small">已确认</el-tag>
              <el-tag v-else-if="row.schedule_confirm_status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
            </div>
          </div>
          <div class="card-actions">
            <el-button v-if="row.status === 'pending'" type="primary" size="small" @click="showScheduleDialog(row)">排班</el-button>
            <el-button v-if="row.status === 'scheduled'" type="warning" size="small" @click="showScheduleDialog(row)">重新排班</el-button>
            <el-button v-if="row.status === 'scheduled'" type="success" size="small" @click="showCompleteDialog(row)">完成</el-button>
            <el-button v-if="row.status === 'scheduled' && !row.schedule_confirm_status" type="primary" size="small" @click="pushConfirm(row)">推送确认</el-button>
            <el-dropdown trigger="click">
              <el-button size="small" type="info">更多</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-if="row.schedule_confirm_status" @click="showConfirmDetail(row)">确认详情</el-dropdown-item>
                  <el-dropdown-item v-if="row.status !== 'completed'" @click="showEditDialog(row)">编辑</el-dropdown-item>
                  <el-dropdown-item v-if="row.change_log && row.change_log.length" @click="showChangeLog(row)">变更记录</el-dropdown-item>
                  <el-dropdown-item divided>
                    <el-popconfirm title="确认删除?" @confirm="deleteTask(row.id)">
                      <template #reference>
                        <span style="color:#f56c6c;width:100%;display:block">删除</span>
                      </template>
                    </el-popconfirm>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <el-empty v-if="!tasks.length" description="暂无任务" />
      </div>
    </el-card>

    <!-- Add/Edit Task Dialog -->
    <el-dialog v-model="taskDialogVisible" :title="isEdit ? '编辑任务' : '录入任务'" :width="isMobile ? '100%' : '700px'" :fullscreen="isMobile">
      <el-form :model="taskForm" :label-width="isMobile ? '90px' : '110px'">
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="24">
            <el-form-item label="用车类型">
              <el-radio-group v-model="taskForm.client_type" @change="onClientTypeChange">
                <el-radio value="personal">个人</el-radio>
                <el-radio value="company">单位</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row v-if="taskForm.client_type === 'personal'" :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="姓名">
              <el-input v-model="taskForm.client_name" placeholder="请输入姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="手机号码">
              <el-input v-model="taskForm.client_phone" placeholder="请输入手机号码" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row v-else :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="用车单位">
              <el-select v-model="taskForm.client_id" placeholder="请选择单位" style="width:100%" @change="onClientChange">
                <el-option v-for="c in clients" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="联系人">
              <el-select v-model="taskForm.contact_id" placeholder="请选择联系人" style="width:100%" @change="onContactChange">
                <el-option v-for="c in currentContacts" :key="c.id" :label="c.name + ' (' + c.phone + ')'" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="车辆类型">
              <el-select v-model="taskForm.vehicle_type" placeholder="请选择" style="width:100%">
                <el-option label="大巴(45座)" value="大巴(45座)" />
                <el-option label="中巴(25座)" value="中巴(25座)" />
                <el-option label="小巴(15座)" value="小巴(15座)" />
                <el-option label="商务车(7座)" value="商务车(7座)" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="出发地点">
              <el-input v-model="taskForm.departure" />
            </el-form-item>
          </el-col>
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="目的地">
              <el-input v-model="taskForm.destination" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="出车时间">
              <el-date-picker v-model="taskForm.departure_time" type="datetime" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width:100%" @change="onTimeChange" />
            </el-form-item>
          </el-col>
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="回程时间">
              <el-date-picker v-model="taskForm.return_time" type="datetime" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width:100%" @change="onTimeChange" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="租用天数">
              <el-input :model-value="computedRentalDays" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="任务里程(km)">
              <el-input-number v-model="taskForm.mileage" :min="0" :precision="1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="租车费(元)">
              <el-input-number v-model="taskForm.rental_fee" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="油电费">
              <el-input-number v-model="taskForm.fuel_fee" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="桥路费">
              <el-input-number v-model="taskForm.bridge_fee" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="差费标准">
              <el-select v-model="taskForm.labor_rate_id" placeholder="选择差费标准" style="width:100%" clearable @change="onLaborRateChange">
                <el-option v-for="r in laborRates" :key="r.id" :label="r.location + ' - ' + r.labor_rate + '元/' + r.days + '天'" :value="r.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="司机人工费">
              <el-input :model-value="taskForm.labor_fee" disabled style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="预计成本">
              <el-input :model-value="estimatedCost" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="预估利润">
              <el-input :model-value="estimatedProfit" disabled />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTask">确定</el-button>
      </template>
    </el-dialog>

    <!-- Schedule Dialog -->
    <el-dialog v-model="scheduleDialogVisible" title="排班分配" :width="isMobile ? '100%' : '600px'" :fullscreen="isMobile">
      <el-form :label-width="isMobile ? '90px' : '100px'">
        <el-form-item label="出车时间">
          <el-input :model-value="scheduleInfo.task_start + ' ~ ' + scheduleInfo.task_end" disabled />
        </el-form-item>
        <el-form-item label="目的地">
          <el-tag>{{ scheduleInfo.destination }}</el-tag>
        </el-form-item>
        <el-form-item label="司机人工费">
          <el-tag>{{ scheduleInfo.labor_fee }} 元</el-tag>
        </el-form-item>
        <el-form-item label="选择车辆">
          <el-select v-model="scheduleForm.vehicle_id" placeholder="请选择车辆" style="width:100%">
            <el-option v-for="v in scheduleInfo.vehicles" :key="v.id" :label="v.plate_number + ' (' + v.vehicle_type + ')'" :value="v.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择司机">
          <el-select v-model="scheduleForm.driver_id" placeholder="请选择司机" style="width:100%">
            <el-option v-for="d in scheduleInfo.drivers" :key="d.id" :label="d.name + ' (' + d.phone + ') - 已获人工费: ¥' + d.total_labor_fee" :value="d.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitSchedule">确认任务</el-button>
      </template>
    </el-dialog>

    <!-- Complete Task Dialog -->
    <el-dialog v-model="completeDialogVisible" title="完成任务 - 录入实际费用" :width="isMobile ? '100%' : '500px'" :fullscreen="isMobile">
      <el-form :model="completeForm" :label-width="isMobile ? '100px' : '110px'">
        <el-form-item label="实际油电费">
          <el-input-number v-model="completeForm.actual_fuel_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="实际桥路费">
          <el-input-number v-model="completeForm.actual_bridge_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="实际司机人工费">
          <el-input-number v-model="completeForm.actual_labor_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="其他费用">
          <el-input-number v-model="completeForm.other_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-divider />
        <el-form-item label="实际成本">
          <el-input :model-value="actualCostDisplay" disabled />
        </el-form-item>
        <el-form-item label="最终利润">
          <el-input :model-value="finalProfitDisplay" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitComplete">确认完成</el-button>
      </template>
    </el-dialog>

    <!-- Change Log Dialog -->
    <el-dialog v-model="changeLogVisible" title="变更记录" :width="isMobile ? '100%' : '750px'" :fullscreen="isMobile">
      <div style="padding:0 20px 0 10px">
      <el-timeline>
        <el-timeline-item v-for="(log, idx) in currentChangeLog" :key="idx" :timestamp="log.changed_at" placement="top">
          <el-card>
            <template v-if="log.snapshot">
              <el-descriptions :column="isMobile ? 1 : 2" size="small" border>
                <el-descriptions-item label="用车联系人">
                  <span :style="isChanged(log, 'client_name') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.client_name }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="联系电话">
                  <span :style="isChanged(log, 'client_phone') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.client_phone || '未设置' }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="出车时间">
                  <span :style="isChanged(log, 'departure_time') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.departure_time }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="回程时间">
                  <span :style="isChanged(log, 'return_time') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.return_time || '未设置' }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="出发地点">
                  <span :style="isChanged(log, 'departure') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.departure }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="目的地">
                  <span :style="isChanged(log, 'destination') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.destination }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="租用天数">
                  <span :style="isChanged(log, 'rental_days') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.rental_days }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="车辆类型">
                  <span :style="isChanged(log, 'vehicle_type') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.vehicle_type }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="里程(km)">
                  <span :style="isChanged(log, 'mileage') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.mileage }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="租车费(元)">
                  <span :style="isChanged(log, 'rental_fee') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.rental_fee }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="油电费">
                  <span :style="isChanged(log, 'fuel_fee') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.fuel_fee }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="桥路费">
                  <span :style="isChanged(log, 'bridge_fee') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.bridge_fee }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="司机人工费">
                  <span :style="isChanged(log, 'labor_fee') ? 'color:#f56c6c;font-weight:bold' : ''">{{ log.snapshot.labor_fee }}</span>
                </el-descriptions-item>
              </el-descriptions>
            </template>
            <template v-else>
              <el-tag type="warning" size="small" style="margin-right:8px">{{ log.field }}</el-tag>
              <span style="color:#909399">{{ log.old_value }}</span>
              <span style="margin:0 6px">→</span>
              <span style="color:#409eff">{{ log.new_value }}</span>
            </template>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      </div>
    </el-dialog>

    <!-- Approval Dialog -->
    <el-dialog v-model="approvalDialogVisible" title="发起云之家审批" :width="isMobile ? '100%' : '800px'" :fullscreen="isMobile">
      <div style="margin-bottom:12px;color:#909399;font-size:13px">
        勾选需要发起审批的已排班任务，所有选中任务将合并为一条审批提交。
      </div>
      <el-table :data="schedulableTasks" border stripe style="width:100%"
        @selection-change="onApprovalSelectionChange" max-height="400">
        <el-table-column type="selection" width="50" align="center"
          :selectable="canSubmitApproval" />
        <el-table-column label="用车方" min-width="120">
          <template #default="{ row }">
            <span v-if="row.client_type === 'company'" style="font-weight:600">{{ row.client_company }}</span>
            <span v-else>{{ row.client_name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="联系人" min-width="110">
          <template #default="{ row }">
            <div>{{ row.client_name }}</div>
            <div style="color:#909399;font-size:12px">{{ row.client_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="departure" label="出发" min-width="80" />
        <el-table-column prop="destination" label="目的地" min-width="90" />
        <el-table-column prop="vehicle_plate" label="车牌" min-width="90" />
        <el-table-column label="司机" min-width="80">
          <template #default="{ row }">{{ row.driver_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="所属公司" min-width="80">
          <template #default="{ row }">
            <el-tag v-if="row.vehicle_company" size="small" :type="row.vehicle_company === '国顺司' ? 'primary' : row.vehicle_company === '国开司' ? 'warning' : 'info'">
              {{ row.vehicle_company }}
            </el-tag>
            <span v-else style="color:#909399">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="departure_time" label="出车时间" min-width="130" />
        <el-table-column prop="return_time" label="回程时间" min-width="130" />
        <el-table-column prop="rental_days" label="天数" width="60" align="center" />
        <el-table-column prop="estimated_profit" label="预估利润" width="90" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.estimated_profit >= 0 ? '#67c23a' : '#f56c6c' }">{{ row.estimated_profit }}</span>
          </template>
        </el-table-column>
        <el-table-column label="可发起" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.yzj_approval_status === 'submitted'" type="success" size="small">已发起</el-tag>
            <el-tag v-else-if="row.yzj_approval_status === 'approved'" type="primary" size="small">已通过</el-tag>
            <el-tag v-else-if="row.yzj_approval_status === 'rejected'" type="danger" size="small">可重发</el-tag>
            <el-tag v-else-if="isPastDeparture(row)" type="info" size="small">已过期</el-tag>
            <el-tag v-else type="primary" size="small">可发起</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!schedulableTasks.length" style="text-align:center;padding:40px 0;color:#909399">
        暂无已排班的任务，请先完成排班
      </div>
      <template #footer>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="color:#909399;font-size:13px">
            已选 {{ approvalSelectedTasks.length }} 条
            <template v-if="approvalSelectedTasks.length">
              （{{ approvalTemplateSummary }}）
            </template>
          </span>
          <div>
            <el-button @click="approvalDialogVisible = false">取消</el-button>
            <el-button type="success" :disabled="!approvalSelectedTasks.length" :loading="approvalLoading" @click="submitApproval">
              发起审批 ({{ approvalSelectedTasks.length }}条)
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- Confirm Detail Dialog -->
    <el-dialog v-model="confirmDialogVisible" title="任务确认详情" :width="isMobile ? '100%' : '600px'" :fullscreen="isMobile">
      <div v-if="confirmDetail" style="padding:0 20px">
        <el-descriptions :column="isMobile ? 1 : 2" border>
          <el-descriptions-item label="客户名称">{{ confirmDetail.customer_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ confirmDetail.customer_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="确认状态">
            <el-tag v-if="confirmDetail.confirm_status === 'pending'" type="warning">待确认</el-tag>
            <el-tag v-else-if="confirmDetail.confirm_status === 'confirmed'" type="success">已确认</el-tag>
            <el-tag v-else-if="confirmDetail.confirm_status === 'rejected'" type="danger">已拒绝</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="确认时间">{{ confirmDetail.confirm_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="确认IP" :span="2">{{ confirmDetail.confirm_ip || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ confirmDetail.confirm_remark || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="confirmDetail.confirm_token" label="确认链接" :span="2">
            <el-link type="primary" :href="`/confirm/${confirmDetail.confirm_token}`" target="_blank">
              {{ `确认链接` }}
            </el-link>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="confirmDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../utils/api'

const isMobile = ref(false)
const checkMobile = () => { isMobile.value = window.innerWidth <= 768 }
onMounted(() => { checkMobile(); window.addEventListener('resize', checkMobile) })
onUnmounted(() => window.removeEventListener('resize', checkMobile))

const tasks = ref([])
const laborRates = ref([])
const clients = ref([])
const taskDialogVisible = ref(false)
const scheduleDialogVisible = ref(false)
const completeDialogVisible = ref(false)
const changeLogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const currentChangeLog = ref([])

// 云之家审批相关
const approvalDialogVisible = ref(false)
const approvalSelectedTasks = ref([])
const approvalLoading = ref(false)
const schedulableTasks = computed(() => tasks.value.filter(t => t.status === 'scheduled'))

const approvalTemplateSummary = computed(() => {
  const groups = {}
  approvalSelectedTasks.value.forEach(t => {
    const c = t.vehicle_company || '外单位'
    groups[c] = (groups[c] || 0) + 1
  })
  return Object.entries(groups).map(([k, v]) => `${k} ${v}条`).join('、')
})

const isPastDeparture = (row) => {
  if (!row.departure_time) return false
  return new Date(row.departure_time) <= new Date()
}

const canSubmitApproval = (row) => {
  if (row.status !== 'scheduled' || isPastDeparture(row)) return false
  const status = row.yzj_approval_status
  return !status || status === 'rejected'
}

const taskForm = ref({
  client_type: 'personal', client_name: '', client_phone: '', client_id: null, contact_id: null,
  departure: '', destination: '', departure_time: '', return_time: '',
  vehicle_type: '', mileage: 0, rental_fee: 0,
  fuel_fee: 0, bridge_fee: 0, labor_fee: 0
})

const currentContacts = computed(() => {
  if (!taskForm.value.client_id) return []
  const client = clients.value.find(c => c.id === taskForm.value.client_id)
  return client ? (client.contacts || []) : []
})

const computedRentalDays = computed(() => {
  const dt = taskForm.value.departure_time
  const rt = taskForm.value.return_time
  if (!dt || !rt) return '请填写出车和回程时间'
  const d = new Date(dt), r = new Date(rt)
  if (r <= d) return '0.5'
  const hours = (r - d) / 3600000
  if (hours <= 12) return '0.5'
  return (Math.ceil(hours / 12) * 0.5).toString()
})

const scheduleInfo = ref({ vehicles: [], drivers: [], labor_rate: 0, task_start: '', task_end: '' })
const scheduleForm = ref({ vehicle_id: null, driver_id: null })
const scheduleTaskId = ref(null)

const completeForm = ref({ actual_fuel_fee: 0, actual_bridge_fee: 0, actual_labor_fee: 0, other_fee: 0 })
const completeTaskId = ref(null)

const estimatedCost = computed(() => (taskForm.value.fuel_fee + taskForm.value.bridge_fee + taskForm.value.labor_fee).toFixed(2))
const estimatedProfit = computed(() => (taskForm.value.rental_fee - taskForm.value.fuel_fee - taskForm.value.bridge_fee - taskForm.value.labor_fee).toFixed(2))
const actualCostDisplay = computed(() => (completeForm.value.actual_fuel_fee + completeForm.value.actual_bridge_fee + completeForm.value.actual_labor_fee + completeForm.value.other_fee).toFixed(2))
const finalProfitDisplay = computed(() => {
  const task = tasks.value.find(t => t.id === completeTaskId.value)
  const rental = task ? task.rental_fee : 0
  return (rental - completeForm.value.actual_fuel_fee - completeForm.value.actual_bridge_fee - completeForm.value.actual_labor_fee - completeForm.value.other_fee).toFixed(2)
})

const fieldMap = { client_name: '用车联系人', client_phone: '联系电话', departure: '出发地点', destination: '目的地', departure_time: '出车时间', return_time: '回程时间', vehicle_type: '车辆类型', mileage: '任务里程', rental_fee: '租车费', fuel_fee: '油电费', bridge_fee: '桥路费', labor_fee: '司机人工费' }
const isChanged = (log, key) => (log.changes || []).some(c => c.field === fieldMap[key])

const loadTasks = async () => {
  try {
    const res = await api.get('/tasks')
    tasks.value = res.data
  } catch (e) {}
}

const showAddDialog = () => {
  isEdit.value = false
  editId.value = null
  taskForm.value = { client_type: 'personal', client_name: '', client_phone: '', client_id: null, contact_id: null, departure: '', destination: '', departure_time: '', return_time: '', vehicle_type: '', mileage: 0, rental_fee: 0, fuel_fee: 0, bridge_fee: 0, labor_rate_id: null, labor_fee: 0 }
  taskDialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  editId.value = row.id
  const matchedRate = laborRates.value.find(r => r.location === row.destination)
  taskForm.value = {
    client_type: row.client_type || 'personal', client_name: row.client_name, client_phone: row.client_phone || '',
    client_id: row.client_id, contact_id: row.contact_id,
    departure: row.departure, destination: row.destination,
    departure_time: row.departure_time, return_time: row.return_time || '', vehicle_type: row.vehicle_type,
    mileage: row.mileage, rental_fee: row.rental_fee, fuel_fee: row.fuel_fee,
    bridge_fee: row.bridge_fee, labor_rate_id: matchedRate ? matchedRate.id : null, labor_fee: row.labor_fee
  }
  taskDialogVisible.value = true
}

const submitTask = async () => {
  if (taskForm.value.client_type === 'personal' && (!taskForm.value.client_name || !taskForm.value.client_phone)) {
    ElMessage.warning('请填写姓名和手机号码')
    return
  }
  if (taskForm.value.client_type === 'company' && (!taskForm.value.client_id || !taskForm.value.contact_id)) {
    ElMessage.warning('请选择用车单位和联系人')
    return
  }
  if (!taskForm.value.departure || !taskForm.value.destination || !taskForm.value.departure_time || !taskForm.value.return_time) {
    ElMessage.warning('请填写必填信息')
    return
  }
  try {
    if (isEdit.value) {
      await api.put(`/tasks/${editId.value}`, taskForm.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/tasks', taskForm.value)
      ElMessage.success('录入成功')
    }
    taskDialogVisible.value = false
    loadTasks()
  } catch (e) {}
}

const showScheduleDialog = async (row) => {
  scheduleTaskId.value = row.id
  scheduleForm.value = { vehicle_id: null, driver_id: null }
  try {
    const res = await api.get(`/tasks/${row.id}/available-resources`)
    scheduleInfo.value = { ...res.data, destination: row.destination, labor_fee: row.labor_fee }
    scheduleDialogVisible.value = true
  } catch (e) {}
}

const submitSchedule = async () => {
  if (!scheduleForm.value.vehicle_id || !scheduleForm.value.driver_id) {
    ElMessage.warning('请选择车辆和司机')
    return
  }
  try {
    await api.post(`/tasks/${scheduleTaskId.value}/schedule`, scheduleForm.value)
    ElMessage.success('排班成功')
    scheduleDialogVisible.value = false
    loadTasks()
  } catch (e) {}
}

const showCompleteDialog = (row) => {
  completeTaskId.value = row.id
  completeForm.value = { actual_fuel_fee: 0, actual_bridge_fee: 0, actual_labor_fee: 0, other_fee: 0 }
  completeDialogVisible.value = true
}

const submitComplete = async () => {
  try {
    await api.post(`/tasks/${completeTaskId.value}/complete`, completeForm.value)
    ElMessage.success('任务已完成')
    completeDialogVisible.value = false
    loadTasks()
  } catch (e) {}
}

const deleteTask = async (id) => {
  try {
    await api.delete(`/tasks/${id}`)
    ElMessage.success('删除成功')
    loadTasks()
  } catch (e) {}
}

const showChangeLog = (row) => {
  currentChangeLog.value = row.change_log || []
  changeLogVisible.value = true
}

const loadLaborRates = async () => {
  try { const res = await api.get('/labor-rates'); laborRates.value = res.data } catch (e) {}
}

const loadClients = async () => {
  try { const res = await api.get('/clients'); clients.value = res.data } catch (e) {}
}

const onClientTypeChange = () => {
  taskForm.value.client_name = ''
  taskForm.value.client_phone = ''
  taskForm.value.client_id = null
  taskForm.value.contact_id = null
}

const onClientChange = () => {
  taskForm.value.contact_id = null
}

const onContactChange = (contactId) => {
  const contact = currentContacts.value.find(c => c.id === contactId)
  if (contact) {
    taskForm.value.client_name = contact.name
    taskForm.value.client_phone = contact.phone
  }
}

const getRentalDays = () => {
  const dt = taskForm.value.departure_time
  const rt = taskForm.value.return_time
  if (!dt || !rt) return 1
  const d = new Date(dt), r = new Date(rt)
  if (r <= d) return 0.5
  const hours = (r - d) / 3600000
  if (hours <= 12) return 0.5
  return Math.ceil(hours / 12) * 0.5
}

const recalcLaborFee = () => {
  if (taskForm.value.labor_rate_id) {
    const rate = laborRates.value.find(r => r.id === taskForm.value.labor_rate_id)
    if (rate) taskForm.value.labor_fee = rate.labor_rate * Math.ceil(getRentalDays() / rate.days)
  }
}

const onLaborRateChange = (rateId) => {
  recalcLaborFee()
}

const onTimeChange = () => {
  recalcLaborFee()
}

// 云之家审批
const showApprovalDialog = () => {
  approvalSelectedTasks.value = []
  approvalDialogVisible.value = true
}

const onApprovalSelectionChange = (selection) => {
  approvalSelectedTasks.value = selection
}

const submitApproval = async () => {
  if (!approvalSelectedTasks.value.length) {
    ElMessage.warning('请至少选择一条任务')
    return
  }

  // 检查是否混合了不同所属公司的车辆
  const companies = new Set(approvalSelectedTasks.value.map(t => t.vehicle_company || '外单位'))
  if (companies.size > 1) {
    ElMessage.warning('不同所属公司的车辆不能混合发起审批，请按公司分别选择')
    return
  }

  const taskIds = approvalSelectedTasks.value.map(t => t.id)
  try {
    approvalLoading.value = true
    const res = await api.post('/tasks/submit-approval', { task_ids: taskIds })
    ElMessage.success(res.msg || '审批已发起')
    approvalDialogVisible.value = false
    loadTasks()
  } catch (e) {
    // api interceptor handles error display
  } finally {
    approvalLoading.value = false
  }
}

// 排班确认相关
const confirmDialogVisible = ref(false)
const confirmDetail = ref(null)

const pushConfirm = async (row) => {
  try {
    // 先获取客户的联系人信息（含企业微信UserID和发送人）
    let wxUserid = ''
    let wxSender = ''
    try {
      const clientRes = await api.get(`/clients/${row.client_id}`)
      if (clientRes.code === 200 && clientRes.data?.contacts) {
        const contact = clientRes.data.contacts.find(c => c.wx_userid)
        if (contact) {
          wxUserid = contact.wx_userid
          wxSender = contact.wx_sender || ''
        }
      }
    } catch (e) {
      // 获取失败不影响推送
    }

    const isExternal = wxUserid.startsWith('wm')
    let confirmMsg = ''
    if (!wxUserid) {
      confirmMsg = `确定要向客户"${row.client_name}"推送任务确认消息吗？\n⚠️ 未配置企业微信用户ID，需手动发送确认链接`
    } else if (isExternal && !wxSender) {
      confirmMsg = `⚠️ 外部联系人未配置发送人，无法自动推送。\n请先在客户管理→联系人中配置"发送人"字段`
    } else {
      confirmMsg = `确定要向客户"${row.client_name}"推送任务确认消息吗？\n将通过企业微信发送`
    }

    await ElMessageBox.confirm(confirmMsg, '推送确认', {
      confirmButtonText: '推送',
      cancelButtonText: '取消',
      type: 'info'
    })

    const res = await api.post(`/task/${row.id}/push-confirm`, {
      wx_userid: wxUserid,
      sender: wxSender
    })

    if (res.code === 200) {
      // 如果有确认链接（外部联系人），自动复制并提示
      if (res.data?.confirm_url) {
        const url = res.data.confirm_url
        // 尝试自动复制
        try {
          await navigator.clipboard.writeText(url)
          ElMessage.success('链接已自动复制，请粘贴发送给客户')
        } catch {
          ElMessage.success('确认链接已生成')
        }
        ElMessageBox.alert(
          `<div style="text-align:center">
            <p style="font-size:15px;margin-bottom:12px">📋 请将以下链接发送给客户</p>
            <div style="background:#f5f7fa;padding:12px;border-radius:8px;margin:8px 0">
              <code style="word-break:break-all;font-size:13px;color:#409eff">${url}</code>
            </div>
            <p style="color:#909399;font-size:12px">客户点击链接即可确认任务</p>
          </div>`,
          '发送确认链接给客户',
          { dangerouslyUseHTMLString: true, confirmButtonText: '复制链接' }
        ).then(() => {
          navigator.clipboard?.writeText(url)
          ElMessage.success('链接已复制到剪贴板')
        }).catch(() => {})
      } else {
        ElMessage.success(res.msg || '推送成功')
      }
      loadTasks()
    }
  } catch (e) {
    if (e !== 'cancel') {
      // api interceptor handles error display
    }
  }
}

const showConfirmDetail = async (row) => {
  try {
    const res = await api.get(`/task/${row.id}/confirmation`)
    if (res.code === 200 && res.data) {
      confirmDetail.value = res.data
      confirmDialogVisible.value = true
    } else {
      ElMessage.info('暂无确认记录')
    }
  } catch (e) {
    // api interceptor handles error display
  }
}

onMounted(() => { loadTasks(); loadLaborRates(); loadClients() })
</script>

<style scoped>
.mobile-task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.mobile-task-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}
.card-client {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.card-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.card-row {
  display: flex;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}
.card-label {
  width: 48px;
  flex-shrink: 0;
  color: #909399;
}
.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
  justify-content: flex-end;
}
:deep(.el-table .el-table__header-wrapper th) {
  white-space: nowrap !important;
  overflow: visible !important;
}
</style>
