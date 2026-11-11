<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div style="display:flex;gap:8px;align-items:center">
            <span style="font-size:18px;font-weight:bold">📋 客户确认管理</span>
            <el-tag type="info">共 {{ filteredTasks.length }} 条</el-tag>
          </div>
          <div style="display:flex;gap:8px;align-items:center">
            <el-button type="primary" @click="openSendDialog" :disabled="!filteredTasks.length">企微客户</el-button>
            <el-button type="success" @click="openExportDialog" :disabled="!filteredTasks.length">导出Excel</el-button>
            <el-button type="warning" @click="openImageDialog" :disabled="!filteredTasks.length">生成图片</el-button>
            <el-button @click="copyTasks">复制任务</el-button>
            <el-button @click="copySummaryLink">复制链接</el-button>
          </div>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div style="margin-bottom:12px;display:flex;gap:10px;flex-wrap:wrap;align-items:center">
        <el-select v-model="filter.status" placeholder="状态" clearable style="width:110px" @change="loadTasks">
          <el-option label="待排班" value="pending" />
          <el-option label="已排班" value="scheduled" />
          <el-option label="已完成" value="completed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
        <el-date-picker v-model="filter.dateRange" type="daterange" format="YYYY-MM-DD" value-format="YYYY-MM-DD"
          start-placeholder="开始日期" end-placeholder="结束日期" clearable class="import-date-range" @change="loadTasks" />
        <el-select v-model="filter.client" placeholder="用车方" clearable filterable style="width:160px" @change="loadTasks">
          <el-option v-for="c in clientOptions" :key="c" :label="c" :value="c" />
        </el-select>
        <el-select v-model="filter.company" placeholder="车属单位" clearable multiple style="width:180px" @change="loadTasks">
          <el-option v-for="c in companyOptions" :key="c" :label="c" :value="c" />
        </el-select>
        <el-button type="primary" @click="loadTasks">查询</el-button>
        <div style="margin-left:auto;display:flex;gap:8px">
          <el-tag type="warning" v-if="tasksPending > 0">待排班: {{ tasksPending }}</el-tag>
          <el-tag type="primary" v-if="tasksScheduled > 0">已排班: {{ tasksScheduled }}</el-tag>
          <el-tag type="success" v-if="tasksCompleted > 0">已完成: {{ tasksCompleted }}</el-tag>
        </div>
      </div>

      <!-- 任务表格 -->
      <el-table :data="filteredTasks" border stripe style="width:100%" max-height="500"
        :header-cell-style="{ whiteSpace: 'nowrap' }" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="40" />
        <el-table-column prop="departure_time" label="出车时间" width="130" />
        <el-table-column prop="departure" label="出发地点" min-width="110" />
        <el-table-column prop="destination" label="目的地" min-width="110" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'completed'" type="success" size="small">已完成</el-tag>
            <el-tag v-else-if="row.status === 'scheduled'" type="primary" size="small">已排班</el-tag>
            <el-tag v-else-if="row.status === 'cancelled'" type="info" size="small">已取消</el-tag>
            <el-tag v-else type="warning" size="small">待排班</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="用车方" min-width="100">
          <template #default="{ row }">{{ row.client_company || row.client_name }}</template>
        </el-table-column>
        <el-table-column label="车辆/司机" min-width="160">
          <template #default="{ row }">
            <div v-if="row.task_vehicles && row.task_vehicles.length">
              <div v-for="(tv, i) in row.task_vehicles" :key="i" style="font-size:12px">
                {{ tv.vehicle_capacity ? tv.vehicle_capacity + '座' : '' }}{{ tv.vehicle_plate }}
                <template v-if="tv.driver_name">｜司机：{{ tv.driver_name }} {{ tv.driver_phone }}</template>
                <template v-if="row.rental_fee">（车费{{ row.rental_fee }}元）</template>
              </div>
            </div>
            <template v-else>
              {{ row.vehicle_plate }}
              <template v-if="row.driver_name">｜司机：{{ row.driver_name }}</template>
              <template v-if="row.rental_fee">（车费{{ row.rental_fee }}元）</template>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 企微发送弹窗（选收件人） -->
    <el-dialog v-model="sendDialogVisible" title="企微客户" width="500px">
      <div style="margin-bottom:8px;color:#909399;font-size:13px">选择收件人：</div>
      <el-select v-model="sendTargets" multiple filterable placeholder="选择企微用户/外部联系人" style="width:100%">
        <el-option v-for="u in wxUsers" :key="u.id" :label="u.name + ' (' + u.id + ')'" :value="u.id" />
        <el-option v-for="(c, ci) in wxContacts" :key="'ext_' + ci + '_' + c.external_userid" :label="c.name + ' (外部)'" :value="'ext_' + ci + '_' + c.external_userid" />
      </el-select>
      <div v-if="sendTargets.length" style="margin-top:8px;color:#67c23a;font-size:12px">
        已选 {{ sendTargets.length }} 位收件人
      </div>
      <template #footer>
        <el-button @click="sendDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="sendBatch" :disabled="!sendTargets.length">发送</el-button>
      </template>
    </el-dialog>

    <!-- 图片预览 -->
    <el-dialog v-model="imageResultVisible" title="表格图片" width="600px">
      <img v-if="imageDataUrl" :src="imageDataUrl" style="width:100%;border:1px solid #e2e8f0;border-radius:6px" />
      <template #footer>
        <el-button @click="imageResultVisible = false">关闭</el-button>
        <el-button @click="downloadImage">下载图片</el-button>
        <el-button v-if="sendTargets.length" type="success" @click="sendImage">发企微</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as XLSX from 'xlsx-js-style'
import api from '../utils/api'

const tasks = ref([])
const selectedRows = ref([])
const filter = ref({ status: 'scheduled', dateRange: null, client: '', company: [] })
const clientOptions = ref([])
const companyOptions = ref([])
const wxUsers = ref([])
const wxContacts = ref([])


const sendDialogVisible = ref(false)
const sendTargets = ref([])
const imagePreview = ref(null)
const imageDataUrl = ref('')
const imageResultVisible = ref(false)

const filteredTasks = computed(() => tasks.value)
const targetTasks = computed(() => selectedRows.value.length ? selectedRows.value : filteredTasks.value)
const tasksPending = computed(() => tasks.value.filter(t => t.status === 'pending').length)
const tasksScheduled = computed(() => tasks.value.filter(t => t.status === 'scheduled').length)
const tasksCompleted = computed(() => tasks.value.filter(t => t.status === 'completed').length)

const onSelectionChange = (rows) => { selectedRows.value = rows }

const loadTasks = async () => {
  const params = {}
  if (filter.value.status) params.status = filter.value.status
  if (filter.value.client) params.client = filter.value.client
  if (filter.value.company.length) params.company = filter.value.company.join(',')
  if (filter.value.dateRange && filter.value.dateRange.length === 2) {
    params.start_date = filter.value.dateRange[0]
    params.end_date = filter.value.dateRange[1]
  }
  try {
    const res = await api.get('/tasks/filtered', { params })
    tasks.value = res.data
  } catch (e) {}
}

const openSendDialog = () => { sendDialogVisible.value = true }
const openExportDialog = () => { exportExcel() }
const openImageDialog = async () => {
  imageDataUrl.value = await generateImage()
  if (!imageDataUrl.value) { ElMessage.error('图片生成失败'); return }
  imageResultVisible.value = true
}

const sendBatch = async () => {
  try {
    const res = await api.post('/confirmations/send-batch', {
      task_ids: targetTasks.value.map(t => t.id),
      columns: [],
      targets: sendTargets.value.map(id => {
        if (id.startsWith('ext_')) return { type: 'external', id: id.split('_').slice(2).join('_') }
        return { type: 'user', id }
      })
    })
    ElMessage.success(`已创建 ${res.data.sent} 条群发任务（需在企微APP确认发送），失败 ${res.data.failed} 条`)
    sendDialogVisible.value = false
  } catch (e) {}
}

const exportExcel = () => {
  const formatLine = (task) => {
    const dt = task.departure_time || ''
    const dep = dt ? `${parseInt(dt.slice(5, 7))}月${parseInt(dt.slice(8, 10))}日-${dt.slice(11, 16)}` : ''
    const route = `${task.departure || ''}--${task.destination || ''}`
    const vehicles = (task.task_vehicles || []).map(tv => {
      const capRaw = tv.vehicle_capacity || ''
      const cap = capRaw ? (capRaw.includes('座') ? capRaw + '车' : capRaw + '座车') : '车'
      const drv = tv.driver_name ? `司机：${tv.driver_name} ${tv.driver_phone || ''}` : ''
      const fee = task.rental_fee ? `（车费${task.rental_fee}元）` : ''
      return `安排${cap}${tv.vehicle_plate || ''}，${drv}${fee}`
    })
    if (!vehicles.length) {
      const drv = task.driver_name ? `司机：${task.driver_name}` : ''
      const fee = task.rental_fee ? `（车费${task.rental_fee}元）` : ''
      vehicles.push(`${drv}${fee}`)
    }
    return `${dep}，${route}，${vehicles.join('；')}`
  }
  const header = ['用车方', '内容']
  const rows = targetTasks.value.map(t => [t.client_company || t.client_name || '', formatLine(t)])
  const ws = XLSX.utils.aoa_to_sheet([header, ...rows])
  ws['!cols'] = header.map(() => ({ wch: 15 }))
  // 样式
  for (let c = 0; c < header.length; c++) {
    const cell = ws[XLSX.utils.encode_cell({ r: 0, c })]
    if (cell) cell.s = { font: { bold: true, size: 11 }, fill: { fgColor: { rgb: 'F5F7FA' } }, border: { top: { style: 'thin' }, bottom: { style: 'thin' }, left: { style: 'thin' }, right: { style: 'thin' } } }
    for (let r = 1; r <= rows.length; r++) {
      const cell2 = ws[XLSX.utils.encode_cell({ r, c })]
      if (cell2) cell2.s = { border: { top: { style: 'thin' }, bottom: { style: 'thin' }, left: { style: 'thin' }, right: { style: 'thin' } } }
    }
  }
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '任务通知')
  XLSX.writeFile(wb, getExportFileName('xlsx'))
  ElMessage.success('Excel已下载')
  }

const generateImage = () => {
  return new Promise((resolve) => {
    // 创建隐藏 div 渲染统一格式
    const div = document.createElement('div')
    div.style.cssText = 'position:fixed;left:-9999px;top:0;background:#fff;padding:20px;font-size:13px;line-height:24px;font-family:Microsoft YaHei,sans-serif;max-width:600px'
    const groups = {}
    for (const t of targetTasks.value) {
      const client = t.client_company || t.client_name || ''
      if (!groups[client]) groups[client] = []
      const dt = t.departure_time || ''
      const dep = dt ? `${parseInt(dt.slice(5, 7))}月${parseInt(dt.slice(8, 10))}日-${dt.slice(11, 16)}` : ''
      const route = `${t.departure || ''}--${t.destination || ''}`
      const vehicles = (t.task_vehicles || []).map(tv => {
        const capRaw = tv.vehicle_capacity || ''
        const cap = capRaw ? (capRaw.includes('座') ? capRaw + '车' : capRaw + '座车') : '车'
        const drv = tv.driver_name ? `司机：${tv.driver_name} ${tv.driver_phone || ''}` : ''
        const fee = t.rental_fee ? `（车费${t.rental_fee}元）` : ''
        return `安排${cap}${tv.vehicle_plate || ''}，${drv}${fee}`
      })
      if (!vehicles.length) {
        const drv = t.driver_name ? `司机：${t.driver_name}` : ''
        const fee = t.rental_fee ? `（车费${t.rental_fee}元）` : ''
        vehicles.push(`${drv}${fee}`)
      }
      groups[client].push(`${dep}，${route}，${vehicles.join('；')}`)
    }
    for (const [client, items] of Object.entries(groups)) {
      const h = document.createElement('div')
      h.style.cssText = 'font-weight:600;font-size:15px;margin:10px 0 4px'
      h.textContent = client
      div.appendChild(h)
      for (const item of items) {
        const d = document.createElement('div')
        d.style.cssText = 'padding:3px 0;border-bottom:1px solid #f0f0f0'
        d.textContent = item
        div.appendChild(d)
      }
    }
    document.body.appendChild(div)
    import('html2canvas').then(({ default: html2canvas }) => {
      html2canvas(div, { scale: 2, backgroundColor: '#fff' }).then(canvas => {
        document.body.removeChild(div)
        resolve(canvas.toDataURL('image/png'))
      }).catch(() => { document.body.removeChild(div); resolve('') })
    }).catch(() => { document.body.removeChild(div); resolve('') })
  })
}

const downloadImage = async () => {
  if (!imageDataUrl.value) {
    imageDataUrl.value = await generateImage()
    if (!imageDataUrl.value) { ElMessage.error('图片生成失败（需安装html2canvas）'); return }
  }
  const a = document.createElement('a')
  a.href = imageDataUrl.value
  a.download = getExportFileName('png')
  a.click()
  ElMessage.success('图片已下载')
}

const getExportFileName = (ext) => {
  const parts = []
  if (filter.value.company.length) parts.push(filter.value.company.join('+'))
  if (filter.value.client) parts.push(filter.value.client)
  const first = targetTasks.value[0]
  const dateStr = first && first.departure_time ? first.departure_time.slice(0, 10) : new Date().toISOString().slice(0, 10)
  if (!parts.length) parts.push('任务通知')
  return parts.join('_') + '_' + dateStr + '.' + ext
}



const sendImage = async () => {
  if (!imageDataUrl.value) {
    imageDataUrl.value = await generateImage()
    if (!imageDataUrl.value) { ElMessage.error('图片生成失败'); return }
  }
  try {
    const b64 = imageDataUrl.value.split(',')[1]
    const upRes = await api.post('/wechat/upload-image', { image: b64 })
    await api.post('/wechat/send-image', {
      media_id: upRes.data.media_id,
      targets: sendTargets.value.map(id => {
        if (id.startsWith('ext_')) return { type: 'external', id: id.split('_').slice(2).join('_') }
        return { type: 'user', id }
      })
    })
    ElMessage.success('图片已发送')
    sendDialogVisible.value = false
    imageResultVisible.value = false
  } catch (e) {}
}

const copyTasks = async () => {
  const groups = {}
  for (const t of targetTasks.value) {
    const client = t.client_company || t.client_name || ''
    if (!groups[client]) groups[client] = []
    const dt = t.departure_time || ''
    const dep = dt ? `${parseInt(dt.slice(5, 7))}月${parseInt(dt.slice(8, 10))}日-${dt.slice(11, 16)}` : ''
    const route = `${t.departure || ''}--${t.destination || ''}`
    const vehicles = (t.task_vehicles || []).map(tv => {
      const capRaw = tv.vehicle_capacity || ''
      const cap = capRaw ? (capRaw.includes('座') ? capRaw + '车' : capRaw + '座车') : '车'
      const drv = tv.driver_name ? `司机：${tv.driver_name} ${tv.driver_phone || ''}` : ''
      const fee = t.rental_fee ? `（车费${t.rental_fee}元）` : ''
      return `安排${cap}${tv.vehicle_plate || ''}，${drv}${fee}`
    })
    if (!vehicles.length) {
      const drv = t.driver_name ? `司机：${t.driver_name}` : ''
      const fee = t.rental_fee ? `（车费${t.rental_fee}元）` : ''
      vehicles.push(`${drv}${fee}`)
    }
    groups[client].push(`${dep}，${route}，${vehicles.join('；')}`)
  }
  const lines = []
  for (const [client, items] of Object.entries(groups)) {
    lines.push(client)
    items.forEach(l => lines.push(l))
  }
  const text = lines.join('\n')
  let ok = false
  if (navigator.clipboard && window.isSecureContext) {
    try { await navigator.clipboard.writeText(text); ok = true } catch (e) {}
  }
  if (!ok) {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0'
    document.body.appendChild(ta)
    ta.focus()
    ta.select()
    try { ok = document.execCommand('copy') } catch (e) { ok = false }
    document.body.removeChild(ta)
  }
  if (ok) ElMessage.success('任务信息已复制到剪贴板')
  else ElMessage.warning('复制失败，请手动复制')
}

const copySummaryLink = async () => {
  try {
    // 编码筛选条件到 hash
    const hashParts = []
    if (filter.value.status) hashParts.push('status=' + encodeURIComponent(filter.value.status))
    if (filter.value.client) hashParts.push('client=' + encodeURIComponent(filter.value.client))
    if (filter.value.company.length) hashParts.push('company=' + encodeURIComponent(filter.value.company.join(',')))
    if (filter.value.dateRange && filter.value.dateRange.length === 2) {
      hashParts.push('start_date=' + encodeURIComponent(filter.value.dateRange[0]))
      hashParts.push('end_date=' + encodeURIComponent(filter.value.dateRange[1]))
    }
    const queryParams = hashParts.join('&')
    const res = await api.get('/confirmations/summary-link' + (queryParams ? '?' + queryParams : ''))
    const url = res.data.full_url
    let ok = false
    if (navigator.clipboard && window.isSecureContext) {
      try { await navigator.clipboard.writeText(url); ok = true } catch (e) {}
    }
    if (!ok) {
      const ta = document.createElement('textarea')
      ta.value = url
      ta.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0'
      document.body.appendChild(ta)
      ta.focus()
      ta.select()
      try { ok = document.execCommand('copy') } catch (e) { ok = false }
      document.body.removeChild(ta)
    }
    if (ok) { ElMessage.success('链接已复制') }
    else { ElMessageBox.alert(url, '请手动复制链接', { confirmButtonText: '关闭' }) }
  } catch (e) {
    ElMessage.error('复制失败')
  }
}

onMounted(async () => {
  loadTasks()
  try {
    const [cliRes, vehRes] = await Promise.all([api.get('/clients'), api.get('/vehicles')])
    const names = new Set()
    for (const c of (cliRes.data || [])) { if (c.name) names.add(c.name) }
    for (const v of (vehRes.data || [])) { if (v.company) names.add(v.company) }
    clientOptions.value = [...names].sort()
    const companies = new Set()
    for (const v of (vehRes.data || [])) { if (v.company) companies.add(v.company) }
    companyOptions.value = [...companies].sort()
  } catch (e) {}
  try {
    const res = await api.get('/users')
    wxUsers.value = (res.data || []).filter(u => u.wx_sender).map(u => ({ id: u.wx_sender, name: u.username }))
  } catch (e) {}
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const sender = user.wx_sender || ''
    if (sender) {
      const res = await api.get('/wx-external-contacts', { params: { sender } })
      wxContacts.value = res.data || []
    }
  } catch (e) {}
})
</script>

<style scoped>
:deep(.import-date-range) {
  width: 220px !important;
  max-width: 220px !important;
}
:deep(.import-date-range .el-range-input) {
  font-size: 12px;
  width: 72px !important;
  min-width: 60px !important;
}
:deep(.import-date-range .el-range-separator) {
  width: 20px !important;
  padding: 0 !important;
}
</style>
