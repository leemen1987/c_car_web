<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:18px;font-weight:bold">📋 客户确认管理</span>
          <el-button @click="loadConfirmations" :loading="loading">刷新</el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div style="margin-bottom:16px;display:flex;gap:12px;flex-wrap:wrap">
        <el-select v-model="filterStatus" placeholder="确认状态" clearable style="width:120px" @change="loadConfirmations">
          <el-option label="待确认" value="pending" />
          <el-option label="已确认" value="confirmed" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        <el-input v-model="filterCustomer" placeholder="客户名称" clearable style="width:150px" @change="loadConfirmations" />
      </div>

      <!-- 统计信息 -->
      <div style="margin-bottom:16px;display:flex;gap:20px">
        <el-tag type="info">总数: {{ confirmations.length }}</el-tag>
        <el-tag type="warning">待确认: {{ confirmations.filter(c => c.confirm_status === 'pending').length }}</el-tag>
        <el-tag type="success">已确认: {{ confirmations.filter(c => c.confirm_status === 'confirmed').length }}</el-tag>
        <el-tag type="danger">已拒绝: {{ confirmations.filter(c => c.confirm_status === 'rejected').length }}</el-tag>
      </div>

      <!-- 数据表格 -->
      <el-table :data="filteredConfirmations" border stripe style="width:100%" v-loading="loading" max-height="600">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="task_no" label="任务编号" width="150" />
        <el-table-column label="客户信息" min-width="180">
          <template #default="{ row }">
            <div>
              <div style="font-weight:600">{{ row.customer_name || '-' }}</div>
              <div style="color:#909399;font-size:12px">{{ row.customer_phone || '-' }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="wx_userid" label="企业微信ID" width="140">
          <template #default="{ row }">
            <span v-if="row.wx_userid">{{ row.wx_userid }}</span>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="联系人" width="100" />
        <el-table-column label="出发地 → 目的地" min-width="180">
          <template #default="{ row }">
            <span>{{ row.departure || '-' }} → {{ row.destination || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="departure_time" label="出车时间" width="150" />
        <el-table-column label="确认状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.confirm_status === 'pending'" type="warning" size="small">待确认</el-tag>
            <el-tag v-else-if="row.confirm_status === 'confirmed'" type="success" size="small">已确认</el-tag>
            <el-tag v-else-if="row.confirm_status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confirm_time" label="确认时间" width="160">
          <template #default="{ row }">
            <span v-if="row.confirm_time">{{ row.confirm_time }}</span>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="confirm_ip" label="确认IP" width="130">
          <template #default="{ row }">
            <span v-if="row.confirm_ip">{{ row.confirm_ip }}</span>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="confirm_remark" label="备注" min-width="150">
          <template #default="{ row }">
            <span v-if="row.confirm_remark">{{ row.confirm_remark }}</span>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <div style="display:flex;flex-wrap:nowrap;gap:4px;white-space:nowrap">
              <el-button type="primary" size="small" @click="showDetail(row)">详情</el-button>
              <el-button v-if="row.confirm_status === 'pending'" type="warning" size="small" @click="copyLink(row)">复制链接</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && filteredConfirmations.length === 0" style="text-align:center;padding:40px;color:#909399">
        暂无确认记录
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="确认详情" :width="isMobile ? '100%' : '860px'" :fullscreen="isMobile">
      <div v-if="currentDetail" style="padding:0 20px">
        <el-descriptions :column="isMobile ? 1 : 2" border size="default">
          <el-descriptions-item label="任务编号">{{ currentDetail.task_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="客户名称">{{ currentDetail.customer_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ currentDetail.customer_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="确认状态">
            <el-tag v-if="currentDetail.confirm_status === 'pending'" type="warning">待确认</el-tag>
            <el-tag v-else-if="currentDetail.confirm_status === 'confirmed'" type="success">已确认</el-tag>
            <el-tag v-else-if="currentDetail.confirm_status === 'rejected'" type="danger">已拒绝</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="出发地">{{ currentDetail.departure || '-' }}</el-descriptions-item>
          <el-descriptions-item label="目的地">{{ currentDetail.destination || '-' }}</el-descriptions-item>
          <el-descriptions-item label="出车时间">{{ currentDetail.departure_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="确认时间">{{ currentDetail.confirm_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="确认IP">{{ currentDetail.confirm_ip || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ currentDetail.confirm_remark || '-' }}</el-descriptions-item>
          <el-descriptions-item label="确认链接" :span="2">
            <el-link v-if="currentDetail.confirm_token" type="primary" @click="copyToClipboard(getConfirmUrl(currentDetail.confirm_token))">
              {{ getConfirmUrl(currentDetail.confirm_token) }}
            </el-link>
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button v-if="currentDetail && currentDetail.confirm_status === 'pending'" type="primary" @click="copyLink(currentDetail)">复制确认链接</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const isMobile = ref(false)
const checkMobile = () => { isMobile.value = window.innerWidth <= 768 }
onMounted(() => { checkMobile(); window.addEventListener('resize', checkMobile) })
onUnmounted(() => window.removeEventListener('resize', checkMobile))

const loading = ref(false)
const confirmations = ref([])
const filterStatus = ref('')
const filterCustomer = ref('')
const detailVisible = ref(false)
const currentDetail = ref(null)

const filteredConfirmations = computed(() => {
  let result = confirmations.value
  if (filterStatus.value) {
    result = result.filter(c => c.confirm_status === filterStatus.value)
  }
  if (filterCustomer.value) {
    const keyword = filterCustomer.value.toLowerCase()
    result = result.filter(c => (c.customer_name || '').toLowerCase().includes(keyword))
  }
  return result
})

const loadConfirmations = async () => {
  loading.value = true
  try {
    const res = await api.get('/confirmations?per_page=100')
    if (res.code === 200) {
      confirmations.value = res.data?.items || []
    }
  } catch (e) {
    console.error('加载确认记录失败', e)
  } finally {
    loading.value = false
  }
}

const getConfirmUrl = (token) => {
  return `${window.location.origin}/confirm/${token}`
}

const showDetail = (row) => {
  currentDetail.value = row
  detailVisible.value = true
}

const copyLink = (row) => {
  const url = getConfirmUrl(row.confirm_token)
  copyToClipboard(url)
}

const copyToClipboard = (text) => {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      ElMessage.success('链接已复制')
    }).catch(() => {
      fallbackCopy(text)
    })
  } else {
    fallbackCopy(text)
  }
}

const fallbackCopy = (text) => {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  try {
    document.execCommand('copy')
    ElMessage.success('链接已复制')
  } catch (e) {
    ElMessage.error('复制失败，请手动复制')
  }
  document.body.removeChild(textarea)
}

onMounted(() => {
  loadConfirmations()
})
</script>

<style scoped>
:deep(.el-table .el-table__header-wrapper th) {
  white-space: nowrap !important;
}
</style>
