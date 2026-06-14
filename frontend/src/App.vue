<template>
  <router-view v-slot="{ Component }">
    <transition name="page-fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<script setup>
</script>

<style>
/* ========== 全局 CSS 变量 ========== */
:root {
  --primary: #4f46e5;
  --primary-light: #818cf8;
  --primary-dark: #3730a3;
  --accent: #06b6d4;
  --sidebar-start: #1e1b4b;
  --sidebar-end: #312e81;
  --bg-page: #f1f5f9;
  --bg-card: #ffffff;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --border-light: #e2e8f0;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);
  --radius: 10px;
  --radius-sm: 6px;
}

/* ========== 全局重置 ========== */
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  color: var(--text-primary);
  background: var(--bg-page);
  -webkit-font-smoothing: antialiased;
}

#app {
  height: 100vh;
}

/* ========== Element Plus 主题覆盖 ========== */
:root {
  --el-color-primary: #4f46e5;
  --el-color-primary-light-3: #818cf8;
  --el-color-primary-light-5: #a5b4fc;
  --el-color-primary-light-7: #c7d2fe;
  --el-color-primary-light-9: #eef2ff;
  --el-color-primary-dark-2: #3730a3;
  --el-border-radius-base: 8px;
  --el-border-radius-small: 6px;
  --el-font-family: inherit;
}

/* 卡片统一风格 */
.el-card {
  border: none !important;
  border-radius: var(--radius) !important;
  box-shadow: var(--shadow-md) !important;
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}
.el-card:hover {
  box-shadow: var(--shadow-lg) !important;
}
.el-card__header {
  border-bottom: 1px solid var(--border-light) !important;
  padding: 16px 20px !important;
}

/* 表格美化 */
.el-table {
  border-radius: var(--radius-sm) !important;
  overflow: hidden;
}
.el-table th.el-table__cell {
  background: #f8fafc !important;
  color: var(--text-secondary) !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.el-table--border .el-table__inner-wrapper::after,
.el-table--border::before,
.el-table--border::after {
  display: none !important;
}
.el-table .el-table__row:hover > td {
  background: #f1f5f9 !important;
}

/* 按钮微调 */
.el-button--primary {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
  border-radius: var(--radius-sm) !important;
  font-weight: 500;
}
.el-button--primary:hover {
  background: var(--primary-light) !important;
  border-color: var(--primary-light) !important;
}
.el-button {
  border-radius: var(--radius-sm) !important;
  font-weight: 500;
  transition: all 0.2s ease;
}

/* 输入框聚焦发光 */
.el-input__wrapper {
  transition: box-shadow 0.2s ease !important;
}
.el-input__wrapper.is-focus {
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.15) !important;
}

/* Tag 美化 */
.el-tag {
  border-radius: 20px !important;
  font-weight: 500;
  border: none !important;
}

/* 对话框圆角 */
.el-dialog {
  border-radius: var(--radius) !important;
  overflow: hidden;
}
.el-dialog__header {
  padding: 20px 24px 16px !important;
  border-bottom: 1px solid var(--border-light);
}
.el-dialog__body {
  padding: 20px 24px !important;
}

/* ========== 页面切换动画 ========== */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ========== 页面通用布局 ========== */
.page-card .el-card__header {
  padding: 18px 24px !important;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}
.page-title .el-icon {
  color: var(--primary);
}

/* 管理页面操作列按钮 */
.page-card .el-table .cell .el-button--primary.is-link,
.page-card .el-table .cell .el-button--danger.is-link {
  font-weight: 500;
}

/* 报表 Tab 美化 */
.page-card .el-tabs__header {
  margin-bottom: 20px !important;
}
.page-card .el-tabs__item {
  font-size: 14px;
  font-weight: 500;
}
.page-card .el-tabs__item.is-active {
  font-weight: 600;
}
.page-card .el-tabs__active-bar {
  height: 3px;
  border-radius: 3px;
}

/* 统计摘要卡片 */
.page-card .el-descriptions {
  border-radius: var(--radius-sm);
  overflow: hidden;
}
</style>
