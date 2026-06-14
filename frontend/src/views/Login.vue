<template>
  <div class="login-container">
    <div class="login-bg"></div>
    <div class="login-card-wrapper">
      <el-card class="login-card">
        <div class="login-header">
          <div class="login-logo">🚌</div>
          <h2 class="login-title">包车排班系统</h2>
          <p class="login-subtitle">Charter Bus Scheduling System</p>
        </div>
        <el-form :model="form" @submit.prevent="handleLogin" label-width="0">
          <el-form-item>
            <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password @keyup.enter="handleLogin" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">登 录</el-button>
          </el-form-item>
        </el-form>
      </el-card>
      <p class="login-footer">© 2026 大众包车 · 业务管理平台</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const router = useRouter()
const loading = ref(false)
const form = ref({ username: '', password: '' })

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await api.post('/login', form.value)
    if (res.code === 200) {
      localStorage.setItem('user', JSON.stringify(res.data))
      ElMessage.success('登录成功')
      router.push('/tasks')
    }
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
}

/* 动态背景 */
.login-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 30%, #4f46e5 60%, #06b6d4 100%);
  animation: bgShift 12s ease-in-out infinite alternate;
}
@keyframes bgShift {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
.login-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(6,182,212,0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(129,140,248,0.15) 0%, transparent 50%);
}

/* 卡片容器 */
.login-card-wrapper {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.login-card {
  width: 400px;
  padding: 24px;
  border-radius: 16px !important;
  background: rgba(255,255,255,0.95) !important;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.3) !important;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25) !important;
}

/* 头部 */
.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.login-logo {
  font-size: 48px;
  margin-bottom: 12px;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
}
.login-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
  letter-spacing: 0.02em;
}
.login-subtitle {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 400;
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 44px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%) !important;
  border: none !important;
  letter-spacing: 0.05em;
  transition: all 0.3s ease !important;
}
.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 25px -5px rgba(79, 70, 229, 0.4) !important;
}

/* 底部版权 */
.login-footer {
  margin-top: 24px;
  font-size: 12px;
  color: rgba(255,255,255,0.5);
}

/* 输入框美化 */
:deep(.login-card .el-input__wrapper) {
  border-radius: 10px !important;
  padding: 4px 12px !important;
  box-shadow: 0 0 0 1px var(--border-light) !important;
  transition: all 0.25s ease !important;
}
:deep(.login-card .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--primary-light) !important;
}
:deep(.login-card .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2) !important;
}
</style>
