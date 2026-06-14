<template>
  <div>
    <el-card class="page-card">
      <template #header>
        <div class="page-header">
          <div class="page-title">
            <el-icon :size="20"><DataAnalysis /></el-icon>
            <span>报表管理</span>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 按用车单位查询 -->
        <el-tab-pane label="按用车单位查询" name="client">
          <el-form :inline="true" style="margin-bottom:15px">
            <el-form-item label="包车类型">
              <el-select v-model="clientQuery.client_type" placeholder="全部" clearable style="width:120px">
                <el-option label="个人包车" value="personal" />
                <el-option label="单位包车" value="company" />
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
            <el-table-column label="确认情况" width="90" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.schedule_confirm_status === 'confirmed'" type="success" size="small">已确认</el-tag>
                <el-tag v-else-if="row.schedule_confirm_status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
                <el-tag v-else-if="row.schedule_confirm_status === 'pending'" type="warning" size="small">待确认</el-tag>
                <span v-else style="color:#c0c4cc">-</span>
              </template>
            </el-table-column>
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
                <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'scheduled' ? 'primary' : 'warning'">
                  {{ row.status === 'completed' ? '已完成' : row.status === 'scheduled' ? '已排班' : '待排班' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 按司机查询 -->
        <el-tab-pane label="按司机查询" name="driver">
          <el-form :inline="true" style="margin-bottom:15px">
            <el-form-item label="包车类型">
              <el-select v-model="driverQuery.client_type" placeholder="全部" clearable style="width:120px">
                <el-option label="个人包车" value="personal" />
                <el-option label="单位包车" value="company" />
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
              <el-table-column label="确认情况" width="90" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.schedule_confirm_status === 'confirmed'" type="success" size="small">已确认</el-tag>
                  <el-tag v-else-if="row.schedule_confirm_status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
                  <el-tag v-else-if="row.schedule_confirm_status === 'pending'" type="warning" size="small">待确认</el-tag>
                  <span v-else style="color:#c0c4cc">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="departure" label="出发" min-width="80" />
              <el-table-column prop="destination" label="目的" min-width="80" />
              <el-table-column prop="departure_time" label="出车时间" min-width="150" />
              <el-table-column prop="labor_fee" label="预估人工费" width="100" align="right" />
              <el-table-column prop="actual_labor_fee" label="实际人工费" width="100" align="right" />
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 按车辆查询 -->
        <el-tab-pane label="按车辆查询" name="vehicle">
          <el-form :inline="true" style="margin-bottom:15px">
            <el-form-item label="包车类型">
              <el-select v-model="vehicleQuery.client_type" placeholder="全部" clearable style="width:120px">
                <el-option label="个人包车" value="personal" />
                <el-option label="单位包车" value="company" />
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
              <el-table-column label="确认情况" width="90" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.schedule_confirm_status === 'confirmed'" type="success" size="small">已确认</el-tag>
                  <el-tag v-else-if="row.schedule_confirm_status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
                  <el-tag v-else-if="row.schedule_confirm_status === 'pending'" type="warning" size="small">待确认</el-tag>
                  <span v-else style="color:#c0c4cc">-</span>
                </template>
              </el-table-column>
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
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const activeTab = ref('client')

const clientQuery = ref({ client: '', client_type: '', month: '', year: '', dateRange: null })
const clientTasks = ref([])
const clientSummary = ref(null)

const driverQuery = ref({ driver_id: null, client_type: '', month: '', year: '', dateRange: null })
const driverResults = ref([])
const allDrivers = ref([])

const vehicleQuery = ref({ vehicle_id: null, client_type: '', month: '', year: '', dateRange: null })
const vehicleResults = ref([])
const allVehicles = ref([])

const queryByClient = async () => {
  const params = { client: clientQuery.value.client }
  if (clientQuery.value.client_type) params.client_type = clientQuery.value.client_type
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

onMounted(async () => {
  try {
    const [drvRes, vehRes] = await Promise.all([api.get('/drivers'), api.get('/vehicles')])
    allDrivers.value = drvRes.data
    allVehicles.value = vehRes.data
  } catch (e) {}
})
</script>
