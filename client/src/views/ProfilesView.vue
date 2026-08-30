<template>
  <div class="profiles-container">
    <div class="header-action-row">
      <div>
        <h2 class="section-title">配置预设方案管理</h2>
        <p class="section-subtitle">保存您的个性化场景配置（游戏、编码、办公、夜间无光），一键直写硬件板载寄存器。</p>
      </div>
      <el-button type="success" :icon="Plus" @click="openCreateDialog">
        新建预设方案
      </el-button>
    </div>

    <div class="profiles-grid">
      <div
        v-for="p in profiles"
        :key="p.id"
        class="rz-card profile-card"
        :class="{ 'glow-green': p.is_active }"
      >
        <div class="profile-card-header">
          <div class="profile-card-title">
            <span class="profile-name">{{ p.name }}</span>
            <span v-if="p.is_active" class="rz-badge rz-badge-success">当前生效</span>
          </div>
          <div class="profile-card-actions">
            <el-button size="small" circle :icon="Edit" @click="openEditDialog(p)" />
            <el-button size="small" type="danger" circle :icon="Delete" @click="deleteProfile(p.id)" />
          </div>
        </div>

        <p class="profile-desc">{{ p.description || '暂无描述' }}</p>

        <div class="profile-meta-grid">
          <div class="meta-item">
            <span class="meta-label">DPI 灵敏度</span>
            <span class="meta-val highlight-green">{{ p.dpi_x }} <small v-if="p.dpi_x !== p.dpi_y">/ {{ p.dpi_y }}</small></span>
          </div>
          <div class="meta-item">
            <span class="meta-label">回报率 (Hz)</span>
            <span class="meta-val highlight-cyan">{{ p.polling_rate }} Hz</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Logo 灯光</span>
            <span v-if="p.led_enabled" class="meta-val" :style="{ color: `rgb(${p.led_r},${p.led_g},${p.led_b})` }">
              ● RGB ({{ p.led_r }},{{ p.led_g }},{{ p.led_b }})
            </span>
            <span v-else class="meta-val text-mute">彻底熄灭</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">更新时间</span>
            <span class="meta-val text-mute">{{ p.updated_at ? p.updated_at.split(' ')[0] : '-' }}</span>
          </div>
        </div>

        <div class="profile-card-footer">
          <el-button
            type="success"
            :plain="!p.is_active"
            :loading="applyingId === p.id"
            style="width: 100%; font-weight: 600;"
            @click="applyProfile(p.id)"
          >
            {{ p.is_active ? '已在设备生效 (点击重新同步)' : '应用此预设到设备' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- 创建/编辑预设弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑预设方案' : '新建预设方案'"
      width="520px"
      destroy-on-close
    >
      <el-form :model="formData" label-width="100px" label-position="left">
        <el-form-item label="方案名称" required>
          <el-input v-model="formData.name" placeholder="例如：CS:GO 竞技模式" />
        </el-form-item>
        <el-form-item label="方案描述">
          <el-input v-model="formData.description" type="textarea" placeholder="填写方案适用场景或特性" />
        </el-form-item>
        <el-form-item label="DPI (X轴)" required>
          <el-slider v-model="formData.dpi_x" :min="100" :max="16000" :step="50" show-input />
        </el-form-item>
        <el-form-item label="DPI (Y轴)">
          <el-slider v-model="formData.dpi_y" :min="100" :max="16000" :step="50" show-input />
        </el-form-item>
        <el-form-item label="回报率" required>
          <el-radio-group v-model="formData.polling_rate">
            <el-radio-button :value="1000">1000 Hz</el-radio-button>
            <el-radio-button :value="500">500 Hz</el-radio-button>
            <el-radio-button :value="125">125 Hz</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="Logo 灯效">
          <el-switch
            v-model="formData.led_enabled_bool"
            active-text="开启静态光"
            inactive-text="关闭 (0-Chroma)"
          />
        </el-form-item>
        <el-form-item v-if="formData.led_enabled_bool" label="灯光颜色">
          <div style="display: flex; align-items: center; gap: 12px;">
            <el-color-picker v-model="formData.hex_color" />
            <el-input v-model="formData.hex_color" style="width: 120px;" />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="success" :loading="submitting" @click="submitProfile">
          保存方案
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import api from '../api'

const profiles = ref([])
const applyingId = ref(null)

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)

const formData = ref({
  id: null,
  name: '',
  description: '',
  dpi_x: 1600,
  dpi_y: 1600,
  polling_rate: 1000,
  led_enabled_bool: true,
  hex_color: '#00FF00'
})

const hexToRgb = (hex) => {
  let c = hex.replace('#', '')
  if (c.length === 3) c = c.split('').map(x => x + x).join('')
  const num = parseInt(c, 16)
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255
  }
}

const rgbToHex = (r, g, b) => {
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase()}`
}

const fetchProfiles = async () => {
  try {
    const res = await api.getProfiles()
    if (res.status === 'ok') {
      profiles.value = res.data || []
    }
  } catch (err) {
    console.error(err)
  }
}

const openCreateDialog = () => {
  isEdit.value = false
  formData.value = {
    id: null,
    name: '',
    description: '',
    dpi_x: 1600,
    dpi_y: 1600,
    polling_rate: 1000,
    led_enabled_bool: false,
    hex_color: '#00FF00'
  }
  dialogVisible.value = true
}

const openEditDialog = (p) => {
  isEdit.value = true
  formData.value = {
    id: p.id,
    name: p.name,
    description: p.description,
    dpi_x: p.dpi_x,
    dpi_y: p.dpi_y,
    polling_rate: p.polling_rate,
    led_enabled_bool: Boolean(p.led_enabled),
    hex_color: rgbToHex(p.led_r, p.led_g, p.led_b)
  }
  dialogVisible.value = true
}

const submitProfile = async () => {
  if (!formData.value.name.trim()) {
    ElMessage.warning('请输入方案名称')
    return
  }
  submitting.value = true
  try {
    const { r, g, b } = hexToRgb(formData.value.hex_color)
    const payload = {
      name: formData.value.name,
      description: formData.value.description,
      dpi_x: formData.value.dpi_x,
      dpi_y: formData.value.dpi_y,
      polling_rate: formData.value.polling_rate,
      led_enabled: formData.value.led_enabled_bool ? 1 : 0,
      led_r: r,
      led_g: g,
      led_b: b
    }

    if (isEdit.value) {
      await api.updateProfile(formData.value.id, payload)
      ElMessage.success('方案修改成功')
    } else {
      await api.createProfile(payload)
      ElMessage.success('新方案创建成功')
    }
    dialogVisible.value = false
    await fetchProfiles()
  } catch (err) {
  } finally {
    submitting.value = false
  }
}

const deleteProfile = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该预设配置方案吗？', '提示', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })
    await api.deleteProfile(id)
    ElMessage.success('已删除预设方案')
    await fetchProfiles()
  } catch (e) {
  }
}

const applyProfile = async (id) => {
  applyingId.value = id
  try {
    const res = await api.applyProfile(id)
    if (res.status === 'ok') {
      ElMessage.success(res.msg || '预设方案已成功写入设备')
      await fetchProfiles()
    }
  } catch (e) {
  } finally {
    applyingId.value = null
  }
}

onMounted(() => {
  fetchProfiles()
})
</script>

<style scoped>
.profiles-container {
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

.profiles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.profile-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.profile-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.profile-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.profile-name {
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
}

.profile-desc {
  font-size: 13px;
  color: var(--rz-text-secondary);
  margin-top: 8px;
  min-height: 38px;
}

.profile-meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  background: #0d131c;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #1c2838;
  margin: 14px 0;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-label {
  font-size: 11px;
  color: var(--rz-text-secondary);
}

.meta-val {
  font-size: 13px;
  font-weight: 600;
  color: #e6edf3;
}

.highlight-green {
  color: var(--rz-green);
  font-family: monospace;
  font-size: 14px;
}

.highlight-cyan {
  color: var(--rz-cyan);
}

.text-mute {
  color: #6e7681;
}

.profile-card-footer {
  margin-top: auto;
}
</style>
