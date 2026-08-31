import asyncio
import datetime
import json
import subprocess
from typing import List, Dict, Any, Optional

from .protocol import (
    list_razer_devices,
    send_packets_to_device,
    build_dpi_packets,
    build_polling_rate_packets,
    build_lighting_packets,
    CMD_CLASS_PERFORMANCE,
    CMD_CLASS_DEVICE,
    CMD_CLASS_LIGHTING,
    CMD_ID_SET_DPI,
    CMD_ID_SET_POLLING_RATE,
    CMD_ID_SET_LIGHTING,
)


class RazerControlLogic:
    def __init__(self, ctx):
        self.ctx = ctx
        self.db = ctx.plugins["db"]
        self.db_path = ctx.data.get_path("razer_control.db")
        self.res = ctx.plugins["response"]
        self.log = ctx.plugins["logger"].get_logger(ctx.service_name)
        self.config = ctx.config

    async def init_db(self):
        """数据库建表与初始预设数据种子写入"""
        await self.db.execute(self.db_path, "PRAGMA journal_mode=WAL;")

        # 1. 预设配置表
        await self.db.execute(self.db_path, """
            CREATE TABLE IF NOT EXISTS razer_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                dpi_x INTEGER NOT NULL DEFAULT 1600,
                dpi_y INTEGER NOT NULL DEFAULT 1600,
                polling_rate INTEGER NOT NULL DEFAULT 1000,
                led_enabled INTEGER NOT NULL DEFAULT 1,
                led_r INTEGER NOT NULL DEFAULT 0,
                led_g INTEGER NOT NULL DEFAULT 255,
                led_b INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # 2. 硬件指令审计日志表
        await self.db.execute(self.db_path, """
            CREATE TABLE IF NOT EXISTS razer_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                command_class INTEGER,
                command_id INTEGER,
                payload TEXT,
                target_device TEXT,
                status TEXT NOT NULL,
                status_code INTEGER,
                message TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # 检查是否需要初始化默认配置
        existing = await self.db.fetchall(self.db_path, "SELECT count(*) as cnt FROM razer_profiles")
        count = existing[0]["cnt"] if existing else 0
        if count == 0:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            default_profiles = [
                ("竞技 FPS 模式 (800 DPI)", "低灵敏度精确定位，1000Hz 极致响应，雷蛇绿经典静态光", 800, 800, 1000, 1, 0, 255, 0, 0),
                ("极简办公模式 (1600 DPI)", "推荐日常工作与编程，关灯省电无眩光，零后台 GPU 占用", 1600, 1600, 1000, 0, 0, 0, 0, 1),
                ("设计精细模式 (1200 DPI)", "平面/3D 设计微操档位，赛博青科技感灯效", 1200, 1200, 1000, 1, 0, 240, 255, 0),
                ("高分屏日常 (2400 DPI)", "4K 超清大屏快速跨屏巡航，霓虹紫流光氛围", 2400, 2400, 1000, 1, 157, 0, 255, 0)
            ]
            for p in default_profiles:
                await self.db.execute(
                    self.db_path,
                    """
                    INSERT INTO razer_profiles (
                        name, description, dpi_x, dpi_y, polling_rate,
                        led_enabled, led_r, led_g, led_b, is_active,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], now, now)
                )
            self.log.info("已初始化 4 个雷蛇默认配置预设")

    async def log_action(self, action: str, cmd_class: int, cmd_id: int, payload: Any, device: str, status: str, status_code: int, message: str):
        """记录硬件通信指令日志"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            payload_str = json.dumps(payload, ensure_ascii=False) if not isinstance(payload, str) else payload
            await self.db.execute(
                self.db_path,
                """
                INSERT INTO razer_logs (
                    action, command_class, command_id, payload, target_device, status, status_code, message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (action, cmd_class, cmd_id, payload_str, device or "Unknown", status, status_code, message, now)
            )
        except Exception as e:
            self.log.warning(f"写入指令审计日志失败: {e}")

    async def get_devices(self) -> Dict[str, Any]:
        """获取已连接的雷蛇设备列表"""
        devices = await asyncio.to_thread(list_razer_devices)
        return {
            "devices": devices,
            "total": len(devices),
            "has_razer": len(devices) > 0
        }

    async def apply_dpi(self, dpi_x: int, dpi_y: Optional[int] = None, target_path: Optional[str] = None) -> Dict[str, Any]:
        """向雷蛇鼠标下发 DPI 设置"""
        packets = build_dpi_packets(dpi_x, dpi_y)
        res = await asyncio.to_thread(send_packets_to_device, packets, target_path)

        await self.log_action(
            action="SET_DPI",
            cmd_class=CMD_CLASS_PERFORMANCE,
            cmd_id=CMD_ID_SET_DPI,
            payload={"dpi_x": dpi_x, "dpi_y": dpi_y or dpi_x},
            device=res.get("device_name"),
            status="SUCCESS" if res["success"] else "FAILED",
            status_code=res.get("status_code", -1),
            message=res.get("message", "")
        )
        return res

    async def apply_polling_rate(self, rate_hz: int, target_path: Optional[str] = None) -> Dict[str, Any]:
        """向雷蛇鼠标下发回报率设置 (1000/500/125Hz)"""
        packets = build_polling_rate_packets(rate_hz)
        res = await asyncio.to_thread(send_packets_to_device, packets, target_path)

        await self.log_action(
            action="SET_POLLING_RATE",
            cmd_class=CMD_CLASS_DEVICE,
            cmd_id=CMD_ID_SET_POLLING_RATE,
            payload={"rate_hz": rate_hz},
            device=res.get("device_name"),
            status="SUCCESS" if res["success"] else "FAILED",
            status_code=res.get("status_code", -1),
            message=res.get("message", "")
        )
        return res

    async def apply_lighting(self, enabled: bool, r: int = 0, g: int = 255, b: int = 0, target_path: Optional[str] = None) -> Dict[str, Any]:
        """向雷蛇鼠标下发静态 RGB / 单色常亮 / 彻底关灯设置"""
        packets = build_lighting_packets(enabled, r, g, b)
        action_name = "SET_LED_RGB" if enabled else "TURN_OFF_LED"
        payload_data = {"enabled": enabled, "r": r, "g": g, "b": b}

        res = await asyncio.to_thread(send_packets_to_device, packets, target_path)

        await self.log_action(
            action=action_name,
            cmd_class=CMD_CLASS_LIGHTING,
            cmd_id=CMD_ID_SET_LIGHTING,
            payload=payload_data,
            device=res.get("device_name"),
            status="SUCCESS" if res["success"] else "FAILED",
            status_code=res.get("status_code", -1),
            message=res.get("message", "")
        )
        return res

    # ---------- 预设配置方案管理 ----------

    async def get_profiles(self) -> List[Dict[str, Any]]:
        """获取所有预设配置方案"""
        rows = await self.db.fetchall(
            self.db_path,
            "SELECT * FROM razer_profiles ORDER BY is_active DESC, id ASC"
        )
        return [dict(r) for r in rows]

    async def create_profile(self, name: str, description: str, dpi_x: int, dpi_y: int, polling_rate: int, led_enabled: int, led_r: int, led_g: int, led_b: int) -> Dict[str, Any]:
        """创建新预设配置"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.db.execute(
            self.db_path,
            """
            INSERT INTO razer_profiles (
                name, description, dpi_x, dpi_y, polling_rate,
                led_enabled, led_r, led_g, led_b, is_active,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (name, description, dpi_x, dpi_y, polling_rate, led_enabled, led_r, led_g, led_b, now, now)
        )
        return self.res.success(msg="预设配置创建成功")

    async def update_profile(self, profile_id: int, name: str, description: str, dpi_x: int, dpi_y: int, polling_rate: int, led_enabled: int, led_r: int, led_g: int, led_b: int) -> Dict[str, Any]:
        """更新已有预设配置"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.db.execute(
            self.db_path,
            """
            UPDATE razer_profiles
            SET name = ?, description = ?, dpi_x = ?, dpi_y = ?, polling_rate = ?,
                led_enabled = ?, led_r = ?, led_g = ?, led_b = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, description, dpi_x, dpi_y, polling_rate, led_enabled, led_r, led_g, led_b, now, profile_id)
        )
        return self.res.success(msg="预设配置更新成功")

    async def delete_profile(self, profile_id: int) -> Dict[str, Any]:
        """删除预设配置"""
        await self.db.execute(self.db_path, "DELETE FROM razer_profiles WHERE id = ?", (profile_id,))
        return self.res.success(msg="预设配置已删除")

    async def apply_profile(self, profile_id: int, target_path: Optional[str] = None) -> Dict[str, Any]:
        """一键应用预设配置到设备"""
        rows = await self.db.fetchall(self.db_path, "SELECT * FROM razer_profiles WHERE id = ?", (profile_id,))
        if not rows:
            return self.res.error(msg="找不到对应的预设配置", code=404)
        
        p = dict(rows[0])
        
        # 1. 设为 active
        await self.db.execute(self.db_path, "UPDATE razer_profiles SET is_active = 0")
        await self.db.execute(self.db_path, "UPDATE razer_profiles SET is_active = 1 WHERE id = ?", (profile_id,))

        # 2. 下发硬件参数
        dpi_res = await self.apply_dpi(p["dpi_x"], p["dpi_y"], target_path)
        rate_res = await self.apply_polling_rate(p["polling_rate"], target_path)
        led_res = await self.apply_lighting(bool(p["led_enabled"]), p["led_r"], p["led_g"], p["led_b"], target_path)

        all_success = dpi_res.get("success", False) and rate_res.get("success", False) and led_res.get("success", False)
        
        return self.res.success(
            data={
                "profile": p,
                "dpi_result": dpi_res,
                "rate_result": rate_res,
                "led_result": led_res,
                "all_success": all_success
            },
            msg=f"预设「{p['name']}」已成功写入设备" if all_success else "预设部分参数写入完成"
        )

    # ---------- 系统优化与 Windows 雷蛇服务检测 ----------

    def _scan_windows_services_sync(self) -> List[Dict[str, Any]]:
        """在 Windows 下探测雷蛇相关服务运行状态"""
        detect_list = self.config.get("detect_services", [])
        
        # 尝试通过 PowerShell Get-Service 获取
        ps_cmd = 'Get-Service -Name "*Razer*", "*Cortex*" | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json -Compress'
        found_map = {}
        try:
            p = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=5)
            if p.returncode == 0 and p.stdout.strip():
                data = json.loads(p.stdout.strip())
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = item.get("Name", "")
                    status_val = item.get("Status", 0)
                    # PowerShell Status: 4=Running, 1=Stopped
                    status_text = "Running" if str(status_val) in ("4", "Running") else "Stopped"
                    start_type = str(item.get("StartType", "Unknown"))
                    found_map[name.lower()] = {
                        "status": status_text,
                        "start_type": start_type,
                        "raw": item
                    }
        except Exception as e:
            self.log.debug(f"PowerShell 服务检测跳过: {e}")

        results = []
        for defn in detect_list:
            svc_name = defn["name"]
            matched = found_map.get(svc_name.lower())
            if matched:
                is_running = (matched["status"] == "Running")
                is_disabled = (matched["start_type"].lower() == "disabled")
            else:
                is_running = False
                is_disabled = True

            results.append({
                "name": svc_name,
                "display_name": defn["display_name"],
                "description": defn["description"],
                "risk_level": defn["risk_level"],
                "impact": defn["impact"],
                "exists": matched is not None,
                "status": matched["status"] if matched else "NotInstalled",
                "is_running": is_running,
                "start_type": matched["start_type"] if matched else "None",
                "is_disabled": is_disabled
            })

        return results

    async def get_system_services(self) -> Dict[str, Any]:
        """获取 Windows 雷蛇服务状态与优化诊断建议"""
        services = await asyncio.to_thread(self._scan_windows_services_sync)
        running_count = sum(1 for s in services if s["is_running"])
        installed_count = sum(1 for s in services if s["exists"])

        # 生成一键清理 PowerShell 脚本
        cleanup_script = (
            "# 1. 停止所有运行中的雷蛇后台常驻服务\n"
            'Get-Service -Name "*Razer*", "*Cortex*" -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq "Running" } | Stop-Service -Force -PassThru\n\n'
            "# 2. 将雷蛇服务启动类型设置为禁用 (彻底杜绝开机自启与 DWM 抢占)\n"
            'Get-Service -Name "*Razer*", "*Cortex*" -ErrorAction SilentlyContinue | Set-Service -StartupType Disabled\n\n'
            "# 3. 校验最终状态 (确认全部显示 Stopped 与 Disabled)\n"
            'Get-Service -Name "*Razer*", "*Cortex*" -ErrorAction SilentlyContinue | Select-Object Name, DisplayName, Status, StartType\n'
        )

        return {
            "services": services,
            "running_count": running_count,
            "installed_count": installed_count,
            "has_bloatware": running_count > 0,
            "cleanup_script": cleanup_script,
            "system_health": "WARNING" if running_count > 0 else "OPTIMAL"
        }

    # ---------- 日志查询 ----------

    async def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的硬件通信指令日志"""
        rows = await self.db.fetchall(
            self.db_path,
            "SELECT * FROM razer_logs ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return [dict(r) for r in rows]
