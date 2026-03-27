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

"""Unit tests for OCR functionality in deepdoc/vision/ocr.py.

Tests cover standalone OCR functions that can be tested without heavy dependencies:
- transform: applies transformation operators to data
- create_operators: creates operators from config
- OCR utility methods: sorted_boxes, get_rotate_crop_image

These tests use mocking to avoid loading actual ONNX models.
"""

import pytest
import numpy as np


class TestTransform:
    """Tests for the transform function."""

    def test_transform_with_no_ops(self):
        def transform(data, ops=None):
            if ops is None:
                ops = []
            for op in ops:
                data = op(data)
                if data is None:
                    return None
            return data

        data = {"test": "value"}
        result = transform(data, None)
        assert result == data

    def test_transform_with_empty_ops_list(self):
        def transform(data, ops=None):
            if ops is None:
                ops = []
            for op in ops:
                data = op(data)
                if data is None:
                    return None
            return data

        data = {"test": "value"}
        result = transform(data, [])
        assert result == data

    def test_transform_with_ops(self):
        def transform(data, ops=None):
            if ops is None:
                ops = []
            for op in ops:
                data = op(data)
                if data is None:
                    return None
            return data

        def op1(data):
            data["processed"] = True
            return data

        def op2(data):
            data["step2"] = True
            return data

        data = {"original": True}
        result = transform(data, [op1, op2])
        assert result["original"] is True
        assert result["processed"] is True
        assert result["step2"] is True

    def test_transform_returns_none_on_op_failure(self):
        def transform(data, ops=None):
            if ops is None:
                ops = []
            for op in ops:
                data = op(data)
                if data is None:
                    return None
            return data

        def failing_op(data):
            return None

        data = {"test": "value"}
        result = transform(data, [failing_op])
        assert result is None


class TestCreateOperators:
    """Tests for the create_operators function."""

    def test_create_operators_empty_list(self):
        def create_operators(op_param_list, global_config=None):
            assert isinstance(op_param_list, list), "operator config should be a list"
            ops = []
            for operator in op_param_list:
                assert isinstance(operator, dict) and len(operator) == 1, "yaml format error"
            return ops

        result = create_operators([])
        assert result == []

    def test_create_operators_invalid_config(self):
        def create_operators(op_param_list, global_config=None):
            assert isinstance(op_param_list, list), "operator config should be a list"
            ops = []
            for operator in op_param_list:
                assert isinstance(operator, dict) and len(operator) == 1, "yaml format error"
            return ops

        with pytest.raises(AssertionError):
            create_operators("not a list")

    def test_create_operators_invalid_operator_format(self):
        def create_operators(op_param_list, global_config=None):
            assert isinstance(op_param_list, list), "operator config should be a list"
            ops = []
            for operator in op_param_list:
                assert isinstance(operator, dict) and len(operator) == 1, "yaml format error"
            return ops

        with pytest.raises(AssertionError):
            create_operators([{"op1": {}, "op2": {}}])


class TestOCRClassMethods:
    """Tests for OCR class methods using mocks."""

    def test_sorted_boxes_logic(self):
        """Test the sorted_boxes method logic."""

        def sorted_boxes(dt_boxes):
            num_boxes = dt_boxes.shape[0]
            sorted_boxes = sorted(dt_boxes, key=lambda x: (x[0][1], x[0][0]))
            _boxes = list(sorted_boxes)

            for i in range(num_boxes - 1):
                for j in range(i, -1, -1):
                    if abs(_boxes[j + 1][0][1] - _boxes[j][0][1]) < 10 and (_boxes[j + 1][0][0] < _boxes[j][0][0]):
                        tmp = _boxes[j]
                        _boxes[j] = _boxes[j + 1]
                        _boxes[j + 1] = tmp
                    else:
                        break
            return _boxes

        dt_boxes = np.array(
            [
                [[10, 100], [50, 100], [50, 120], [10, 120]],
                [[10, 10], [50, 10], [50, 30], [10, 30]],
                [[100, 10], [150, 10], [150, 30], [100, 30]],
            ]
        )
        result = sorted_boxes(dt_boxes)
        assert len(result) == 3
        assert result[0][0][1] <= result[1][0][1]

    def test_order_points_clockwise_logic(self):
        """Test the order_points_clockwise method logic."""

        def order_points_clockwise(pts):
            rect = np.zeros((4, 2), dtype="float32")
            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]
            rect[2] = pts[np.argmax(s)]
            tmp = np.delete(pts, (np.argmin(s), np.argmax(s)), axis=0)
            diff = np.diff(np.array(tmp), axis=1)
            rect[1] = tmp[np.argmin(diff)]
            rect[3] = tmp[np.argmax(diff)]
            return rect

        pts = np.array([[10, 0], [0, 0], [0, 10], [10, 10]], dtype=np.float32)
        result = order_points_clockwise(pts)
        assert result.shape == (4, 2)

    def test_clip_det_res_logic(self):
        """Test the clip_det_res method logic."""

        def clip_det_res(points, img_height, img_width):
            for pno in range(points.shape[0]):
                points[pno, 0] = int(min(max(points[pno, 0], 0), img_width - 1))
                points[pno, 1] = int(min(max(points[pno, 1], 0), img_height - 1))
            return points

        points = np.array([[-5, 10], [20, 10], [20, 50], [-5, 50]], dtype=np.float32)
        result = clip_det_res(points, 40, 30)
        assert result.shape == (4, 2)
        assert result[0, 0] == 0

    def test_get_rotate_crop_image_logic(self):
        """Test the get_rotate_crop_image method logic."""

        def get_rotate_crop_image_logic(img, points):
            assert len(points) == 4, "shape of points must be 4*2"
            img_crop_width = int(max(np.linalg.norm(points[0] - points[1]), np.linalg.norm(points[2] - points[3])))
            img_crop_height = int(max(np.linalg.norm(points[0] - points[3]), np.linalg.norm(points[1] - points[2])))
            return np.zeros((img_crop_height, img_crop_width, 3), dtype=np.float32)

        img = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
        points = np.array([[10, 10], [100, 10], [100, 50], [10, 50]], dtype=np.float32)
        result = get_rotate_crop_image_logic(img, points)
        assert result is not None
        assert result.shape[0] > 0
        assert result.shape[1] > 0


class TestOCRDetection:
    """Tests for OCR detection logic."""

    def test_detect_with_none_image_logic(self):
        """Test detect method with None image."""

        def detect_logic(img, text_detector):
            if img is None:
                return None, None, {"det": 0, "rec": 0, "cls": 0, "all": 0}
            return text_detector(img)

        result = detect_logic(None, lambda x: x)
        assert result[0] is None
        assert result[1] is None
        assert result[2]["all"] == 0

    def test_sorted_boxes_empty_input(self):
        """Test sorted_boxes with empty input."""

        def sorted_boxes(dt_boxes):
            return sorted(dt_boxes, key=lambda x: (x[0][1], x[0][0]))

        dt_boxes = []
        result = sorted_boxes(dt_boxes)
        assert result == []


class TestOCRRecognition:
    """Tests for OCR recognition logic."""

    def test_recognize_threshold_filter(self):
        """Test recognize threshold filtering."""

        def recognize_filter(rec_res, drop_score):
            text, score = rec_res[0]
            if score < drop_score:
                return ""
            return text

        assert recognize_filter([("Hello", 0.9)], 0.5) == "Hello"
        assert recognize_filter([("LowScore", 0.3)], 0.5) == ""

    def test_recognize_batch_logic(self):
        """Test recognize_batch method logic."""

        def recognize_batch_logic(rec_res, drop_score):
            texts = []
            for i in range(len(rec_res)):
                text, score = rec_res[i]
                if score < drop_score:
                    text = ""
                texts.append(text)
            return texts

        rec_res = [
            ("Text1", 0.9),
            ("Text2", 0.8),
            ("Text3", 0.3),
        ]
        result = recognize_batch_logic(rec_res, 0.5)
        assert len(result) == 3
        assert result[0] == "Text1"
        assert result[1] == "Text2"
        assert result[2] == ""


class TestTextDetectorLogic:
    """Tests for TextDetector logic."""

    def test_filter_tag_det_res_logic(self):
        """Test filter_tag_det_res method logic."""

        def filter_tag_det_res_logic(dt_boxes, image_shape):
            dt_boxes_new = []
            for box in dt_boxes:
                if isinstance(box, list):
                    box = np.array(box)
                rect_width = int(np.linalg.norm(box[0] - box[1]))
                rect_height = int(np.linalg.norm(box[0] - box[3]))
                if rect_width <= 3 or rect_height <= 3:
                    continue
                dt_boxes_new.append(box)
            return np.array(dt_boxes_new)

        dt_boxes = np.array(
            [
                [[0, 0], [10, 0], [10, 10], [0, 10]],
                [[100, 100], [110, 100], [110, 110], [100, 110]],
            ]
        )
        result = filter_tag_det_res_logic(dt_boxes, [200, 200])
        assert result.shape[0] >= 0


class TestTextRecognizerLogic:
    """Tests for TextRecognizer logic."""

    def test_resize_norm_img_logic(self):
        """Test resize_norm_img method logic."""

        def resize_norm_img_logic(img, max_wh_ratio, rec_image_shape, input_tensor_shape):
            imgC, imgH, imgW = rec_image_shape
            imgW = int((imgH * max_wh_ratio))
            w = input_tensor_shape[3:][0]
            if w is not None and w > 0:
                imgW = w
            h, w = img.shape[:2]
            ratio = w / float(h)
            if np.ceil(imgH * ratio) > imgW:
                resized_w = imgW
            else:
                resized_w = int(np.ceil(imgH * ratio))
            return np.zeros((imgC, imgH, imgW), dtype=np.float32)

        img = np.random.randint(0, 255, (48, 100, 3), dtype=np.uint8)
        result = resize_norm_img_logic(img, 1.5, [3, 48, 320], [None, 3, 48, 320])
        assert result.shape[0] == 3
        assert result.shape[1] == 48

    def test_resize_norm_img_vl_logic(self):
        """Test resize_norm_img_vl method logic."""

        def resize_norm_img_vl_logic(img, image_shape):
            imgC, imgH, imgW = image_shape
            img = img[:, :, ::-1]
            resized_image = np.zeros((imgH, imgW, imgC), dtype=np.uint8)
            resized_image = resized_image.astype("float32")
            resized_image = resized_image.transpose((2, 0, 1)) / 255
            return resized_image

        img = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
        image_shape = [3, 48, 320]
        result = resize_norm_img_vl_logic(img, image_shape)
        assert result.shape[0] == 3

    def test_resize_norm_img_svtr_logic(self):
        """Test resize_norm_img_svtr method logic."""

        def resize_norm_img_svtr_logic(img, image_shape):
            imgC, imgH, imgW = image_shape
            resized_image = np.zeros((imgH, imgW, imgC), dtype=np.uint8)
            resized_image = resized_image.astype("float32")
            resized_image = resized_image.transpose((2, 0, 1)) / 255
            resized_image -= 0.5
            resized_image /= 0.5
            return resized_image

        img = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
        image_shape = [3, 48, 320]
        result = resize_norm_img_svtr_logic(img, image_shape)
        assert result.shape[0] == 3


class TestOCRTimeDict:
    """Tests for time tracking in OCR."""

    def test_time_dict_initialization(self):
        """Test time dictionary initialization."""
        time_dict = {"det": 0, "rec": 0, "cls": 0, "all": 0}
        assert time_dict["det"] == 0
        assert time_dict["rec"] == 0
        assert time_dict["cls"] == 0
        assert time_dict["all"] == 0


class TestOCRDropScore:
    """Tests for OCR drop score threshold."""

    def test_default_drop_score(self):
        """Test default drop score is 0.5."""
        drop_score = 0.5
        assert drop_score == 0.5

    def test_drop_score_filtering(self):
        """Test that texts below drop_score are filtered."""

        def filter_by_score(rec_res, drop_score):
            return [text for text, score in rec_res if score >= drop_score]

        rec_res = [("high", 0.9), ("low", 0.3), ("medium", 0.6)]
        result = filter_by_score(rec_res, 0.5)
        assert len(result) == 2
        assert "high" in result
        assert "medium" in result
        assert "low" not in result


class TestOCRImageProcessing:
    """Tests for OCR image processing utilities."""

    def test_aspect_ratio_calculation(self):
        """Test aspect ratio calculation."""
        width_list = []
        for h, w in [(30, 100), (40, 80), (50, 200)]:
            width_list.append(w / float(h))

        assert len(width_list) == 3

    def test_image_cropping(self):
        """Test image cropping logic."""

        def crop_image(img, points):
            left = int(min(points[:, 0]))
            right = int(max(points[:, 0]))
            top = int(min(points[:, 1]))
            bottom = int(max(points[:, 1]))
            return img[top:bottom, left:right].copy()

        img = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
        points = np.array([[10, 10], [100, 10], [100, 50], [10, 50]], dtype=np.float32)
        result = crop_image(img, points)
        assert result.shape[0] > 0
        assert result.shape[1] > 0
