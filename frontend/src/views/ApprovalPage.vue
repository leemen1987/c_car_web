<template>
  <div class="approval-page">
    <div class="approval-header">
      <span class="logo">🚌</span>
      <h2>包车审批</h2>
    </div>

    <div v-if="loading" class="approval-card">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="errorMsg" class="approval-card">
      <el-result icon="warning" :title="errorMsg" sub-title="请检查链接是否正确或联系管理员">
      </el-result>
    </div>

    <template v-else-if="data">
      <!-- 任务详情 -->
      <div class="approval-card">
        <div class="card-title">任务信息</div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="任务编号">{{ data.task.task_no }}</el-descriptions-item>
          <el-descriptions-item label="用车方">{{ data.task.client_name }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ data.task.client_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="路线">{{ data.task.departure || '-' }} → {{ data.task.destination || '-' }}</el-descriptions-item>
          <el-descriptions-item label="出车时间">{{ data.task.departure_time }}</el-descriptions-item>
          <el-descriptions-item label="回程时间">{{ data.task.return_time || '待定' }}</el-descriptions-item>
          <el-descriptions-item label="车辆配置">{{ data.task.vehicle_type || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-descriptions :column="2" border style="margin-top:12px">
          <el-descriptions-item label="租车费">¥{{ data.task.rental_fee }}</el-descriptions-item>
          <el-descriptions-item label="油电费">¥{{ data.task.fuel_fee }}</el-descriptions-item>
          <el-descriptions-item label="桥路费">¥{{ data.task.bridge_fee }}</el-descriptions-item>
          <el-descriptions-item label="司机人工费">¥{{ data.task.labor_fee }}</el-descriptions-item>
          <el-descriptions-item label="预估利润" :span="2">
            <span :style="{ color: data.task.estimated_profit >= 0 ? '#67c23a' : '#f56c6c', fontWeight: 600 }">
              ¥{{ data.task.estimated_profit }}
            </span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 流程进度 -->
      <div class="approval-card">
        <div class="card-title">审批进度（第 {{ data.current_level }} / {{ data.total_levels }} 级）</div>
        <el-steps :active="data.current_level - 1" :finish-status="data.flow_status === 'rejected' ? 'error' : 'success'" align-center>
          <el-step v-for="lv in data.levels" :key="lv.level" :title="`第${lv.level}级`" :description="lvDesc(lv)" />
        </el-steps>
      </div>

      <!-- 审批操作 -->
      <div class="approval-card">
        <template v-if="data.my_step.status === 'pending' && data.flow_status === 'pending'">
          <div class="card-title">审批意见</div>
          <el-input v-model="comment" type="textarea" :rows="3" placeholder="请输入审批意见（选填）" />
          <div class="action-bar">
            <el-button type="danger" size="large" :loading="acting" @click="act('reject')">拒 绝</el-button>
            <el-button type="success" size="large" :loading="acting" @click="act('approve')">通 过</el-button>
          </div>
        </template>
        <el-result v-else :icon="resultIcon" :title="resultTitle" :sub-title="resultSub">
        </el-result>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const route = useRoute()
const token = route.params.token
const loading = ref(true)
const errorMsg = ref('')
const data = ref(null)
const comment = ref('')
const acting = ref(false)

const lvDesc = (lv) => {
  if (lv.status === 'approved') return `${lv.name} 已通过${lv.acted_at ? ' ' + lv.acted_at : ''}`
  if (lv.status === 'rejected') return `${lv.name} 已拒绝`
  return `${lv.name} 待审批`
}

const resultIcon = computed(() => data.value?.flow_status === 'rejected' ? 'error' : 'success')
const resultTitle = computed(() => data.value?.flow_status === 'rejected' ? '审批已拒绝' : (data.value?.flow_status === 'approved' ? '审批已通过' : `已通过，等待第${data.value?.current_level}级审批`))
const resultSub = computed(() => {
  const lv = data.value?.levels?.find(l => l.status === 'rejected')
  return lv?.comment ? `拒绝意见：${lv.comment}` : ''
})

const load = async () => {
  try {
    const res = await api.get(`/approval/${token}`)
    if (res.code === 200) {
      data.value = res.data
    } else {
      errorMsg.value = res.msg || '链接无效'
    }
  } catch (e) {
    errorMsg.value = e?.response?.data?.msg || '加载失败'
  } finally {
    loading.value = false
  }
}

const act = async (action) => {
  const tip = action === 'reject' ? '确认拒绝该审批？' : '确认通过该审批？'
  try {
    await new Promise((resolve, reject) => {
      import('element-plus').then(({ ElMessageBox }) => {
        ElMessageBox.confirm(tip, '请确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(resolve).catch(reject)
      })
    })
  } catch { return }

  try {
    acting.value = true
    const res = await api.post(`/approval/${token}/act`, { action, comment: comment.value })
    if (res.code === 200) {
      ElMessage.success(res.msg)
      data.value.my_step.status = action === 'approve' ? 'approved' : 'rejected'
      data.value.flow_status = action === 'approve'
        ? (res.msg.includes('全部审批完成') ? 'approved' : 'pending')
        : 'rejected'
      // 刷新进度
      const refreshed = await api.get(`/approval/${token}`)
      if (refreshed.code === 200) data.value = refreshed.data
    } else {
      ElMessage.error(res.msg || '操作失败')
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.msg || '操作失败')
  } finally {
    acting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.approval-page {
  min-height: 100vh;
  background: var(--bg-page, #f1f5f9);
  padding: 24px 16px 48px;
  max-width: 720px;
  margin: 0 auto;
}
.approval-header {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  margin-bottom: 20px;
}
.approval-header h2 {
  font-size: 20px;
  color: var(--text-primary, #1e293b);
}
.logo { font-size: 28px; }
.approval-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 14px;
  color: var(--text-primary, #1e293b);
  padding-left: 10px;
  border-left: 3px solid var(--primary, #4f46e5);
}
.action-bar {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 20px;
}
.action-bar .el-button {
  width: 140px;
  height: 44px;
  font-size: 16px;
}
@media (max-width: 480px) {
  .approval-page { padding: 12px 8px 32px; }
  .action-bar .el-button { width: 120px; }
}
</style>
