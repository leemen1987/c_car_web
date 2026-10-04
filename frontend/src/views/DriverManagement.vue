<template>
  <div>
    <el-card class="page-card">
      <template #header>
        <div class="page-header">
          <div class="page-title">
            <el-icon :size="20"><User /></el-icon>
            <span>司机管理</span>
          </div>
          <div style="display:flex;align-items:center;gap:12px">
            <span v-if="settlementRange" style="color:#909399;font-size:13px">结算周期：{{ settlementRange }}</span>
            <el-button type="primary" @click="showAdd">
              <el-icon><Plus /></el-icon>
              <span style="margin-left:4px">添加司机</span>
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="driversWithStats" stripe style="width:100%" row-key="id">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div style="padding:12px 20px">
              <div v-if="row._stats && row._stats.tasks.length" style="margin-bottom:8px">
                <el-table :data="row._stats.tasks" border size="small" max-height="300">
                  <el-table-column type="index" label="序号" width="55" align="center" />
                  <el-table-column prop="departure_time" label="出车时间" width="145" />
                  <el-table-column label="路线" min-width="180">
                    <template #default="{ row: t }">{{ t.departure }} → {{ t.destination }}</template>
                  </el-table-column>
                  <el-table-column prop="client_name" label="用车单位" min-width="100" />
                  <el-table-column prop="labor_fee" label="预估人工费" width="100" align="right" />
                  <el-table-column prop="actual_labor_fee" label="实际人工费" width="100" align="right" />
                  <el-table-column label="状态" width="80" align="center">
                    <template #default="{ row: t }">
                      <el-tag :type="t.status === 'completed' ? 'success' : 'primary'" size="small">
                        {{ t.status === 'completed' ? '已完成' : '已排班' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
                <div style="margin-top:8px;text-align:right;color:#606266;font-size:13px">
                  共 {{ row._stats.task_count }} 个任务，合计 <strong style="color:#409eff">¥{{ row._stats.total_fee.toFixed(2) }}</strong>
                </div>
              </div>
              <el-empty v-else description="结算周期内无任务" :image-size="60" />
            </div>
          </template>
        </el-table-column>
        <el-table-column type="index" label="ID" width="60" align="center" />
        <el-table-column prop="name" label="姓名" min-width="120" />
        <el-table-column prop="phone" label="手机号码" min-width="140" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'available' ? 'success' : row.status === 'busy' ? 'warning' : 'info'">
              {{ row.status === 'available' ? '空闲' : row.status === 'busy' ? '忙碌' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="本月结算" width="120" align="right">
          <template #default="{ row }">
            <span :style="{ fontWeight: 600, color: row._stats?.total_fee > 0 ? '#409eff' : '#c0c4cc' }">
              ¥{{ (row._stats?.total_fee || 0).toFixed(0) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="240" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showEdit(row)">编辑</el-button>
            <el-button type="info" size="small" plain @click="openHistory(row)">历史</el-button>
            <el-popconfirm title="确认删除?" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑司机' : '添加司机'" width="450px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="姓名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="手机号码">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width:100%">
            <el-option label="空闲" value="available" />
            <el-option label="忙碌" value="busy" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 历史任务弹窗 -->
    <el-dialog v-model="historyVisible" :title="`${historyDriver?.name || ''} - 历史任务与结算`" width="960px" top="5vh">
      <div v-if="historyData">
        <!-- 结算月份选择 -->
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;padding:10px 14px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0">
          <span style="font-size:13px;color:#606266">结算月份：</span>
          <el-select v-model="historyMonth" style="width:200px" @change="loadHistory(1)">
            <el-option label="全部历史" value="" />
            <el-option v-for="m in historyData.available_months" :key="m" :label="`${m}（结算周期至${m}-25）`" :value="m" />
          </el-select>
          <el-button type="primary" size="small" @click="loadHistory(1)">查询</el-button>
          <span v-if="historyMonth" style="font-size:12px;color:#909399">
            周期：{{ historyMonth }}的周期为上月26日 - {{ historyMonth }}-25
          </span>
        </div>

        <!-- 总计徽标 -->
        <div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap">
          <el-tag type="info" size="large">总任务 {{ historyData.totals.task_count }}</el-tag>
          <el-tag type="primary" size="large">总人工费 ¥{{ historyData.totals.total_labor_fee.toFixed(0) }}</el-tag>
          <el-tag type="success" size="large">已收 ¥{{ historyData.totals.paid_labor_fee.toFixed(0) }}</el-tag>
          <el-tag type="danger" size="large">未收 ¥{{ historyData.totals.unpaid_labor_fee.toFixed(0) }}</el-tag>
        </div>

        <!-- 按结算周期汇总（点击行选择该周期） -->
        <div style="margin-bottom:16px">
          <div style="font-size:14px;font-weight:600;margin-bottom:8px;color:#303133">按结算周期汇总（点击行选择该周期）</div>
          <el-table :data="historyData.period_summary" border size="small" max-height="200" highlight-current-row @current-change="onPeriodSelect">
            <el-table-column prop="period" label="结算周期" min-width="200" />
            <el-table-column prop="task_count" label="任务数" width="80" align="center" />
            <el-table-column label="总人工费" width="110" align="right">
              <template #default="{ row }">¥{{ row.total_labor_fee.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column label="已收" width="110" align="right">
              <template #default="{ row }">
                <span style="color:#67c23a">¥{{ row.paid_labor_fee.toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="未收" width="110" align="right">
              <template #default="{ row }">
                <span :style="{ color: row.unpaid_labor_fee > 0 ? '#f56c6c' : '#909399' }">¥{{ row.unpaid_labor_fee.toFixed(2) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 任务明细 -->
        <div style="font-size:14px;font-weight:600;margin-bottom:8px;color:#303133">任务明细</div>
        <el-table :data="historyData.tasks" border size="small" max-height="360">
          <el-table-column prop="departure_time" label="出车时间" width="145" />
          <el-table-column label="路线" min-width="160">
            <template #default="{ row }">{{ row.departure }} → {{ row.destination }}</template>
          </el-table-column>
          <el-table-column prop="client_name" label="用车单位" min-width="100" />
          <el-table-column label="预估人工费" width="100" align="right">
            <template #default="{ row }">¥{{ row.labor_fee }}</template>
          </el-table-column>
          <el-table-column label="实际人工费" width="100" align="right">
            <template #default="{ row }">¥{{ row.actual_labor_fee || '-' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' ? 'success' : 'primary'" size="small">
                {{ row.status === 'completed' ? '已完成' : '已排班' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="收款" width="130" align="center">
            <template #default="{ row }">
              <template v-if="row.is_paid">
                <el-tag type="success" size="small">已收款</el-tag>
                <div v-if="row.paid_date" style="font-size:11px;color:#909399">{{ row.paid_date }}</div>
              </template>
              <el-tag v-else type="danger" size="small">未收款</el-tag>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div style="display:flex;justify-content:flex-end;margin-top:12px">
          <el-pagination
            v-model:current-page="historyPage"
            :page-size="historyData.per_page"
            :total="historyData.total"
            layout="prev, pager, next, total"
            @current-change="loadHistory"
          />
        </div>
      </div>
      <el-skeleton v-else :rows="6" animated />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const drivers = ref([])
const settlementStats = ref({})
const settlementRange = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = ref({ name: '', phone: '', status: 'available' })

const driversWithStats = computed(() => {
  return drivers.value.map(d => ({
    ...d,
    _stats: settlementStats.value[d.id] || null
  }))
})

const loadData = async () => {
  try { const res = await api.get('/drivers'); drivers.value = res.data } catch (e) {}
}

const loadSettlementStats = async () => {
  try {
    const res = await api.get('/drivers/settlement-stats')
    if (res.code === 200) {
      const map = {}
      for (const d of res.data.drivers) {
        map[d.driver_id] = d
      }
      settlementStats.value = map
      settlementRange.value = `${res.data.settlement_start}-${res.data.settlement_end}`
    }
  } catch (e) {}
}

const showAdd = () => { isEdit.value = false; form.value = { name: '', phone: '', status: 'available' }; dialogVisible.value = true }
const showEdit = (row) => { isEdit.value = true; editId.value = row.id; form.value = { name: row.name, phone: row.phone, status: row.status }; dialogVisible.value = true }

// 历史任务
const historyVisible = ref(false)
const historyDriver = ref(null)
const historyData = ref(null)
const historyPage = ref(1)
const historyMonth = ref('')

const openHistory = (row) => {
  historyDriver.value = row
  historyData.value = null
  historyPage.value = 1
  // 默认选中当前结算月份（周期结束月）
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth() + 1
  historyMonth.value = now.getDate() >= 26
    ? (m === 12 ? `${y + 1}-01` : `${y}-${String(m + 1).padStart(2, '0')}`)
    : `${y}-${String(m).padStart(2, '0')}`
  historyVisible.value = true
  loadHistory(1)
}

const loadHistory = async (page) => {
  try {
    const res = await api.get(`/drivers/${historyDriver.value.id}/history`, {
      params: { page, per_page: 20, settlement_month: historyMonth.value }
    })
    if (res.code === 200) {
      historyData.value = res.data
      historyPage.value = res.data.page
    }
  } catch (e) {}
}

// 点击周期汇总行 → 选择该周期
const onPeriodSelect = (row) => {
  if (!row) return
  // period 格式 "2026-07-26 ~ 2026-08-25" → 结算月 "2026-08"
  const month = row.period.split(' ~ ')[1]?.slice(0, 7)
  if (month && month !== historyMonth.value) {
    historyMonth.value = month
    loadHistory(1)
  }
}

const submitForm = async () => {
  if (!form.value.name || !form.value.phone) { ElMessage.warning('请填写完整信息'); return }
  try {
    if (isEdit.value) { await api.put(`/drivers/${editId.value}`, form.value) } else { await api.post('/drivers', form.value) }
    ElMessage.success('操作成功')
    dialogVisible.value = false
    loadData()
  } catch (e) {}
}

const handleDelete = async (id) => {
  try { await api.delete(`/drivers/${id}`); ElMessage.success('删除成功'); loadData() } catch (e) {}
}

onMounted(() => { loadData(); loadSettlementStats() })
</script>
