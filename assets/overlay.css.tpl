/* ==========================================================================
   CUSTOM SKIN OVERLAY · 自定义皮肤层
   --------------------------------------------------------------------------
   生成时间：{{TIMESTAMP}}
   背景图　：{{BG_NAME}}（{{BG_SIZE}}，比例 {{BG_RATIO}}）
   作用范围：首页主区（.wb-home-route / .teams-container），不触及左侧栏
   替换方式：换图后重跑 workbuddy-skin-change 技能，或直接改 --custom-skin-bg 的 URL
   回滚方式：删除本段，或恢复同目录下的 skin.css.bak-*
   ========================================================================== */

:root,
body {
  --custom-skin-bg: url("{{BG_URL}}");
  --custom-skin-veil:
    radial-gradient(96% 74% at 50% 46%,
      rgba(3, 7, 20, 0.80) 0%,
      rgba(3, 7, 20, 0.52) 40%,
      rgba(3, 7, 20, 0.12) 74%),
    linear-gradient(180deg,
      rgba(4, 9, 24, 0.34) 0%,
      rgba(4, 9, 24, 0.14) 30%,
      rgba(4, 9, 24, 0.52) 74%,
      rgba(4, 9, 24, 0.74) 100%);

  --wb-welcome-bg-image: var(--custom-skin-veil), var(--custom-skin-bg) !important;
}

/* 首页主区：底图铺满，cover 等比裁切，不变形 */
:root .wb-home-route {
  --wb-custom-img-main-content-welcome: var(--custom-skin-veil), var(--custom-skin-bg) !important;
  background-image: var(--custom-skin-veil), var(--custom-skin-bg) !important;
  background-size: cover, cover, cover !important;
  background-position: center center, center center, {{BG_POSITION}} !important;
  background-repeat: no-repeat, no-repeat, no-repeat !important;
  background-attachment: scroll, scroll, scroll !important;

  /* 深色底图上的文字层级 */
  --cb-text-primary: #f3f8fff2 !important;
  --cb-text-secondary: #dbe7f8cc !important;
  --cb-text-tertiary: #c3d4ea99 !important;
  --cb-text-quaternary: #cfdcece0 !important;
}

/* 标题兜底：不依赖具体类名，给首页所有标题级元素加投影，保证压在插画上仍锐利 */
:root .wb-home-route h1,
:root .wb-home-route h2,
:root .wb-home-route h3,
:root .wb-home-route [class*="title"],
:root .wb-home-route [class*="Title"] {
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.9), 0 4px 28px rgba(0, 0, 0, 0.85), 0 0 70px rgba(2, 6, 18, 0.75) !important;
}

/* 输入框：深色玻璃，保证在插画上仍有层次 */
:root .wb-home-route .wb-home-composer__input-slot {
  background: rgba(7, 14, 32, 0.62) !important;
  -webkit-backdrop-filter: blur(20px) saturate(150%);
  backdrop-filter: blur(20px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.16) !important;
  border-radius: 16px !important;
  box-shadow: 0 18px 48px -20px rgba(0, 0, 0, 0.65) !important;
}

:root .wb-home-route .wb-home-composer__input-slot [class*="mainArea"] {
  --cb-main-area-background: transparent !important;
  --wb-main-area-background: transparent !important;
  background: transparent !important;
}

/* 快捷场景标签：玻璃胶囊 */
:root .wb-home-route .wb-home-composer .quick-actions__item {
  background: rgba(255, 255, 255, 0.10) !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  color: #e8f1ff !important;
}

:root .wb-home-route .wb-home-composer .quick-actions__item:hover {
  background: rgba(255, 255, 255, 0.20) !important;
}

:root .wb-home-route .wb-home-composer .quick-actions__item.quick-actions__item--selected {
  background: rgba(94, 103, 250, 0.85) !important;
  border-color: rgba(160, 176, 255, 0.55) !important;
  color: #ffffff !important;
}

/* 首页容器透明，让底图贯通 */
:root .wb-home-route .claw-workspace__main {
  background: transparent !important;
}

/* 对话流底部遮罩改为深色，避免浅色断层 */
:root .wb-home-route .cr-message-list__bottom-mask {
  --cr-message-list-bottom-mask-bg: transparent !important;
  background: linear-gradient(to bottom, rgba(4, 9, 24, 0), rgba(4, 9, 24, 0.72)) !important;
}

/* CUSTOM SKIN OVERLAY END */
