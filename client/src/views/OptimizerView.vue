<template>
  <div class="optimizer-container">
    <!-- 头部横幅 -->
    <div class="rz-card banner-card glow-green">
      <div class="banner-left">
        <div class="banner-icon">
          <el-icon :size="32" color="#00ff00"><Odometer /></el-icon>
        </div>
        <div>
          <h2 class="banner-title">系统常驻服务轻量化与 DWM 防卡顿助手</h2>
          <p class="banner-desc">
            检测 Windows 系统中由于雷蛇官方驱动（Synapse / Chroma / Game Manager）驻留后台带来的卡顿诱因，提供一键精简脚本与浏览器渲染调优方案。
          </p>
        </div>
      </div>
      <div class="banner-right">
        <el-button type="success" plain :loading="scanning" :icon="Refresh" @click="fetchServices">
          重新诊断服务
        </el-button>
      </div>
    </div>

    <!-- 诊断汇总指标 -->
    <div class="stat-metrics-row">
      <div class="rz-card metric-card">
        <span class="metric-label">已检测雷蛇后台服务</span>
        <div class="metric-val">{{ serviceList.length }} <small>项</small></div>
      </div>
      <div class="rz-card metric-card">
        <span class="metric-label">当前运行中服务 (占用资源)</span>
        <div class="metric-val" :class="runningCount > 0 ? 'text-danger' : 'text-success'">
          {{ runningCount }} <small>项</small>
        </div>
      </div>
      <div class="rz-card metric-card">
        <span class="metric-label">系统健康状态</span>
        <div class="metric-val" :class="runningCount > 0 ? 'text-warning' : 'text-success'">
          {{ runningCount > 0 ? '存在后台卡顿隐患' : '已彻底轻量化 (纯净)' }}
        </div>
      </div>
    </div>

    <!-- 一键清理 PowerShell 脚本区块 -->
    <div class="rz-card script-card">
      <div class="script-header">
        <div class="title-with-icon">
          <el-icon color="#00ff00"><DocumentCopy /></el-icon>
          <h3>一键停止并禁用雷蛇后台常驻服务 (PowerShell)</h3>
        </div>
        <el-button type="success" size="small" :icon="CopyDocument" @click="copyScript">
          复制一键清理脚本
        </el-button>
      </div>
      <p class="script-intro">
        以 <b>管理员身份</b> 打开 PowerShell 终端，粘贴并回车执行下列命令即可一键停止并禁用全部雷蛇开机自启服务，硬件参数已固化至板载，不影响鼠标正常使用：
      </p>
      <pre class="script-code"><code>{{ cleanupScript }}</code></pre>
    </div>

    <!-- 服务详细排查列表 -->
    <div class="rz-card services-list-card">
      <div class="list-header">
        <h3>雷蛇后台常驻服务清单与风险排查</h3>
        <span class="rz-badge rz-badge-info">实时进程/服务检测</span>
      </div>

      <el-table :data="serviceList" style="width: 100%" v-loading="scanning" row-class-name="rz-table-row">
        <el-table-column prop="name" label="服务名称 (Service Name)" min-width="180">
          <template #default="{ row }">
            <div style="font-weight: 600; color: #fff;">{{ row.name }}</div>
            <div style="font-size: 11px; color: #8b949e;">{{ row.display_name }}</div>
          </template>
        </el-table-column>

        <el-table-column prop="risk_level" label="卡顿影响等级" width="130">
          <template #default="{ row }">
            <span
              class="rz-badge"
              :class="{
                'rz-badge-danger': row.risk_level === 'Critical',
                'rz-badge-warning': row.risk_level === 'High',
                'rz-badge-info': row.risk_level === 'Medium'
              }"
            >
              {{ row.risk_level }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="impact" label="卡顿诱因与行为机制" min-width="260">
          <template #default="{ row }">
            <span style="font-size: 12px; color: #cbd5e1;">{{ row.impact }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="运行状态" width="120">
          <template #default="{ row }">
            <span v-if="row.is_running" class="status-dot dot-running">● 运行中</span>
            <span v-else-if="row.exists" class="status-dot dot-stopped">○ 已停止</span>
            <span v-else class="status-dot dot-none">- 未安装</span>
          </template>
        </el-table-column>

        <el-table-column prop="start_type" label="启动类型" width="120">
          <template #default="{ row }">
            <span :class="row.is_disabled ? 'text-success' : (row.is_running ? 'text-danger' : '')" style="font-size: 12px; font-weight: 600;">
              {{ row.start_type }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 浏览器与 DWM MPO 硬件加速调优指南 -->
    <div class="rz-card guide-card">
      <div class="list-header">
        <div class="title-with-icon">
          <el-icon color="#00ff00"><Tools /></el-icon>
          <h3>Chrome / Edge 浏览器与 Windows DWM 防掉帧优化建议</h3>
        </div>
      </div>
      <div class="guide-steps">
        <div class="step-item">
          <div class="step-num">1</div>
          <div class="step-content">
            <h4>调整 Chrome 图形后端 (解决 MPO 多平面叠加冲突)</h4>
            <p>
              在 Chrome / Edge 地址栏输入 <code>chrome://flags</code>，搜索 <b>Choose ANGLE graphics backend</b>，将默认值改为 <b>OpenGL</b> 或 <b>D3D11on12</b>。重启浏览器后可彻底解除 Chrome 与 Windows DWM 在窗口切换时的硬件合成死锁。
            </p>
          </div>
        </div>

        <div class="step-item">
          <div class="step-num">2</div>
          <div class="step-content">
            <h4>解除雷云与关联游戏/程序的监听绑定</h4>
            <p>
              如暂未卸载雷云，请在 Synapse 菜单中进入 <b>PROFILES -> LINKED GAMES / APPS</b>，解除对 <code>chrome.exe</code>、<code>explorer.exe</code>、<code>taskmgr.exe</code> 等程序的绑定，避免雷云频繁 Hook 注入触发重绘。
            </p>
          </div>
        </div>

        <div class="step-item">
          <div class="step-num">3</div>
          <div class="step-content">
            <h4>关闭 Chroma Visualizer 屏幕取色与音频采样</h4>
            <p>
              雷蛇 Chroma 幻彩的屏幕捕获（Ambient Awareness）和音频可视化功能会持续以极高帧率抓取桌面缓冲区，极大推高 GPU 占用。请在需要纯净体验时彻底关闭该模块。
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, DocumentCopy, CopyDocument, Tools, Odometer } from '@element-plus/icons-vue'
import api from '../api'

const scanning = ref(false)
const serviceList = ref([])
const runningCount = ref(0)
const cleanupScript = ref('')

const fetchServices = async () => {
  scanning.value = true
  try {
    const res = await api.getSystemServices()
    if (res && (res.status === 'success' || res.code === 200 || res.status === 'ok') && res.data) {
      serviceList.value = res.data.services || []
      runningCount.value = res.data.running_count || 0
      cleanupScript.value = res.data.cleanup_script || ''
    }
  } catch (err) {
    console.error(err)
  } finally {
    scanning.value = false
  }
}

const copyScript = async () => {
  try {
    await navigator.clipboard.writeText(cleanupScript.value)
    ElMessage.success('PowerShell 清理脚本已成功复制到剪贴板')
  } catch (err) {
    ElMessage.info('复制失败，请手动选中代码框内容复制')
  }
}

onMounted(() => {
  fetchServices()
})
</script>

<style scoped>
.optimizer-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.banner-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #131b26 0%, #172a38 100%);
}

.banner-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.banner-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: rgba(0, 255, 0, 0.1);
  border: 1px solid rgba(0, 255, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-title {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
}

.banner-desc {
  font-size: 13px;
  color: var(--rz-text-secondary);
  margin-top: 4px;
  max-width: 800px;
}

.stat-metrics-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-label {
  font-size: 12px;
  color: var(--rz-text-secondary);
}

.metric-val {
  font-size: 24px;
  font-weight: 800;
  color: #fff;
}

.metric-val small {
  font-size: 13px;
  font-weight: 400;
  color: var(--rz-text-secondary);
}

.text-danger {
  color: #ff4d4f !important;
}

.text-warning {
  color: #ffb000 !important;
}

.text-success {
  color: #00ff00 !important;
}

/* 脚本区块 */
.script-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.script-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-with-icon h3 {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.script-intro {
  font-size: 13px;
  color: var(--rz-text-secondary);
}

.script-code {
  background: #090d14;
  border: 1px solid #1c2838;
  border-radius: 8px;
  padding: 14px;
  font-family: Consolas, "Courier New", monospace;
  font-size: 12px;
  color: #00f0ff;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* 服务列表表格 */
.services-list-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-dot {
  font-size: 12px;
  font-weight: 600;
}

.dot-running {
  color: #ff4d4f;
}

.dot-stopped {
  color: #00ff00;
}

.dot-none {
  color: #6e7681;
}

/* 调优步骤 */
.guide-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.guide-steps {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.step-item {
  display: flex;
  gap: 14px;
  background: #0d131c;
  padding: 14px;
  border-radius: 8px;
  border: 1px solid #1c2838;
}

.step-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--rz-green-dark);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 15px;
  flex-shrink: 0;
}

.step-content h4 {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
}

.step-content p {
  font-size: 13px;
  color: var(--rz-text-secondary);
  line-height: 1.5;
}

.step-content code {
  background: #1a2535;
  color: var(--rz-green);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}
</style>
