-- log_pull.lua — Agent 拉取网关流量日志（读取后删除）

local cjson = require "cjson.safe"
local shared_dict = ngx.shared.log_buffer

local keys = shared_dict:get_keys(1024)
local logs = {}

for _, key in ipairs(keys) do
    if string.sub(key, 1, 4) == "log:" then
        local val = shared_dict:get(key)
        if val then
            local obj = cjson.decode(val)
            if obj then
                logs[#logs + 1] = obj
            end
            shared_dict:delete(key)
        end
    end
end

ngx.header["Content-Type"] = "application/json"
if #logs == 0 then
    ngx.say('{"logs":[],"count":0}')
    return
end

ngx.say(cjson.encode({ logs = logs, count = #logs }))
