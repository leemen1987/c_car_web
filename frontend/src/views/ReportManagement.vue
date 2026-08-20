<template>
  <div>
    <el-card class="page-card">
      <template #header>
        <div class="page-header">
          <div class="page-title">
            <el-icon :size="20"><DataAnalysis /></el-icon>
            <span>报表管理</span>
          </div>
          <el-button text size="small" @click="showSearch = !showSearch">
            {{ showSearch ? '收起筛选' : '展开筛选' }} <el-icon><ArrowUp v-if="showSearch" /><ArrowDown v-else /></el-icon>
          </el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 按用车单位查询 -->
        <el-tab-pane label="按用车单位查询" name="client">
          <el-form v-show="showSearch" :inline="true" style="margin-bottom:15px">
            <el-form-item label="包车类型">
              <el-select v-model="clientQuery.client_type" placeholder="全部" clearable style="width:120px">
                <el-option label="个人包车" value="personal" />
                <el-option label="单位包车" value="company" />
              </el-select>
            </el-form-item>
            <el-form-item label="收款状态">
              <el-select v-model="clientQuery.is_paid" placeholder="全部" clearable style="width:100px">
                <el-option label="已收款" value="1" />
                <el-option label="未收款" value="0" />
              </el-select>
            </el-form-item>
            <el-form-item label="收款方式">
              <el-select v-model="clientQuery.paid_method" placeholder="全部" clearable style="width:120px">
                <el-option label="转账" value="转账" />
                <el-option label="二维码" value="二维码" />
                <el-option label="现金" value="现金" />
              </el-select>
            </el-form-item>
            <el-form-item label="用车单位">
              <el-input v-model="clientQuery.client" placeholder="输入单位名称" clearable />
            </el-form-item>
            <el-form-item label="月份">
              <el-date-picker v-model="clientQuery.month" type="month" format="YYYY-MM" value-format="YYYY-MM" placeholder="选择月份" clearable />
            </el-form-item>
            <el-form-item label="年份">
              <el-date-picker v-model="clientQuery.year" type="year" format="YYYY" value-format="YYYY" placeholder="选择年份" clearable />
            </el-form-item>
            <el-form-item label="自定义时间">
              <el-date-picker v-model="clientQuery.dateRange" type="daterange" format="YYYY-MM-DD" value-format="YYYY-MM-DD" start-placeholder="开始日期" end-placeholder="结束日期" clearable />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="queryByClient">查询</el-button>
              <el-button type="success" @click="exportClient" :disabled="!clientTasks.length">导出Excel</el-button>
            </el-form-item>
          </el-form>

          <el-descriptions v-if="clientSummary" :column="4" border style="margin-bottom:15px">
            <el-descriptions-item label="任务总数">{{ clientSummary.total_tasks }}</el-descriptions-item>
            <el-descriptions-item label="总租车费">¥{{ clientSummary.total_rental_fee?.toFixed(2) }}</el-descriptions-item>
            <el-descriptions-item label="总实际成本">¥{{ clientSummary.total_actual_cost?.toFixed(2) }}</el-descriptions-item>
            <el-descriptions-item label="总利润">
              <span :style="{ color: clientSummary.total_final_profit >= 0 ? '#67c23a' : '#f56c6c' }">¥{{ clientSummary.total_final_profit?.toFixed(2) }}</span>
            </el-descriptions-item>
          </el-descriptions>

          <el-table :data="clientTasks" border stripe max-height="400">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column label="包车类型" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.client_type === 'company' ? 'primary' : 'success'" size="small">
                  {{ row.client_type === 'company' ? '单位' : '个人' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="用车单位" min-width="120">
              <template #default="{ row }">
                {{ row.client_type === 'company' ? (row.client_company || row.client_name) : row.client_name }}
              </template>
            </el-table-column>
            <el-table-column prop="contact_name" label="联系人" width="90" />
            <el-table-column prop="departure" label="出发地点" min-width="100" />
            <el-table-column prop="destination" label="目的地" min-width="100" />
            <el-table-column prop="vehicle_plate" label="车牌号" min-width="100" />
            <el-table-column prop="driver_name" label="司机" min-width="100" />
            <el-table-column prop="departure_time" label="出车时间" min-width="150" />
            <el-table-column prop="rental_fee" label="租车费" width="100" align="right" />
            <el-table-column prop="actual_cost" label="实际成本" width="100" align="right" />
            <el-table-column prop="final_profit" label="最终利润" width="100" align="right">
              <template #default="{ row }">
                <span :style="{ color: row.final_profit >= 0 ? '#67c23a' : '#f56c6c' }">{{ row.final_profit }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'scheduled' ? 'primary' : row.status === 'cancelled' ? 'danger' : 'warning'">
                  {{ row.status === 'completed' ? '已完成' : row.status === 'scheduled' ? '已排班' : row.status === 'cancelled' ? '已取消' : '待排班' }}
                </el-tag>
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
            <el-table-column label="确认情况" width="90" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.schedule_confirm_status === 'confirmed'" type="success" size="small">已确认</el-tag>
                <el-tag v-else-if="row.schedule_confirm_status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
                <el-tag v-else-if="row.schedule_confirm_status === 'pending'" type="warning" size="small">待确认</el-tag>
                <span v-else style="color:#c0c4cc">-</span>
              </template>
            </el-table-column>
            <el-table-column v-if="canEdit()" label="操作" width="70" align="center">
              <template #default="{ row }">
                <el-button size="small" plain @click="openEdit(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 按司机查询 -->
        <el-tab-pane label="按司机查询" name="driver">
          <el-form v-show="showSearch" :inline="true" style="margin-bottom:15px">
            <el-form-item label="包车类型">
              <el-select v-model="driverQuery.client_type" placeholder="全部" clearable style="width:120px">
                <el-option label="个人包车" value="personal" />
                <el-option label="单位包车" value="company" />
              </el-select>
            </el-form-item>
            <el-form-item label="收款状态">
              <el-select v-model="driverQuery.is_paid" placeholder="全部" clearable style="width:100px">
                <el-option label="已收款" value="1" />
                <el-option label="未收款" value="0" />
              </el-select>
            </el-form-item>
            <el-form-item label="收款方式">
              <el-select v-model="driverQuery.paid_method" placeholder="全部" clearable style="width:120px">
                <el-option label="转账" value="转账" />
                <el-option label="二维码" value="二维码" />
                <el-option label="现金" value="现金" />
              </el-select>
            </el-form-item>
            <el-form-item label="司机">
              <el-select v-model="driverQuery.driver_id" placeholder="选择司机" clearable style="width:200px">
                <el-option v-for="d in allDrivers" :key="d.id" :label="d.name + ' (' + d.phone + ')'" :value="d.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="月份">
              <el-date-picker v-model="driverQuery.month" type="month" format="YYYY-MM" value-format="YYYY-MM" placeholder="选择月份" clearable />
            </el-form-item>
            <el-form-item label="年份">
              <el-date-picker v-model="driverQuery.year" type="year" format="YYYY" value-format="YYYY" placeholder="选择年份" clearable />
            </el-form-item>
            <el-form-item label="自定义时间">
              <el-date-picker v-model="driverQuery.dateRange" type="daterange" format="YYYY-MM-DD" value-format="YYYY-MM-DD" start-placeholder="开始日期" end-placeholder="结束日期" clearable />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="queryByDriver">查询</el-button>
              <el-button type="success" @click="exportDriver" :disabled="!driverResults.length">导出Excel</el-button>
            </el-form-item>
          </el-form>

          <div v-for="(ds, idx) in driverResults" :key="idx" style="margin-bottom:20px">
            <el-descriptions :column="4" border style="margin-bottom:10px">
              <el-descriptions-item label="司机姓名">{{ ds.driver_name }}</el-descriptions-item>
              <el-descriptions-item label="手机号码">{{ ds.driver_phone }}</el-descriptions-item>
              <el-descriptions-item label="任务数">{{ ds.task_count }}</el-descriptions-item>
              <el-descriptions-item label="总人工费">¥{{ ds.total_actual_labor_fee?.toFixed(2) }}</el-descriptions-item>
            </el-descriptions>
            <el-table :data="ds.tasks" border stripe size="small">
              <el-table-column type="index" label="序号" width="60" align="center" />
              <el-table-column label="包车类型" width="90" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.client_type === 'company' ? 'primary' : 'success'" size="small">
                    {{ row.client_type === 'company' ? '单位' : '个人' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="用车单位" min-width="120">
                <template #default="{ row }">
                  {{ row.client_type === 'company' ? (row.client_company || row.client_name) : row.client_name }}
                </template>
              </el-table-column>
              <el-table-column prop="contact_name" label="联系人" width="90" />
              <el-table-column prop="departure" label="出发" min-width="80" />
              <el-table-column prop="destination" label="目的" min-width="80" />
              <el-table-column prop="departure_time" label="出车时间" min-width="150" />
              <el-table-column prop="labor_fee" label="预估人工费" width="100" align="right" />
              <el-table-column prop="actual_labor_fee" label="实际人工费" width="100" align="right" />
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
              <el-table-column label="确认情况" width="90" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.schedule_confirm_status === 'confirmed'" type="success" size="small">已确认</el-tag>
                  <el-tag v-else-if="row.schedule_confirm_status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
                  <el-tag v-else-if="row.schedule_confirm_status === 'pending'" type="warning" size="small">待确认</el-tag>
                  <span v-else style="color:#c0c4cc">-</span>
                </template>
              </el-table-column>
              <el-table-column v-if="canEdit()" label="操作" width="70" align="center">
                <template #default="{ row }">
                  <el-button size="small" plain @click="openEdit(row)">编辑</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 按车辆查询 -->
        <el-tab-pane label="按车辆查询" name="vehicle">
          <el-form v-show="showSearch" :inline="true" style="margin-bottom:15px">
            <el-form-item label="包车类型">
              <el-select v-model="vehicleQuery.client_type" placeholder="全部" clearable style="width:120px">
                <el-option label="个人包车" value="personal" />
                <el-option label="单位包车" value="company" />
              </el-select>
            </el-form-item>
            <el-form-item label="收款状态">
              <el-select v-model="vehicleQuery.is_paid" placeholder="全部" clearable style="width:100px">
                <el-option label="已收款" value="1" />
                <el-option label="未收款" value="0" />
              </el-select>
            </el-form-item>
            <el-form-item label="收款方式">
              <el-select v-model="vehicleQuery.paid_method" placeholder="全部" clearable style="width:120px">
                <el-option label="转账" value="转账" />
                <el-option label="二维码" value="二维码" />
                <el-option label="现金" value="现金" />
              </el-select>
            </el-form-item>
            <el-form-item label="车辆">
              <el-select v-model="vehicleQuery.vehicle_id" placeholder="选择车辆" clearable style="width:200px">
                <el-option v-for="v in allVehicles" :key="v.id" :label="v.plate_number + ' (' + v.vehicle_type + ')'" :value="v.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="月份">
              <el-date-picker v-model="vehicleQuery.month" type="month" format="YYYY-MM" value-format="YYYY-MM" placeholder="选择月份" clearable />
            </el-form-item>
            <el-form-item label="年份">
              <el-date-picker v-model="vehicleQuery.year" type="year" format="YYYY" value-format="YYYY" placeholder="选择年份" clearable />
            </el-form-item>
            <el-form-item label="自定义时间">
              <el-date-picker v-model="vehicleQuery.dateRange" type="daterange" format="YYYY-MM-DD" value-format="YYYY-MM-DD" start-placeholder="开始日期" end-placeholder="结束日期" clearable />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="queryByVehicle">查询</el-button>
              <el-button type="success" @click="exportVehicle" :disabled="!vehicleResults.length">导出Excel</el-button>
            </el-form-item>
          </el-form>

          <div v-for="(vs, idx) in vehicleResults" :key="idx" style="margin-bottom:20px">
            <el-descriptions :column="4" border style="margin-bottom:10px">
              <el-descriptions-item label="车牌号">{{ vs.plate_number }}</el-descriptions-item>
              <el-descriptions-item label="车辆类型">{{ vs.vehicle_type }}</el-descriptions-item>
              <el-descriptions-item label="任务数">{{ vs.task_count }}</el-descriptions-item>
              <el-descriptions-item label="总利润">
                <span :style="{ color: vs.total_final_profit >= 0 ? '#67c23a' : '#f56c6c' }">¥{{ vs.total_final_profit?.toFixed(2) }}</span>
              </el-descriptions-item>
            </el-descriptions>
            <el-table :data="vs.tasks" border stripe size="small">
              <el-table-column type="index" label="序号" width="60" align="center" />
              <el-table-column label="包车类型" width="90" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.client_type === 'company' ? 'primary' : 'success'" size="small">
                    {{ row.client_type === 'company' ? '单位' : '个人' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="用车单位" min-width="120">
                <template #default="{ row }">
                  {{ row.client_type === 'company' ? (row.client_company || row.client_name) : row.client_name }}
                </template>
              </el-table-column>
              <el-table-column prop="contact_name" label="联系人" width="90" />
              <el-table-column prop="departure" label="出发" min-width="80" />
              <el-table-column prop="destination" label="目的" min-width="80" />
              <el-table-column prop="departure_time" label="出车时间" min-width="155" />
              <el-table-column prop="rental_fee" label="租车费" width="100" align="right" />
              <el-table-column prop="actual_cost" label="实际成本" width="100" align="right" />
              <el-table-column prop="final_profit" label="最终利润" width="100" align="right">
                <template #default="{ row }">
                  <span :style="{ color: row.final_profit >= 0 ? '#67c23a' : '#f56c6c' }">{{ row.final_profit }}</span>
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
              <el-table-column label="确认情况" width="90" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.schedule_confirm_status === 'confirmed'" type="success" size="small">已确认</el-tag>
                  <el-tag v-else-if="row.schedule_confirm_status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
                  <el-tag v-else-if="row.schedule_confirm_status === 'pending'" type="warning" size="small">待确认</el-tag>
                  <span v-else style="color:#c0c4cc">-</span>
                </template>
              </el-table-column>
              <el-table-column v-if="canEdit()" label="操作" width="70" align="center">
                <template #default="{ row }">
                  <el-button size="small" plain @click="openEdit(row)">编辑</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 编辑任务弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑任务费用" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="租车费(元)">
          <el-input-number v-model="editForm.rental_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="实际油电费">
          <el-input-number v-model="editForm.actual_fuel_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="实际桥路费">
          <el-input-number v-model="editForm.actual_bridge_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="实际人工费">
          <el-input-number v-model="editForm.actual_labor_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="其他费用">
          <el-input-number v-model="editForm.other_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="是否已收款">
          <el-switch v-model="editForm.is_paid" />
        </el-form-item>
        <template v-if="editForm.is_paid">
          <el-form-item label="收款日期">
            <el-date-picker v-model="editForm.paid_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
          <el-form-item label="收款方式">
            <el-select v-model="editForm.paid_method" style="width:100%">
              <el-option label="转账" value="转账" />
              <el-option label="二维码" value="二维码" />
              <el-option label="现金" value="现金" />
            </el-select>
          </el-form-item>
        </template>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import api from '../utils/api'
import * as XLSX from 'xlsx'

const router = useRouter()
const activeTab = ref('client')
const showSearch = ref(true)
const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const canEdit = () => user.value.role === 'admin' || (user.value.permissions || []).includes('report_edit')

const editDialogVisible = ref(false)
const editForm = ref({ id: null, rental_fee: 0, actual_fuel_fee: 0, actual_bridge_fee: 0, actual_labor_fee: 0, other_fee: 0, is_paid: false, paid_date: '', paid_method: '', remark: '' })

const openEdit = (row) => {
  editForm.value = {
    id: row.id,
    rental_fee: row.rental_fee || 0,
    actual_fuel_fee: row.actual_fuel_fee || 0,
    actual_bridge_fee: row.actual_bridge_fee || 0,
    actual_labor_fee: row.actual_labor_fee || 0,
    other_fee: row.other_fee || 0,
    is_paid: row.is_paid || false,
    paid_date: row.paid_date || '',
    paid_method: row.paid_method || '',
    remark: row.remark || ''
  }
  editDialogVisible.value = true
}

const saveEdit = async () => {
  try {
    await api.put(`/tasks/${editForm.value.id}`, editForm.value)
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    if (activeTab.value === 'client') queryByClient()
    else if (activeTab.value === 'driver') queryByDriver()
    else if (activeTab.value === 'vehicle') queryByVehicle()
  } catch (e) {}
}

const clientQuery = ref({ client: '', client_type: '', paid_method: '', is_paid: '', month: '', year: '', dateRange: null })
const clientTasks = ref([])
const clientSummary = ref(null)

const driverQuery = ref({ driver_id: null, client_type: '', paid_method: '', is_paid: '', month: '', year: '', dateRange: null })
const driverResults = ref([])
const allDrivers = ref([])

const vehicleQuery = ref({ vehicle_id: null, client_type: '', paid_method: '', is_paid: '', month: '', year: '', dateRange: null })
const vehicleResults = ref([])
const allVehicles = ref([])

const queryByClient = async () => {
  const params = { client: clientQuery.value.client }
  if (clientQuery.value.client_type) params.client_type = clientQuery.value.client_type
  if (clientQuery.value.paid_method) params.paid_method = clientQuery.value.paid_method
  if (clientQuery.value.is_paid) params.is_paid = clientQuery.value.is_paid
  if (clientQuery.value.month) params.month = clientQuery.value.month
  if (clientQuery.value.year) params.year = clientQuery.value.year
  if (clientQuery.value.dateRange) {
    params.start_date = clientQuery.value.dateRange[0]
    params.end_date = clientQuery.value.dateRange[1]
  }
  try {
    const res = await api.get('/reports/by-client', { params })
    clientTasks.value = res.data.tasks
    clientSummary.value = res.data.summary
  } catch (e) {}
}

const queryByDriver = async () => {
  const params = {}
  if (driverQuery.value.driver_id) params.driver_id = driverQuery.value.driver_id
  if (driverQuery.value.client_type) params.client_type = driverQuery.value.client_type
  if (driverQuery.value.paid_method) params.paid_method = driverQuery.value.paid_method
  if (driverQuery.value.is_paid) params.is_paid = driverQuery.value.is_paid
  if (driverQuery.value.month) params.month = driverQuery.value.month
  if (driverQuery.value.year) params.year = driverQuery.value.year
  if (driverQuery.value.dateRange) {
    params.start_date = driverQuery.value.dateRange[0]
    params.end_date = driverQuery.value.dateRange[1]
  }
  try {
    const res = await api.get('/reports/by-driver', { params })
    driverResults.value = res.data
  } catch (e) {}
}

const queryByVehicle = async () => {
  const params = {}
  if (vehicleQuery.value.vehicle_id) params.vehicle_id = vehicleQuery.value.vehicle_id
  if (vehicleQuery.value.client_type) params.client_type = vehicleQuery.value.client_type
  if (vehicleQuery.value.paid_method) params.paid_method = vehicleQuery.value.paid_method
  if (vehicleQuery.value.is_paid) params.is_paid = vehicleQuery.value.is_paid
  if (vehicleQuery.value.month) params.month = vehicleQuery.value.month
  if (vehicleQuery.value.year) params.year = vehicleQuery.value.year
  if (vehicleQuery.value.dateRange) {
    params.start_date = vehicleQuery.value.dateRange[0]
    params.end_date = vehicleQuery.value.dateRange[1]
  }
  try {
    const res = await api.get('/reports/by-vehicle', { params })
    vehicleResults.value = res.data
  } catch (e) {}
}

const statusMap = { completed: '已完成', scheduled: '已排班', pending: '待排班', cancelled: '已取消' }
const confirmMap = { confirmed: '已确认', rejected: '已拒绝', pending: '待确认' }

const exportToExcel = (rows, columns, filename) => {
  const data = rows.map(r => columns.map(c => c.formatter ? c.formatter(r) : r[c.prop] ?? ''))
  const ws = XLSX.utils.aoa_to_sheet([columns.map(c => c.label), ...data])
  ws['!cols'] = columns.map(c => ({ wch: c.width || 15 }))
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
  XLSX.writeFile(wb, filename + '.xlsx')
  ElMessage.success('导出成功')
}

const exportClient = () => {
  const cols = [
    { label: '包车类型', formatter: r => r.client_type === 'company' ? '单位' : '个人', width: 10 },
    { label: '用车单位', formatter: r => r.client_type === 'company' ? (r.client_company || r.client_name) : r.client_name, width: 15 },
    { label: '联系人', prop: 'contact_name', width: 10 },
    { label: '确认情况', formatter: r => confirmMap[r.schedule_confirm_status] || '-', width: 10 },
    { label: '出发地点', prop: 'departure', width: 12 },
    { label: '目的地', prop: 'destination', width: 12 },
    { label: '车牌号', prop: 'vehicle_plate', width: 10 },
    { label: '司机', prop: 'driver_name', width: 10 },
    { label: '出车时间', prop: 'departure_time', width: 18 },
    { label: '租车费', prop: 'rental_fee', width: 10 },
    { label: '实际成本', prop: 'actual_cost', width: 10 },
    { label: '最终利润', prop: 'final_profit', width: 10 },
    { label: '状态', formatter: r => statusMap[r.status] || r.status, width: 10 },
  ]
  exportToExcel(clientTasks.value, cols, '按用车单位报表')
}

const exportDriver = () => {
  const cols = [
    { label: '包车类型', formatter: r => r.client_type === 'company' ? '单位' : '个人', width: 10 },
    { label: '用车单位', formatter: r => r.client_type === 'company' ? (r.client_company || r.client_name) : r.client_name, width: 15 },
    { label: '联系人', prop: 'contact_name', width: 10 },
    { label: '出发', prop: 'departure', width: 12 },
    { label: '目的', prop: 'destination', width: 12 },
    { label: '出车时间', prop: 'departure_time', width: 18 },
    { label: '预估人工费', prop: 'labor_fee', width: 12 },
    { label: '实际人工费', prop: 'actual_labor_fee', width: 12 },
  ]
  const allRows = driverResults.value.flatMap(ds => ds.tasks.map(t => ({ ...t, _driver: ds.driver_name })))
  const driverCols = [{ label: '司机', formatter: r => r._driver, width: 10 }, ...cols]
  exportToExcel(allRows, driverCols, '按司机报表')
}

const exportVehicle = () => {
  const cols = [
    { label: '包车类型', formatter: r => r.client_type === 'company' ? '单位' : '个人', width: 10 },
    { label: '用车单位', formatter: r => r.client_type === 'company' ? (r.client_company || r.client_name) : r.client_name, width: 15 },
    { label: '联系人', prop: 'contact_name', width: 10 },
    { label: '出发', prop: 'departure', width: 12 },
    { label: '目的', prop: 'destination', width: 12 },
    { label: '出车时间', prop: 'departure_time', width: 18 },
    { label: '租车费', prop: 'rental_fee', width: 10 },
    { label: '实际成本', prop: 'actual_cost', width: 10 },
    { label: '最终利润', prop: 'final_profit', width: 10 },
  ]
  const allRows = vehicleResults.value.flatMap(vs => vs.tasks.map(t => ({ ...t, _plate: vs.plate_number })))
  const vehicleCols = [{ label: '车牌号', formatter: r => r._plate, width: 12 }, ...cols]
  exportToExcel(allRows, vehicleCols, '按车辆报表')
}

onMounted(async () => {
  try {
    const [drvRes, vehRes] = await Promise.all([api.get('/drivers'), api.get('/vehicles')])
    allDrivers.value = drvRes.data
    allVehicles.value = vehRes.data
  } catch (e) {}
})
</script>
