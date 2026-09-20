"""Fixed 1080x1920 layout. Everything lives above y=1810 so TikTok's caption
and button chrome never covers a number that matters."""

W, H = 1080, 1920

HOOK_Y = 150            # centre of the big hook line
SUB_Y = 244             # rotating one-line caption

HUD_Y = 318             # "第N世代" baseline-ish centre
HUD_L = 48
HUD_R = 1032

FIELD_X, FIELD_Y = 40, 392
FIELD_W, FIELD_H = 1000, 1000
FIELD_PAD = 22          # keeps bodies fully inside the frame

HIST_TITLE_Y = 1434
HIST_X0, HIST_X1 = 56, 1024
HIST_TOP, HIST_BASE = 1478, 1690
HIST_MAXH = HIST_BASE - HIST_TOP

LEG_X0, LEG_X1 = 150, 930
LEG_Y0, LEG_H = 1730, 24
LEG_LABEL_Y = 1776

FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_INDEX = 0          # Noto Sans CJK JP Bold
