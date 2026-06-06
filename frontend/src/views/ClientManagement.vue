<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:18px;font-weight:bold">用车单位管理</span>
          <el-button type="primary" @click="showAdd">新增用车单位</el-button>
        </div>
      </template>

      <el-table :data="clients" border stripe>
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="name" label="单位名称" min-width="160" />
        <el-table-column prop="address" label="地址" min-width="200" />
        <el-table-column label="联系人" min-width="200">
          <template #default="{ row }">
            <span v-if="!row.contacts?.length" style="color:#909399">无联系人</span>
            <el-tag v-for="c in row.contacts" :key="c.id" size="small" style="margin:2px">{{ c.name }} {{ c.phone }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="260" align="center">
          <template #default="{ row }">
            <el-button type="success" size="small" @click="showContacts(row)">管理联系人</el-button>
            <el-button type="primary" size="small" @click="showEdit(row)">编辑</el-button>
            <el-popconfirm title="确认删除? 删除单位将同时删除所有联系人" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add/Edit Client Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用车单位' : '新增用车单位'" width="450px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="单位名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- Contacts Dialog -->
    <el-dialog v-model="contactsVisible" :title="currentClient.name + ' - 联系人管理'" width="550px">
      <div style="margin-bottom:12px">
        <el-button type="primary" size="small" @click="showAddContact">添加联系人</el-button>
      </div>
      <el-table :data="currentClient.contacts || []" border stripe size="small">
        <el-table-column prop="name" label="姓名" min-width="100" />
        <el-table-column prop="phone" label="手机号码" min-width="140" />
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-popconfirm title="确认删除?" @confirm="deleteContact(row.id)">
              <template #reference>
                <el-button type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- Add Contact Inline Form -->
      <el-dialog v-model="contactFormVisible" title="添加联系人" width="400px" append-to-body>
        <el-form :model="contactForm" label-width="80px">
          <el-form-item label="姓名">
            <el-input v-model="contactForm.name" />
          </el-form-item>
          <el-form-item label="手机号码">
            <el-input v-model="contactForm.phone" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="contactFormVisible = false">取消</el-button>
          <el-button type="primary" @click="submitContact">确定</el-button>
        </template>
      </el-dialog>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const clients = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = ref({ name: '', address: '' })

const contactsVisible = ref(false)
const currentClient = ref({ id: null, name: '', contacts: [] })
const contactFormVisible = ref(false)
const contactForm = ref({ name: '', phone: '' })

const loadData = async () => {
  try { const res = await api.get('/clients'); clients.value = res.data } catch (e) {}
}

const showAdd = () => { isEdit.value = false; form.value = { name: '', address: '' }; dialogVisible.value = true }
const showEdit = (row) => { isEdit.value = true; editId.value = row.id; form.value = { name: row.name, address: row.address }; dialogVisible.value = true }

const submitForm = async () => {
  if (!form.value.name) { ElMessage.warning('请输入单位名称'); return }
  try {
    if (isEdit.value) { await api.put(`/clients/${editId.value}`, form.value) } else { await api.post('/clients', form.value) }
    ElMessage.success('操作成功')
    dialogVisible.value = false
    loadData()
  } catch (e) {}
}

const handleDelete = async (id) => {
  try { await api.delete(`/clients/${id}`); ElMessage.success('删除成功'); loadData() } catch (e) {}
}

const showContacts = (row) => {
  currentClient.value = { ...row }
  contactsVisible.value = true
}

const showAddContact = () => {
  contactForm.value = { name: '', phone: '' }
  contactFormVisible.value = true
}

const submitContact = async () => {
  if (!contactForm.value.name) { ElMessage.warning('请输入联系人姓名'); return }
  try {
    await api.post(`/clients/${currentClient.value.id}/contacts`, contactForm.value)
    ElMessage.success('添加成功')
    contactFormVisible.value = false
    // Reload contacts
    const res = await api.get(`/clients/${currentClient.value.id}`)
    currentClient.value = res.data
    loadData()
  } catch (e) {}
}

const deleteContact = async (contactId) => {
  try {
    await api.delete(`/clients/${currentClient.value.id}/contacts/${contactId}`)
    ElMessage.success('删除成功')
    const res = await api.get(`/clients/${currentClient.value.id}`)
    currentClient.value = res.data
    loadData()
  } catch (e) {}
}

onMounted(loadData)
</script>
