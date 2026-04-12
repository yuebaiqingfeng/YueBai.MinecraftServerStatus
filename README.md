# Minecraft Server Status 插件
我的世界服务器状态查询插件，作者：月白清风

## 功能介绍
- ✅ 服务器基础状态查询：在线人数、网络延迟、服务器版本
- ✅ 支持通过RCON获取服务器TPS，监控服务器运行性能
- ✅ 在线玩家列表查询，支持完整玩家名展示
- ✅ 已安装插件列表查询（服务器开启query后可用）
- ✅ 查询缓存功能：30秒内重复查询直接返回缓存，减少服务器压力
- ✅ 服务器离线友好提示，不会再出现无响应的情况
- ✅ 全mcstatus版本兼容，不管新旧版本的mcstatus都可以正常使用
- ✅ 多触发命令，`查服`/`服务器状态`/`信息`都可以触发查询

## 安装方法
1. 将整个插件文件夹放入maibot的插件目录
2. 执行 `pip install -r requirements.txt` 安装所需的Python依赖
3. 重启机器人
4. 按照下方说明修改配置文件即可使用

## 配置说明
插件的配置文件为 `config.toml`，你需要在 `server_config.group_server_mapping` 中配置你的群组与服务器的映射关系：
```toml
[server_config.group_server_mapping]
# 配置格式：平台:群ID = { ip = "服务器IP/域名", port = 游戏端口, name = "服务器显示名称", rcon_password = "RCON密码", rcon_port = "RCON端口" }

# 示例1：基础服务器配置，仅查询基础状态信息
"qq:123456789" = { ip = "mc.example.com", port = 25565, name = "我的生存服务器" }

# 示例2：带RCON的服务器配置，可额外获取服务器TPS
"qq:987654321" = { ip = "mc2.example.com", port = 34432, name = "我的小游戏服", rcon_password = "你的RCON密码", rcon_port = 25575 }
```

### RCON配置说明（获取TPS需要）
如果你需要获取服务器的TPS信息，需要先开启服务器的RCON功能：
1. 修改服务器的 `server.properties` 文件，添加/修改以下配置：
   ```properties
   enable-rcon=true
   rcon.password=你的RCON密码
   rcon.port=25575
   server-ip=0.0.0.0
   ```
2. **重启服务器**，让配置生效（修改配置后必须重启才会生效）
3. 在插件的配置中，填写对应的 `rcon_password` 和 `rcon_port` 即可

## 使用命令
在你配置好的群组中，发送以下任意一个命令，就可以查询服务器的状态：
- `查服`
- `服务器状态`
- `信息`

## 依赖说明
插件需要以下Python模块：
| 模块名 | 作用 |
| ---- | ---- |
| mcstatus | 用于查询服务器的基础状态信息 |
| aio-mc-rcon | 异步RCON客户端，用于连接服务器RCON获取TPS |

你可以执行 `pip install -r requirements.txt` 来一键安装所有依赖。

## 开源协议
本插件采用 **GPL-3.0 协议**，你可以自由使用、修改、分发该插件，修改后的衍生作品也需要采用相同的协议开源。
