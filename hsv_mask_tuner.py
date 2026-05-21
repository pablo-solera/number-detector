import cv2
import numpy as np

# =========================
# CONFIG BÁSICA
# =========================
IMAGE_PATH = "input/TEST_4.jpg"  # <- cambia esto a tu ruta

img = cv2.imread(IMAGE_PATH)
if img is None:
    raise FileNotFoundError(f"No se pudo leer la imagen: {IMAGE_PATH}")

hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

win_controls = "HSV Controls"
win_mask = "Mask"
win_overlay = "Overlay"
win_image = "Image (click to sample HSV)"

# =========================
# UTILIDADES
# =========================
def nothing(_=None):
    pass

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        h, s, v = hsv_img[y, x]
        b, g, r = img[y, x]
        print(f"[CLICK] x={x}, y={y}  HSV(OpenCV)={int(h)},{int(s)},{int(v)}  BGR={int(b)},{int(g)},{int(r)}")
        # Sugerencia: centra un rango alrededor de H con +-5..10
        # (OJO: H está en 0-179)
        hmin = clamp(int(h) - 10, 0, 179)
        hmax = clamp(int(h) + 10, 0, 179)
        smin = clamp(int(s) - 60, 0, 255)
        vmin = clamp(int(v) - 60, 0, 255)

        cv2.setTrackbarPos("H min", win_controls, hmin)
        cv2.setTrackbarPos("H max", win_controls, hmax)
        cv2.setTrackbarPos("S min", win_controls, smin)
        cv2.setTrackbarPos("V min", win_controls, vmin)
        print(f"      Sugerido: H[{hmin},{hmax}] S>={smin} V>={vmin}")

def get_trackbar(name):
    return cv2.getTrackbarPos(name, win_controls)

# =========================
# UI: Trackbars
# =========================
cv2.namedWindow(win_controls, cv2.WINDOW_NORMAL)
cv2.resizeWindow(win_controls, 520, 260)

cv2.createTrackbar("H min", win_controls, 90, 179, nothing)
cv2.createTrackbar("H max", win_controls, 130, 179, nothing)
cv2.createTrackbar("S min", win_controls, 50, 255, nothing)
cv2.createTrackbar("S max", win_controls, 255, 255, nothing)
cv2.createTrackbar("V min", win_controls, 50, 255, nothing)
cv2.createTrackbar("V max", win_controls, 255, 255, nothing)

# Morfología / unión de letras (clave para texto)
cv2.createTrackbar("Open iters",  win_controls, 1, 5, nothing)
cv2.createTrackbar("Close iters", win_controls, 2, 8, nothing)

# Dilatación horizontal para unir palabras en una línea
cv2.createTrackbar("Dilate X", win_controls, 25, 80, nothing)  # ancho kernel
cv2.createTrackbar("Dilate Y", win_controls, 3, 30, nothing)   # alto kernel
cv2.createTrackbar("Dilate iters", win_controls, 1, 5, nothing)

# =========================
# Ventanas de visualización
# =========================
cv2.namedWindow(win_image, cv2.WINDOW_NORMAL)
cv2.namedWindow(win_mask, cv2.WINDOW_NORMAL)
cv2.namedWindow(win_overlay, cv2.WINDOW_NORMAL)

cv2.resizeWindow(win_image, 900, 600)
cv2.resizeWindow(win_mask, 900, 600)
cv2.resizeWindow(win_overlay, 900, 600)

cv2.setMouseCallback(win_image, on_mouse)

print("Controles:")
print("- Mueve sliders para ajustar la máscara.")
print("- Click en el texto azul para imprimir HSV y auto-ajustar rangos base.")
print("- Teclas:  q/ESC = salir,  p = imprimir parámetros actuales")

# =========================
# Loop principal
# =========================
while True:
    hmin = get_trackbar("H min")
    hmax = get_trackbar("H max")
    smin = get_trackbar("S min")
    smax = get_trackbar("S max")
    vmin = get_trackbar("V min")
    vmax = get_trackbar("V max")

    # Asegura min <= max
    if hmin > hmax:
        hmin, hmax = hmax, hmin
        cv2.setTrackbarPos("H min", win_controls, hmin)
        cv2.setTrackbarPos("H max", win_controls, hmax)
    if smin > smax:
        smin, smax = smax, smin
        cv2.setTrackbarPos("S min", win_controls, smin)
        cv2.setTrackbarPos("S max", win_controls, smax)
    if vmin > vmax:
        vmin, vmax = vmax, vmin
        cv2.setTrackbarPos("V min", win_controls, vmin)
        cv2.setTrackbarPos("V max", win_controls, vmax)

    lower = np.array([hmin, smin, vmin], dtype=np.uint8)
    upper = np.array([hmax, smax, vmax], dtype=np.uint8)

    mask = cv2.inRange(hsv_img, lower, upper)

    # Morfología
    open_iters = get_trackbar("Open iters")
    close_iters = get_trackbar("Close iters")

    k3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    if open_iters > 0:
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k3, iterations=open_iters)
    if close_iters > 0:
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k3, iterations=close_iters)

    # Dilatación para unir caracteres/palabras
    dx = max(1, get_trackbar("Dilate X"))
    dy = max(1, get_trackbar("Dilate Y"))
    dil_iters = get_trackbar("Dilate iters")

    k_line = cv2.getStructuringElement(cv2.MORPH_RECT, (dx, dy))
    if dil_iters > 0:
        mask_d = cv2.dilate(mask, k_line, iterations=dil_iters)
    else:
        mask_d = mask.copy()

    # Overlay: pinta lo detectado sobre la imagen
    overlay = img.copy()
    colored = cv2.bitwise_and(img, img, mask=mask_d)
    overlay = cv2.addWeighted(overlay, 0.7, colored, 0.9, 0)

    # Mostrar
    cv2.imshow(win_image, img)
    cv2.imshow(win_mask, mask_d)
    cv2.imshow(win_overlay, overlay)

    key = cv2.waitKey(15) & 0xFF
    if key in (27, ord('q')):  # ESC o q
        break
    if key == ord('p'):
        print("=== PARÁMETROS ACTUALES ===")
        print(f"lower = np.array([{hmin}, {smin}, {vmin}])")
        print(f"upper = np.array([{hmax}, {smax}, {vmax}])")
        print(f"open_iters={open_iters}, close_iters={close_iters}")
        print(f"dilate_kernel=({dx},{dy}), dilate_iters={dil_iters}")

cv2.destroyAllWindows()
