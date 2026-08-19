<template>
  <div>
    <el-card class="page-card">
      <template #header>
        <div class="page-header">
          <div class="page-title">
            <el-icon :size="20"><Van /></el-icon>
            <span>车辆管理</span>
          </div>
          <div style="display:flex;gap:8px">
            <el-button type="success" @click="showCompanyManage">
              <el-icon><OfficeBuilding /></el-icon>
              <span style="margin-left:4px">车属单位管理</span>
            </el-button>
            <el-button type="primary" @click="showAdd">
              <el-icon><Plus /></el-icon>
              <span style="margin-left:4px">添加车辆</span>
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="vehicles" stripe style="width:100%">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="plate_number" label="车牌号" min-width="120" />
        <el-table-column prop="brand_model" label="品牌型号" min-width="120" />
        <el-table-column prop="capacity" label="核定载人数" min-width="100" />
        <el-table-column prop="vehicle_type" label="车辆类型" min-width="100" />
        <el-table-column prop="company" label="所属公司" min-width="100" />
        <el-table-column prop="usage_type" label="使用性质" min-width="90" />
        <el-table-column prop="registration_date" label="注册日期" min-width="110" />
        <el-table-column prop="inspection_expiry" label="检验有效期" min-width="110" />
        <el-table-column prop="insurance_expiry" label="保险到期" min-width="110" />
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

    <!-- 添加/编辑车辆弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑车辆' : '添加车辆'" width="600px">
      <el-form :model="form" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="车牌号">
              <el-input v-model="form.plate_number" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品牌型号">
              <el-input v-model="form.brand_model" placeholder="如：宇通ZK6122" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="核定载人数">
              <el-input v-model="form.capacity" placeholder="如：45" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="车辆类型">
              <el-input v-model="form.vehicle_type" placeholder="如：大巴、中巴" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="使用性质">
              <el-input v-model="form.usage_type" placeholder="如：营运" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属公司">
              <el-select v-model="form.company" placeholder="请选择所属公司" style="width:100%" filterable allow-create>
                <el-option v-for="c in companies" :key="c.id" :label="c.name" :value="c.name" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width:100%">
                <el-option label="可用" value="available" />
                <el-option label="忙碌" value="busy" />
                <el-option label="维修中" value="maintenance" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="注册日期">
              <el-date-picker v-model="form.registration_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发证日期">
              <el-date-picker v-model="form.issue_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="检验有效期">
              <el-date-picker v-model="form.inspection_expiry" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="强制报废期">
              <el-date-picker v-model="form.scrap_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="保险到期">
              <el-date-picker v-model="form.insurance_expiry" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 车属单位管理弹窗 -->
    <el-dialog v-model="companyDialogVisible" title="车属单位管理" width="650px">
      <div style="margin-bottom:12px">
        <el-button type="primary" size="small" @click="showAddCompany">新增车属单位</el-button>
      </div>
      <el-table :data="companies" border stripe size="small">
        <el-table-column prop="name" label="单位名称" min-width="100" />
        <el-table-column prop="contact_person" label="联系人" min-width="80" />
        <el-table-column prop="phone" label="手机号码" min-width="110" />
        <el-table-column prop="address" label="单位地址" min-width="140" />
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showEditCompany(row)">编辑</el-button>
            <el-popconfirm title="确认删除?" @confirm="deleteCompany(row.id)">
              <template #reference>
                <el-button type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 新增/编辑车属单位弹窗 -->
    <el-dialog v-model="companyFormVisible" :title="isEditCompany ? '编辑车属单位' : '新增车属单位'" width="450px">
      <el-form :model="companyForm" label-width="80px">
        <el-form-item label="单位名称">
          <el-input v-model="companyForm.name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="companyForm.contact_person" />
        </el-form-item>
        <el-form-item label="手机号码">
          <el-input v-model="companyForm.phone" />
        </el-form-item>
        <el-form-item label="单位地址">
          <el-input v-model="companyForm.address" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="companyFormVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCompanyForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const vehicles = ref([])
const companies = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = ref({ plate_number: '', capacity: '', vehicle_type: '', company: '', status: 'available', registration_date: '', issue_date: '', usage_type: '', brand_model: '', inspection_expiry: '', scrap_date: '', insurance_expiry: '' })

const companyDialogVisible = ref(false)
const companyFormVisible = ref(false)
const isEditCompany = ref(false)
const editCompanyId = ref(null)
const companyForm = ref({ name: '', contact_person: '', phone: '', address: '' })

const loadData = async () => {
  try { const res = await api.get('/vehicles'); vehicles.value = res.data } catch (e) {}
}

const loadCompanies = async () => {
  try { const res = await api.get('/vehicle-companies'); companies.value = res.data } catch (e) {}
}

const defaultForm = { plate_number: '', capacity: '', vehicle_type: '', company: '', status: 'available', registration_date: '', issue_date: '', usage_type: '', brand_model: '', inspection_expiry: '', scrap_date: '', insurance_expiry: '' }

const showAdd = () => { isEdit.value = false; form.value = { ...defaultForm }; dialogVisible.value = true }
const showEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  form.value = {
    plate_number: row.plate_number,
    capacity: row.capacity || '',
    vehicle_type: row.vehicle_type || '',
    company: row.company || '',
    status: row.status,
    registration_date: row.registration_date || '',
    issue_date: row.issue_date || '',
    usage_type: row.usage_type || '',
    brand_model: row.brand_model || '',
    inspection_expiry: row.inspection_expiry || '',
    scrap_date: row.scrap_date || '',
    insurance_expiry: row.insurance_expiry || ''
  }
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!form.value.plate_number || !form.value.vehicle_type) { ElMessage.warning('请填写完整信息'); return }
  try {
    if (isEdit.value) { await api.put(`/vehicles/${editId.value}`, form.value) } else { await api.post('/vehicles', form.value) }
    ElMessage.success('操作成功')
    dialogVisible.value = false
    loadData()
    loadCompanies()
  } catch (e) {}
}

const handleDelete = async (id) => {
  try { await api.delete(`/vehicles/${id}`); ElMessage.success('删除成功'); loadData() } catch (e) {}
}

const showCompanyManage = () => { companyDialogVisible.value = true }

const showAddCompany = () => {
  isEditCompany.value = false
  companyForm.value = { name: '', contact_person: '', phone: '', address: '' }
  companyFormVisible.value = true
}

const showEditCompany = (row) => {
  isEditCompany.value = true
  editCompanyId.value = row.id
  companyForm.value = { name: row.name, contact_person: row.contact_person || '', phone: row.phone || '', address: row.address || '' }
  companyFormVisible.value = true
}

const submitCompanyForm = async () => {
  if (!companyForm.value.name.trim()) { ElMessage.warning('请输入单位名称'); return }
  try {
    if (isEditCompany.value) {
      await api.put(`/vehicle-companies/${editCompanyId.value}`, companyForm.value)
    } else {
      await api.post('/vehicle-companies', companyForm.value)
    }
    ElMessage.success('操作成功')
    companyFormVisible.value = false
    loadCompanies()
    loadData()
  } catch (e) {}
}

const deleteCompany = async (id) => {
  try { await api.delete(`/vehicle-companies/${id}`); ElMessage.success('删除成功'); loadCompanies() } catch (e) {}
}

onMounted(() => { loadData(); loadCompanies() })
</script>
