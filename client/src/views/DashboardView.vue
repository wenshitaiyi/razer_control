<template>
  <div class="dashboard-container">
    <!-- 设备状态卡片 -->
    <div class="rz-card device-header-card glow-green">
      <div class="device-header-left">
        <div class="device-icon-box">
          <el-icon :size="32" color="#00ff00"><Mouse /></el-icon>
        </div>
        <div class="device-info-text">
          <div class="device-title-row">
            <h2 class="device-name">{{ currentDeviceName }}</h2>
            <span v-if="hasDevice" class="rz-badge rz-badge-success">● 已直连 HID</span>
            <span v-else class="rz-badge rz-badge-warning">未发现雷蛇设备 (展示模拟)</span>
          </div>
          <p class="device-desc-text">
            <span>VID: <b>0x1532</b> (Razer)</span>
            <span v-if="selectedDevice" style="margin-left: 12px;">PID: <b>{{ selectedDevice.product_id_hex }}</b></span>
            <span v-if="selectedDevice" style="margin-left: 12px;">接口: <b>#{{ selectedDevice.interface_number }}</b></span>
            <span style="margin-left: 12px;" class="text-mute">通讯模式: 90-byte Feature Report (0-Daemon)</span>
          </p>
        </div>
      </div>
      <div class="device-header-right">
        <el-button
          type="success"
          plain
          :loading="scanning"
          @click="fetchDevices"
          :icon="Refresh"
        >
          刷新硬件
        </el-button>
      </div>
    </div>

    <!-- 主控制网格 -->
    <div class="controls-grid">
      <!-- 1. DPI 灵敏度控制卡片 -->
      <div class="rz-card control-card">
        <div class="card-header">
          <div class="title-with-icon">
            <el-icon color="#00ff00"><Odometer /></el-icon>
            <h3>DPI 灵敏度调节</h3>
          </div>
          <span class="rz-badge rz-badge-info">Class: 0x04 | ID: 0x05</span>
        </div>

        <div class="control-body">
          <div class="dpi-display-box">
            <span class="dpi-val">{{ dpiX }}</span>
            <span class="dpi-unit">DPI</span>
            <span v-if="splitXY" class="dpi-y-tag"> (Y: {{ dpiY }})</span>
          </div>

          <div class="slider-row">
            <span class="slider-label">灵敏度 (X轴)</span>
            <el-slider
              v-model="dpiX"
              :min="100"
              :max="16000"
              :step="50"
              show-input
              :show-input-controls="false"
            />
          </div>

          <div v-if="splitXY" class="slider-row">
            <span class="slider-label">灵敏度 (Y轴)</span>
            <el-slider
              v-model="dpiY"
              :min="100"
              :max="16000"
              :step="50"
              show-input
              :show-input-controls="false"
            />
          </div>

          <!-- 快速档位预设 -->
          <div class="preset-chips">
            <span class="chip-label">常用档位:</span>
            <button
              v-for="d in [400, 800, 1200, 1600, 2400, 3200, 6400]"
              :key="d"
              class="dpi-chip"
              :class="{ active: dpiX === d && (!splitXY || dpiY === d) }"
              @click="setDpiPreset(d)"
            >
              {{ d }}
            </button>
            <el-checkbox v-model="splitXY" label="独立 X/Y 轴" size="small" style="margin-left: auto;" />
          </div>

          <div class="apply-footer">
            <el-button
              type="success"
              class="rz-btn-apply"
              :loading="savingDpi"
              @click="applyDpi"
            >
              应用 DPI 设定
            </el-button>
          </div>
        </div>
      </div>

      <!-- 2. 回报率 (Polling Rate) 卡片 -->
      <div class="rz-card control-card">
        <div class="card-header">
          <div class="title-with-icon">
            <el-icon color="#00ff00"><Timer /></el-icon>
            <h3>轮询回报率 (Polling Rate)</h3>
          </div>
          <span class="rz-badge rz-badge-info">Class: 0x00 | ID: 0x05</span>
        </div>

        <div class="control-body">
          <div class="polling-options">
            <div
              v-for="opt in pollingOptions"
              :key="opt.rate"
              class="polling-card"
              :class="{ active: pollingRate === opt.rate }"
              @click="pollingRate = opt.rate"
            >
              <div class="polling-hz">{{ opt.rate }} Hz</div>
              <div class="polling-latency">延迟 {{ opt.latency }}</div>
              <div class="polling-desc">{{ opt.desc }}</div>
              <span v-if="opt.recommended" class="polling-tag">官方推荐</span>
            </div>
          </div>

          <div class="polling-tip-box">
            <el-icon color="#ffb000" style="margin-right: 6px;"><Warning /></el-icon>
            <span>提示：1000Hz 为业界公认最佳平衡点，完全规避 4K/8K 极端轮询导致的 Windows DWM / GPU 渲染卡顿。</span>
          </div>

          <div class="apply-footer">
            <el-button
              type="success"
              class="rz-btn-apply"
              :loading="savingPolling"
              @click="applyPollingRate"
            >
              应用回报率设定
            </el-button>
          </div>
        </div>
      </div>

      <!-- 3. RGB 灯效 / 关灯控制卡片 -->
      <div class="rz-card control-card">
        <div class="card-header">
          <div class="title-with-icon">
            <el-icon color="#00ff00"><Sunny /></el-icon>
            <h3>RGB 灯效 / 一键熄灭</h3>
          </div>
          <span class="rz-badge rz-badge-info">Class: 0x0F | ID: 0x02</span>
        </div>

        <div class="control-body">
          <!-- 开关与调色器 -->
          <div class="lighting-toggle-row">
            <span class="slider-label">Logo 氛围灯效</span>
            <el-switch
              v-model="ledEnabled"
              active-text="开启静态光"
              inactive-text="彻底关闭 (零眩光/省电)"
              inline-prompt
              style="--el-switch-on-color: #00ff00; --el-switch-off-color: #334155;"
            />
          </div>

          <div v-if="ledEnabled" class="color-picker-box">
            <div class="color-preview-circle" :style="{ backgroundColor: ledColor, boxShadow: `0 0 16px ${ledColor}` }"></div>
            <div class="color-inputs">
              <el-color-picker v-model="ledColor" :predefine="colorPresets" />
              <el-input v-model="ledColor" size="small" style="width: 110px; margin-left: 12px;" />
            </div>
          </div>

          <!-- 预设色板 -->
          <div v-if="ledEnabled" class="color-palette-row">
            <div
              v-for="c in colorPresets"
              :key="c"
              class="palette-dot"
              :style="{ backgroundColor: c }"
              :class="{ active: ledColor.toLowerCase() === c.toLowerCase() }"
              @click="ledColor = c"
            ></div>
          </div>

          <div v-else class="led-off-banner">
            <el-icon color="#8b949e" :size="24"><Moon /></el-icon>
            <p>已选择彻底熄灭灯光。可消除 Chroma 渲染管线开销并大幅提升续航。</p>
          </div>

          <div class="apply-footer">
            <el-button
              type="success"
              class="rz-btn-apply"
              :loading="savingLed"
              @click="applyLighting"
            >
              {{ ledEnabled ? '应用 RGB 静态灯效' : '一键熄灭 Logo 灯' }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- 4. 快捷预设方案卡片 -->
      <div class="rz-card control-card">
        <div class="card-header">
          <div class="title-with-icon">
            <el-icon color="#00ff00"><CollectionTag /></el-icon>
            <h3>快捷预设方案 (一键直达)</h3>
          </div>
          <span class="rz-badge rz-badge-info">SQLite 持久化</span>
        </div>

        <div class="control-body">
          <div class="quick-profile-list">
            <div
              v-for="p in quickProfiles"
              :key="p.id"
              class="quick-profile-item"
              :class="{ active: p.is_active }"
              @click="applyQuickProfile(p.id)"
            >
              <div class="profile-item-left">
                <div class="profile-name">{{ p.name }}</div>
                <div class="profile-params">
                  <span>{{ p.dpi_x }} DPI</span> ·
                  <span>{{ p.polling_rate }} Hz</span> ·
                  <span v-if="p.led_enabled" :style="{ color: `rgb(${p.led_r},${p.led_g},${p.led_b})` }">● 灯光</span>
                  <span v-else class="text-mute">关灯</span>
                </div>
              </div>
              <div class="profile-item-right">
                <el-button size="small" type="success" plain :loading="applyingId === p.id">应用</el-button>
              </div>
            </div>
          </div>

          <div class="profile-hint">
            可在「配置预设」标签页自定义更多场景方案。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Mouse, Refresh, Odometer, Timer, Sunny, Moon, Warning, CollectionTag
} from '@element-plus/icons-vue'
import api from '../api'

const scanning = ref(false)
const devices = ref([])
const selectedDevice = ref(null)

const dpiX = ref(1600)
const dpiY = ref(1600)
const splitXY = ref(false)
const savingDpi = ref(false)

const pollingRate = ref(1000)
const savingPolling = ref(false)

const ledEnabled = ref(false)
const ledColor = ref('#00FF00')
const savingLed = ref(false)

const quickProfiles = ref([])
const applyingId = ref(null)

const colorPresets = [
  '#00FF00', // 雷蛇绿
  '#00F0FF', // 赛博青
  '#9D00FF', // 霓虹紫
  '#FFB000', // 温暖琥珀
  '#FF2A2A', // 烈焰红
  '#FFFFFF', // 极地白
]

const pollingOptions = [
  { rate: 1000, latency: '1.0 ms', desc: '电竞与日常标准，零掉帧', recommended: true },
  { rate: 500, latency: '2.0 ms', desc: '平衡省电模式', recommended: false },
  { rate: 125, latency: '8.0 ms', desc: '低功耗续航档位', recommended: false },
]

const hasDevice = computed(() => devices.value.length > 0)
const currentDeviceName = computed(() => {
  if (selectedDevice.value) {
    return selectedDevice.value.product_string
  }
  return 'Razer 游戏鼠标 (直通控制)'
})

const hexToRgb = (hex) => {
  let c = hex.replace('#', '')
  if (c.length === 3) {
    c = c.split('').map(x => x + x).join('')
  }
  const num = parseInt(c, 16)
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255
  }
}

const fetchDevices = async () => {
  scanning.value = true
  try {
    const res = await api.getDevices()
    if (res.status === 'ok' && res.data) {
      devices.value = res.data.devices || []
      if (devices.value.length > 0) {
        selectedDevice.value = devices.value.find(d => d.is_control_interface) || devices.value[0]
      }
    }
  } catch (err) {
    console.error(err)
  } finally {
    scanning.value = false
  }
}

const fetchProfiles = async () => {
  try {
    const res = await api.getProfiles()
    if (res.status === 'ok') {
      quickProfiles.value = res.data || []
    }
  } catch (err) {
    console.error(err)
  }
}

const setDpiPreset = (val) => {
  dpiX.value = val
  dpiY.value = val
}

const applyDpi = async () => {
  savingDpi.value = true
  try {
    const targetY = splitXY.value ? dpiY.value : dpiX.value
    const path = selectedDevice.value?.path || null
    const res = await api.setDpi(dpiX.value, targetY, path)
    if (res.status === 'ok') {
      ElMessage.success(res.msg || `DPI 已成功设置为 ${dpiX.value}`)
    }
  } catch (e) {
    // 错误在拦截器已弹窗
  } finally {
    savingDpi.value = false
  }
}

const applyPollingRate = async () => {
  savingPolling.value = true
  try {
    const path = selectedDevice.value?.path || null
    const res = await api.setPollingRate(pollingRate.value, path)
    if (res.status === 'ok') {
      ElMessage.success(res.msg || `回报率已设置为 ${pollingRate.value} Hz`)
    }
  } catch (e) {
  } finally {
    savingPolling.value = false
  }
}

const applyLighting = async () => {
  savingLed.value = true
  try {
    const path = selectedDevice.value?.path || null
    const { r, g, b } = hexToRgb(ledColor.value)
    const res = await api.setLighting(ledEnabled.value, r, g, b, path)
    if (res.status === 'ok') {
      ElMessage.success(res.msg || (ledEnabled.value ? '灯效已更新' : '已彻底熄灭灯光'))
    }
  } catch (e) {
  } finally {
    savingLed.value = false
  }
}

const applyQuickProfile = async (id) => {
  applyingId.value = id
  try {
    const path = selectedDevice.value?.path || null
    const res = await api.applyProfile(id, path)
    if (res.status === 'ok') {
      ElMessage.success(res.msg || '预设方案已成功生效')
      await fetchProfiles()
      // 同步界面参数
      const cur = quickProfiles.value.find(p => p.id === id)
      if (cur) {
        dpiX.value = cur.dpi_x
        dpiY.value = cur.dpi_y
        pollingRate.value = cur.polling_rate
        ledEnabled.value = Boolean(cur.led_enabled)
        ledColor.value = `#${((1 << 24) + (cur.led_r << 16) + (cur.led_g << 8) + cur.led_b).toString(16).slice(1).toUpperCase()}`
      }
    }
  } catch (e) {
  } finally {
    applyingId.value = null
  }
}

onMounted(async () => {
  await fetchDevices()
  await fetchProfiles()
})
</script>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.device-header-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #131b26 0%, #162536 100%);
}

.device-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.device-icon-box {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: rgba(0, 255, 0, 0.1);
  border: 1px solid rgba(0, 255, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.device-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.device-name {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
}

.device-desc-text {
  font-size: 13px;
  color: var(--rz-text-secondary);
}

.text-mute {
  color: #6e7681;
}

.controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 20px;
}

.control-card {
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--rz-border);
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-with-icon h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--rz-text-primary);
}

.control-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.dpi-display-box {
  display: flex;
  align-items: baseline;
  justify-content: center;
  background: #0d131c;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #1c2838;
}

.dpi-val {
  font-size: 32px;
  font-weight: 800;
  color: var(--rz-green);
  font-family: monospace;
}

.dpi-unit {
  font-size: 14px;
  color: var(--rz-text-secondary);
  margin-left: 6px;
  font-weight: 600;
}

.dpi-y-tag {
  font-size: 14px;
  color: var(--rz-cyan);
  margin-left: 8px;
}

.slider-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.slider-label {
  font-size: 13px;
  color: var(--rz-text-secondary);
}

.preset-chips {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.chip-label {
  font-size: 12px;
  color: var(--rz-text-secondary);
}

.dpi-chip {
  background: #182332;
  border: 1px solid var(--rz-border);
  color: var(--rz-text-primary);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.dpi-chip:hover {
  border-color: var(--rz-green);
  color: var(--rz-green);
}

.dpi-chip.active {
  background: var(--rz-green-dark);
  border-color: var(--rz-green);
  color: #fff;
  font-weight: 600;
}

.apply-footer {
  margin-top: auto;
  padding-top: 8px;
}

.rz-btn-apply {
  width: 100%;
  background-color: #00aa00 !important;
  border-color: #00aa00 !important;
  font-weight: 600;
}

.rz-btn-apply:hover {
  background-color: var(--rz-green) !important;
  border-color: var(--rz-green) !important;
  color: #000 !important;
}

/* 回报率卡片 */
.polling-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.polling-card {
  background: #0d131c;
  border: 1px solid #1c2838;
  border-radius: 8px;
  padding: 12px 8px;
  text-align: center;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.polling-card:hover {
  border-color: #2e4460;
}

.polling-card.active {
  border-color: var(--rz-green);
  background: rgba(0, 255, 0, 0.08);
  box-shadow: 0 0 10px rgba(0, 255, 0, 0.15);
}

.polling-hz {
  font-size: 18px;
  font-weight: 700;
  color: var(--rz-text-primary);
}

.polling-latency {
  font-size: 12px;
  color: var(--rz-cyan);
  margin-top: 2px;
}

.polling-desc {
  font-size: 11px;
  color: var(--rz-text-secondary);
  margin-top: 4px;
}

.polling-tag {
  position: absolute;
  top: -8px;
  right: 4px;
  background: var(--rz-green-dark);
  color: #fff;
  font-size: 9px;
  padding: 1px 4px;
  border-radius: 3px;
}

.polling-tip-box {
  background: rgba(255, 176, 0, 0.08);
  border: 1px solid rgba(255, 176, 0, 0.25);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12px;
  color: #e6edf3;
  display: flex;
  align-items: flex-start;
}

/* 灯效卡片 */
.lighting-toggle-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.color-picker-box {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #0d131c;
  padding: 14px;
  border-radius: 8px;
  border: 1px solid #1c2838;
}

.color-preview-circle {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 2px solid #ffffff;
  transition: all 0.3s;
}

.color-inputs {
  display: flex;
  align-items: center;
}

.color-palette-row {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.palette-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.palette-dot:hover {
  transform: scale(1.15);
}

.palette-dot.active {
  border-color: #ffffff;
  box-shadow: 0 0 8px #ffffff;
}

.led-off-banner {
  background: #0d131c;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  color: var(--rz-text-secondary);
  font-size: 13px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

/* 快捷预设 */
.quick-profile-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-profile-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #0d131c;
  border: 1px solid #1c2838;
  border-radius: 8px;
  padding: 10px 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-profile-item:hover {
  border-color: #2e4460;
}

.quick-profile-item.active {
  border-color: var(--rz-green);
  background: rgba(0, 255, 0, 0.05);
}

.profile-name {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.profile-params {
  font-size: 12px;
  color: var(--rz-text-secondary);
  margin-top: 2px;
}

.profile-hint {
  font-size: 12px;
  color: var(--rz-text-secondary);
  text-align: center;
}
</style>
