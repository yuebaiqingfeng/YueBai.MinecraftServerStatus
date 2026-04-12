# Minecraft Server Status Plugin
# 作者：月白清风
# 协议：GPL-3.0 License
from typing import List, Tuple, Type, Optional, Dict
import re
import random
import time

from mcstatus import JavaServer
from aiomcrcon import Client as RCONClient

from src.plugin_system import BasePlugin, register_plugin, ComponentInfo, BaseCommand
from src.plugin_system.base.config_types import ConfigField


# 查询缓存
status_cache: Dict[str, tuple[float, str]] = {}
CACHE_EXPIRE = 30  # 缓存过期时间，30秒


class MinecraftServerStatusCommand(BaseCommand):
    command_name = "minecraft_server_status"
    command_description = "我的世界服务器状态查询，支持查询在线人数、延迟、TPS等信息"
    command_pattern = r"^(查服|服务器状态|信息)$" 
    
    async def execute(self) -> Tuple[bool, Optional[str], bool]:
        try:
            # 获取当前会话信息
            chat_stream = self.message.chat_stream
            platform = chat_stream.platform
            group_id = chat_stream.group_info.group_id
            full_group_id = f"{platform}:{group_id}"
            group_id_str = str(full_group_id)
            
            # 加载服务器映射配置
            group_mapping = self.get_config("server_config.group_server_mapping", {})
            group_mapping = {str(k): v for k, v in group_mapping.items()}
            
            # 未配置的群组直接忽略
            if group_id_str not in group_mapping:
                print(f"[MCServerStatus] 未配置的群组: {group_id_str}")
                return False, "group_not_configured", False
            
            # 检查缓存
            now = time.time()
            cache_key = f"status_{group_id_str}"
            if cache_key in status_cache:
                cache_time, cache_msg = status_cache[cache_key]
                if now - cache_time < CACHE_EXPIRE:
                    print(f"[MCServerStatus] 使用缓存结果, 群组: {group_id_str}")
                    await self.send_text(cache_msg)
                    return True, "cache_hit", True
            
            # 解析服务器配置
            server_config = group_mapping[group_id_str]
            print(f"[MCServerStatus] 加载服务器配置: {server_config}")
            server_ip = server_config["ip"]
            game_port = server_config.get("server_port", server_config.get("port"))  # 双配置名兼容
            display_name = server_config.get("name", f"服务器({server_ip})")
            rcon_port = server_config.get("rcon_port", 25575)
            # 处理RCON密码
            rcon_password = str(server_config.get("rcon_password", "")).strip()
            print(f"[MCServerStatus] RCON配置: 端口={rcon_port}")
            
            # 初始化服务器查询客户端
            if game_port:
                server = JavaServer.lookup(f"{server_ip}:{game_port}")
            else:
                server = JavaServer.lookup(server_ip)
            
            # 获取基础状态信息
            try:
                status = await server.async_status()
            except Exception as e:
                # 服务器离线提示
                offline_msg = f"🎮 「 {display_name} 」当前离线 ❌\n无法连接到服务器，请检查服务器是否正常运行。"
                await self.send_text(offline_msg)
                print(f"[MCServerStatus] 服务器离线: {e}")
                return True, "server_offline", True
            
            # 获取扩展查询信息
            query = None
            try:
                query = await server.async_query()
            except Exception:
                pass
            
            # 获取服务器TPS
            tps = None
            try:
                if rcon_password:
                    rcon_client = RCONClient(server_ip, rcon_port, rcon_password, timeout=5)
                    try:
                        await rcon_client.connect()
                        raw_tps = (await rcon_client.send_cmd("tps")).strip()
                        tps = re.sub(r'§[0-9a-fk-or]', '', raw_tps)
                        print(f"[MCServerStatus] 成功获取TPS: {tps}")
                    finally:
                        await rcon_client.close()
            except Exception as e:
                print(f"[MCServerStatus] RCON处理失败: {e}，将跳过TPS获取")
                pass
            
            # 构建回复消息
            msg = f"🎮 「 {display_name} 」状态 🎮\n"
            msg += f"👥 在线人数：{status.players.online} / {status.players.max}\n"
            msg += f"📶 网络延迟：{status.latency:.0f} ms\n"
            msg += f"🔌 服务器版本：{status.version.name}\n"
            if tps:
                msg += f"⚡ 服务器TPS：{tps}\n"
            msg += "──────────────\n"
            
            # 处理玩家列表
            if query:
                if status.players.online > 0 and query.players:
                    msg += f"✨ 在线玩家：{'、'.join(query.players)}\n"
                elif status.players.online == 0:
                    tips = ["服务器无人问津", "这里空空如也～", "安静的服务器等待热闹～"]
                    msg += f"✨ {random.choice(tips)}\n"
                else:
                    msg += "✨ 在线玩家：暂无\n"
                # 处理已安装插件信息
                if query.plugins:
                    plugins = [p.name for p in query.plugins][:10]
                    msg += f"🔌 已安装插件：{', '.join(plugins)}"
                    if len(query.plugins) > 10:
                        msg += f" 等{len(query.plugins)}个"
            else:
                if status.players.online > 0 and status.players.sample:
                    players = [p.name for p in status.players.sample if p.name]
                    if players:
                        msg += f"✨ 在线玩家：{'、'.join(players)}"
                    else:
                        msg += f"✨ 在线玩家：暂无"
                elif status.players.online == 0:
                    tips = ["服务器无人问津", "这里空空如也～", "安静的服务器等待热闹～"]
                    msg += f"✨ {random.choice(tips)}"
                else:
                    msg += "✨ 在线玩家：服务器未返回详情"
            
            # 存入缓存
            status_cache[cache_key] = (now, msg)
            print(f"[MCServerStatus] 查询完成，结果已缓存")
            
            await self.send_text(msg)
            return True, "success", True
            
        except Exception as e:
            print(f"[MCServerStatus] 执行错误: {e}")
            return False, "error", False


@register_plugin
class MinecraftServerStatusPlugin(BasePlugin):
    plugin_name = "minecraft_server_status"
    plugin_author = "月白清风"
    enable_plugin = True
    dependencies = []
    python_dependencies = ["mcstatus", "aio-mc-rcon"]
    config_file_name = "config.toml" 
    
    config_section_descriptions = {
        "plugin": "插件基本配置",
        "server_config": "服务器配置，仅已配置的群组可使用该功能"
    }
    
    config_schema = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="是否启用插件"),
            "config_version": ConfigField(type=str, default="1.0.0", description="配置文件版本")
        },
        "server_config": {
            "group_server_mapping": ConfigField(
                type=dict,
                default={
                    # 示例1：基础服务器配置，仅查询基础状态
                    "qq:123456789": {
                        "ip": "mc.example.com",
                        "port": 25565,
                        "name": "我的生存服务器"
                    },
                    # 示例2：带RCON的服务器配置，可获取TPS
                    "qq:987654321": {
                        "ip": "mc2.example.com",
                        "port": 34432,
                        "name": "我的小游戏服",
                        "rcon_password": "你的RCON密码",
                        "rcon_port": 25575
                    }
                },
                description="群组服务器映射，键为平台:群ID，可配置ip/port/name/rcon_password/rcon_port，未配置的群会静默忽略，无port自解析port值"
            )
        }
    }
    
    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        return [(MinecraftServerStatusCommand.get_command_info(), MinecraftServerStatusCommand)]
