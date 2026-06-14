<template>
  <div>
    <el-card class="page-card">
      <template #header>
        <div class="page-header">
          <div class="page-title">
            <el-icon :size="20"><OfficeBuilding /></el-icon>
            <span>用车单位管理</span>
          </div>
          <el-button type="primary" @click="showAdd">
            <el-icon><Plus /></el-icon>
            <span style="margin-left:4px">新增用车单位</span>
          </el-button>
        </div>
      </template>

      <el-table :data="clients" stripe style="width:100%">
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
        <el-table-column prop="name" label="姓名" min-width="80" />
        <el-table-column prop="phone" label="手机号码" min-width="120" />
        <el-table-column prop="wx_userid" label="企业微信ID" min-width="140">
          <template #default="{ row }">
            <span v-if="row.wx_userid">{{ row.wx_userid }}</span>
            <span v-else style="color:#c0c4cc">未配置</span>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.wx_userid && row.wx_userid.startsWith('wm')" type="warning" size="small">外部</el-tag>
            <el-tag v-else-if="row.wx_userid" type="success" size="small">内部</el-tag>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="wx_sender" label="发送人" min-width="100">
          <template #default="{ row }">
            <span v-if="row.wx_sender">{{ row.wx_sender }}</span>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="editContact(row)">编辑</el-button>
            <el-popconfirm title="确认删除?" @confirm="deleteContact(row.id)">
              <template #reference>
                <el-button type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- Add Contact Inline Form -->
      <el-dialog v-model="contactFormVisible" :title="contactForm.id ? '编辑联系人' : '添加联系人'" width="500px" append-to-body>
        <el-form :model="contactForm" label-width="100px">
          <el-form-item label="姓名">
            <el-input v-model="contactForm.name" />
          </el-form-item>
          <el-form-item label="手机号码">
            <el-input v-model="contactForm.phone" />
          </el-form-item>
          <el-form-item label="发送人账号">
            <el-input v-model="contactForm.wx_sender" placeholder="你的企业微信账号（内部员工）" />
            <div style="color:#909399;font-size:12px;margin-top:4px">填入后可自动获取你的外部联系人列表</div>
          </el-form-item>
          <el-form-item label="企业微信ID">
            <div style="display:flex;gap:8px;width:100%">
              <el-input v-model="contactForm.wx_userid" placeholder="外部联系人ID（wm开头）" style="flex:1" />
              <el-button type="primary" :loading="fetchingContacts" @click="fetchExternalContacts" :disabled="!contactForm.wx_sender">获取</el-button>
            </div>
          </el-form-item>
          <!-- 外部联系人选择列表 -->
          <el-form-item v-if="externalContacts.length > 0" label="选择客户">
            <el-select v-model="contactForm.wx_userid" filterable placeholder="从外部联系人中选择" style="width:100%" @change="onExternalContactSelect">
              <el-option v-for="c in externalContacts" :key="c.external_userid" :label="`${c.name} (${c.corp_name || '个人'})`" :value="c.external_userid">
                <span>{{ c.name }}</span>
                <span v-if="c.corp_name" style="color:#909399;margin-left:8px">{{ c.corp_name }}</span>
                <span style="color:#c0c4cc;margin-left:8px;font-size:12px">{{ c.external_userid }}</span>
              </el-option>
            </el-select>
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
const externalContacts = ref([])
const fetchingContacts = ref(false)

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
  contactForm.value = { name: '', phone: '', wx_userid: '', wx_sender: '' }
  externalContacts.value = []
  contactFormVisible.value = true
}

const editContact = (row) => {
  contactForm.value = { id: row.id, name: row.name, phone: row.phone, wx_userid: row.wx_userid || '', wx_sender: row.wx_sender || '' }
  externalContacts.value = []
  contactFormVisible.value = true
}

const fetchExternalContacts = async () => {
  if (!contactForm.value.wx_sender) {
    ElMessage.warning('请先填写发送人账号')
    return
  }
  fetchingContacts.value = true
  try {
    const res = await api.get(`/wx-external-contacts?sender=${contactForm.value.wx_sender}`)
    if (res.code === 200) {
      externalContacts.value = res.data || []
      if (externalContacts.value.length === 0) {
        ElMessage.info('未找到外部联系人')
      }
    }
  } catch (e) {
    ElMessage.error('获取外部联系人失败')
  } finally {
    fetchingContacts.value = false
  }
}

const onExternalContactSelect = (val) => {
  const selected = externalContacts.value.find(c => c.external_userid === val)
  if (selected) {
    contactForm.value.name = selected.name
    contactForm.value.external_corp_name = selected.corp_name || ''
  }
}

const submitContact = async () => {
  if (!contactForm.value.name) { ElMessage.warning('请输入联系人姓名'); return }
  try {
    if (contactForm.value.id) {
      await api.put(`/clients/${currentClient.value.id}/contacts/${contactForm.value.id}`, contactForm.value)
    } else {
      await api.post(`/clients/${currentClient.value.id}/contacts`, contactForm.value)
    }
    ElMessage.success('操作成功')
    contactFormVisible.value = false
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
