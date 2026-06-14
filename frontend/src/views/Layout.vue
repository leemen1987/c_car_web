<template>
  <el-container style="height:100vh">
    <!-- Desktop sidebar -->
    <el-aside v-if="!isMobile" width="240px" class="app-sidebar">
      <div class="logo">包车排班系统</div>
      <el-menu :default-active="activeMenu" class="sidebar-menu" router>
        <el-menu-item index="/tasks" v-if="hasPermission('task')">
          <el-icon><Document /></el-icon>
          <span>任务管理</span>
        </el-menu-item>
        <el-menu-item index="/confirmations" v-if="hasPermission('task')">
          <el-icon><CircleCheck /></el-icon>
          <span>客户确认</span>
        </el-menu-item>
        <el-menu-item index="/drivers" v-if="hasPermission('driver')">
          <el-icon><User /></el-icon>
          <span>司机管理</span>
        </el-menu-item>
        <el-menu-item index="/vehicles" v-if="hasPermission('vehicle')">
          <el-icon><Van /></el-icon>
          <span>车辆管理</span>
        </el-menu-item>
        <el-menu-item index="/clients" v-if="hasPermission('client')">
          <el-icon><OfficeBuilding /></el-icon>
          <span>用车单位</span>
        </el-menu-item>
        <el-menu-item index="/labor-rates" v-if="hasPermission('labor_rate')">
          <el-icon><Money /></el-icon>
          <span>差费标准</span>
        </el-menu-item>
        <el-menu-item index="/reports" v-if="hasPermission('report')">
          <el-icon><DataAnalysis /></el-icon>
          <span>报表管理</span>
        </el-menu-item>
        <el-menu-item index="/permissions" v-if="user?.role === 'admin'">
          <el-icon><Setting /></el-icon>
          <span>权限控制</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- Mobile drawer -->
    <el-drawer v-model="drawerVisible" direction="ltr" :size="260" :show-close="false" :with-header="false" class="mobile-drawer">
      <div class="logo">包车排班系统</div>
      <el-menu :default-active="activeMenu" class="sidebar-menu" router @select="drawerVisible = false">
        <el-menu-item index="/tasks" v-if="hasPermission('task')">
          <el-icon><Document /></el-icon>
          <span>任务管理</span>
        </el-menu-item>
        <el-menu-item index="/confirmations" v-if="hasPermission('task')">
          <el-icon><CircleCheck /></el-icon>
          <span>客户确认</span>
        </el-menu-item>
        <el-menu-item index="/drivers" v-if="hasPermission('driver')">
          <el-icon><User /></el-icon>
          <span>司机管理</span>
        </el-menu-item>
        <el-menu-item index="/vehicles" v-if="hasPermission('vehicle')">
          <el-icon><Van /></el-icon>
          <span>车辆管理</span>
        </el-menu-item>
        <el-menu-item index="/clients" v-if="hasPermission('client')">
          <el-icon><OfficeBuilding /></el-icon>
          <span>用车单位</span>
        </el-menu-item>
        <el-menu-item index="/labor-rates" v-if="hasPermission('labor_rate')">
          <el-icon><Money /></el-icon>
          <span>差费标准</span>
        </el-menu-item>
        <el-menu-item index="/reports" v-if="hasPermission('report')">
          <el-icon><DataAnalysis /></el-icon>
          <span>报表管理</span>
        </el-menu-item>
        <el-menu-item index="/permissions" v-if="user?.role === 'admin'">
          <el-icon><Setting /></el-icon>
          <span>权限控制</span>
        </el-menu-item>
      </el-menu>
    </el-drawer>

    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-icon v-if="isMobile" @click="drawerVisible = true" class="hamburger"><Operation /></el-icon>
          <span v-if="isMobile" class="mobile-title">包车排班系统</span>
        </div>
        <div class="header-right">
          <div class="user-info">
            <el-avatar :size="30" style="background:var(--primary);margin-right:8px">
              {{ user?.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <span class="username">{{ user?.username }}</span>
            <el-tag size="small" type="info" effect="plain" style="margin-left:6px">
              {{ user?.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </div>
          <el-button text class="logout-btn" @click="logout">
            <el-icon><SwitchButton /></el-icon>
            <span style="margin-left:4px">退出</span>
          </el-button>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../utils/api'

const route = useRoute()
const router = useRouter()
const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const drawerVisible = ref(false)
const isMobile = ref(false)

const checkMobile = () => { isMobile.value = window.innerWidth <= 768 }
onMounted(() => { checkMobile(); window.addEventListener('resize', checkMobile) })
onUnmounted(() => window.removeEventListener('resize', checkMobile))

const activeMenu = computed(() => route.path)

const hasPermission = (perm) => {
  if (user.value.role === 'admin') return true
  return (user.value.permissions || []).includes(perm)
}

const logout = async () => {
  try { await api.post('/logout') } catch (e) {}
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
/* ========== 侧边栏 ========== */
.app-sidebar {
  background: linear-gradient(180deg, var(--sidebar-start) 0%, var(--sidebar-end) 100%);
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 0.3s ease;
}
.app-sidebar::-webkit-scrollbar {
  width: 0;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.02em;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  user-select: none;
}
.logo-icon {
  font-size: 22px;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

:deep(.sidebar-menu) {
  border-right: none !important;
  background: transparent !important;
  padding: 8px 0;
}
:deep(.sidebar-menu .el-menu-item) {
  height: 46px;
  line-height: 46px;
  margin: 2px 10px;
  border-radius: 8px;
  color: rgba(255,255,255,0.65) !important;
  transition: all 0.25s ease;
}
:deep(.sidebar-menu .el-menu-item:hover) {
  background: rgba(255,255,255,0.08) !important;
  color: #fff !important;
}
:deep(.sidebar-menu .el-menu-item.is-active) {
  background: rgba(255,255,255,0.12) !important;
  color: #fff !important;
  font-weight: 600;
  position: relative;
}
:deep(.sidebar-menu .el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--accent);
  border-radius: 0 3px 3px 0;
}
:deep(.sidebar-menu .el-menu-item span) {
  margin-left: 8px;
  font-size: 14px;
}

/* ========== 顶栏 ========== */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  padding: 0 24px !important;
  height: 60px !important;
  position: sticky;
  top: 0;
  z-index: 10;
}
.header-left {
  display: flex;
  align-items: center;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.hamburger {
  font-size: 22px;
  cursor: pointer;
  color: var(--text-primary);
  transition: color 0.2s;
}
.hamburger:hover {
  color: var(--primary);
}
.mobile-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-left: 10px;
}
.user-info {
  display: flex;
  align-items: center;
}
.username {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}
.logout-btn {
  color: var(--text-muted) !important;
  font-size: 14px;
  transition: color 0.2s;
}
.logout-btn:hover {
  color: #ef4444 !important;
}

/* ========== 主内容区 ========== */
.app-main {
  background: var(--bg-page);
  padding: 24px !important;
  overflow-y: auto;
}

/* ========== 移动端抽屉 ========== */
:deep(.mobile-drawer .el-drawer__body) {
  background: linear-gradient(180deg, var(--sidebar-start) 0%, var(--sidebar-end) 100%);
  padding: 0;
}
</style>
