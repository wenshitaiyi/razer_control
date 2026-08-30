<template>
  <div class="logs-container">
    <div class="header-action-row">
      <div>
        <h2 class="section-title">硬件通信与指令审计日志</h2>
        <p class="section-subtitle">查看所有向雷蛇 HID 接口下发的底层 90 字节 Feature Report 指令及设备 ACK 状态。</p>
      </div>
      <el-button type="success" plain :icon="Refresh" :loading="loading" @click="fetchLogs">
        刷新日志
      </el-button>
    </div>

    <div class="rz-card logs-table-card">
      <el-table :data="logs" style="width: 100%" v-loading="loading" empty-text="暂无硬件通信日志">
        <el-table-column prop="id" label="ID" width="70" />
        
        <el-table-column prop="created_at" label="执行时间" width="170">
          <template #default="{ row }">
            <span style="font-family: monospace; color: var(--rz-cyan);">{{ row.created_at }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="action" label="操作类型" width="180">
          <template #default="{ row }">
            <span class="action-tag" :class="getActionClass(row.action)">{{ row.action }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="target_device" label="目标设备" min-width="160">
          <template #default="{ row }">
            <span style="font-weight: 600; color: #fff;">{{ row.target_device || '默认控制接口' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="payload" label="指令载荷 (Payload)" min-width="220">
          <template #default="{ row }">
            <code class="payload-code">{{ row.payload }}</code>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="ACK 状态" width="120">
          <template #default="{ row }">
            <span
              class="rz-badge"
              :class="row.status === 'SUCCESS' ? 'rz-badge-success' : 'rz-badge-danger'"
            >
              {{ row.status }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="message" label="返回信息" min-width="200">
          <template #default="{ row }">
            <span style="font-size: 12px; color: #8b949e;">{{ row.message }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import api from '../api'

const logs = ref([])
const loading = ref(false)

const fetchLogs = async () => {
  loading.value = true
  try {
    const res = await api.getLogs(60)
    if (res && (res.status === 'success' || res.code === 200 || res.status === 'ok')) {
      logs.value = res.data || []
    }
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const getActionClass = (action) => {
  if (action === 'SET_DPI') return 'tag-dpi'
  if (action === 'SET_POLLING_RATE') return 'tag-polling'
  if (action === 'SET_LED_RGB') return 'tag-rgb'
  if (action === 'TURN_OFF_LED') return 'tag-off'
  return ''
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.logs-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header-action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.section-subtitle {
  font-size: 13px;
  color: var(--rz-text-secondary);
  margin-top: 4px;
}

.logs-table-card {
  padding: 16px;
}

.action-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  background: #1c2838;
  color: #fff;
}

.tag-dpi {
  background: rgba(0, 255, 0, 0.15);
  color: #00ff00;
  border: 1px solid rgba(0, 255, 0, 0.3);
}

.tag-polling {
  background: rgba(0, 240, 255, 0.15);
  color: #00f0ff;
  border: 1px solid rgba(0, 240, 255, 0.3);
}

.tag-rgb {
  background: rgba(157, 0, 255, 0.15);
  color: #c772ff;
  border: 1px solid rgba(157, 0, 255, 0.3);
}

.tag-off {
  background: rgba(255, 255, 255, 0.1);
  color: #8b949e;
  border: 1px solid #30363d;
}

.payload-code {
  font-family: Consolas, monospace;
  font-size: 12px;
  color: #e6edf3;
  background: #090d14;
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
