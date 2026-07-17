from abc import ABC, abstractmethod
from typing import List, Dict, Type
import time
import random


class BaseModelAdapter(ABC):
    model_name: str = "base"
    model_version: str = "1.0"

    def __init__(self):
        self.loaded = False

    @abstractmethod
    def load(self, weights_path: str = None):
        raise NotImplementedError

    @abstractmethod
    def run(self, frame, meta: Dict = None) -> List[Dict]:
        raise NotImplementedError

    def unload(self):
        self.loaded = False

    def health(self) -> Dict:
        return {"model": self.model_name, "version": self.model_version, "loaded": self.loaded}


class MockAdapter(BaseModelAdapter):
    def __init__(self, model_name: str, event_types: List[str]):
        super().__init__()
        self.model_name = model_name
        self.event_types = event_types

    def load(self, weights_path: str = None):
        time.sleep(0.05)
        self.loaded = True

    def run(self, frame, meta: Dict = None) -> List[Dict]:
        if random.random() < 0.3:
            return []
        return [{
            "event_type": random.choice(self.event_types),
            "confidence": round(random.uniform(0.6, 0.99), 2),
            "bbox": [round(random.uniform(0, 0.7), 2), round(random.uniform(0, 0.7), 2), 0.2, 0.2],
            "model_name": self.model_name,
            "model_version": self.model_version,
        }]


_REGISTRY: Dict[str, Type[BaseModelAdapter]] = {}


def register_adapter(model_name: str):
    def decorator(cls):
        _REGISTRY[model_name] = cls
        return cls
    return decorator


def get_adapter(model_name: str) -> BaseModelAdapter:
    if model_name not in _REGISTRY:
        raise ValueError(f"No adapter registered for model: {model_name}")
    return _REGISTRY[model_name]()


register_adapter("ppe")(lambda: MockAdapter("ppe", ["no_helmet", "no_vest", "compliant"]))


import cv2
if not hasattr(cv2, 'imshow'):
    cv2.imshow = lambda *args, **kwargs: None
if not hasattr(cv2, 'waitKey'):
    cv2.waitKey = lambda *args, **kwargs: -1


from ultralytics import YOLO
from huggingface_hub import hf_hub_download

@register_adapter("ppe")
class PPEAdapter(BaseModelAdapter):
    model_name = "ppe"
    model_version = "1.0"

    def load(self, weights_path: str = None):
        path = weights_path or hf_hub_download(
            repo_id="Hansung-Cho/yolov8-ppe-detection", filename="best.pt"
        )
        self._model = YOLO(path)
        self.loaded = True

    def run(self, frame, meta: Dict = None) -> List[Dict]:
        results = self._model(frame, conf=0.4, verbose=False)[0]
        detections = []
        names = results.names
        h, w = frame.shape[:2]

        persons = [b for b in results.boxes if names[int(b.cls)].lower() == "person"]
        hardhats = [b for b in results.boxes if names[int(b.cls)].lower() == "hardhat"]
        vests = [b for b in results.boxes if names[int(b.cls)].lower() == "safety vest"]

        def center_in_box(inner_box, outer_xyxy, pad_ratio=0.15):
            cx = inner_box.xyxy[0][[0, 2]].mean().item()
            cy = inner_box.xyxy[0][[1, 3]].mean().item()
            x1, y1, x2, y2 = outer_xyxy
            pad_x = (x2 - x1) * pad_ratio
            pad_y = (y2 - y1) * pad_ratio
            return (x1 - pad_x) <= cx <= (x2 + pad_x) and (y1 - pad_y) <= cy <= (y2 + pad_y)

        for p in persons:
            x1, y1, x2, y2 = p.xyxy[0].tolist()
            has_helmet = any(center_in_box(hh, (x1, y1, x2, y2)) for hh in hardhats)
            has_vest = any(center_in_box(v, (x1, y1, x2, y2)) for v in vests)
            event_type = "compliant" if (has_helmet and has_vest) else (
                "no_helmet" if not has_helmet else "no_vest"
            )
            detections.append({
                "event_type": event_type,
                "confidence": round(float(p.conf[0]), 2),
                "bbox": [round(x1 / w, 3), round(y1 / h, 3), round((x2 - x1) / w, 3), round((y2 - y1) / h, 3)],
                "model_name": self.model_name,
                "model_version": self.model_version,
            })
        return detections


import os
from django.conf import settings

SHOPLIFTING_WEIGHTS = os.path.join(settings.BASE_DIR, "core", "weights", "shoplifting_v1.pt")

@register_adapter("shoplifting")
class ShopliftingAdapter(BaseModelAdapter):
    model_name = "shoplifting"
    model_version = "1.0"
    EVENT_MAP = {"shoplifting": "shoplifting", "suspicious": "suspicious_activity"}

    def load(self, weights_path: str = None):
        self._model = YOLO(weights_path or SHOPLIFTING_WEIGHTS)
        self.loaded = True

    def run(self, frame, meta: Dict = None) -> List[Dict]:
        results = self._model(frame, conf=0.5, verbose=False)[0]
        detections = []
        names = results.names
        h, w = frame.shape[:2]

        for box in results.boxes:
            label = names[int(box.cls)].lower()
            if label not in self.EVENT_MAP:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "event_type": self.EVENT_MAP[label],
                "confidence": round(float(box.conf[0]), 2),
                "bbox": [round(x1 / w, 3), round(y1 / h, 3), round((x2 - x1) / w, 3), round((y2 - y1) / h, 3)],
                "model_name": self.model_name,
                "model_version": self.model_version,
            })
        return detections


from inference_sdk import InferenceHTTPClient

@register_adapter("theft")
class TheftAdapter(BaseModelAdapter):
    model_name = "theft"
    model_version = "1.0"
    MODEL_ID = "theft-detection-w9jvg/1"
    EVENT_MAP = {"theft": "theft", "alart": "suspicious_activity"}

    def load(self, weights_path: str = None):
        self._client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key=settings.ROBOFLOW_API_KEY,
        )
        self.loaded = True

    def run(self, frame, meta: Dict = None) -> List[Dict]:
        ok, buf = cv2.imencode(".jpg", frame)
        if not ok:
            return []
        result = self._client.infer(buf.tobytes(), model_id=self.MODEL_ID)
        detections = []
        h, w = frame.shape[:2]

        for pred in result.get("predictions", []):
            label = pred["class"].lower()
            if label not in self.EVENT_MAP:
                continue
            x_center, y_center = pred["x"], pred["y"]
            bw, bh = pred["width"], pred["height"]
            x1 = (x_center - bw / 2) / w
            y1 = (y_center - bh / 2) / h
            detections.append({
                "event_type": self.EVENT_MAP[label],
                "confidence": round(pred["confidence"], 2),
                "bbox": [round(x1, 3), round(y1, 3), round(bw / w, 3), round(bh / h, 3)],
                "model_name": self.model_name,
                "model_version": self.model_version,
            })
        return detections


@register_adapter("attendance")
class AttendanceAdapter(BaseModelAdapter):
    model_name = "attendance"
    model_version = "1.0"

    def load(self, weights_path: str = None):
        self._model = YOLO(weights_path or "yolov8n.pt")
        self.loaded = True

    def run(self, frame, meta: Dict = None) -> List[Dict]:
        results = self._model(frame, conf=0.5, classes=[0], verbose=False)[0]
        detections = []
        h, w = frame.shape[:2]

        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "event_type": "person_present",
                "confidence": round(float(box.conf[0]), 2),
                "bbox": [round(x1 / w, 3), round(y1 / h, 3), round((x2 - x1) / w, 3), round((y2 - y1) / h, 3)],
                "model_name": self.model_name,
                "model_version": self.model_version,
            })
        return detections


try:
    from transformers import ViTImageProcessor, ViTForImageClassification
    from PIL import Image
    import torch

    @register_adapter("facial_expression")
    class FacialExpressionAdapter(BaseModelAdapter):
        model_name = "facial_expression"
        model_version = "1.0"
        EMOTIONS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

        def load(self, weights_path: str = None):
            self._processor = ViTImageProcessor.from_pretrained('abhilash88/face-emotion-detection')
            self._model = ViTForImageClassification.from_pretrained('abhilash88/face-emotion-detection')
            self._face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.loaded = True

        def run(self, frame, meta: Dict = None) -> List[Dict]:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
            detections = []
            h, w = frame.shape[:2]

            for (x, y, fw, fh) in faces:
                face_crop = frame[y:y+fh, x:x+fw]
                face_img = Image.fromarray(cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB))
                inputs = self._processor(face_img, return_tensors="pt")
                with torch.no_grad():
                    outputs = self._model(**inputs)
                    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                    idx = torch.argmax(probs, dim=-1).item()

                detections.append({
                    "event_type": self.EMOTIONS[idx].lower(),
                    "confidence": round(probs[0][idx].item(), 2),
                    "bbox": [round(x / w, 3), round(y / h, 3), round(fw / w, 3), round(fh / h, 3)],
                    "model_name": self.model_name,
                    "model_version": self.model_version,
                })
            return detections
except ImportError as e:
    print(f"[adapters] Skipping FacialExpressionAdapter, import failed: {e}")