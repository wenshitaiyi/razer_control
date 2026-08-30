<template>
  <div class="about-container">
    <!-- 项目宗旨横幅 -->
    <div class="rz-card hero-card glow-green">
      <h1 class="hero-title rz-gradient-title">为什么开发本雷蛇辅助控制服务？</h1>
      <p class="hero-desc">
        彻底摆脱臃肿卡顿的官方雷云（Razer Synapse / Central / Chroma）常驻全家桶。
        通过纯粹的 <b>Python HID Direct 90-Byte 协议直通</b>，在零后台守护进程、零 GPU 占用的前提下，实现对雷蛇硬件板载 DPI、1000Hz 轮询率与静态灯效的精准控制。
      </p>
    </div>

    <!-- 核心卡顿机理深度剖析 (根据技术复盘整理) -->
    <div class="rz-card section-card">
      <div class="section-header">
        <el-icon color="#ff4d4f" :size="20"><WarningFilled /></el-icon>
        <h3>官方驱动带来的 Windows DWM / GPU 渲染卡顿机理</h3>
      </div>

      <div class="issues-grid">
        <div class="issue-card">
          <div class="issue-tag red-tag">痛点 1 · MPO 与 DWM 硬件加速图层冲突</div>
          <h4>Chrome / VS Code 切换时的严重掉帧</h4>
          <p>
            雷蛇 Chroma 幻彩驱动会在 Windows 桌面窗口管理器（DWM）之上建立透明 XAML 覆盖层。当用户在启用了 MPO（Multi-Plane Overlay）多平面叠加的浏览器或编辑器（Chrome / Edge / VS Code）与桌面窗口间切换焦点时，DWM 无法进行硬件直通合成，被迫退化为 <b>Full Dirty Rect Repaint（全屏脏矩形全量重绘）</b>，瞬间造成 GPU 占用飙升 <b>30% ~ 60%</b> 并不定频掉帧。
          </p>
        </div>

        <div class="issue-card">
          <div class="issue-tag orange-tag">痛点 2 · 进程注入与后台频繁轮询</div>
          <h4>Game Manager 频繁扫描 explorer / 任务管理器</h4>
          <p>
            雷云后台常驻的 <code>Razer Game Manager Service</code> 持续轮询前台活动进程，并尝试向 <code>explorer.exe</code>、<code>taskmgr.exe</code> 注入钩子。每次 Alt+Tab 切换窗口，雷云均会尝试重新判定 Profile 配置文件，带来明显的输入卡顿与微秒级鼠标顿挫。
          </p>
        </div>

        <div class="issue-card">
          <div class="issue-tag yellow-tag">痛点 3 · 8+ 常驻守护服务与超大内存占用</div>
          <h4>开机常驻 8 个后台服务，消耗数百兆内存</h4>
          <p>
            雷蛇全家桶包含 Central、Synapse、Chroma Server、Chroma Stream、Cortex 等多达 8 个 Windows 驱动服务，开机即常驻数百兆内存，频繁写入日志文件，并长期保持数十个后台线程唤醒。
          </p>
        </div>
      </div>
    </div>

    <!-- 架构对比：传统雷云 vs 本项目直通架构 -->
    <div class="rz-card section-card">
      <div class="section-header">
        <el-icon color="#00ff00" :size="20"><DataAnalysis /></el-icon>
        <h3>技术方案对比：传统官方全家桶 VS 本项目直通控制</h3>
      </div>

      <div class="comparison-table-wrapper">
        <table class="comparison-table">
          <thead>
            <tr>
              <th>对比维度</th>
              <th>雷蛇官方雷云 (Synapse 3/4)</th>
              <th>本项目 (Razer Control Hub)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><b>后台守护进程</b></td>
              <td class="bad-text">8+ 个常驻后台 Windows 服务</td>
              <td class="good-text"><b>0 守护进程 (纯按需瞬时通信)</b></td>
            </tr>
            <tr>
              <td><b>内存与 CPU 开销</b></td>
              <td class="bad-text">常驻 300MB ~ 600MB 内存</td>
              <td class="good-text"><b>常驻 0 占用 (微服务按需调用)</b></td>
            </tr>
            <tr>
              <td><b>GPU / DWM 影响</b></td>
              <td class="bad-text">XAML 悬浮层强占，频繁触发 DWM 重绘</td>
              <td class="good-text"><b>完全无注入，GPU 0% 额外渲染开销</b></td>
            </tr>
            <tr>
              <td><b>硬件通信原理</b></td>
              <td class="bad-text">多层 RPC 封装 + 复杂云端同步</td>
              <td class="good-text"><b>底层直接下发 90-Byte HID Feature Report</b></td>
            </tr>
            <tr>
              <td><b>参数保存机制</b></td>
              <td class="warn-text">依赖本地云账号配置频繁重载</td>
              <td class="good-text"><b>写入硬件板载寄存器，关机重启依然生效</b></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 硬件底层 90 字节 Feature Report 协议技术细节 -->
    <div class="rz-card section-card">
      <div class="section-header">
        <el-icon color="#00f0ff" :size="20"><Cpu /></el-icon>
        <h3>雷蛇 90-Byte HID Feature Report 协议解析</h3>
      </div>

      <div class="protocol-box">
        <p class="protocol-intro">
          本项目基于 Python <code>hidapi</code> 库，直接与雷蛇鼠标的 USB / 2.4G 接收器（VID <code>0x1532</code>）建立通信管道，报文格式严格遵循雷蛇标准 90 字节数据帧：
        </p>

        <div class="packet-breakdown">
          <div class="packet-byte-item">
            <span class="byte-index">Byte 0</span>
            <span class="byte-name">Status (0x00)</span>
          </div>
          <div class="packet-byte-item">
            <span class="byte-index">Byte 1</span>
            <span class="byte-name">TransID (0xFF)</span>
          </div>
          <div class="packet-byte-item">
            <span class="byte-index">Byte 2..3</span>
            <span class="byte-name">Protocol (0x00)</span>
          </div>
          <div class="packet-byte-item">
            <span class="byte-index">Byte 4</span>
            <span class="byte-name">Data Size</span>
          </div>
          <div class="packet-byte-item highlight-packet">
            <span class="byte-index">Byte 5</span>
            <span class="byte-name">Cmd Class</span>
          </div>
          <div class="packet-byte-item highlight-packet">
            <span class="byte-index">Byte 6</span>
            <span class="byte-name">Cmd ID</span>
          </div>
          <div class="packet-byte-item">
            <span class="byte-index">Byte 7..87</span>
            <span class="byte-name">Arguments 载荷</span>
          </div>
          <div class="packet-byte-item highlight-packet">
            <span class="byte-index">Byte 88</span>
            <span class="byte-name">XOR Checksum</span>
          </div>
          <div class="packet-byte-item">
            <span class="byte-index">Byte 89</span>
            <span class="byte-name">Reserved (0x00)</span>
          </div>
        </div>

        <div class="protocol-code-sample">
          <pre><code># 校验和计算公式：第 2 字节至第 87 字节连续异或
checksum = 0
for byte in report[2:88]:
    checksum ^= byte
report[88] = checksum</code></pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { WarningFilled, DataAnalysis, Cpu } from '@element-plus/icons-vue'
</script>

<style scoped>
.about-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-card {
  padding: 30px;
  background: linear-gradient(135deg, #131b26 0%, #152936 100%);
}

.hero-title {
  font-size: 24px;
  margin-bottom: 12px;
}

.hero-desc {
  font-size: 14px;
  color: #cbd5e1;
  line-height: 1.7;
}

.section-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-header h3 {
  font-size: 17px;
  font-weight: 700;
  color: #fff;
}

/* 痛点网格 */
.issues-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.issue-card {
  background: #0d131c;
  border: 1px solid #1c2838;
  border-radius: 10px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.issue-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  align-self: flex-start;
}

.red-tag {
  background: rgba(255, 77, 79, 0.15);
  color: #ff4d4f;
  border: 1px solid rgba(255, 77, 79, 0.4);
}

.orange-tag {
  background: rgba(255, 122, 69, 0.15);
  color: #ff7a45;
  border: 1px solid rgba(255, 122, 69, 0.4);
}

.yellow-tag {
  background: rgba(255, 176, 0, 0.15);
  color: #ffb000;
  border: 1px solid rgba(255, 176, 0, 0.4);
}

.issue-card h4 {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.issue-card p {
  font-size: 12px;
  color: var(--rz-text-secondary);
  line-height: 1.6;
}

/* 对比表格 */
.comparison-table-wrapper {
  overflow-x: auto;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.comparison-table th,
.comparison-table td {
  padding: 12px 16px;
  border: 1px solid var(--rz-border);
  text-align: left;
}

.comparison-table th {
  background: #090d14;
  color: #fff;
  font-weight: 600;
}

.comparison-table tbody tr:nth-child(even) {
  background: #0e1622;
}

.bad-text {
  color: #ff7875;
}

.good-text {
  color: var(--rz-green);
}

.warn-text {
  color: #ffc069;
}

/* 协议解析 */
.protocol-box {
  background: #0d131c;
  border: 1px solid #1c2838;
  border-radius: 8px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.protocol-intro {
  font-size: 13px;
  color: var(--rz-text-secondary);
  line-height: 1.6;
}

.packet-breakdown {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.packet-byte-item {
  background: #151e2b;
  border: 1px solid #253346;
  border-radius: 6px;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.highlight-packet {
  border-color: var(--rz-green);
  background: rgba(0, 255, 0, 0.08);
}

.byte-index {
  font-size: 11px;
  color: var(--rz-cyan);
  font-family: monospace;
}

.byte-name {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
}

.protocol-code-sample pre {
  background: #090d14;
  border: 1px solid #1c2838;
  border-radius: 6px;
  padding: 12px;
  font-family: Consolas, monospace;
  font-size: 12px;
  color: #00ff00;
}
</style>
