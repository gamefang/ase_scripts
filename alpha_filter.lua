--[[
==Alpha Threshold Filter (LUA)==
Filters pixels based on alpha threshold:
- Pixels with alpha < threshold are set to fully transparent.
- Pixels with alpha >= threshold are set to fully opaque.
]]--

-- 設置透明度閾值（0 到 255）
local alphaThreshold = 200  -- 例如 128 表示 50% 透明度

-- 獲取當前活動的 Cel
local cel = app.activeCel
if not cel then
    return app.alert("沒有選中 Cel，請確保圖層包含內容並選中一個 Cel！")
end

-- 獲取 Cel 的圖像
local image = cel.image

-- 遍歷圖像的所有像素
for y = 0, image.height - 1 do
    for x = 0, image.width - 1 do
        local pixel = image:getPixel(x, y)
        local alpha = app.pixelColor.rgbaA(pixel)  -- 獲取像素的 Alpha 值

        if alpha < alphaThreshold then
            -- 如果 Alpha 值小於閾值，設置為完全透明
            image:putPixel(x, y, app.pixelColor.rgba(0, 0, 0, 0))
        else
            -- 如果 Alpha 值大於等於閾值，設置為完全不透明
            local r = app.pixelColor.rgbaR(pixel)
            local g = app.pixelColor.rgbaG(pixel)
            local b = app.pixelColor.rgbaB(pixel)
            image:putPixel(x, y, app.pixelColor.rgba(r, g, b, 255))
        end
    end
end

app.refresh()  -- 刷新界面