<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:18px;font-weight:bold">权限控制</span>
          <el-button type="primary" @click="showAddUser">添加用户</el-button>
        </div>
      </template>

      <el-table :data="users" border stripe>
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="role" label="角色" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">{{ row.role === 'admin' ? '管理员' : '普通用户' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="权限" min-width="300">
          <template #default="{ row }">
            <el-tag v-for="p in row.permissions" :key="p" style="margin:2px" size="small">{{ permLabel(p) }}</el-tag>
            <span v-if="!row.permissions?.length" style="color:#909399">无</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showEditUser(row)">编辑</el-button>
            <el-popconfirm title="确认删除?" @confirm="deleteUser(row.id)">
              <template #reference>
                <el-button type="danger" size="small" :disabled="row.id === currentUserId">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '添加用户'" width="500px">
      <el-form :model="userForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="userForm.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="userForm.password" type="password" :placeholder="isEdit ? '留空则不修改' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userForm.role" style="width:100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="页面权限">
          <el-checkbox-group v-model="userForm.permissions">
            <el-checkbox label="task">任务管理</el-checkbox>
            <el-checkbox label="client">用车单位</el-checkbox>
            <el-checkbox label="driver">司机管理</el-checkbox>
            <el-checkbox label="vehicle">车辆管理</el-checkbox>
            <el-checkbox label="labor_rate">差费标准</el-checkbox>
            <el-checkbox label="report">报表管理</el-checkbox>
            <el-checkbox label="permission">权限控制</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUser">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const users = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const currentUserId = ref(JSON.parse(localStorage.getItem('user') || '{}').id)

const userForm = ref({ username: '', password: '', role: 'user', permissions: [] })

const permLabel = (p) => {
  const map = { task: '任务管理', client: '用车单位', driver: '司机管理', vehicle: '车辆管理', labor_rate: '差费标准', report: '报表管理', permission: '权限控制' }
  return map[p] || p
}

const loadUsers = async () => {
  try {
    const res = await api.get('/users')
    users.value = res.data
  } catch (e) {}
}

const showAddUser = () => {
  isEdit.value = false
  editId.value = null
  userForm.value = { username: '', password: '', role: 'user', permissions: [] }
  dialogVisible.value = true
}

const showEditUser = (row) => {
  isEdit.value = true
  editId.value = row.id
  userForm.value = { username: row.username, password: '', role: row.role, permissions: [...row.permissions] }
  dialogVisible.value = true
}

const submitUser = async () => {
  if (!userForm.value.username) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!isEdit.value && !userForm.value.password) {
    ElMessage.warning('请输入密码')
    return
  }
  try {
    if (isEdit.value) {
      await api.put(`/users/${editId.value}`, userForm.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/users', userForm.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadUsers()
  } catch (e) {}
}

const deleteUser = async (id) => {
  try {
    await api.delete(`/users/${id}`)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (e) {}
}

onMounted(loadUsers)
</script>
