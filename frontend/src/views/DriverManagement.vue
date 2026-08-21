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
        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showEdit(row)">编辑</el-button>
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
