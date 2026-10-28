---
name: workbuddy-skin-change
description: 给 WorkBuddy 客户端换皮肤背景图。用户发来一张图片并说「换皮肤 / 换主题背景 / 用这张图做主题 / 换成这个背景」，或提到 workbuddy 皮肤、外观背景时使用。默认作用对象是「经典 QQ」主题，只改首页主区背景与配套的玻璃质感，不动左侧栏、不动应用包，全程可回滚。
metadata:
  version: "1.0.0"
  date: "2026-10-28"
---

# workbuddy-skin-change — 换 WorkBuddy 皮肤背景

把用户给的任意一张图装进 WorkBuddy 主题缓存，作为首页主区背景。不做拉伸，只用等比 `cover`。

## 触发方式

用户说「用 XXX 技能」并附图，或直接说「把这张图换成主题背景」。默认目标主题 **经典 QQ**（`workbuddy-skin-qqblue`）。

## 图片参数要求（需要用户提供的内容）

| 项目 | 推荐值 | 可接受范围 | 原因 |
|---|---|---|---|
| 分辨率 | 2560 × 1440 | 最短边 ≥ 900px | 1440 宽窗口下主区约 1200px，2× 屏需 2400px |
| 画面比例 | 16:9（1.778） | 1.5 : 1 ～ 2.0 : 1 | 主区比例约 1.33，cover 后左右各裁约 12% |
| 格式 | JPG（插画/照片） | PNG / WebP / AVIF | 需要透明通道时才用 PNG |
| 文件体积 | < 4 MB | 上限 15 MB | 超过 15 MB 脚本直接拒绝 |
| 构图 | 主体居中，或偏左 1/3 | — | 左右边缘各 12% 会被裁掉，别放关键内容 |
| 亮度 | 中低调（深蓝/墨绿/暗红） | — | 界面文字统一转白，底图过亮会糊 |
| 忌用 | 纯白底、大面积浅色、文字密集 | — | 白字压不住，可读性崩 |

**不改变画面比例**：脚本只设置 `background-size: cover`，等比缩放后居中裁切，永远不拉伸。宽高比不合时裁切量变大，但画面不变形。

可选参数（用户不提就用默认）：

- `--position`：背景定位，默认 `center 38%`。主体偏下用 `center 20%`，偏上用 `center 60%`。
- `--theme`：目标主题，默认 `qq`。支持 `purple` / `mint` / `green` / `jinqiu` / `sapphire`。

## 执行步骤

1. **收图落盘**。用户附图时，取 `image_local_path`，复制到 `/tmp/wbskin-src/` 下保留原扩展名。
2. **跑脚本**：

   ```bash
   python3 ~/.workbuddy/skills/workbuddy-skin-change/scripts/apply_skin.py \
     --image /tmp/wbskin-src/<file> --theme qq
   ```

   脚本自动完成：定位主题目录 → 备份 `skin.css.bak-<时间戳>` → 图片复制进 `assets/custom/skin-bg-<时间戳>.<ext>` → 用 `assets/overlay.css.tpl` 渲染自定义层 → 替换 CSS 里的 `CUSTOM SKIN OVERLAY` 段 → 校验花括号平衡。

3. **读脚本输出**。`ok: true` 才算成功；`warnings` 里若提示比例或分辨率问题，原样转述给用户。
4. **告知生效方式**：在「设置 → 外观」切到经典 QQ（或切走再切回），点「新建任务」回首页看。首屏若还是旧样式，重启应用一次。
5. **需要先看效果**时，用内置预览模板出图，比让用户反复切主题快：

   ```bash
   python3 - <<'PY'
   from pathlib import Path
   tpl = Path.home()/'.workbuddy/skills/workbuddy-skin-change/assets/preview.html'
   html = tpl.read_text(encoding='utf-8').replace('__BG__', '<图片绝对路径>')
   Path('/tmp/wbskin-preview.html').write_text(html, encoding='utf-8')
   PY
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
     --no-sandbox --hide-scrollbars --screenshot=/tmp/wbskin-preview.png \
     --window-size=1440,900 file:///tmp/wbskin-preview.html
   ```

   预览是模拟首页结构，用于检查构图、蒙版强度、文字对比度，不替代应用内实机确认。

## 撤销

```bash
python3 ~/.workbuddy/skills/workbuddy-skin-change/scripts/apply_skin.py --revert --theme qq
```

恢复到最近一次 `skin.css.bak-*`。也可以直接删掉 CSS 里 `CUSTOM SKIN OVERLAY` 到 `CUSTOM SKIN OVERLAY END` 之间的整段。

## 机制（改之前先懂这个）

- 主题 = 服务端下发的 zip，解压到 `~/.workbuddy/appearance-resources/<resourceKey>-<updatedAt>/`。
- 客户端读同目录的 `skin.v2.css`，注入 `<style data-skin-sheet="skin">`。
- 读取逻辑 `tryReadCachedCss()` 只读文件内容，**不校验 hash、不校验签名**，缓存命中就直接用。
- 因此本地文件就是事实上的皮肤源；官方 8 个主题本身也是同一套 `--cb-*` / `--wb-*` CSS 变量。
- 新版客户端只认 `skin.v2.css`；若目录里只有 `skin.css`，脚本会自动派生一份。

## 已知限制

| 限制 | 表现 | 处理 |
|---|---|---|
| 主题在服务端更新 | 生成新 `updatedAt` 目录，overlay 失效 | 重跑脚本 |
| LRU 清理 | 旧主题目录被回收，改动一起没了 | 重跑脚本 |
| 应用升级 | 缓存路径或加载机制可能变 | 重跑脚本；仍无效则报告，不要改应用包 |
| 只覆盖首页 | 对话页、设置页仍是原主题浅色 | 属预期；需要全站深色要另做方案 |
| 侧栏保持浅色 | 与深色主区形成明暗分区 | 属预期，QQ 主题的识别特征 |
| 切到别的主题 | 自定义层不生效 | 脚本只改指定主题，切走就看不到 |

## 不要做的事

- 不要改 `/Applications/WorkBuddy.app` 里的任何文件。
- 不要为「铺满」而拉伸图片（`background-size: 100% 100%` 之类）。
- 不要在没备份的情况下直接覆盖 `skin.v2.css`。
- 不要把用户原图删掉；脚本只做复制。
