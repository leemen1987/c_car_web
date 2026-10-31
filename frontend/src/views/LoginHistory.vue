<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:18px;font-weight:bold">历史操作</span>
          <div style="display:flex;gap:8px;align-items:center">
            <el-date-picker v-model="dateRange" type="daterange" format="YYYY-MM-DD" value-format="YYYY-MM-DD"
              start-placeholder="开始日期" end-placeholder="结束日期" clearable style="width:240px" />
            <el-select v-model="query.username" placeholder="用户名" clearable filterable style="width:140px">
              <el-option v-for="u in userNames" :key="u" :label="u" :value="u" />
            </el-select>
            <el-select v-model="query.action" placeholder="操作类型" clearable style="width:120px">
              <el-option label="登录" value="login" />
              <el-option label="登出" value="logout" />
            </el-select>
            <el-button type="primary" @click="loadLogs">查询</el-button>
            <span style="color:#909399;font-size:13px">共 {{ total }} 条</span>
          </div>
        </div>
      </template>

      <el-table :data="logs" border stripe style="width:100%" :max-height="tableHeight">
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.action === 'login' ? 'success' : 'info'" size="small">
              {{ row.action === 'login' ? '登录' : '登出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP地址" width="150" />
        <el-table-column prop="user_agent" label="浏览器" min-width="200" show-overflow-tooltip />
      </el-table>

      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top:15px;justify-content:flex-end"
        @current-change="loadLogs"
        @size-change="loadLogs"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import api from '../utils/api'

const logs = ref([])
const total = ref(0)
const dateRange = ref(null)
const userNames = ref([])
const query = ref({ username: '', action: '', page: 1, page_size: 50 })

const tableHeight = ref(400)
const updateTableHeight = () => {
  const el = document.querySelector('.el-card')
  const top = el ? el.getBoundingClientRect().top : 200
  tableHeight.value = Math.max(300, window.innerHeight - top - 140)
}

const loadLogs = async () => {
  const params = {
    page: query.value.page,
    page_size: query.value.page_size
  }
  if (query.value.username) params.username = query.value.username
  if (query.value.action) params.action = query.value.action
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  try {
    const res = await api.get('/login-logs', { params })
    logs.value = res.data.list
    total.value = res.data.total
  } catch (e) {}
}

onMounted(() => {
  updateTableHeight()
  window.addEventListener('resize', updateTableHeight)
  loadLogs()
  // 收集用户名选项
  api.get('/login-logs', { params: { page: 1, page_size: 500 } }).then(res => {
    const names = new Set()
    for (const l of (res.data.list || [])) {
      if (l.username) names.add(l.username)
    }
    userNames.value = [...names].sort()
  }).catch(() => {})
})

onUnmounted(() => {
  window.removeEventListener('resize', updateTableHeight)
})
</script>
