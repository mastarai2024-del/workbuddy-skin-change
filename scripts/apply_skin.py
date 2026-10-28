#!/usr/bin/env python3
"""
workbuddy-skin-change · 把一张图片装进 WorkBuddy 主题的首页背景。

用法：
    python3 apply_skin.py --image /path/to/pic.jpg
    python3 apply_skin.py --image pic.jpg --theme qq --position "center 30%"
    python3 apply_skin.py --image pic.jpg --dry-run
    python3 apply_skin.py --revert            # 撤销自定义层

约束：
    - 只做等比 cover，绝不拉伸画面（满足「不改变画面比例」）。
    - 改动只落在主题缓存目录，不碰应用包。
    - 每次改动前自动备份，可用 --revert 或手工恢复 skin.css.bak-*。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
RES_ROOT = HOME / ".workbuddy" / "appearance-resources"
SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "overlay.css.tpl"

# 主题别名 → 主题目录内的资源文件夹名（或目录名前缀）
THEME_ALIASES = {
    "qq": "workbuddy-skin-qqblue",
    "经典qq": "workbuddy-skin-qqblue",
    "qqblue": "workbuddy-skin-qqblue",
    "purple": "workbuddy-skin-purple",
    "clearsky": "workbuddy-skin-purple",
    "mint": "workbuddy-skin-mint",
    "green": "workbuddy-skin-green",
    "forest": "workbuddy-skin-green",
    "jinqiu": "WorkBuddy皮肤_激战金秋-龙狮城_v10",
    "sapphire": "theme-tkhlwz",
    "blue-video": "workbuddy-skin-blue-video-fallback",
}

OVERLAY_START = "CUSTOM SKIN OVERLAY"
OVERLAY_END = "/* CUSTOM SKIN OVERLAY END */"
OVERLAY_RE = re.compile(
    r"/\* ={10,}\n\s*CUSTOM SKIN OVERLAY.*?/\* CUSTOM SKIN OVERLAY END \*/",
    re.DOTALL,
)

MAX_BYTES = 15 * 1024 * 1024
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    sys.exit(code)


def image_size(path: Path):
    """用 sips 读真实像素尺寸；失败返回 None。"""
    try:
        out = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            capture_output=True, text=True, timeout=20,
        ).stdout
        w = re.search(r"pixelWidth:\s*(\d+)", out)
        h = re.search(r"pixelHeight:\s*(\d+)", out)
        if w and h:
            return int(w.group(1)), int(h.group(1))
    except Exception:
        pass
    return None


def resolve_theme_dir(theme: str) -> Path:
    if not RES_ROOT.is_dir():
        fail(f"主题缓存目录不存在：{RES_ROOT}。请先启动 WorkBuddy 并在「设置 → 外观」里切换过一次主题。")

    alias = theme.strip()
    marker = THEME_ALIASES.get(alias.lower(), alias)

    candidates = []
    for d in RES_ROOT.iterdir():
        if not d.is_dir():
            continue
        if (d / marker).exists() or d.name == marker or d.name.startswith(marker):
            candidates.append(d)

    if not candidates:
        available = sorted(p.name for p in RES_ROOT.iterdir() if p.is_dir())
        fail(
            "找不到主题目录：%s。当前已缓存的主题目录：%s"
            % (marker, ", ".join(available))
        )

    # 同主题可能有多个 updatedAt 版本，取最近修改的
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def ensure_v2_css(theme_dir: Path):
    """新版客户端读 skin.v2.css；不存在时从 skin.css 派生，并记录来源。"""
    v2 = theme_dir / "skin.v2.css"
    v1 = theme_dir / "skin.css"
    created = False
    if not v2.exists():
        if not v1.exists():
            fail(f"主题目录里既没有 skin.v2.css 也没有 skin.css：{theme_dir}")
        shutil.copy2(v1, v2)
        created = True
    return v2, created


def backup_once(css_path: Path):
    """只保留最早的一份原始备份；重复执行不覆盖它，保证 --revert 永远回到官方原版。"""
    existing = sorted(css_path.parent.glob("skin.css.bak-*"))
    if existing:
        return existing[0]
    stamp = time.strftime("%Y%m%d-%H%M%S")
    bak = css_path.parent / f"skin.css.bak-{stamp}"
    shutil.copy2(css_path, bak)
    return bak


def find_existing_bak(theme_dir: Path):
    """返回最早的一份备份（原始官方版本）。"""
    baks = sorted(theme_dir.glob("skin.css.bak-*"))
    return baks[0] if baks else None


def render_overlay(bg_url: str, bg_name: str, size_txt: str, ratio_txt: str, position: str):
    tpl = TEMPLATE.read_text(encoding="utf-8")
    stamp = time.strftime("%Y-%m-%d %H:%M")
    return (
        tpl.replace("{{TIMESTAMP}}", stamp)
        .replace("{{BG_NAME}}", bg_name)
        .replace("{{BG_SIZE}}", size_txt)
        .replace("{{BG_RATIO}}", ratio_txt)
        .replace("{{BG_POSITION}}", position)
        .replace("{{BG_URL}}", bg_url)
    )


def to_local_file_url(p: Path) -> str:
    # WorkBuddy 自建的 local-file 协议：local-file:///绝对路径
    # 路径段做百分号编码，中文/空格都能安全通过
    from urllib.parse import quote
    return "local-file://" + quote(str(p), safe="/")


def check_css(css: str):
    return css.count("{") == css.count("}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    ap.add_argument("--theme", default="qq")
    ap.add_argument("--position", default="center 38%",
                    help="背景定位，如 center 38%% / left center / 50%% 25%%")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    theme_dir = resolve_theme_dir(args.theme)
    css_path, created = ensure_v2_css(theme_dir)

    # ── 撤销 ─────────────────────────────────────────────
    if args.revert:
        bak = find_existing_bak(theme_dir)
        if not bak:
            fail("没有找到备份文件 skin.css.bak-*，无法撤销。")
        if args.dry_run:
            print(json.dumps({"ok": True, "dryRun": True, "wouldRestore": str(bak)}, ensure_ascii=False))
            return
        shutil.copy2(bak, css_path)
        print(json.dumps({
            "ok": True,
            "action": "revert",
            "themeDir": str(theme_dir),
            "restoredFrom": str(bak),
            "cssPath": str(css_path),
        }, ensure_ascii=False))
        return

    if not args.image:
        fail("缺少 --image 参数")

    src = Path(args.image).expanduser().resolve()
    if not src.is_file():
        fail(f"图片不存在：{src}")
    ext = src.suffix.lower()
    if ext not in ALLOWED_EXT:
        fail(f"不支持的图片格式：{ext}，可用：{', '.join(sorted(ALLOWED_EXT))}")
    size_bytes = src.stat().st_size
    if size_bytes > MAX_BYTES:
        fail(f"图片过大：{size_bytes/1048576:.1f} MB，上限 15 MB")

    dim = image_size(src)
    if not dim:
        fail("无法读取图片尺寸，请确认文件未损坏")
    w, h = dim
    ratio = w / h
    ratio_txt = f"{ratio:.3f}:1"
    size_txt = f"{w}×{h}"

    warnings = []
    if ratio < 1.15:
        warnings.append(f"图片偏竖（{ratio_txt}），首页主区偏横，cover 会裁掉上下较多内容")
    elif ratio > 2.4:
        warnings.append(f"图片过宽（{ratio_txt}），cover 会裁掉左右较多内容")
    if w < 1600:
        warnings.append(f"宽度 {w}px 低于推荐值 1600px，高分屏上会偏软")
    if max(w, h) > 6000:
        warnings.append(f"尺寸 {size_txt} 偏大，渲染会占用较多显存，建议压到 3000px 以内")

    # 资源落位：优先主题包自带的 <skin-name>/assets/custom，没有则建在主题根
    subdirs = [p for p in theme_dir.iterdir() if p.is_dir() and (p / "assets").is_dir()]
    custom_dir = (subdirs[0] / "assets" / "custom") if subdirs else (theme_dir / "assets" / "custom")
    custom_dir.mkdir(parents=True, exist_ok=True)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest_name = f"skin-bg-{stamp}{ext}"
    dest = custom_dir / dest_name

    result = {
        "ok": True,
        "action": "apply",
        "theme": args.theme,
        "themeDir": str(theme_dir),
        "cssPath": str(css_path),
        "image": str(dest),
        "imageSize": size_txt,
        "ratio": ratio_txt,
        "position": args.position,
        "v2CreatedFromV1": created,
        "warnings": warnings,
        "dryRun": bool(args.dry_run),
    }

    if args.dry_run:
        print(json.dumps(result, ensure_ascii=False))
        return

    bak = backup_once(css_path)
    result["backup"] = str(bak)

    shutil.copy2(src, dest)
    bg_url = to_local_file_url(dest)
    overlay = render_overlay(bg_url, dest_name, size_txt, ratio_txt, args.position)

    css = css_path.read_text(encoding="utf-8")
    had_overlay = bool(OVERLAY_RE.search(css))
    if had_overlay:
        css_new = OVERLAY_RE.sub(lambda _: overlay.rstrip(), css, count=1)
    else:
        css_new = css.rstrip() + "\n\n\n" + overlay

    if not check_css(css_new):
        fail("生成后的 CSS 花括号不平衡，已中止，原文件未改动")

    tmp = css_path.with_suffix(".css.tmp")
    tmp.write_text(css_new, encoding="utf-8")
    os.replace(tmp, css_path)

    result["replacedExistingOverlay"] = had_overlay
    result["cssChars"] = len(css_new)
    result["nextStep"] = (
        "在 WorkBuddy「设置 → 外观」里切到目标主题（或切走再切回），"
        "然后点「新建任务」回到首页查看；首屏若仍是旧样式，重启应用一次。"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
