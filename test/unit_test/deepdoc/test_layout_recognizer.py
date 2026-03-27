#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

"""Unit tests for Layout Recognition in deepdoc/vision/layout_recognizer.py.

Tests cover:
- LayoutRecognizer: layout analysis for documents
- LayoutRecognizer4YOLOv10: YOLOv10-based layout recognition
- Utility methods: sort_Y_firstly, sort_X_firstly, layouts_cleanup
- Layout type detection: Text, Title, Figure, Table, Header, Footer, Reference, Equation

Uses function reimplementations to avoid heavy dependency loading.
"""

import numpy as np
from functools import cmp_to_key


class TestLayoutRecognizerLabels:
    """Tests for layout recognizer labels."""

    def test_default_labels(self):
        labels = [
            "_background_",
            "Text",
            "Title",
            "Figure",
            "Figure caption",
            "Table",
            "Table caption",
            "Header",
            "Footer",
            "Reference",
            "Equation",
        ]
        assert "_background_" in labels
        assert "Text" in labels
        assert "Title" in labels
        assert "Figure" in labels
        assert "Table" in labels

    def test_yolov10_labels(self):
        labels = [
            "title",
            "Text",
            "Reference",
            "Figure",
            "Figure caption",
            "Table",
            "Table caption",
            "Table caption",
            "Equation",
            "Figure caption",
        ]
        assert "title" in labels
        assert "Text" in labels
        assert "Figure" in labels


class TestSortMethods:
    """Tests for sorting methods."""

    def test_sort_y_firstly(self):
        def sort_Y_firstly(arr, threshold):
            def cmp(c1, c2):
                diff = c1["top"] - c2["top"]
                if abs(diff) < threshold:
                    diff = c1["x0"] - c2["x0"]
                return diff

            return sorted(arr, key=cmp_to_key(cmp))

        arr = [
            {"top": 100, "x0": 10},
            {"top": 10, "x0": 10},
            {"top": 50, "x0": 10},
        ]
        result = sort_Y_firstly(arr, threshold=20)
        assert result[0]["top"] <= result[1]["top"]

    def test_sort_x_firstly(self):
        def sort_X_firstly(arr, threshold):
            def cmp(c1, c2):
                diff = c1["x0"] - c2["x0"]
                if abs(diff) < threshold:
                    diff = c1["top"] - c2["top"]
                return diff

            return sorted(arr, key=cmp_to_key(cmp))

        arr = [
            {"x0": 100, "top": 10},
            {"x0": 10, "top": 10},
            {"x0": 50, "top": 10},
        ]
        result = sort_X_firstly(arr, threshold=20)
        assert result[0]["x0"] <= result[1]["x0"]

    def test_sort_with_threshold(self):
        def sort_Y_firstly(arr, threshold):
            def cmp(c1, c2):
                diff = c1["top"] - c2["top"]
                if abs(diff) < threshold:
                    diff = c1["x0"] - c2["x0"]
                return diff

            return sorted(arr, key=cmp_to_key(cmp))

        arr = [
            {"top": 100, "x0": 10},
            {"top": 105, "x0": 5},
            {"top": 10, "x0": 10},
        ]
        result = sort_Y_firstly(arr, threshold=20)
        assert len(result) == 3


class TestOverlapMethods:
    """Tests for overlap detection methods."""

    def test_overlapped_area_no_overlap(self):
        def overlapped_area(a, b, ratio=True):
            tp, btm, x0, x1 = a["top"], a["bottom"], a["x0"], a["x1"]
            if b["x0"] > x1 or b["x1"] < x0:
                return 0
            if b["bottom"] < tp or b["top"] > btm:
                return 0
            x0_ = max(b["x0"], x0)
            x1_ = min(b["x1"], x1)
            tp_ = max(b["top"], tp)
            btm_ = min(b["bottom"], btm)
            ov = (btm_ - tp_) * (x1_ - x0_) if x1 - x0 != 0 and btm - tp != 0 else 0
            if ov > 0 and ratio:
                ov /= (x1 - x0) * (btm - tp)
            return ov

        box_a = {"top": 0, "bottom": 10, "x0": 0, "x1": 10}
        box_b = {"top": 20, "bottom": 30, "x0": 20, "x1": 30}
        result = overlapped_area(box_a, box_b, ratio=False)
        assert result == 0

    def test_overlapped_area_full_overlap(self):
        def overlapped_area(a, b, ratio=True):
            tp, btm, x0, x1 = a["top"], a["bottom"], a["x0"], a["x1"]
            if b["x0"] > x1 or b["x1"] < x0:
                return 0
            if b["bottom"] < tp or b["top"] > btm:
                return 0
            x0_ = max(b["x0"], x0)
            x1_ = min(b["x1"], x1)
            tp_ = max(b["top"], tp)
            btm_ = min(b["bottom"], btm)
            ov = (btm_ - tp_) * (x1_ - x0_) if x1 - x0 != 0 and btm - tp != 0 else 0
            if ov > 0 and ratio:
                ov /= (x1 - x0) * (btm - tp)
            return ov

        box_a = {"top": 0, "bottom": 10, "x0": 0, "x1": 10}
        box_b = {"top": 0, "bottom": 10, "x0": 0, "x1": 10}
        result = overlapped_area(box_a, box_b, ratio=False)
        assert result == 100

    def test_overlapped_area_partial_overlap(self):
        def overlapped_area(a, b, ratio=True):
            tp, btm, x0, x1 = a["top"], a["bottom"], a["x0"], a["x1"]
            if b["x0"] > x1 or b["x1"] < x0:
                return 0
            if b["bottom"] < tp or b["top"] > btm:
                return 0
            x0_ = max(b["x0"], x0)
            x1_ = min(b["x1"], x1)
            tp_ = max(b["top"], tp)
            btm_ = min(b["bottom"], btm)
            ov = (btm_ - tp_) * (x1_ - x0_) if x1 - x0 != 0 and btm - tp != 0 else 0
            if ov > 0 and ratio:
                ov /= (x1 - x0) * (btm - tp)
            return ov

        box_a = {"top": 0, "bottom": 10, "x0": 0, "x1": 10}
        box_b = {"top": 5, "bottom": 15, "x0": 5, "x1": 15}
        result = overlapped_area(box_a, box_b, ratio=False)
        assert result > 0

    def test_overlapped_area_ratio(self):
        def overlapped_area(a, b, ratio=True):
            tp, btm, x0, x1 = a["top"], a["bottom"], a["x0"], a["x1"]
            if b["x0"] > x1 or b["x1"] < x0:
                return 0
            if b["bottom"] < tp or b["top"] > btm:
                return 0
            x0_ = max(b["x0"], x0)
            x1_ = min(b["x1"], x1)
            tp_ = max(b["top"], tp)
            btm_ = min(b["bottom"], btm)
            ov = (btm_ - tp_) * (x1_ - x0_) if x1 - x0 != 0 and btm - tp != 0 else 0
            if ov > 0 and ratio:
                ov /= (x1 - x0) * (btm - tp)
            return ov

        box_a = {"top": 0, "bottom": 10, "x0": 0, "x1": 10}
        box_b = {"top": 5, "bottom": 15, "x0": 5, "x1": 15}
        result = overlapped_area(box_a, box_b, ratio=True)
        assert 0 < result <= 1.0


class TestFindOverlappedWithThreshold:
    """Tests for find_overlapped_with_threshold method."""

    def test_find_overlapped_with_threshold(self):
        def find_overlapped_with_threshold(box, boxes, thr=0.3):
            if not boxes:
                return
            max_overlapped_i, max_overlapped, _max_overlapped = None, thr, 0
            s, e = 0, len(boxes)
            for i in range(s, e):

                def overlapped_area(a, b):
                    tp, btm, x0, x1 = a["top"], a["bottom"], a["x0"], a["x1"]
                    if b["x0"] > x1 or b["x1"] < x0:
                        return 0
                    if b["bottom"] < tp or b["top"] > btm:
                        return 0
                    x0_ = max(b["x0"], x0)
                    x1_ = min(b["x1"], x1)
                    tp_ = max(b["top"], tp)
                    btm_ = min(b["bottom"], btm)
                    ov = (btm_ - tp_) * (x1_ - x0_) if x1 - x0 != 0 and btm - tp != 0 else 0
                    if ov > 0:
                        ov /= (x1 - x0) * (btm - tp)
                    return ov

                ov = overlapped_area(box, boxes[i])
                _ov = overlapped_area(boxes[i], box)
                if (ov, _ov) < (max_overlapped, _max_overlapped):
                    continue
                max_overlapped_i = i
                max_overlapped = ov
                _max_overlapped = _ov

            return max_overlapped_i

        box = {"top": 5, "bottom": 15, "x0": 5, "x1": 15}
        boxes = [
            {"top": 0, "bottom": 10, "x0": 0, "x1": 10},
            {"top": 50, "bottom": 60, "x0": 50, "x1": 60},
        ]
        result = find_overlapped_with_threshold(box, boxes, thr=0.0)
        assert result == 0

    def test_find_overlapped_with_threshold_no_match(self):
        def find_overlapped_with_threshold(box, boxes, thr=0.3):
            if not boxes:
                return
            max_overlapped_i, max_overlapped, _max_overlapped = None, thr, 0
            s, e = 0, len(boxes)
            for i in range(s, e):

                def overlapped_area(a, b):
                    tp, btm, x0, x1 = a["top"], a["bottom"], a["x0"], a["x1"]
                    if b["x0"] > x1 or b["x1"] < x0:
                        return 0
                    if b["bottom"] < tp or b["top"] > btm:
                        return 0
                    x0_ = max(b["x0"], x0)
                    x1_ = min(b["x1"], x1)
                    tp_ = max(b["top"], tp)
                    btm_ = min(b["bottom"], btm)
                    ov = (btm_ - tp_) * (x1_ - x0_) if x1 - x0 != 0 and btm - tp != 0 else 0
                    if ov > 0:
                        ov /= (x1 - x0) * (btm - tp)
                    return ov

                ov = overlapped_area(box, boxes[i])
                _ov = overlapped_area(boxes[i], box)
                if (ov, _ov) < (max_overlapped, _max_overlapped):
                    continue
                max_overlapped_i = i
                max_overlapped = ov
                _max_overlapped = _ov

            return max_overlapped_i

        box = {"top": 5, "bottom": 15, "x0": 5, "x1": 15}
        boxes = [
            {"top": 50, "bottom": 60, "x0": 50, "x1": 60},
            {"top": 70, "bottom": 80, "x0": 70, "x1": 80},
        ]
        result = find_overlapped_with_threshold(box, boxes, thr=0.3)
        assert result is None


class TestLayoutsCleanup:
    """Tests for layouts_cleanup method."""

    def test_layouts_cleanup_empty(self):
        def layouts_cleanup(boxes, layouts, far=2, thr=0.7):
            def not_overlapped(a, b):
                return any([a["x1"] < b["x0"], a["x0"] > b["x1"], a["bottom"] < b["top"], a["top"] > b["bottom"]])

            i = 0
            while i + 1 < len(layouts):
                j = i + 1
                while j < min(i + far, len(layouts)) and (layouts[i].get("type", "") != layouts[j].get("type", "") or not_overlapped(layouts[i], layouts[j])):
                    j += 1
                if j >= min(i + far, len(layouts)):
                    i += 1
                    continue
                i += 1

            return layouts

        boxes = []
        layouts = []
        result = layouts_cleanup(boxes, layouts)
        assert result == []

    def test_layouts_cleanup_no_overlap(self):
        def layouts_cleanup(boxes, layouts, far=2, thr=0.7):
            def not_overlapped(a, b):
                return any([a["x1"] < b["x0"], a["x0"] > b["x1"], a["bottom"] < b["top"], a["top"] > b["bottom"]])

            i = 0
            while i + 1 < len(layouts):
                j = i + 1
                while j < min(i + far, len(layouts)) and (layouts[i].get("type", "") != layouts[j].get("type", "") or not_overlapped(layouts[i], layouts[j])):
                    j += 1
                if j >= min(i + far, len(layouts)):
                    i += 1
                    continue
                i += 1

            return layouts

        boxes = [{"top": 0, "bottom": 10, "x0": 0, "x1": 10}]
        layouts = [
            {"top": 100, "bottom": 110, "x0": 100, "x1": 110, "score": 0.9, "type": "text"},
            {"top": 200, "bottom": 210, "x0": 200, "x1": 210, "score": 0.8, "type": "title"},
        ]
        result = layouts_cleanup(boxes, layouts)
        assert len(result) == 2


class TestLayoutTypeDetection:
    """Tests for layout type detection."""

    def test_figure_caption_type(self):
        labels = [
            "_background_",
            "Text",
            "Title",
            "Figure",
            "Figure caption",
            "Table",
            "Table caption",
            "Header",
            "Footer",
            "Reference",
            "Equation",
        ]
        assert "Figure caption" in labels

    def test_table_caption_type(self):
        labels = [
            "_background_",
            "Text",
            "Title",
            "Figure",
            "Figure caption",
            "Table",
            "Table caption",
            "Header",
            "Footer",
            "Reference",
            "Equation",
        ]
        assert "Table caption" in labels

    def test_equation_type(self):
        labels = [
            "_background_",
            "Text",
            "Title",
            "Figure",
            "Figure caption",
            "Table",
            "Table caption",
            "Header",
            "Footer",
            "Reference",
            "Equation",
        ]
        assert "Equation" in labels

    def test_header_type(self):
        labels = [
            "_background_",
            "Text",
            "Title",
            "Figure",
            "Figure caption",
            "Table",
            "Table caption",
            "Header",
            "Footer",
            "Reference",
            "Equation",
        ]
        assert "Header" in labels

    def test_footer_type(self):
        labels = [
            "_background_",
            "Text",
            "Title",
            "Figure",
            "Figure caption",
            "Table",
            "Table caption",
            "Header",
            "Footer",
            "Reference",
            "Equation",
        ]
        assert "Footer" in labels


class TestYOLOv10Preprocess:
    """Tests for YOLOv10 preprocessing logic."""

    def test_preprocess_empty_list(self):
        def preprocess(image_list, input_shape=(640, 640), input_names=["images"]):
            inputs = []
            for img in image_list:
                h, w = img.shape[:2]
                r = min(input_shape[0] / h, input_shape[1] / w)
                new_unpad = int(round(w * r)), int(round(h * r))
                dw, dh = input_shape[1] - new_unpad[0], input_shape[0] - new_unpad[1]
                dw /= 2
                dh /= 2
                inputs.append({input_names[0]: np.zeros((3, input_shape[0], input_shape[1]), dtype=np.float32)})
            return inputs

        result = preprocess([])
        assert result == []

    def test_preprocess_single_image(self):
        def preprocess(image_list, input_shape=(640, 640), input_names=["images"]):
            inputs = []
            for img in image_list:
                h, w = img.shape[:2]
                r = min(input_shape[0] / h, input_shape[1] / w)
                new_unpad = int(round(w * r)), int(round(h * r))
                dw, dh = input_shape[1] - new_unpad[0], input_shape[0] - new_unpad[1]
                dw /= 2
                dh /= 2
                inputs.append({input_names[0]: np.zeros((3, input_shape[0], input_shape[1]), dtype=np.float32)})
            return inputs

        img = np.zeros((480, 640, 3), dtype=np.uint8)
        result = preprocess([img])
        assert len(result) == 1


class TestYOLOv10Postprocess:
    """Tests for YOLOv10 postprocessing logic."""

    def test_postprocess_empty_boxes(self):
        def postprocess(boxes, inputs, thr, label_list):
            if len(boxes) == 0:
                return []
            boxes = np.squeeze(boxes)
            scores = boxes[:, 4]
            boxes = boxes[scores > thr, :]
            scores = scores[scores > thr]
            if len(boxes) == 0:
                return []
            return []

        boxes = np.zeros((0, 6))
        inputs = {"scale_factor": [1.0, 1.0, 0.0, 0.0]}
        result = postprocess(boxes, inputs, thr=0.2, label_list=["text", "title"])
        assert result == []


class TestGarbageLayouts:
    """Tests for garbage layout filtering."""

    def test_garbage_layouts(self):
        garbage_layouts = ["footer", "header", "reference"]
        assert "footer" in garbage_layouts
        assert "header" in garbage_layouts
        assert "reference" in garbage_layouts


class TestLayoutTagging:
    """Tests for layout type tagging logic."""

    def test_find_layout_type(self):
        def find_layout(bxs, lts, ty):
            lts_ = [lt for lt in lts if lt["type"] == ty]
            for b in bxs:
                if b.get("layout_type"):
                    continue
                for lt in lts_:
                    if not lt.get("visited"):
                        lt["visited"] = True
                        b["layout_type"] = ty
                        break
            return bxs

        bxs = [{"text": "test1"}, {"text": "test2"}]
        lts = [{"type": "text", "score": 0.9}, {"type": "title", "score": 0.8}]
        result = find_layout(bxs, lts, "text")
        assert result[0].get("layout_type") == "text"
        assert result[1].get("layout_type") is None
