from PIL import Image
import os

base = "F:/Cache/.workbuddy/plugins/marketplaces/my-experts/plugins/xhs-content-studio/accounts/薄肌小王/发布包_D1/重渲v2"

# 主图 = card1 封面 (1080x1080)
im = Image.open(os.path.join(base, "card1_封面_主图.png")).convert("RGB")
im = im.resize((1080, 1080), Image.LANCZOS)
im.save(os.path.join(base, "card1_封面.jpg"), "JPEG", quality=92)

# 详情图 = card4 四步模板 (1080x1440)，来源必须是 card4 自己的详情图
im2 = Image.open(os.path.join(base, "card4_四步模板_详情图.png")).convert("RGB")
im2 = im2.resize((1080, 1440), Image.LANCZOS)
im2.save(os.path.join(base, "card4_四步模板.jpg"), "JPEG", quality=92)

print("converted: card1_封面.jpg, card4_四步模板.jpg")
