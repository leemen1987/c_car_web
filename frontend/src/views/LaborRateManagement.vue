<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:18px;font-weight:bold">差费标准管理</span>
          <el-button type="primary" @click="showAdd">添加标准</el-button>
        </div>
      </template>

      <el-table :data="rates" border stripe>
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="location" label="目的地" min-width="200" />
        <el-table-column prop="labor_rate" label="人工费标准(元)" min-width="160" align="right" />
        <el-table-column prop="days" label="天数" width="100" align="center" />
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-popconfirm title="确认删除?" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="添加差费标准" width="450px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="目的地">
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item label="人工费(元)">
          <el-input-number v-model="form.labor_rate" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="天数">
          <el-input-number v-model="form.days" :min="1" style="width:100%" />
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

const rates = ref([])
const dialogVisible = ref(false)
const form = ref({ location: '', labor_rate: 0, days: 1 })

const loadData = async () => {
  try { const res = await api.get('/labor-rates'); rates.value = res.data } catch (e) {}
}

const showAdd = () => { form.value = { location: '', labor_rate: 0, days: 1 }; dialogVisible.value = true }

const submitForm = async () => {
  if (!form.value.location) { ElMessage.warning('请输入目的地'); return }
  try { await api.post('/labor-rates', form.value); ElMessage.success('添加成功'); dialogVisible.value = false; loadData() } catch (e) {}
}

const handleDelete = async (id) => {
  try { await api.delete(`/labor-rates/${id}`); ElMessage.success('删除成功'); loadData() } catch (e) {}
}

onMounted(loadData)
</script>
