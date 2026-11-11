<template>
  <div style="max-width:1100px;margin:20px auto;padding:20px">
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:18px;font-weight:bold">📋 任务汇总</span>
          <span style="color:#909399;font-size:13px">共 {{ tasks.length }} 条</span>
        </div>
      </template>
      <div v-if="groupedTasks.length">
        <div v-for="(group, gi) in groupedTasks" :key="gi" style="margin-bottom:16px">
          <div style="font-weight:600;font-size:15px;margin-bottom:6px;color:#303133">{{ group.client }}</div>
          <div v-for="(item, ii) in group.items" :key="ii" style="font-size:13px;line-height:22px;padding:4px 8px;border-bottom:1px solid #f0f0f0">
            {{ item }}
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无任务数据" />
    </el-card>
    <div style="text-align:center;margin-top:12px;color:#909399;font-size:12px">
      包车调度系统 · 任务汇总
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../utils/api'

const route = useRoute()
const tasks = ref([])

const formatTaskLine = (task) => {
  const dep = task.departure_time ? task.departure_time.slice(5).replace('-', '月') + '日-' + task.departure_time.slice(11) : ''
  const route = `${task.departure || ''}--${task.destination || ''}`
  const vehicles = (task.task_vehicles || []).map(tv => {
    const cap = tv.vehicle_capacity ? `${tv.vehicle_capacity}座车` : '车'
    const plate = tv.vehicle_plate || ''
    const drv = tv.driver_name ? `司机：${tv.driver_name} ${tv.driver_phone || ''}` : ''
    const fee = task.rental_fee ? `（车费${task.rental_fee}元）` : ''
    return `安排${cap}${plate}，${drv}${fee}`
  })
  if (!vehicles.length) {
    const drv = task.driver_name ? `司机：${task.driver_name}` : ''
    const fee = task.rental_fee ? `（车费${task.rental_fee}元）` : ''
    vehicles.push(`${drv}${fee}`)
  }
  return `${dep}，${route}，${vehicles.join('；')}`
}

const groupedTasks = computed(() => {
  const groups = {}
  for (const t of tasks.value) {
    const client = t.client_company || t.client_name || '未知'
    if (!groups[client]) groups[client] = { client, items: [] }
    groups[client].items.push(formatTaskLine(t))
  }
  return Object.values(groups)
})

onMounted(async () => {
  try {
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
  } catch (e) {}
})
</script>
