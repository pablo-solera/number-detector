from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from number_detector.application.settings import DetectionSettings
from number_detector.domain.models.bounding_box import BoundingBox
from number_detector.domain.models.image_region import ImageRegion


class OpenCVImageReader:
    def read(self, image_path: str | Path):
        return cv2.imread(str(image_path))


class OpenCVRedDetector:
    """OpenCV implementation for finding red text regions.

    This class intentionally focuses on *regions* to OCR, not individual glyphs.
    """

    def __init__(self, settings: DetectionSettings, debug: bool = False, debug_dir: str | None = None):
        self.s = settings
        self.debug = debug
        self.debug_dir = Path(debug_dir) if debug_dir else None
        if self.debug and self.debug_dir:
            self.debug_dir.mkdir(parents=True, exist_ok=True)

    def _save(self, filename: str, img) -> None:
        if not (self.debug and self.debug_dir):
            return
        cv2.imwrite(str(self.debug_dir / filename), img)

    def _build_red_mask(self, bgr):
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        lower1 = np.array([0, self.s.s_min, self.s.v_min])
        upper1 = np.array([10, 255, 255])
        lower2 = np.array([170, self.s.s_min, self.s.v_min])
        upper2 = np.array([180, 255, 255])

        mask_hsv = cv2.bitwise_or(cv2.inRange(hsv, lower1, upper1), cv2.inRange(hsv, lower2, upper2))

        # RGB red dominance (helps when HSV misses washed-out reds)
        b, g, r = cv2.split(bgr)
        mask_rgb = ((r.astype(np.int16) - g.astype(np.int16)) > self.s.red_rgb_delta) & \
                   ((r.astype(np.int16) - b.astype(np.int16)) > self.s.red_rgb_delta) & \
                   (r > self.s.red_rgb_r_min)
        mask_rgb = (mask_rgb.astype(np.uint8) * 255)

        mask = cv2.bitwise_or(mask_hsv, mask_rgb)
        return mask

    def _remove_line_components(self, mask: np.ndarray) -> np.ndarray:
        """Remove thin/long leader lines so they don't merge with digits after dilation."""
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        clean = mask.copy()
        for i in range(1, n):
            x, y, w, h, area = stats[i]
            aspect = w / max(h, 1)
            if (h <= 8 and aspect >= 12.0) or (aspect >= 25.0 and area < 2000):
                clean[labels == i] = 0
        return clean

    def _merge_part_bboxes(self, boxes: list[BoundingBox]) -> list[BoundingBox]:
        merged: list[BoundingBox] = []
        for bb in sorted(boxes, key=lambda box: (box.y, box.x)):
            if not merged:
                merged.append(bb)
                continue

            prev = merged[-1]
            vertical_overlap = min(prev.y + prev.h, bb.y + bb.h) - max(prev.y, bb.y)
            min_height = min(prev.h, bb.h)
            gap = bb.x - (prev.x + prev.w)

            if vertical_overlap >= min_height * 0.55 and gap <= self.s.part_merge_gap:
                x1 = min(prev.x, bb.x)
                y1 = min(prev.y, bb.y)
                x2 = max(prev.x + prev.w, bb.x + bb.w)
                y2 = max(prev.y + prev.h, bb.y + bb.h)
                if x2 - x1 > self.s.part_max_w or y2 - y1 > self.s.part_max_h:
                    merged.append(bb)
                    continue
                merged[-1] = BoundingBox(x1, y1, x2 - x1, y2 - y1)
            else:
                merged.append(bb)

        return merged

    def find_part_bboxes(self, bgr, name: str = "") -> list[BoundingBox]:
        mask = self._build_red_mask(bgr)
        mask = self._remove_line_components(mask)

        k = cv2.getStructuringElement(cv2.MORPH_RECT, self.s.text_dilate_kernel)
        dil = cv2.dilate(mask, k, iterations=self.s.text_dilate_iters)

        if name:
            self._save(f"{name}_parts_red_mask.png", mask)
            self._save(f"{name}_parts_red_dilated.png", dil)

        n, _, stats, _ = cv2.connectedComponentsWithStats(dil, connectivity=8)

        out: list[BoundingBox] = []
        for i in range(1, n):
            x, y, w, h, area = stats[i]

            if h < self.s.part_min_h:
                continue
            if w > self.s.part_max_w or h > self.s.part_max_h:
                continue
            if (w / max(h, 1)) > 5.0:
                continue

            out.append(BoundingBox(int(x), int(y), int(w), int(h)))

        out = self._merge_part_bboxes(out)
        return sorted(out, key=lambda bb: (bb.y, bb.x))

    def find_part_regions(self, bgr, name: str = "") -> list[ImageRegion]:
        regions: list[ImageRegion] = []
        height, width = bgr.shape[:2]
        for bb in self.find_part_bboxes(bgr, name=name):
            pad = self.s.part_roi_padding
            x1 = max(bb.x - pad, 0)
            y1 = max(bb.y - pad, 0)
            x2 = min(bb.x + bb.w + pad, width)
            y2 = min(bb.y + bb.h + pad, height)
            roi = bgr[y1:y2, x1:x2]
            regions.append(ImageRegion(bbox=bb, image=roi))
        return regions

    def find_motor_bboxes(self, bgr, name: str = "") -> list[tuple[BoundingBox, np.ndarray]]:
        """Return motor candidate regions as (bbox_in_full_image, roi_bgr)."""
        H, W = bgr.shape[:2]
        top_h = int(H * self.s.motor_region_pct)
        top = bgr[:top_h, :]

        mask = self._build_red_mask(top)
        k = cv2.getStructuringElement(cv2.MORPH_RECT, self.s.motor_dilate_kernel)
        dil = cv2.dilate(mask, k, iterations=self.s.motor_dilate_iters)

        if name:
            self._save(f"{name}_motor_top.png", top)
            self._save(f"{name}_motor_red_mask.png", mask)
            self._save(f"{name}_motor_red_dilated.png", dil)

        n, _, stats, _ = cv2.connectedComponentsWithStats(dil, connectivity=8)

        out: list[tuple[BoundingBox, np.ndarray]] = []
        for i in range(1, n):
            x, y, w, h, area = stats[i]
            if area < 120 or w < 40 or h < 10:
                continue
            # discard thin long lines
            if (w / max(h, 1)) > 25.0 and h <= 8:
                continue

            # create bbox in full-image coordinates
            bb = BoundingBox(int(x), int(y), int(w), int(h))

            pad = 10
            x1 = max(int(x) - pad, 0)
            y1 = max(int(y) - pad, 0)
            x2 = min(int(x + w) + pad, top.shape[1])
            y2 = min(int(y + h) + pad, top.shape[0])
            roi = top[y1:y2, x1:x2]
            out.append((bb, roi))

        out.sort(key=lambda t: (t[0].y, t[0].x))
        return out

    def find_motor_regions(self, bgr, name: str = "") -> list[ImageRegion]:
        return [ImageRegion(bbox=bb, image=roi) for bb, roi in self.find_motor_bboxes(bgr, name=name)]
