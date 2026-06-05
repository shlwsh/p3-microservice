-- log_capture.lua
-- Nginx 流量日志采集脚本（OpenResty Lua）
--
-- 在 log_by_lua 阶段执行，采集每个请求的关键指标：
-- URL、Method、状态码、响应时长、客户端 IP、请求/响应大小
-- 写入 ngx.shared.DICT 供 Agent 定时读取

local cjson = require "cjson.safe"
local shared_dict = ngx.shared.log_buffer

-- 采集请求数据
local function capture_request()
    local entry = {
        url           = ngx.var.uri,
        method        = ngx.req.get_method(),
        status_code   = ngx.status,
        response_time_ms = math.floor((ngx.now() - ngx.req.start_time()) * 1000),
        client_ip     = ngx.var.remote_addr,
        request_size  = tonumber(ngx.var.request_length) or 0,
        response_size = tonumber(ngx.var.bytes_sent) or 0,
        upstream_addr = ngx.var.upstream_addr or "",
        timestamp     = math.floor(ngx.now() * 1000), -- Unix 毫秒
        query_string  = ngx.var.query_string or "",
    }

    return entry
end

-- 预筛选：仅采集满足条件的请求
local function should_capture(entry)
    -- 条件 1：响应时间 > 预筛选阈值（由 Center 下发，默认 50ms）
    local threshold = shared_dict:get("min_response_time_ms") or 50
    if entry.response_time_ms >= threshold then
        return true
    end

    -- 条件 2：错误状态码
    if entry.status_code >= 400 then
        return true
    end

    -- 条件 3：采样（正常请求按比例采集）
    local sampling_rate = shared_dict:get("sampling_rate") or 0.1
    if math.random() < sampling_rate then
        return true
    end

    return false
end

-- 写入共享内存
local function write_to_shared(entry)
    local json_str, err = cjson.encode(entry)
    if not json_str then
        ngx.log(ngx.ERR, "[LogCapture] JSON 编码失败: ", err)
        return
    end

    -- 使用自增 ID 作为键
    local id = shared_dict:incr("log_seq", 1, 0)
    local key = "log:" .. tostring(id)

    -- 设置 60 秒过期（防止 Agent 宕机导致内存泄漏）
    local ok, err = shared_dict:set(key, json_str, 60)
    if not ok then
        ngx.log(ngx.WARN, "[LogCapture] 共享内存写入失败: ", err)
    end
end

-- 主逻辑
local entry = capture_request()
if should_capture(entry) then
    write_to_shared(entry)
end
