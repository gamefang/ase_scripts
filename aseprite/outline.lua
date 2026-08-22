--[[
==Pixel Outline v1.01 (LUA)==
Outlines current layer with custom outline width of fg colour

By Rik Nicol / @hot_pengu / https://github.com/rikfuzz/aseprite-scripts
Modified to support custom outline width

Requirements
Aseprite (Currently requires Aseprite v1.2.10-beta2)
Click "Open Scripts Folder" in File > Scripts and drag the script into the folder.
]]--

-- 设置描边宽度（例如 2 表示 2 像素宽）
local outlineWidth = 1

-- 创建新图像，比原图像大 2 * outlineWidth
local newImage = Image(app.activeImage.width + 2 * outlineWidth, app.activeImage.height + 2 * outlineWidth)
newImage:putImage(app.activeImage, outlineWidth, outlineWidth)

local function clrpx(color)
    return app.pixelColor.rgba(color.red, color.green, color.blue, color.alpha)
end

local outlineColor = app.fgColor
outlineColor = clrpx(outlineColor)

local function isTransparent(a)
    return app.pixelColor.rgbaA(a) == 0
end

local function getPixel(x, y)
    if x >= newImage.width or y >= newImage.height or x < 0 or y < 0 then
        return app.pixelColor.rgba(0, 0, 0, 0)
    end
    return newImage:getPixel(x, y)
end

local function putPixel(color, x, y)
    return newImage:putPixel(x, y, color)
end

local outlinePlacesX = {}
local outlinePlacesY = {}

local function pushOutline(x, y)
    table.insert(outlinePlacesX, x)
    table.insert(outlinePlacesY, y)
end

local function ol()
    local testGrid = {}
    local imageGrid = {}

    for y = 0, newImage.height - 1 do
        for x = 0, newImage.width - 1 do
            if isTransparent(getPixel(x, y)) then
                -- 检查周围 outlineWidth 范围内的像素
                for dy = -outlineWidth, outlineWidth do
                    for dx = -outlineWidth, outlineWidth do
                        if not isTransparent(getPixel(x + dx, y + dy)) then
                            pushOutline(x, y)
                            break
                        end
                    end
                end
            end
        end
    end

    for i = 1, #outlinePlacesX do
        putPixel(outlineColor, outlinePlacesX[i], outlinePlacesY[i])
    end
end

ol()

app.transaction(
    function()
        app.activeCel.position = {x = app.activeCel.position.x - outlineWidth, y = app.activeCel.position.y - outlineWidth}
        app.activeCel.image = newImage
    end
)