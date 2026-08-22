-- 获取当前精灵（Sprite）
local sprite = app.activeSprite
if not sprite then
    app.alert("没有找到精灵！")
    return
end

-- 获取所有图层
local layers = sprite.layers

-- 遍历每个图层
for i, layer in ipairs(layers) do
	-- 获取图层的图像（Cel）
	local cel = layer.cels[1]
	if cel then
		-- 获取图像的像素数据
		local image = cel.image
		local width = image.width
		local height = image.height

		-- 统计非透明像素点数量
		local non_transparent_count = 0
		for y = 0, height - 1 do
			for x = 0, width - 1 do
				local color = image:getPixel(x, y)
				local alpha = app.pixelColor.rgbaA(color)  -- 获取 alpha 值
				if alpha > 0 then
					non_transparent_count = non_transparent_count + 1
				end
			end
		end

		-- 输出结果
		print("图层: " .. layer.name .. " | 非透明像素点数量: " .. non_transparent_count .. "\n")
	else
		print("图层: " .. layer.name .. " | 没有图像")
	end
end

-- 提示完成
-- app.alert("非透明像素点统计完成！请查看控制台输出。")