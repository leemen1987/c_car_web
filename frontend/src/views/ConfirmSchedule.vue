<template>
  <div class="confirm-page">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>加载中...</p>
    </div>

    <!-- 错误提示 -->
    <div v-else-if="error" class="error-container">
      <el-icon :size="60" color="#f56c6c"><CircleCloseFilled /></el-icon>
      <h2>链接无效</h2>
      <p>{{ error }}</p>
    </div>

    <!-- 确认内容 -->
    <div v-else class="confirm-content">
      <!-- 头部 -->
      <div class="header">
        <div class="logo">🚌 车辆任务确认</div>
      </div>

      <!-- 任务卡片 -->
      <div class="task-card">
        <div class="card-header">
          <span class="task-no">{{ taskInfo.task_no || '任务确认' }}</span>
          <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
        </div>

        <div class="card-body">
          <div class="info-section">
            <h4>📅 出车信息</h4>
            <div class="info-row">
              <span class="label">出车时间</span>
              <span class="value">{{ taskInfo.departure_time || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="label">回程时间</span>
              <span class="value">{{ taskInfo.return_time || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="label">出发地点</span>
              <span class="value">{{ taskInfo.departure || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="label">目的地</span>
              <span class="value">{{ taskInfo.destination || '-' }}</span>
            </div>
          </div>

          <div class="info-section">
            <h4>🚗 车辆信息</h4>
            <div class="info-row">
              <span class="label">车辆类型</span>
              <span class="value">{{ taskInfo.vehicle_type || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="label">车牌号码</span>
              <span class="value">{{ taskInfo.vehicle_plate || '-' }}</span>
            </div>
          </div>

          <div class="info-section">
            <h4>👤 驾驶员信息</h4>
            <div class="info-row">
              <span class="label">驾驶员</span>
              <span class="value">{{ taskInfo.driver_name || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="label">联系电话</span>
              <span class="value">
                <a v-if="taskInfo.driver_phone" :href="'tel:' + taskInfo.driver_phone" class="phone-link">
                  {{ taskInfo.driver_phone }}
                </a>
                <span v-else>-</span>
              </span>
            </div>
          </div>

          <div class="info-section" v-if="taskInfo.rental_fee">
            <h4>💰 费用信息</h4>
            <div class="info-row">
              <span class="label">租车费</span>
              <span class="value">¥{{ taskInfo.rental_fee || 0 }}</span>
            </div>
            <div class="info-row">
              <span class="label">租用天数</span>
              <span class="value">{{ taskInfo.rental_days || 1 }}天</span>
            </div>
          </div>
        </div>

        <!-- 确认操作区 -->
        <div v-if="confirmStatus === 'pending'" class="card-footer">
          <div class="info-input-section">
            <el-input
              v-model="phoneNumber"
              placeholder="请填写您的手机号码（选填）"
              maxlength="20"
              clearable
            >
              <template #prefix>
                <el-icon><Phone /></el-icon>
              </template>
            </el-input>
          </div>
          <div class="remark-section">
            <el-input
              v-model="remark"
              type="textarea"
              :rows="2"
              placeholder="如有异议请填写说明（选填）"
              maxlength="200"
              show-word-limit
            />
          </div>
          <div class="button-group">
            <el-button
              type="danger"
              size="large"
              :loading="submitting"
              @click="handleReject"
            >
              有异议
            </el-button>
            <el-button
              type="success"
              size="large"
              :loading="submitting"
              @click="handleConfirm"
            >
              确认任务
            </el-button>
          </div>
        </div>

        <!-- 已确认状态 -->
        <div v-else class="confirmed-section">
          <el-result
            :icon="confirmStatus === 'confirmed' ? 'success' : 'warning'"
            :title="confirmStatus === 'confirmed' ? '已确认任务' : '已提交异议'"
            :sub-title="'确认时间：' + (confirmTime || '-')"
          >
            <template #extra>
              <div v-if="confirmRemark" class="confirm-remark">
                <p><strong>备注：</strong>{{ confirmRemark }}</p>
              </div>
            </template>
          </el-result>
        </div>
      </div>

      <!-- 底部信息 -->
      <div class="footer">
        <p v-if="pushTime">推送时间：{{ pushTime }}</p>
        <p v-if="createdBy">发起人：{{ createdBy }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, CircleCloseFilled } from '@element-plus/icons-vue'
import axios from 'axios'

const route = useRoute()
const token = route.params.token

const loading = ref(true)
const error = ref('')
const taskInfo = ref({})
const confirmStatus = ref('pending')
const confirmTime = ref('')
const confirmRemark = ref('')
const pushTime = ref('')
const createdBy = ref('')
const phoneNumber = ref('')
const remark = ref('')
const submitting = ref(false)

const statusType = computed(() => {
  const map = {
    pending: 'warning',
    confirmed: 'success',
    rejected: 'danger'
  }
  return map[confirmStatus.value] || 'info'
})

const statusText = computed(() => {
  const map = {
    pending: '待确认',
    confirmed: '已确认',
    rejected: '已拒绝'
  }
  return map[confirmStatus.value] || '未知'
})

const fetchConfirmData = async () => {
  try {
    const response = await axios.get(`/api/confirm/${token}`)
    if (response.data.code === 200) {
      const data = response.data.data
      taskInfo.value = data.task_info || {}
      confirmStatus.value = data.confirm_status || 'pending'
      confirmTime.value = data.confirm_time || ''
      pushTime.value = data.push_time || ''
      createdBy.value = data.created_by_name || ''
      confirmRemark.value = ''

      // 检查URL参数中是否有从OAuth回调传来的手机号和姓名
      const urlParams = new URLSearchParams(window.location.search)
      const phoneFromUrl = urlParams.get('phone')
      const nameFromUrl = urlParams.get('name')
      if (phoneFromUrl) {
        phoneNumber.value = phoneFromUrl
      }
    } else {
      error.value = response.data.msg || '获取数据失败'
    }
  } catch (err) {
    error.value = '网络错误或链接无效'
  } finally {
    loading.value = false
  }
}

const handleConfirm = async () => {
  await ElMessageBox.confirm('确认该任务信息无误？', '确认任务', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'info'
  })

  submitting.value = true
  try {
    const response = await axios.post(`/api/confirm/${token}`, {
      action: 'confirm',
      phone: phoneNumber.value,
      remark: remark.value
    })
    if (response.data.code === 200) {
      ElMessage.success('确认成功')
      confirmStatus.value = 'confirmed'
      confirmTime.value = response.data.data.confirm_time
      confirmRemark.value = remark.value
    } else {
      ElMessage.error(response.data.msg || '确认失败')
    }
  } catch (err) {
    ElMessage.error('网络错误，请重试')
  } finally {
    submitting.value = false
  }
}

const handleReject = async () => {
  if (!remark.value.trim()) {
    ElMessage.warning('请填写异议说明')
    return
  }

  await ElMessageBox.confirm('确认提交异议？', '提交异议', {
    confirmButtonText: '提交',
    cancelButtonText: '取消',
    type: 'warning'
  })

  submitting.value = true
  try {
    const response = await axios.post(`/api/confirm/${token}`, {
      action: 'reject',
      phone: phoneNumber.value,
      remark: remark.value
    })
    if (response.data.code === 200) {
      ElMessage.success('已提交异议')
      confirmStatus.value = 'rejected'
      confirmTime.value = response.data.data.confirm_time
      confirmRemark.value = remark.value
    } else {
      ElMessage.error(response.data.msg || '提交失败')
    }
  } catch (err) {
    ElMessage.error('网络错误，请重试')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchConfirmData()
})
</script>

<style scoped>
.confirm-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  color: #fff;
}

.loading-container p,
.error-container p {
  margin-top: 16px;
  font-size: 16px;
}

.error-container h2 {
  margin-top: 16px;
  color: #fff;
}

.confirm-content {
  max-width: 500px;
  margin: 0 auto;
}

.header {
  text-align: center;
  padding: 20px 0;
}

.logo {
  font-size: 24px;
  font-weight: bold;
  color: #fff;
}

.task-card {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.task-no {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.card-body {
  padding: 20px;
}

.info-section {
  margin-bottom: 20px;
}

.info-section:last-child {
  margin-bottom: 0;
}

.info-section h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.info-row .label {
  color: #666;
  font-size: 14px;
  flex-shrink: 0;
  width: 80px;
}

.info-row .value {
  color: #333;
  font-size: 14px;
  text-align: right;
  flex: 1;
  word-break: break-all;
}

.phone-link {
  color: #409eff;
  text-decoration: none;
}

.phone-link:hover {
  text-decoration: underline;
}

.card-footer {
  padding: 20px;
  background: #f9f9f9;
  border-top: 1px solid #eee;
}

.info-input-section {
  margin-bottom: 12px;
}

.remark-section {
  margin-bottom: 16px;
}

.button-group {
  display: flex;
  gap: 16px;
}

.button-group .el-button {
  flex: 1;
}

.confirmed-section {
  padding: 20px;
  background: #f9f9f9;
  border-top: 1px solid #eee;
}

.confirm-remark {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
  margin-top: 12px;
  text-align: left;
}

.confirm-remark p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.footer {
  text-align: center;
  padding: 20px 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}

.footer p {
  margin: 4px 0;
}

/* 响应式调整 */
@media (max-width: 375px) {
  .confirm-page {
    padding: 12px;
  }

  .card-body {
    padding: 16px;
  }

  .info-row .label {
    width: 70px;
    font-size: 13px;
  }

  .info-row .value {
    font-size: 13px;
  }
}
</style>
