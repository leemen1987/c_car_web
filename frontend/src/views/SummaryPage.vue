<template>
  <div style="max-width:1100px;margin:20px auto;padding:20px">
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:18px;font-weight:bold">📋 任务汇总</span>
          <span style="color:#909399;font-size:13px">共 {{ tasks.length }} 条</span>
        </div>
      </template>
      <el-table v-if="tasks.length" :data="tasks" border stripe style="width:100%" :header-cell-style="{ whiteSpace: 'nowrap' }">
        <el-table-column prop="task_no" label="编号" width="130" />
        <el-table-column label="用车方" min-width="110">
          <template #default="{ row }">{{ row.client_company || row.client_name }}</template>
        </el-table-column>
        <el-table-column label="出发→目的" min-width="120">
          <template #default="{ row }">{{ row.departure }}→{{ row.destination }}</template>
        </el-table-column>
        <el-table-column prop="departure_time" label="出车" width="110" />
        <el-table-column prop="return_time" label="回程" width="110" />
        <el-table-column prop="rental_days" label="天数" width="60" align="center" />
        <el-table-column prop="rental_fee" label="租车费" width="90" align="right" />
        <el-table-column label="车牌/司机" min-width="120">
          <template #default="{ row }">
            <div v-if="row.task_vehicles && row.task_vehicles.length">
              <div v-for="(tv, i) in row.task_vehicles" :key="i" style="font-size:12px">
                {{ tv.vehicle_plate }} {{ tv.driver_name }}
              </div>
            </div>
            <template v-else>{{ row.vehicle_plate }} {{ row.driver_name }}</template>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'completed'" type="success" size="small">已完成</el-tag>
            <el-tag v-else-if="row.status === 'scheduled'" type="primary" size="small">已排班</el-tag>
            <el-tag v-else-if="row.status === 'cancelled'" type="info" size="small">已取消</el-tag>
            <el-tag v-else type="warning" size="small">待排班</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无任务数据" />
    </el-card>
    <div style="text-align:center;margin-top:12px;color:#909399;font-size:12px">
      包车调度系统 · 任务汇总
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../utils/api'

const route = useRoute()
const tasks = ref([])

onMounted(async () => {
  try {
    // 从 hash 参数获取筛选条件（发送时序列化的）
    const hash = route.hash.replace('#', '')
    const params = {}
    if (hash) {
      for (const kv of hash.split('&')) {
        const [k, v] = kv.split('=')
        if (k && v) params[decodeURIComponent(k)] = decodeURIComponent(v)
      }
    }
    if (!params.status) params.status = 'scheduled'
    const res = await api.get('/tasks/filtered', { params })
    tasks.value = res.data
  } catch (e) {
    // 公开页面可能未登录，显示空
  }
})
</script>
