<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:18px;font-weight:bold">车辆管理</span>
          <el-button type="primary" @click="showAdd">添加车辆</el-button>
        </div>
      </template>

      <el-table :data="vehicles" border stripe>
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="plate_number" label="车牌号" min-width="120" />
        <el-table-column prop="vehicle_type" label="车辆类型" min-width="140" />
        <el-table-column prop="company" label="所属公司" min-width="100" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'available' ? 'success' : row.status === 'busy' ? 'warning' : 'info'">
              {{ row.status === 'available' ? '可用' : row.status === 'busy' ? '忙碌' : '维修中' }}
            </el-tag>
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑车辆' : '添加车辆'" width="450px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="车牌号">
          <el-input v-model="form.plate_number" />
        </el-form-item>
        <el-form-item label="车辆类型">
          <el-select v-model="form.vehicle_type" style="width:100%">
            <el-option label="大巴(45座)" value="大巴(45座)" />
            <el-option label="中巴(25座)" value="中巴(25座)" />
            <el-option label="小巴(15座)" value="小巴(15座)" />
            <el-option label="商务车(7座)" value="商务车(7座)" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属公司">
          <el-select v-model="form.company" placeholder="请选择所属公司" style="width:100%">
            <el-option label="国顺司" value="国顺司" />
            <el-option label="国开司" value="国开司" />
            <el-option label="外单位" value="外单位" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width:100%">
            <el-option label="可用" value="available" />
            <el-option label="忙碌" value="busy" />
            <el-option label="维修中" value="maintenance" />
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const vehicles = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = ref({ plate_number: '', vehicle_type: '', company: '', status: 'available' })

const loadData = async () => {
  try { const res = await api.get('/vehicles'); vehicles.value = res.data } catch (e) {}
}

const showAdd = () => { isEdit.value = false; form.value = { plate_number: '', vehicle_type: '', company: '', status: 'available' }; dialogVisible.value = true }
const showEdit = (row) => { isEdit.value = true; editId.value = row.id; form.value = { plate_number: row.plate_number, vehicle_type: row.vehicle_type, company: row.company || '', status: row.status }; dialogVisible.value = true }

const submitForm = async () => {
  if (!form.value.plate_number || !form.value.vehicle_type) { ElMessage.warning('请填写完整信息'); return }
  try {
    if (isEdit.value) { await api.put(`/vehicles/${editId.value}`, form.value) } else { await api.post('/vehicles', form.value) }
    ElMessage.success('操作成功')
    dialogVisible.value = false
    loadData()
  } catch (e) {}
}

const handleDelete = async (id) => {
  try { await api.delete(`/vehicles/${id}`); ElMessage.success('删除成功'); loadData() } catch (e) {}
}

onMounted(loadData)
</script>
