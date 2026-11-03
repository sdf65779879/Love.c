# 来源与许可

本项目是以 Vue 3 + FastAPI 重写的 LikeGirl 情侣小站，参考项目：
https://github.com/Cleanwn/LikeGirl

原项目作者：Ki.；Cleanwn/LikeGirl 为二次分发仓库。
原项目版本：Like Girl 5.2.1-Stable。
原项目作者主页：https://blog.kikiw.cn/
原项目版权信息：Copyright (c) 2023 - 2025 by Ki All Rights Reserved.

本项目复用了该仓库以下视觉资源，保留原作者归属：
- `frontend/public/images/cover.png` ← `Style/img/bgCover.png`
- `frontend/public/images/likegirl_card_1.svg` 至 `likegirl_card_6.svg` ← `Style/img/card/`

所有 PHP 运行代码均以 Python 和 Vue 3 重新实现，没有引入 PHP 运行环境。
本重写版本及随附代码以 GNU Affero General Public License v3.0（AGPL-3.0）提供，全文见 LICENSE。
页脚提供参考项目链接，以及当前部署版本的源码下载。Docker 构建时自动打包源码，排除凭据、上传数据和数据库。
如果修改或另行部署，请确保页脚源码入口可以获取该部署对应的完整源码。

示例人物“阿辰”“小满”、示例故事、心愿、礼物均为演示内容。头像为本重写版本绘制的占位图，可通过管理后台替换。

足迹地图参考 [zkeyoned/map-of-us-template](https://github.com/zkeyoned/map-of-us-template) 的 ChinaMap、ProvinceMap 和 geo 投影代码。离线图形及城市目录由其 china-geo.json、provinces.ts 和 cities.ts 生成，仅包含地理数据。原项目 MIT 许可见 [MAP-LICENSE.txt](backend/app/data/MAP-LICENSE.txt)。
