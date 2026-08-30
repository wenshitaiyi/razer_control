import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api/razer_control',
  timeout: 8000,
})

api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const msg = error.response?.data?.msg || error.message || '网络请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default {
  // 设备与控制
  getDevices: () => api.get('/devices'),
  setDpi: (dpi_x, dpi_y = null, target_path = null) =>
    api.post('/dpi', { dpi_x, dpi_y: dpi_y || dpi_x, target_path }),
  setPollingRate: (rate_hz, target_path = null) =>
    api.post('/polling-rate', { rate_hz, target_path }),
  setLighting: (enabled, r = 0, g = 255, b = 0, target_path = null) =>
    api.post('/lighting', { enabled, r, g, b, target_path }),

  // 预设配置方案
  getProfiles: () => api.get('/profiles'),
  createProfile: (data) => api.post('/profiles', data),
  updateProfile: (id, data) => api.put(`/profiles/${id}`, data),
  deleteProfile: (id) => api.delete(`/profiles/${id}`),
  applyProfile: (id, target_path = null) =>
    api.post(`/profiles/${id}/apply${target_path ? `?target_path=${encodeURIComponent(target_path)}` : ''}`),

  // 系统服务与优化
  getSystemServices: () => api.get('/system/services'),

  // 审计日志
  getLogs: (limit = 50) => api.get(`/logs?limit=${limit}`),
}
