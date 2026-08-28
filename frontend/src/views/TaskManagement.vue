<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:18px;font-weight:bold">任务管理</span>
            <el-select v-model="statusFilter" style="width:120px" size="default">
              <el-option label="默认" value="" />
              <el-option label="全部" value="all" />
              <el-option label="待排班" value="pending" />
              <el-option label="已排班" value="scheduled" />
              <el-option label="已完成" value="completed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
            <span style="color:#909399;font-size:13px">共 {{ filteredTasks.length }} 条</span>
          </div>
          <div style="display:flex;gap:8px;align-items:center">
            <el-button type="success" @click="showApprovalDialog">发起审批</el-button>
            <el-button type="primary" @click="showAddDialog">录入任务</el-button>
            <el-button v-if="user.role === 'admin'" @click="showSettings"><el-icon><Setting /></el-icon><span style="margin-left:4px">费率</span></el-button>
          </div>
        </div>
      </template>

      <!-- Desktop table -->
      <el-table v-if="!isMobile" :data="filteredTasks" border stripe style="width:100%" max-height="600" :header-cell-style="{ whiteSpace: 'nowrap' }">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'pending'" type="warning">待排班</el-tag>
            <el-tag v-else-if="row.status === 'scheduled'" type="primary">已排班</el-tag>
            <el-tag v-else-if="row.status === 'completed'" type="success">已完成</el-tag>
            <el-tag v-else-if="row.status === 'cancelled'" type="danger">已取消</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="用车方" min-width="120">
          <template #default="{ row }">
            <span v-if="row.client_type === 'company'" style="font-weight:600">{{ row.client_company }}</span>
            <span v-else>{{ row.client_name }}</span>
            <el-tag v-if="row.self_drive" type="info" size="small" style="margin-left:4px">自驾车</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="联系人" min-width="120">
          <template #default="{ row }">
            <div v-if="row.client_type === 'company'">
              <div>{{ row.client_name }}</div>
              <div style="color:#909399;font-size:12px">{{ row.client_phone }}</div>
            </div>
            <span v-else>{{ row.client_name }} {{ row.client_phone }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="departure" label="出发地点" min-width="100" />
        <el-table-column prop="destination" label="目的地" min-width="100" />
        <el-table-column label="车牌号" min-width="140" align="center">
          <template #default="{ row }">
            <div v-if="row.task_vehicles && row.task_vehicles.length > 1">
              <div v-for="(tv, idx) in row.task_vehicles" :key="idx" style="font-size:12px;line-height:1.4">
                {{ idx + 1 }}. {{ tv.vehicle_plate || '待分配' }}
              </div>
            </div>
            <span v-else-if="row.vehicle_plate">{{ row.vehicle_plate }}</span>
            <span v-else style="color:#909399">未排班</span>
            <el-tag v-if="row.vehicle_count > 1" size="small" type="info" style="margin-top:2px">{{ row.vehicle_count }}台</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="驾驶司机" min-width="140">
          <template #default="{ row }">
            <div v-if="row.task_vehicles && row.task_vehicles.length > 1">
              <div v-for="(tv, idx) in row.task_vehicles" :key="idx" style="font-size:12px;line-height:1.4">
                {{ idx + 1 }}. {{ tv.driver_name || '待分配' }}
              </div>
            </div>
            <div v-else-if="row.driver_name">
              <div>{{ row.driver_name }}</div>
              <div style="color:#909399;font-size:12px">{{ row.driver_phone }}</div>
            </div>
            <span v-else style="color:#909399">未排班</span>
          </template>
        </el-table-column>
        <el-table-column prop="departure_time" label="出车时间" min-width="140" />
        <el-table-column prop="return_time" label="回程时间" min-width="140" />
        <el-table-column prop="rental_days" label="天数" width="70" align="center" />
        <el-table-column prop="vehicle_type" label="核定载人数" min-width="100" />
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
        <el-table-column label="审批" width="160" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.yzj_approval_status === 'submitted'" type="success" size="small">已发起</el-tag>
            <el-tag v-else-if="row.yzj_approval_status === 'approved'" type="primary" size="small">已通过</el-tag>
            <el-tag v-else-if="row.yzj_approval_status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
            <span v-else style="color:#c0c4cc">-</span>
            <div v-if="row.yzj_serial" style="font-size:11px;color:#909399;margin-top:2px">{{ row.yzj_serial }}</div>
          </template>
        </el-table-column>
        <el-table-column label="起始里程" width="90" align="right">
          <template #default="{ row }">
            <span v-if="row.start_mileage">{{ row.start_mileage.toLocaleString() }}</span>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="结束里程" width="90" align="right">
          <template #default="{ row }">
            <span v-if="row.end_mileage">{{ row.end_mileage.toLocaleString() }}</span>
            <span v-else style="color:#c0c4cc">-</span>
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
        <el-table-column label="发票" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.invoice_no" type="success" size="small">已开</el-tag>
            <span v-else-if="row.status === 'completed'" style="color:#e6a23c;cursor:pointer;font-size:12px" @click="showInvoiceDialog(row)">未开</span>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="收款" width="120" align="center">
          <template #default="{ row }">
            <template v-if="row.status === 'completed'">
              <el-tag v-if="row.is_paid" type="success" size="small">已收款</el-tag>
              <el-tag v-else type="danger" size="small">未收款</el-tag>
              <div v-if="row.is_paid && row.paid_date" style="font-size:11px;color:#909399;margin-top:2px">{{ row.paid_date }} {{ row.paid_method || '' }}</div>
            </template>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <div style="display:flex;flex-wrap:nowrap;gap:4px;justify-content:center;align-items:center">
              <el-button v-if="row.status === 'pending'" type="primary" size="small" @click="showScheduleDialog(row)">排班</el-button>
              <el-button v-if="row.status === 'scheduled'" type="warning" size="small" @click="showScheduleDialog(row)">重新排班</el-button>
              <el-button v-if="row.status === 'scheduled'" type="success" size="small" :disabled="!isPastReturn(row)" @click="showCompleteDialog(row)">完成</el-button>
              <el-button v-if="row.status === 'pending' || row.status === 'scheduled'" type="danger" size="small" plain @click="showCancelDialog(row)">取消</el-button>
              <el-button v-if="(row.status === 'completed' || row.status === 'cancelled') && row.change_log && row.change_log.length" type="info" size="small" @click="showChangeLog(row)">变更记录</el-button>
              <el-dropdown trigger="click">
                <el-button size="small" type="info" plain>更多 <el-icon style="margin-left:2px"><ArrowDown /></el-icon></el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item v-if="row.status === 'scheduled' && !row.schedule_confirm_status" @click="pushConfirm(row)">推送确认</el-dropdown-item>
                    <el-dropdown-item v-if="row.schedule_confirm_status" @click="showConfirmDetail(row)">确认详情</el-dropdown-item>
                    <el-dropdown-item v-if="row.status === 'completed'" @click="showInvoiceDialog(row)">录入发票</el-dropdown-item>
                    <el-dropdown-item v-if="row.status !== 'completed' && row.status !== 'cancelled' && row.change_log && row.change_log.length" @click="showChangeLog(row)">变更记录</el-dropdown-item>
                    <el-dropdown-item v-if="row.status !== 'completed' && row.status !== 'cancelled'" @click="showEditDialog(row)">编辑</el-dropdown-item>
                    <el-dropdown-item divided>
                      <span style="color:#f56c6c;width:100%;display:block" @click="confirmDelete(row.id)">删除</span>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Mobile card list -->
      <div v-else class="mobile-task-list">
        <div v-for="row in filteredTasks" :key="row.id" class="mobile-task-card">
          <div class="card-header">
            <span class="card-client">
              <template v-if="row.client_type === 'company'">{{ row.client_company }} ({{ row.client_name }} {{ row.client_phone }})</template>
              <template v-else>{{ row.client_name }}<span v-if="row.client_phone" style="font-size:12px;color:#909399;font-weight:normal;margin-left:6px">{{ row.client_phone }}</span></template>
            </span>
            <el-tag v-if="row.status === 'pending'" type="warning" size="small">待排班</el-tag>
            <el-tag v-else-if="row.status === 'scheduled'" type="primary" size="small">已排班</el-tag>
            <el-tag v-else-if="row.status === 'completed'" type="success" size="small">已完成</el-tag>
            <el-tag v-else-if="row.status === 'cancelled'" type="danger" size="small">已取消</el-tag>
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
            <el-button v-if="row.status === 'scheduled'" type="success" size="small" :disabled="!isPastReturn(row)" @click="showCompleteDialog(row)">完成</el-button>
            <el-button v-if="row.status === 'pending' || row.status === 'scheduled'" type="danger" size="small" @click="showCancelDialog(row)">取消</el-button>
            <el-button v-if="row.status === 'scheduled' && !row.schedule_confirm_status" type="primary" size="small" @click="pushConfirm(row)">推送确认</el-button>
            <el-dropdown trigger="click">
              <el-button size="small" type="info">更多</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-if="row.schedule_confirm_status" @click="showConfirmDetail(row)">确认详情</el-dropdown-item>
                  <el-dropdown-item v-if="row.status === 'completed'" @click="showInvoiceDialog(row)">录入发票</el-dropdown-item>
                  <el-dropdown-item v-if="row.status !== 'completed' && row.status !== 'cancelled'" @click="showEditDialog(row)">编辑</el-dropdown-item>
                  <el-dropdown-item v-if="row.change_log && row.change_log.length" @click="showChangeLog(row)">变更记录</el-dropdown-item>
                  <el-dropdown-item divided>
                    <span style="color:#f56c6c;width:100%;display:block" @click="confirmDelete(row.id)">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <el-empty v-if="!filteredTasks.length" description="暂无任务" />
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
              <el-checkbox v-model="taskForm.self_drive" style="margin-left:16px">自驾车</el-checkbox>
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
        <el-row v-else-if="taskForm.client_type === 'company'" :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="用车单位">
              <el-select v-model="taskForm.client_id" placeholder="请选择单位" style="width:100%" filterable @change="onClientChange">
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
            <el-form-item label="核定载人数">
              <el-select v-model="taskForm.vehicle_type" placeholder="请选择核定载人数" style="width:100%" filterable allow-create @change="onCapacityChange">
                <el-option v-for="t in vehicleTypes" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="用车数量">
              <el-input-number v-model="taskForm.vehicle_count" :min="1" :max="50" style="width:100%" @change="onVehicleCountChange" />
            </el-form-item>
          </el-col>
        </el-row>
        <template v-if="!taskForm.self_drive">
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="出发地点">
              <el-input v-model="taskForm.departure" @blur="onLocationChange" />
            </el-form-item>
          </el-col>
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="目的地">
              <el-input v-model="taskForm.destination" @blur="onLocationChange" />
            </el-form-item>
          </el-col>
        </el-row>
        </template>
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="出车时间">
              <el-date-picker v-model="taskForm.departure_time" type="datetime" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width:100%" :disabled-date="disablePastDates" @change="onDepartureTimeChange" />
            </el-form-item>
          </el-col>
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="回程时间">
              <el-date-picker v-model="taskForm.return_time" type="datetime" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width:100%" :disabled-date="disableBeforeDeparture" @change="onTimeChange" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="租用天数">
              <el-input :model-value="computedRentalDays" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="租车费(元)">
              <el-input-number v-model="taskForm.rental_fee" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <template v-if="!taskForm.self_drive">
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="isMobile ? 24 : 12">
            <el-form-item label="任务里程(km)">
              <el-input-number v-model="taskForm.mileage" :min="0" :precision="1" style="width:100%" @change="onMileageChange" />
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
        </template>
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
        <el-row :gutter="isMobile ? 0 : 20">
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="taskForm.remark" type="textarea" :rows="2" placeholder="选填" />
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
    <el-dialog v-model="scheduleDialogVisible" title="排班分配" :width="isMobile ? '100%' : '700px'" :fullscreen="isMobile">
      <el-form :label-width="isMobile ? '90px' : '100px'">
        <el-form-item label="出车时间">
          <el-input :model-value="scheduleInfo.task_start + ' ~ ' + scheduleInfo.task_end" disabled />
        </el-form-item>
        <template v-if="!currentScheduleTask?.self_drive">
        <el-form-item label="目的地">
          <el-tag>{{ scheduleInfo.destination }}</el-tag>
        </el-form-item>
        <el-form-item label="司机人工费">
          <el-tag>{{ scheduleInfo.labor_fee }} 元</el-tag>
        </el-form-item>
        <el-form-item v-if="scheduleInfo.settlement_start" label="结算周期">
          <span style="color:#909399;font-size:13px">{{ scheduleInfo.settlement_start }}-{{ scheduleInfo.settlement_end }}</span>
        </el-form-item>
        </template>
        
        <el-divider content-position="left">{{ currentScheduleTask?.self_drive ? '车辆分配' : '车辆分配（' + scheduleAssignments.length + '台）' }}</el-divider>
        
        <template v-if="currentScheduleTask?.self_drive">
        <!-- 自驾车排班布局 -->
        <div v-for="(a, idx) in scheduleAssignments" :key="idx" style="margin-bottom:16px;padding:12px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0">
          <el-form-item label="选择车辆" style="margin-bottom:8px">
            <el-select v-model="a.vehicle_id" placeholder="请选择车辆" style="width:100%" filterable @change="(val) => onScheduleVehicleChange(idx, val)">
              <el-option v-for="v in getAvailableVehicles(idx)" :key="v.id" :label="v.plate_number + (v.capacity ? ' (' + v.capacity + ')' : '')" :value="v.id" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="a.vehicle_id" label="当前里程" style="margin-bottom:0">
            <span style="font-weight:600;color:#409eff">{{ getVehicleMileage(a.vehicle_id).toLocaleString() }} km</span>
          </el-form-item>
        </div>
        <el-form-item label="备注">
          <el-input v-model="scheduleRemark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
        </template>
        
        <template v-else>
        <!-- 普通排班布局 -->
        <div v-for="(a, idx) in scheduleAssignments" :key="idx" style="display:flex;gap:8px;margin-bottom:10px;align-items:center">
          <span style="width:30px;color:#909399;font-size:13px">{{ idx + 1 }}.</span>
          <el-select v-model="a.vehicle_id" placeholder="选择车辆" style="flex:1" filterable>
            <el-option v-for="v in getAvailableVehicles(idx)" :key="v.id" :label="v.plate_number + (v.capacity ? ' (' + v.capacity + ')' : '')" :value="v.id" />
          </el-select>
          <el-select v-model="a.driver_id" placeholder="选择司机" style="flex:1" filterable>
            <el-option v-for="d in getAvailableDrivers(idx)" :key="d.id" :label="d.name + ' (' + d.phone + ') ¥' + d.total_labor_fee" :value="d.id" />
          </el-select>
        </div>
        <el-form-item label="备注" style="margin-top:12px">
          <el-input v-model="scheduleRemark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitSchedule">确认排班</el-button>
      </template>
    </el-dialog>

    <!-- Complete Task Dialog -->
    <el-dialog v-model="completeDialogVisible" :title="isSelfDriveComplete ? '完成任务 - 录入里程' : '完成任务 - 录入实际费用'" :width="isMobile ? '100%' : '500px'" :fullscreen="isMobile">
      <el-form :model="completeForm" :label-width="isMobile ? '100px' : '110px'">
        <template v-if="!isSelfDriveComplete">
        <el-form-item label="油电费(预估)">
          <el-input :model-value="completeForm.actual_fuel_fee" disabled />
        </el-form-item>
        <el-form-item label="桥路费(预估)">
          <el-input :model-value="completeForm.actual_bridge_fee" disabled />
        </el-form-item>
        <el-form-item label="实际司机人工费">
          <el-input-number v-model="completeForm.actual_labor_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        </template>
        <el-form-item label="其他费用">
          <el-input-number v-model="completeForm.other_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <template v-if="showMileageFields">
          <el-divider>里程数</el-divider>
          <el-form-item label="起始里程(km)">
            <el-input v-if="isSelfDriveComplete" :model-value="completeForm.start_mileage?.toLocaleString()" disabled />
            <el-input-number v-else v-model="completeForm.start_mileage" :min="0" :precision="0" style="width:100%" />
          </el-form-item>
          <el-form-item label="结束里程(km)">
            <el-input-number v-model="completeForm.end_mileage" :min="completeForm.start_mileage" :precision="0" style="width:100%" />
          </el-form-item>
        </template>
        <el-divider />
        <el-form-item label="实际成本">
          <el-input :model-value="actualCostDisplay" disabled />
        </el-form-item>
        <el-form-item label="最终利润">
          <el-input :model-value="finalProfitDisplay" disabled />
        </el-form-item>
        <el-divider />
        <el-form-item label="备注">
          <el-input v-model="completeForm.remark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
        <el-form-item label="是否已收款">
          <el-switch v-model="completeForm.is_paid" />
        </el-form-item>
        <template v-if="completeForm.is_paid">
          <el-form-item label="收款日期">
            <el-date-picker v-model="completeForm.paid_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:100%" placeholder="请选择收款日期" />
          </el-form-item>
          <el-form-item label="收款方式">
            <el-select v-model="completeForm.paid_method" style="width:100%" placeholder="请选择收款方式">
              <el-option label="转账" value="转账" />
              <el-option label="二维码" value="二维码" />
              <el-option label="现金" value="现金" />
            </el-select>
          </el-form-item>
        </template>
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
            <template v-if="log.snapshot && log.snapshot.cancel_reason">
              <el-alert type="error" :closable="false" style="margin-bottom:8px">
                <template #title>
                  <span style="font-weight:bold">任务取消</span>
                </template>
                <div>取消原因：{{ log.snapshot.cancel_reason }}</div>
                <div v-if="log.snapshot.cancelled_at" style="margin-top:4px;color:#909399;font-size:12px">取消时间：{{ log.snapshot.cancelled_at }}</div>
              </el-alert>
              <template v-if="log.snapshot.client_name !== undefined">
                <el-descriptions :column="isMobile ? 1 : 2" size="small" border style="margin-top:8px">
                  <el-descriptions-item label="用车联系人">{{ log.snapshot.client_name }}</el-descriptions-item>
                  <el-descriptions-item label="出发 → 目的地">{{ log.snapshot.departure }} → {{ log.snapshot.destination }}</el-descriptions-item>
                  <el-descriptions-item label="出车时间">{{ log.snapshot.departure_time }}</el-descriptions-item>
                  <el-descriptions-item label="核定载人数">{{ log.snapshot.vehicle_type }}</el-descriptions-item>
                </el-descriptions>
              </template>
            </template>
            <template v-else-if="log.snapshot">
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
                <el-descriptions-item label="核定载人数">
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

    <!-- Cancel Task Dialog -->
    <el-dialog v-model="cancelDialogVisible" title="取消任务" :width="isMobile ? '100%' : '450px'" :fullscreen="isMobile">
      <el-form label-width="80px">
        <el-form-item label="取消原因">
          <el-input v-model="cancelReason" type="textarea" :rows="3" placeholder="请输入取消原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="cancelTask">确定取消</el-button>
      </template>
    </el-dialog>

    <!-- Invoice Dialog -->
    <el-dialog v-model="invoiceDialogVisible" title="录入发票信息" :width="isMobile ? '100%' : '500px'" :fullscreen="isMobile">
      <el-form :model="invoiceForm" label-width="100px">
        <el-form-item label="发票类型">
          <el-select v-model="invoiceForm.invoice_type" style="width:100%" placeholder="请选择发票类型">
            <el-option label="增值税普通发票" value="增值税普通发票" />
            <el-option label="增值税专用发票" value="增值税专用发票" />
            <el-option label="收据" value="收据" />
          </el-select>
        </el-form-item>
        <el-form-item label="发票号码">
          <el-input v-model="invoiceForm.invoice_no" placeholder="请输入发票号码" />
        </el-form-item>
        <el-form-item label="包车合同编号">
          <el-input v-model="invoiceForm.contract_no" placeholder="请输入包车合同编号" />
        </el-form-item>
        <el-form-item label="发票金额">
          <el-input-number v-model="invoiceForm.invoice_amount" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="开票日期">
          <el-date-picker v-model="invoiceForm.invoice_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:100%" placeholder="请选择开票日期" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="invoiceForm.invoice_remark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="invoiceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitInvoice">保存</el-button>
      </template>
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

    <!-- 费率设置弹窗 -->
    <el-dialog v-model="settingsVisible" title="油电费费率配置" width="580px">
      <el-divider content-position="left">核定载人数单价</el-divider>
      <div style="margin-bottom:8px">
        <el-button type="primary" size="small" @click="addFuelRate">新增规则</el-button>
      </div>
      <el-table :data="fuelRates" border size="small">
        <el-table-column label="核定载人数" min-width="140">
          <template #default="{ row, $index }">
            <div style="display:flex;gap:4px;align-items:center">
              <el-input-number v-model="row.min" :min="1" :max="200" size="small" style="width:70px" controls-position="right" />
              <span>~</span>
              <el-input-number v-model="row.max" :min="1" :max="200" size="small" style="width:70px" controls-position="right" />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="单价(元/km)" width="130">
          <template #default="{ row }">
            <el-input-number v-model="row.rate" :min="0" :max="100" :precision="1" size="small" style="width:90px" controls-position="right" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="70" align="center">
          <template #default="{ $index }">
            <el-button type="danger" size="small" link @click="fuelRates.splice($index, 1)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-divider content-position="left">里程预估加成比例</el-divider>
      <div style="margin-bottom:8px">
        <el-button type="primary" size="small" @click="addMileageMultiplier">新增区间</el-button>
      </div>
      <el-table :data="mileageMultipliers" border size="small">
        <el-table-column label="里程区间(km)" min-width="160">
          <template #default="{ row }">
            <div style="display:flex;gap:4px;align-items:center">
              <el-input-number v-model="row.min_km" :min="0" :max="99999" size="small" style="width:75px" controls-position="right" />
              <span>~</span>
              <el-input-number v-model="row.max_km" :min="0" :max="99999" size="small" style="width:75px" controls-position="right" />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="加成(%)" width="110">
          <template #default="{ row }">
            <el-input-number v-model="row.multiplier" :min="0" :max="100" size="small" style="width:80px" controls-position="right" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="70" align="center">
          <template #default="{ $index }">
            <el-button type="danger" size="small" link @click="mileageMultipliers.splice($index, 1)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="settingsVisible = false">取消</el-button>
        <el-button type="primary" @click="saveFuelRates">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute } from 'vue-router'
import api from '../utils/api'

const route = useRoute()

const isMobile = ref(false)
const checkMobile = () => { isMobile.value = window.innerWidth <= 768 }
onMounted(() => { checkMobile(); window.addEventListener('resize', checkMobile) })
onUnmounted(() => window.removeEventListener('resize', checkMobile))

const tasks = ref([])
const statusFilter = ref('')
const settingsVisible = ref(false)
const fuelRates = ref([])
const mileageMultipliers = ref([])

const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

const defaultFuelRates = [
  { min: 31, max: 51, rate: 2.5 },
  { min: 15, max: 17, rate: 1.5 },
  { min: 7, max: 7, rate: 1 },
  { min: 5, max: 5, rate: 0.7 }
]

const defaultMileageMultipliers = [
  { min_km: 0, max_km: 100, multiplier: 10 },
  { min_km: 100, max_km: 500, multiplier: 5 },
  { min_km: 500, max_km: 9999, multiplier: 3 }
]

const loadFuelRates = async () => {
  try {
    const res = await api.get('/system-config/fuel_rates')
    if (res.code === 200 && res.data) {
      fuelRates.value = JSON.parse(res.data)
    } else {
      fuelRates.value = [...defaultFuelRates]
    }
  } catch (e) {
    fuelRates.value = [...defaultFuelRates]
  }
}

const loadMileageMultipliers = async () => {
  try {
    const res = await api.get('/system-config/mileage_multipliers')
    if (res.code === 200 && res.data) {
      mileageMultipliers.value = JSON.parse(res.data)
    } else {
      mileageMultipliers.value = [...defaultMileageMultipliers]
    }
  } catch (e) {
    mileageMultipliers.value = [...defaultMileageMultipliers]
  }
}

const addFuelRate = () => {
  fuelRates.value.push({ min: 1, max: 1, rate: 1 })
}

const addMileageMultiplier = () => {
  mileageMultipliers.value.push({ min_km: 0, max_km: 100, multiplier: 5 })
}

const showSettings = () => {
  settingsVisible.value = true
}

const saveFuelRates = async () => {
  try {
    await api.put('/system-config/fuel_rates', { value: fuelRates.value })
    await api.put('/system-config/mileage_multipliers', { value: mileageMultipliers.value })
    ElMessage.success('保存成功')
    settingsVisible.value = false
  } catch (e) {}
}

const filteredTasks = computed(() => {
  if (statusFilter.value === 'all') return tasks.value
  if (statusFilter.value) return tasks.value.filter(t => t.status === statusFilter.value)
  return tasks.value.filter(t => t.status !== 'cancelled')
})
const laborRates = ref([])
const clients = ref([])
const vehicles = ref([])
const vehicleTypes = computed(() => [...new Set(vehicles.value.map(v => v.capacity).filter(Boolean))])
const taskDialogVisible = ref(false)
const scheduleDialogVisible = ref(false)
const completeDialogVisible = ref(false)
const changeLogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const currentChangeLog = ref([])
const cancelDialogVisible = ref(false)
const cancelTaskId = ref(null)
const cancelReason = ref('')
const invoiceDialogVisible = ref(false)
const invoiceTaskId = ref(null)
const invoiceForm = ref({ invoice_type: '', invoice_no: '', invoice_amount: 0, invoice_date: '', invoice_remark: '', contract_no: '' })

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

const isPastReturn = (row) => {
  if (!row.return_time) return true
  return new Date(row.return_time) <= new Date()
}

const canSubmitApproval = (row) => {
  if (row.status !== 'scheduled' || isPastDeparture(row)) return false
  const status = row.yzj_approval_status
  return !status || status === 'rejected'
}

const taskForm = ref({
  client_type: 'personal', client_name: '', client_phone: '', client_id: null, contact_id: null,
  departure: '', destination: '', departure_time: '', return_time: '',
  vehicle_type: '', vehicle_count: 1, self_drive: false, mileage: 0, rental_fee: 0,
  fuel_fee: 0, bridge_fee: 0, labor_fee: 0, remark: ''
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
const scheduleAssignments = ref([])
const currentScheduleTask = ref(null)
const scheduleRemark = ref('')

const getVehicleMileage = (vehicleId) => {
  const v = vehicles.value.find(v => v.id === vehicleId)
  return v?.mileage || 0
}

const onScheduleVehicleChange = (idx, val) => {
  // 选择车辆时自动带出里程数（用于自驾车显示）
}

const completeForm = ref({ actual_fuel_fee: 0, actual_bridge_fee: 0, actual_labor_fee: 0, other_fee: 0, remark: '', is_paid: false, paid_date: '', paid_method: '', start_mileage: 0, end_mileage: 0 })
const completeTaskId = ref(null)
const currentCompleteTask = ref(null)

const showMileageFields = computed(() => {
  const task = currentCompleteTask.value
  if (!task || !task.vehicle_id) return false
  // 自驾车也显示里程（只读）
  if (task.self_drive) return true
  // 核定载人数12座以下且不是国开司的车辆
  const capacity = parseInt(task.vehicle_type)
  if (isNaN(capacity) || capacity > 12) return false
  const vehicle = vehicles.value.find(v => v.id === task.vehicle_id)
  if (vehicle && vehicle.company === '国开司') return false
  return true
})

const isSelfDriveComplete = computed(() => currentCompleteTask.value?.self_drive || false)

const estimatedCost = computed(() => (taskForm.value.fuel_fee + taskForm.value.bridge_fee + taskForm.value.labor_fee).toFixed(2))
const estimatedProfit = computed(() => (taskForm.value.rental_fee - taskForm.value.fuel_fee - taskForm.value.bridge_fee - taskForm.value.labor_fee).toFixed(2))
const actualCostDisplay = computed(() => (completeForm.value.actual_fuel_fee + completeForm.value.actual_bridge_fee + completeForm.value.actual_labor_fee + completeForm.value.other_fee).toFixed(2))
const finalProfitDisplay = computed(() => {
  const task = tasks.value.find(t => t.id === completeTaskId.value)
  const rental = task ? task.rental_fee : 0
  return (rental - completeForm.value.actual_fuel_fee - completeForm.value.actual_bridge_fee - completeForm.value.actual_labor_fee - completeForm.value.other_fee).toFixed(2)
})

const fieldMap = { client_name: '用车联系人', client_phone: '联系电话', departure: '出发地点', destination: '目的地', departure_time: '出车时间', return_time: '回程时间', vehicle_type: '核定载人数', mileage: '任务里程', rental_fee: '租车费', fuel_fee: '油电费', bridge_fee: '桥路费', labor_fee: '司机人工费' }
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
  taskForm.value = { client_type: 'personal', client_name: '', client_phone: '', client_id: null, contact_id: null, departure: '', destination: '', departure_time: '', return_time: '', vehicle_type: '', vehicle_count: 1, self_drive: false, mileage: 0, rental_fee: 0, fuel_fee: 0, bridge_fee: 0, labor_rate_id: null, labor_fee: 0, remark: '' }
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
    bridge_fee: row.bridge_fee, labor_rate_id: matchedRate ? matchedRate.id : null, labor_fee: row.labor_fee,
    remark: row.remark || ''
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
  if (!taskForm.value.self_drive && (!taskForm.value.departure || !taskForm.value.destination)) {
    ElMessage.warning('请填写出发地和目的地')
    return
  }
  if (!taskForm.value.departure_time || !taskForm.value.return_time) {
    ElMessage.warning('请填写出车和回程时间')
    return
  }
  if (new Date(taskForm.value.departure_time) < new Date()) {
    ElMessage.warning('出车时间不能选择过去的时间')
    return
  }
  if (new Date(taskForm.value.return_time) < new Date(taskForm.value.departure_time)) {
    ElMessage.warning('回程时间不能早于出车时间')
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
  currentScheduleTask.value = row
  scheduleForm.value = { vehicle_id: null, driver_id: null }
  scheduleRemark.value = row.remark || ''
  
  // 根据 vehicle_count 初始化分配列表
  const count = row.vehicle_count || 1
  scheduleAssignments.value = Array.from({ length: count }, () => ({ vehicle_id: null, driver_id: null }))
  
  // 如果已有排班记录，填充
  if (row.task_vehicles && row.task_vehicles.length > 0) {
    row.task_vehicles.forEach((tv, idx) => {
      if (idx < scheduleAssignments.value.length) {
        scheduleAssignments.value[idx].vehicle_id = tv.vehicle_id
        scheduleAssignments.value[idx].driver_id = tv.driver_id
      }
    })
  }
  
  try {
    const res = await api.get(`/tasks/${row.id}/available-resources`)
    scheduleInfo.value = { ...res.data, destination: row.destination, labor_fee: row.labor_fee }
    scheduleDialogVisible.value = true
  } catch (e) {}
}

const getAvailableVehicles = (currentIdx) => {
  const selectedIds = scheduleAssignments.value
    .map((a, idx) => idx !== currentIdx ? a.vehicle_id : null)
    .filter(Boolean)
  return scheduleInfo.value.vehicles.filter(v => !selectedIds.includes(v.id))
}

const getAvailableDrivers = (currentIdx) => {
  const selectedIds = scheduleAssignments.value
    .map((a, idx) => idx !== currentIdx ? a.driver_id : null)
    .filter(Boolean)
  return scheduleInfo.value.drivers.filter(d => !selectedIds.includes(d.id))
}

const submitSchedule = async () => {
  const isSelfDrive = currentScheduleTask.value?.self_drive
  // 验证所有分配都已填写
  for (let i = 0; i < scheduleAssignments.value.length; i++) {
    const a = scheduleAssignments.value[i]
    if (!a.vehicle_id) {
      ElMessage.warning(`请为第${i + 1}台车选择车辆`)
      return
    }
    if (!isSelfDrive && !a.driver_id) {
      ElMessage.warning(`请为第${i + 1}台车选择司机`)
      return
    }
  }
  try {
    await api.post(`/tasks/${scheduleTaskId.value}/schedule`, { 
      assignments: scheduleAssignments.value,
      remark: scheduleRemark.value
    })
    ElMessage.success('排班成功')
    scheduleDialogVisible.value = false
    loadTasks()
  } catch (e) {}
}

const showCompleteDialog = (row) => {
  completeTaskId.value = row.id
  currentCompleteTask.value = row
  
  // 计算起始里程数（从车辆当前里程获取）
  let startMileage = 0
  if (row.vehicle_id) {
    const vehicle = vehicles.value.find(v => v.id === row.vehicle_id)
    if (vehicle) {
      // 自驾车或核定载人数12座以下且不是国开司的车辆
      if (row.self_drive) {
        startMileage = vehicle.mileage || 0
      } else {
        const capacity = parseInt(row.vehicle_type)
        if (!isNaN(capacity) && capacity <= 12 && vehicle.company !== '国开司') {
          startMileage = vehicle.mileage || 0
        }
      }
    }
  }
  
  completeForm.value = {
    actual_fuel_fee: row.fuel_fee || 0,
    actual_bridge_fee: row.bridge_fee || 0,
    actual_labor_fee: 0,
    other_fee: 0,
    remark: '',
    is_paid: false,
    paid_date: '',
    paid_method: '',
    start_mileage: startMileage,
    end_mileage: 0
  }
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

const confirmDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确认删除该任务？', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteTask(id)
  } catch (e) {}
}

const showChangeLog = (row) => {
  currentChangeLog.value = row.change_log || []
  changeLogVisible.value = true
}

const showCancelDialog = (row) => {
  cancelTaskId.value = row.id
  cancelReason.value = ''
  cancelDialogVisible.value = true
}

const cancelTask = async () => {
  if (!cancelReason.value.trim()) { ElMessage.warning('请输入取消原因'); return }
  try {
    await api.post(`/tasks/${cancelTaskId.value}/cancel`, { reason: cancelReason.value.trim() })
    ElMessage.success('任务已取消')
    cancelDialogVisible.value = false
    loadTasks()
  } catch (e) {}
}

const showInvoiceDialog = (row) => {
  invoiceTaskId.value = row.id
  invoiceForm.value = {
    invoice_type: row.invoice_type || '',
    invoice_no: row.invoice_no || '',
    invoice_amount: row.invoice_amount || 0,
    invoice_date: row.invoice_date || '',
    invoice_remark: row.invoice_remark || '',
    contract_no: row.contract_no || ''
  }
  invoiceDialogVisible.value = true
}

const submitInvoice = async () => {
  try {
    await api.post(`/tasks/${invoiceTaskId.value}/invoice`, invoiceForm.value)
    ElMessage.success('发票信息已保存')
    invoiceDialogVisible.value = false
    loadTasks()
  } catch (e) {}
}

const loadLaborRates = async () => {
  try { const res = await api.get('/labor-rates'); laborRates.value = res.data } catch (e) {}
}

const loadClients = async () => {
  try { const res = await api.get('/clients'); clients.value = res.data } catch (e) {}
}

const loadVehicles = async () => {
  try { const res = await api.get('/vehicles'); vehicles.value = res.data } catch (e) {}
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
    if (rate) {
      const count = taskForm.value.vehicle_count || 1
      taskForm.value.labor_fee = rate.labor_rate * Math.ceil(getRentalDays() / rate.days) * count
    }
  }
}

const getFuelRate = (capacity) => {
  const c = parseInt(capacity)
  if (!c || isNaN(c)) return null
  const rates = fuelRates.value.length > 0 ? fuelRates.value : defaultFuelRates
  for (const r of rates) {
    if (c >= r.min && c <= r.max) return r.rate
  }
  return null
}

const recalcFuelFee = () => {
  const rate = getFuelRate(taskForm.value.vehicle_type)
  const mileage = taskForm.value.mileage
  if (rate && mileage > 0) {
    taskForm.value.fuel_fee = Math.round(rate * mileage * 100) / 100
  }
}

const onCapacityChange = () => {
  recalcFuelFee()
}

const onMileageChange = () => {
  recalcFuelFee()
}

const tollLoading = ref(false)
const singleDistance = ref(0)  // 单车单程距离
const singleTolls = ref(0)    // 单车单程过路费

const getMileageMultiplier = (distance) => {
  const multipliers = mileageMultipliers.value.length > 0 ? mileageMultipliers.value : defaultMileageMultipliers
  for (const m of multipliers) {
    if (distance >= m.min_km && distance < m.max_km) return m.multiplier
  }
  return 10 // 默认10%
}

const onLocationChange = async () => {
  const dep = taskForm.value.departure?.trim()
  const dest = taskForm.value.destination?.trim()
  if (!dep || !dest) return
  try {
    tollLoading.value = true
    const res = await api.get('/estimate-toll', { params: { departure: dep, destination: dest } })
    if (res.code === 200 && res.data) {
      singleDistance.value = res.data.distance
      singleTolls.value = res.data.tolls
      const count = taskForm.value.vehicle_count || 1
      const multiplier = getMileageMultiplier(singleDistance.value)
      const mileage = Math.round(singleDistance.value * 2 * (1 + multiplier / 100) * 10) / 10
      taskForm.value.mileage = Math.round(mileage * count * 10) / 10
      taskForm.value.bridge_fee = singleTolls.value * 2 * count
      recalcFuelFee()
      ElMessage.success(`预估：过路费${taskForm.value.bridge_fee}元，里程${taskForm.value.mileage}km（来回含${multiplier}%余量${count > 1 ? '，' + count + '车' : ''}）`)
    }
  } catch (e) {
    // 静默失败，不打扰用户
  } finally {
    tollLoading.value = false
  }
}

const onVehicleCountChange = () => {
  if (singleDistance.value > 0) {
    const count = taskForm.value.vehicle_count || 1
    const multiplier = getMileageMultiplier(singleDistance.value)
    const mileage = Math.round(singleDistance.value * 2 * (1 + multiplier / 100) * 10) / 10
    taskForm.value.mileage = Math.round(mileage * count * 10) / 10
    taskForm.value.bridge_fee = singleTolls.value * 2 * count
    recalcFuelFee()
  }
  recalcLaborFee()
}

const onLaborRateChange = (rateId) => {
  recalcLaborFee()
}

const onTimeChange = () => {
  recalcLaborFee()
}

const disablePastDates = (date) => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date < today
}

const disableBeforeDeparture = (date) => {
  const dt = taskForm.value.departure_time
  if (!dt) return disablePastDates(date)
  const dep = new Date(dt)
  dep.setHours(0, 0, 0, 0)
  return date < dep
}

const onDepartureTimeChange = () => {
  const dt = taskForm.value.departure_time
  const rt = taskForm.value.return_time
  if (dt && rt && new Date(rt) < new Date(dt)) {
    taskForm.value.return_time = ''
    ElMessage.warning('回程时间已清空，请重新选择')
  }
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
    // 先获取客户的联系人信息（含企业微信UserID）
    let wxUserid = ''
    try {
      const clientRes = await api.get(`/clients/${row.client_id}`)
      if (clientRes.code === 200 && clientRes.data?.contacts) {
        const contact = clientRes.data.contacts.find(c => c.wx_userid)
        if (contact) {
          wxUserid = contact.wx_userid
        }
      }
    } catch (e) {
      // 获取失败不影响推送
    }

    // 发送人使用当前用户在设置中配置的账号
    let wxSender = user.value.wx_sender || ''

    const isExternal = wxUserid.startsWith('wm')
    let confirmMsg = ''
    if (!wxUserid) {
      confirmMsg = `确定要向客户"${row.client_name}"推送任务确认消息吗？\n⚠️ 未配置企业微信用户ID，需手动发送确认链接`
    } else if (isExternal && !wxSender) {
      confirmMsg = `⚠️ 未配置发送人账号，无法自动推送。\n请先在右上角设置中配置"发送人账号"`
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

onMounted(async () => {
  await loadTasks()
  loadLaborRates(); loadClients(); loadVehicles(); loadFuelRates(); loadMileageMultipliers()
  const editId = route.query.edit
  if (editId) {
    const task = tasks.value.find(t => t.id === Number(editId))
    if (task) showEditDialog(task)
  }
})
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
