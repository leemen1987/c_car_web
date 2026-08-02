<template>
  <div>
    <el-card class="page-card">
      <template #header>
        <div class="page-header">
          <div class="page-title">
            <el-icon :size="20"><Calendar /></el-icon>
            <span>长租管理</span>
          </div>
          <el-button type="primary" @click="showAddContract">
            <el-icon><Plus /></el-icon>
            <span style="margin-left:4px">新增合同</span>
          </el-button>
        </div>
      </template>

      <!-- 合同列表 -->
      <el-table :data="contracts" stripe style="width:100%">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="contract_no" label="合同编号" min-width="160" />
        <el-table-column label="用车单位" min-width="120">
          <template #default="{ row }">{{ row.client_name }}</template>
        </el-table-column>
        <el-table-column prop="vehicle_plate" label="车牌号" min-width="100" />
        <el-table-column prop="driver_name" label="司机" min-width="90" />
        <el-table-column prop="start_date" label="开始日期" width="110" />
        <el-table-column prop="end_date" label="结束日期" width="110" />
        <el-table-column prop="monthly_rental_fee" label="月租金" width="100" align="right" />
        <el-table-column label="账单" width="140" align="center">
          <template #default="{ row }">
            <span style="color:#67c23a">已收 ¥{{ row.paid_total?.toFixed(0) || 0 }}</span>
            <span v-if="row.unpaid_total > 0" style="color:#f56c6c;margin-left:6px">未收 ¥{{ row.unpaid_total?.toFixed(0) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : row.status === 'expired' ? 'info' : 'danger'" size="small">
              {{ row.status === 'active' ? '执行中' : row.status === 'expired' ? '已到期' : '已终止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="success" size="small" @click="showBills(row)">账单</el-button>
            <el-button type="primary" size="small" @click="showEditContract(row)">编辑</el-button>
            <el-button v-if="row.status === 'active'" type="warning" size="small" @click="terminateContract(row)">终止</el-button>
            <el-popconfirm title="确认删除? 将同时删除所有账单" @confirm="deleteContract(row.id)">
              <template #reference>
                <el-button type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑合同弹窗 -->
    <el-dialog v-model="contractDialogVisible" :title="isEditContract ? '编辑合同' : '新增合同'" width="550px">
      <el-form :model="contractForm" label-width="100px">
        <el-form-item label="用车单位">
          <el-select v-model="contractForm.client_id" filterable placeholder="选择用车单位" style="width:100%">
            <el-option v-for="c in allClients" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="车辆">
          <el-select v-model="contractForm.vehicle_id" filterable placeholder="选择车辆" style="width:100%">
            <el-option v-for="v in allVehicles" :key="v.id" :label="v.plate_number + ' (' + v.vehicle_type + ')'" :value="v.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="司机">
          <el-select v-model="contractForm.driver_id" filterable clearable placeholder="选择司机" style="width:100%">
            <el-option v-for="d in allDrivers" :key="d.id" :label="d.name + ' (' + d.phone + ')'" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期">
              <el-date-picker v-model="contractForm.start_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期">
              <el-date-picker v-model="contractForm.end_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:100%" clearable />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="月租金(元)">
          <el-input-number v-model="contractForm.monthly_rental_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="contractForm.remark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="contractDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitContract">确定</el-button>
      </template>
    </el-dialog>

    <!-- 月度账单弹窗 -->
    <el-dialog v-model="billsDialogVisible" :title="currentContract?.contract_no + ' - 月度账单'" width="900px">
      <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
        <div>
          <span style="color:#909399;font-size:13px">用车单位：{{ currentContract?.client_name }}　车牌：{{ currentContract?.vehicle_plate }}　月租金：¥{{ currentContract?.monthly_rental_fee }}</span>
        </div>
        <el-button type="primary" size="small" @click="showAddBill">新增账单</el-button>
      </div>
      <el-table :data="bills" border stripe size="small">
        <el-table-column prop="bill_month" label="账单月份" width="100" align="center" />
        <el-table-column prop="rental_fee" label="月租金" width="90" align="right" />
        <el-table-column prop="fuel_fee" label="油费" width="80" align="right" />
        <el-table-column prop="bridge_fee" label="桥路费" width="80" align="right" />
        <el-table-column prop="other_fee" label="其他费用" width="80" align="right" />
        <el-table-column prop="total_amount" label="合计" width="100" align="right">
          <template #default="{ row }">
            <span style="font-weight:600">¥{{ row.total_amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="收款" width="180">
          <template #default="{ row }">
            <div v-if="row.is_paid">
              <el-tag type="success" size="small">已收</el-tag>
              <span style="margin-left:4px;font-size:12px;color:#909399">{{ row.paid_date }} {{ row.paid_method }}</span>
            </div>
            <span v-else style="color:#f56c6c;font-size:12px">未收</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="100" />
        <el-table-column label="操作" width="160" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showEditBill(row)">编辑</el-button>
            <el-popconfirm title="确认删除?" @confirm="deleteBill(row.id)">
              <template #reference>
                <el-button type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 新增/编辑账单弹窗 -->
    <el-dialog v-model="billFormVisible" :title="isEditBill ? '编辑账单' : '新增账单'" width="500px">
      <el-form :model="billForm" label-width="100px">
        <el-form-item label="账单月份">
          <el-date-picker v-model="billForm.bill_month" type="month" format="YYYY-MM" value-format="YYYY-MM" placeholder="选择月份" style="width:100%" :disabled="isEditBill" />
        </el-form-item>
        <el-form-item label="月租金(元)">
          <el-input-number v-model="billForm.rental_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="油费(元)">
          <el-input-number v-model="billForm.fuel_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="桥路费(元)">
          <el-input-number v-model="billForm.bridge_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="其他费用(元)">
          <el-input-number v-model="billForm.other_fee" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="合计">
          <el-input :model-value="billTotal" disabled />
        </el-form-item>
        <el-divider />
        <el-form-item label="是否已收款">
          <el-switch v-model="billForm.is_paid" />
        </el-form-item>
        <template v-if="billForm.is_paid">
          <el-form-item label="收款日期">
            <el-date-picker v-model="billForm.paid_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
          <el-form-item label="收款方式">
            <el-select v-model="billForm.paid_method" style="width:100%">
              <el-option label="转账" value="转账" />
              <el-option label="二维码" value="二维码" />
              <el-option label="现金" value="现金" />
            </el-select>
          </el-form-item>
        </template>
        <el-form-item label="备注">
          <el-input v-model="billForm.remark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="billFormVisible = false">取消</el-button>
        <el-button type="primary" @click="submitBill">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const contracts = ref([])
const allClients = ref([])
const allVehicles = ref([])
const allDrivers = ref([])

// 合同
const contractDialogVisible = ref(false)
const isEditContract = ref(false)
const editContractId = ref(null)
const contractForm = ref({ client_id: null, vehicle_id: null, driver_id: null, start_date: '', end_date: '', monthly_rental_fee: 0, remark: '' })

// 账单
const billsDialogVisible = ref(false)
const currentContract = ref(null)
const bills = ref([])
const billFormVisible = ref(false)
const isEditBill = ref(false)
const editBillId = ref(null)
const billForm = ref({ bill_month: '', rental_fee: 0, fuel_fee: 0, bridge_fee: 0, other_fee: 0, is_paid: false, paid_date: '', paid_method: '', remark: '' })

const billTotal = computed(() => (billForm.value.rental_fee + billForm.value.fuel_fee + billForm.value.bridge_fee + billForm.value.other_fee).toFixed(2))

const loadContracts = async () => {
  try { const res = await api.get('/long-rental-contracts'); contracts.value = res.data } catch (e) {}
}

const loadBaseData = async () => {
  try {
    const [c, v, d] = await Promise.all([api.get('/clients'), api.get('/vehicles'), api.get('/drivers')])
    allClients.value = c.data
    allVehicles.value = v.data
    allDrivers.value = d.data
  } catch (e) {}
}

const showAddContract = () => {
  isEditContract.value = false
  contractForm.value = { client_id: null, vehicle_id: null, driver_id: null, start_date: '', end_date: '', monthly_rental_fee: 0, remark: '' }
  contractDialogVisible.value = true
}

const showEditContract = (row) => {
  isEditContract.value = true
  editContractId.value = row.id
  contractForm.value = {
    client_id: row.client_id, vehicle_id: row.vehicle_id, driver_id: row.driver_id,
    start_date: row.start_date, end_date: row.end_date || '',
    monthly_rental_fee: row.monthly_rental_fee, remark: row.remark || ''
  }
  contractDialogVisible.value = true
}

const submitContract = async () => {
  if (!contractForm.value.client_id || !contractForm.value.vehicle_id || !contractForm.value.start_date) {
    ElMessage.warning('请选择用车单位、车辆和开始日期')
    return
  }
  try {
    if (isEditContract.value) {
      await api.put(`/long-rental-contracts/${editContractId.value}`, contractForm.value)
    } else {
      await api.post('/long-rental-contracts', contractForm.value)
    }
    ElMessage.success('操作成功')
    contractDialogVisible.value = false
    loadContracts()
  } catch (e) {}
}

const terminateContract = async (row) => {
  try {
    await api.put(`/long-rental-contracts/${row.id}`, { status: 'terminated' })
    ElMessage.success('合同已终止')
    loadContracts()
  } catch (e) {}
}

const deleteContract = async (id) => {
  try {
    await api.delete(`/long-rental-contracts/${id}`)
    ElMessage.success('删除成功')
    loadContracts()
  } catch (e) {}
}

// 账单
const showBills = async (row) => {
  currentContract.value = row
  billsDialogVisible.value = true
  try { const res = await api.get(`/long-rental-contracts/${row.id}/bills`); bills.value = res.data } catch (e) {}
}

const showAddBill = () => {
  isEditBill.value = false
  billForm.value = {
    bill_month: '', rental_fee: currentContract.value?.monthly_rental_fee || 0,
    fuel_fee: 0, bridge_fee: 0, other_fee: 0,
    is_paid: false, paid_date: '', paid_method: '', remark: ''
  }
  billFormVisible.value = true
}

const showEditBill = (row) => {
  isEditBill.value = true
  editBillId.value = row.id
  billForm.value = {
    bill_month: row.bill_month, rental_fee: row.rental_fee,
    fuel_fee: row.fuel_fee, bridge_fee: row.bridge_fee, other_fee: row.other_fee,
    is_paid: row.is_paid, paid_date: row.paid_date || '', paid_method: row.paid_method || '',
    remark: row.remark || ''
  }
  billFormVisible.value = true
}

const submitBill = async () => {
  if (!billForm.value.bill_month) { ElMessage.warning('请选择账单月份'); return }
  try {
    if (isEditBill.value) {
      await api.put(`/long-rental-bills/${editBillId.value}`, billForm.value)
    } else {
      await api.post(`/long-rental-contracts/${currentContract.value.id}/bills`, billForm.value)
    }
    ElMessage.success('操作成功')
    billFormVisible.value = false
    const res = await api.get(`/long-rental-contracts/${currentContract.value.id}/bills`)
    bills.value = res.data
    loadContracts()
  } catch (e) {}
}

const deleteBill = async (id) => {
  try {
    await api.delete(`/long-rental-bills/${id}`)
    ElMessage.success('删除成功')
    const res = await api.get(`/long-rental-contracts/${currentContract.value.id}/bills`)
    bills.value = res.data
    loadContracts()
  } catch (e) {}
}

onMounted(() => { loadContracts(); loadBaseData() })
</script>
