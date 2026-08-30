# Razer Control Hub · 雷蛇设备辅助控制子服务

> **零常驻守护进程 · 90-Byte HID 协议直通 · 释放 DWM 与 GPU 渲染算力**

---

## 1. 原始需求与设计背景

### 1.1 用户原始需求
> "我先要要写一个子服务，雷蛇设备辅助控制，前端vue工程式开发。发你的文章是用来参考的。里面有我写这个服务的原因，需要在网页上展示这个项目的目的。项目写好之后需要再帮我建立一个private git仓库上传到github上面"

### 1.2 项目设计背景与痛点起因
在 Windows 系统下使用雷蛇官方驱动（Razer Synapse 3/4、Chroma Studio、Cortex 等）存在严重的性能负担与卡顿诱因：
1. **DWM 渲染与 MPO 冲突**：雷蛇 Chroma 悬浮覆盖层导致 Chrome/Edge/VS Code 在窗口切换时触发 Windows DWM 强制全屏脏矩形重绘（Full Dirty Rect Repaint），造成 GPU 占用突增 **30%~60%** 与明显掉帧；
2. **Game Manager 频繁进程注入**：后台持续轮询 `explorer.exe` 与 `taskmgr.exe`，导致 Alt+Tab 切换窗口时发生微顿挫；
3. **庞大的全家桶常驻开销**：开机自启多达 8 个守护服务，常驻 500MB+ 内存与持续磁盘日志读写。

本项目通过 Python 底层 `hidapi` 直接向雷蛇设备（VID `0x1532`）下发 **90 字节 Feature Report 控制协议**，配置直接固化至板载寄存器，完全无需任何后台守护进程常驻，从根本上解决 DWM 与 GPU 卡顿。

---

## 2. 核心特性与架构

```
┌──────────────────────────────────────────────────────────┐
│                   Vue 3 + Vite 工程前端                  │
│  (设备控制看板 / 预设方案管理 / 服务轻量化助手 / 背景解析)│
└───────────────────────────┬──────────────────────────────┘
                            │ RESTful HTTP / JSON
┌───────────────────────────▼──────────────────────────────┐
│           FastAPI 后端路由 (/api/razer_control)          │
│         RazerControlLogic 业务层 + SQLite 预设持久化     │
└───────────────────────────┬──────────────────────────────┘
                            │ 90-Byte Feature Report
┌───────────────────────────▼──────────────────────────────┐
│                Python hidapi 底层直通驱动                │
└───────────────────────────┬──────────────────────────────┘
                            │ USB / 2.4G HID (VID 0x1532)
┌───────────────────────────▼──────────────────────────────┐
│           雷蛇鼠标硬件 (DeathAdder V2 Pro / 等)           │
└──────────────────────────────────────────────────────────┘
```

- **DPI 灵敏度精准调节**：支持 100~35000 DPI 任意步长、独立 X/Y 轴与常用预设档位（400/800/1200/1600/2400/3200）。
- **轮询回报率切换**：1000Hz（推荐稳定）、500Hz、125Hz 极简下发。
- **Logo 静态 RGB 与一键关灯**：支持任意 Hex 调色盘或一键彻底熄灭，去除光污染与渲染开销。
- **个性化场景预设**：基于 SQLite 本地存储多套参数方案，一键直写硬件。
- **Windows 服务精简助手**：内置一键禁用雷蛇全家桶开机自启 PowerShell 脚本与 Chrome MPO 调优指南。
- **完整通信审计**：记录每笔向 HID 端口发送的 Hex 载荷与 ACK 返回码。

---

## 3. 接口概览

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/razer_control/health` | GET | 服务存活探测 |
| `/api/razer_control/devices` | GET | 扫描系统连接的雷蛇 HID 设备 |
| `/api/razer_control/dpi` | POST | 下发 DPI 灵敏度参数 |
| `/api/razer_control/polling-rate` | POST | 下发回报率参数 (1000/500/125Hz) |
| `/api/razer_control/lighting` | POST | 下发静态 RGB 灯效或彻底熄灭 |
| `/api/razer_control/profiles` | GET/POST | 预设配置方案获取与创建 |
| `/api/razer_control/profiles/{id}` | PUT/DELETE | 预设配置方案修改与删除 |
| `/api/razer_control/profiles/{id}/apply` | POST | 一键将指定预设应用至设备 |
| `/api/razer_control/system/services` | GET | 检测 Windows 雷蛇服务运行状态 |
| `/api/razer_control/logs` | GET | 查询最近硬件通信审计日志 |

---

## 4. 前端开发与构建

```bash
# 进入前端源码目录
cd services/razer_control/client

# 安装依赖
npm install

# 本地调试
npm run dev

# 构建输出到 ../dist (框架统一托管在 /ui/razer_control/)
npm run build
```

---

## 5. 快速启动与访问

在项目根目录下启动主框架：
```powershell
.\venv\Scripts\python.exe main.py
```
- **Web 控制台界面**：`http://localhost:8000/ui/razer_control/`
- **Swagger API 文档**：`http://localhost:8000/docs`
