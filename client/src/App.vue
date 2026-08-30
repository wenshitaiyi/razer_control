<template>
  <div class="app-layout">
    <!-- 顶部导航栏 -->
    <header class="navbar">
      <div class="nav-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="#00ff00">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14h2v2h-2zm0-10h2v8h-2z" />
          </svg>
        </div>
        <div class="brand-text">
          <span class="brand-title">RAZER CONTROL HUB</span>
          <span class="brand-tag">0-Daemon HID</span>
        </div>
      </div>

      <nav class="nav-links">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="nav-tab"
          :class="{ active: currentTab === tab.key }"
          @click="currentTab = tab.key"
        >
          <el-icon class="tab-icon"><component :is="tab.icon" /></el-icon>
          <span>{{ tab.label }}</span>
        </button>
      </nav>

      <div class="nav-extra">
        <span class="hub-status-pill">
          <span class="status-indicator"></span> Py-Lite-Server
        </span>
      </div>
    </header>

    <!-- 主体内容区域 -->
    <main class="main-content">
      <DashboardView v-if="currentTab === 'dashboard'" />
      <ProfilesView v-else-if="currentTab === 'profiles'" />
      <OptimizerView v-else-if="currentTab === 'optimizer'" />
      <AboutView v-else-if="currentTab === 'about'" />
      <LogsView v-else-if="currentTab === 'logs'" />
    </main>

    <!-- 底部标识 -->
    <footer class="app-footer">
      <span>Razer Control Hub · 基于 Python HIDAPI 与 Vue 3 构建的轻量级雷蛇硬件控制台</span>
      <span style="color: #6e7681;">| 告别雷云全家桶，释放 DWM / GPU 算力</span>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import {
  Mouse, CollectionTag, Odometer, InfoFilled, Document
} from '@element-plus/icons-vue'

import DashboardView from './views/DashboardView.vue'
import ProfilesView from './views/ProfilesView.vue'
import OptimizerView from './views/OptimizerView.vue'
import AboutView from './views/AboutView.vue'
import LogsView from './views/LogsView.vue'

const currentTab = ref('dashboard')

const tabs = [
  { key: 'dashboard', label: '设备控制中心', icon: Mouse },
  { key: 'profiles', label: '配置预设方案', icon: CollectionTag },
  { key: 'optimizer', label: '系统轻量化助手', icon: Odometer },
  { key: 'about', label: '项目背景与原理解析', icon: InfoFilled },
  { key: 'logs', label: '通信审计日志', icon: Document }
]
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  height: 64px;
  background: rgba(19, 27, 38, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--rz-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo {
  width: 36px;
  height: 36px;
  background: rgba(0, 255, 0, 0.1);
  border: 1px solid rgba(0, 255, 0, 0.3);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 1px;
  color: #ffffff;
}

.brand-tag {
  font-size: 10px;
  color: var(--rz-green);
  font-weight: 700;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-tab {
  background: transparent;
  border: 1px solid transparent;
  color: var(--rz-text-secondary);
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.nav-tab:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.05);
}

.nav-tab.active {
  color: #ffffff;
  background: #182535;
  border-color: rgba(0, 255, 0, 0.4);
  box-shadow: 0 0 10px rgba(0, 255, 0, 0.15);
}

.tab-icon {
  font-size: 15px;
}

.nav-tab.active .tab-icon {
  color: var(--rz-green);
}

.hub-status-pill {
  font-size: 12px;
  background: #0d131c;
  border: 1px solid #1c2838;
  padding: 4px 10px;
  border-radius: 20px;
  color: #8b949e;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--rz-green);
  box-shadow: 0 0 8px var(--rz-green);
}

.main-content {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 28px 20px;
}

.app-footer {
  padding: 20px;
  text-align: center;
  border-top: 1px solid var(--rz-border);
  font-size: 12px;
  color: var(--rz-text-secondary);
  display: flex;
  justify-content: center;
  gap: 8px;
}
</style>
