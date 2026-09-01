from fastapi import APIRouter, Request, Query
from pydantic import BaseModel, Field
from typing import Optional

from plugins.audit_utils import record_audit
from .service import RazerControlLogic

_logic = None
_ctx = None
LOCAL_USER = {"username": "local_admin", "role": "admin"}


# ---------- Pydantic 请求模型 ----------

class DpiPayload(BaseModel):
    dpi_x: int = Field(..., description="X 轴 DPI (100 ~ 35000)", ge=100, le=35000)
    dpi_y: Optional[int] = Field(None, description="Y 轴 DPI (默认与 X 轴相同)", ge=100, le=35000)
    target_path: Optional[str] = Field(None, description="目标设备 HID 路径 (留空自动选择)")


class PollingRatePayload(BaseModel):
    rate_hz: int = Field(..., description="回报率 (1000, 500, 125)")
    target_path: Optional[str] = Field(None, description="目标设备 HID 路径")


class LightingPayload(BaseModel):
    enabled: bool = Field(True, description="是否启用灯效 (False 代表彻底关灯)")
    mode: Optional[str] = Field("static", description="灯效模式: static (常亮), breathing (呼吸), none (关闭)")
    brightness: Optional[int] = Field(100, description="亮度百分比 (0~100)", ge=0, le=100)
    r: int = Field(0, description="红色分量 (0~255)", ge=0, le=255)
    g: int = Field(255, description="绿色分量 (0~255)", ge=0, le=255)
    b: int = Field(0, description="蓝色分量 (0~255)", ge=0, le=255)
    target_path: Optional[str] = Field(None, description="目标设备 HID 路径")


class ProfileCreatePayload(BaseModel):
    name: str = Field(..., description="预设方案名称", min_length=1, max_length=60)
    description: Optional[str] = Field("", description="预设描述")
    dpi_x: int = Field(1600, ge=100, le=35000)
    dpi_y: int = Field(1600, ge=100, le=35000)
    polling_rate: int = Field(1000)
    led_enabled: int = Field(1, ge=0, le=1)
    led_r: int = Field(0, ge=0, le=255)
    led_g: int = Field(255, ge=0, le=255)
    led_b: int = Field(0, ge=0, le=255)


class ProfileUpdatePayload(BaseModel):
    name: str = Field(..., description="预设方案名称", min_length=1, max_length=60)
    description: Optional[str] = Field("", description="预设描述")
    dpi_x: int = Field(1600, ge=100, le=35000)
    dpi_y: int = Field(1600, ge=100, le=35000)
    polling_rate: int = Field(1000)
    led_enabled: int = Field(1, ge=0, le=1)
    led_r: int = Field(0, ge=0, le=255)
    led_g: int = Field(255, ge=0, le=255)
    led_b: int = Field(0, ge=0, le=255)


async def start(ctx):
    global _logic, _ctx
    _ctx = ctx

    log = ctx.plugins["logger"].get_logger(ctx.service_name)
    res = ctx.plugins["response"]

    # 1. 实例化业务逻辑并初始化数据库
    _logic = RazerControlLogic(ctx)
    await _logic.init_db()

    # 2. 创建接口路由器
    api_prefix = ctx.config.get("api_prefix", "/api/razer_control")
    router = APIRouter(prefix=api_prefix, tags=["Razer Control (雷蛇硬件辅助控制)"])

    # ---------- 核心设备控制接口 ----------

    @router.get("/health")
    async def health_check():
        """服务存活检查"""
        return res.success(data={"status": "healthy", "service": ctx.service_name}, msg="雷蛇硬件控制服务运行正常")

    @router.get("/devices")
    async def get_connected_devices():
        """扫描当前系统连接的所有雷蛇 HID 设备"""
        data = await _logic.get_devices()
        return res.success(data=data)

    @router.post("/dpi")
    async def set_dpi(req: Request, payload: DpiPayload):
        """设置鼠标 DPI 灵敏度"""
        result = await _logic.apply_dpi(payload.dpi_x, payload.dpi_y, payload.target_path)
        await record_audit(ctx, req, result, LOCAL_USER)
        if result.get("success"):
            return res.success(data=result, msg=result.get("message", "DPI 设置成功"))
        return res.error(msg=result.get("message", "DPI 设置失败"), code=500, data=result)

    @router.post("/polling-rate")
    async def set_polling_rate(req: Request, payload: PollingRatePayload):
        """设置鼠标回报率 (1000Hz / 500Hz / 125Hz)"""
        result = await _logic.apply_polling_rate(payload.rate_hz, payload.target_path)
        await record_audit(ctx, req, result, LOCAL_USER)
        if result.get("success"):
            return res.success(data=result, msg=result.get("message", "回报率设置成功"))
        return res.error(msg=result.get("message", "回报率设置失败"), code=500, data=result)

    @router.post("/lighting")
    async def set_lighting(req: Request, payload: LightingPayload):
        """设置鼠标灯效 (常亮/呼吸/关灯及亮度调节)"""
        result = await _logic.apply_lighting(
            enabled=payload.enabled,
            mode=payload.mode or "static",
            brightness=payload.brightness if payload.brightness is not None else 100,
            r=payload.r,
            g=payload.g,
            b=payload.b,
            target_path=payload.target_path
        )
        await record_audit(ctx, req, result, LOCAL_USER)
        if result.get("success"):
            return res.success(data=result, msg=result.get("message", "灯效设置成功"))
        return res.error(msg=result.get("message", "灯效设置失败"), code=500, data=result)

    # ---------- 预设配置管理 ----------

    @router.get("/profiles")
    async def get_profiles():
        """获取所有预设方案"""
        data = await _logic.get_profiles()
        return res.success(data=data)

    @router.post("/profiles")
    async def create_profile(req: Request, payload: ProfileCreatePayload):
        """新增预设方案"""
        result = await _logic.create_profile(
            name=payload.name,
            description=payload.description or "",
            dpi_x=payload.dpi_x,
            dpi_y=payload.dpi_y,
            polling_rate=payload.polling_rate,
            led_enabled=payload.led_enabled,
            led_r=payload.led_r,
            led_g=payload.led_g,
            led_b=payload.led_b
        )
        await record_audit(ctx, req, result, LOCAL_USER)
        return result

    @router.put("/profiles/{profile_id}")
    async def update_profile(req: Request, profile_id: int, payload: ProfileUpdatePayload):
        """修改预设方案"""
        result = await _logic.update_profile(
            profile_id=profile_id,
            name=payload.name,
            description=payload.description or "",
            dpi_x=payload.dpi_x,
            dpi_y=payload.dpi_y,
            polling_rate=payload.polling_rate,
            led_enabled=payload.led_enabled,
            led_r=payload.led_r,
            led_g=payload.led_g,
            led_b=payload.led_b
        )
        await record_audit(ctx, req, result, LOCAL_USER)
        return result

    @router.delete("/profiles/{profile_id}")
    async def delete_profile(req: Request, profile_id: int):
        """删除预设方案"""
        result = await _logic.delete_profile(profile_id)
        await record_audit(ctx, req, result, LOCAL_USER)
        return result

    @router.post("/profiles/{profile_id}/apply")
    async def apply_profile(req: Request, profile_id: int, target_path: Optional[str] = Query(None)):
        """一键应用指定预设配置到雷蛇设备"""
        result = await _logic.apply_profile(profile_id, target_path)
        await record_audit(ctx, req, result, LOCAL_USER)
        return result

    # ---------- 系统优化与 Windows 雷蛇服务检测 ----------

    @router.get("/system/services")
    async def get_system_services():
        """检测 Windows 雷蛇后台常驻服务并提供优化指南"""
        data = await _logic.get_system_services()
        return res.success(data=data)

    # ---------- 操作日志 ----------

    @router.get("/logs")
    async def get_logs(limit: int = Query(50, ge=1, le=200)):
        """查询最近硬件指令下发审计日志"""
        data = await _logic.get_logs(limit)
        return res.success(data=data)

    # 3. 挂载路由到主应用
    app = ctx.plugins.get("web_app")
    if app:
        app.include_router(router)
        log.info(f"子服务 {ctx.service_name} API 路由加载完成 (路径前缀: {api_prefix})")
