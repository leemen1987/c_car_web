<template>
  <el-container style="height:100vh">
    <!-- Desktop sidebar -->
    <el-aside v-if="!isMobile" width="220px" style="background:#304156">
      <div class="logo">包车排班系统</div>
      <el-menu :default-active="activeMenu" background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff" router>
        <el-menu-item index="/tasks" v-if="hasPermission('task')">
          <el-icon><Document /></el-icon>
          <span>任务管理</span>
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
    <el-drawer v-model="drawerVisible" direction="ltr" :size="240" :show-close="false" :with-header="false" style="background:#304156">
      <div class="logo">包车排班系统</div>
      <el-menu :default-active="activeMenu" background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff" router @select="drawerVisible = false">
        <el-menu-item index="/tasks" v-if="hasPermission('task')">
          <el-icon><Document /></el-icon>
          <span>任务管理</span>
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
        <div style="display:flex;align-items:center">
          <el-icon v-if="isMobile" @click="drawerVisible = true" style="font-size:22px;cursor:pointer;margin-right:10px"><Operation /></el-icon>
          <span v-if="isMobile" style="font-size:16px;font-weight:bold">包车排班系统</span>
        </div>
        <div style="display:flex;align-items:center">
          <span style="margin-right:15px;color:#606266;font-size:13px">{{ user?.username }} ({{ user?.role === 'admin' ? '管理员' : '普通用户' }})</span>
          <el-button type="danger" size="small" @click="logout">退出</el-button>
        </div>
      </el-header>
      <el-main :style="isMobile ? 'background:#f0f2f5;padding:10px' : 'background:#f0f2f5;padding:20px'">
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
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #eee;
}
:deep(.el-menu-item) {
  display: flex;
  align-items: center;
  justify-content: center;
}
:deep(.el-menu-item span) {
  margin-left: 6px;
}
</style>
