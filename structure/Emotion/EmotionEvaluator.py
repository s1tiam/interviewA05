from __future__ import annotations

import os
import numpy as np
import soundfile as sf
import torch
import librosa
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from transformers import pipeline


class EmotionEvaluator:
    """
    语音情感与非语义评估模块
    - 使用 superb/wav2vec2-base-superb-er 模型进行情感分类
    - 提取音频特征：音量、停顿次数、语调起伏
    - 计算语速（字/秒）并评分
    - 生成面试场景专属的改进建议
    """

    def __init__(self):
        """
        初始化情感评估器
        - 加载 superb/wav2vec2-base-superb-er 模型
        - 自动适配 CPU/GPU
        """
        # 设置模型缓存路径
        os.environ["TRANSFORMERS_CACHE"] = "./models_cache"

        # 确保缓存目录存在
        os.makedirs("./models_cache", exist_ok=True)

        # 面试场景情绪映射字典
        self.EMOTION_MAP = {
            "neutral": "平静",
            "calm": "自信",
            "happy": "自信",
            "sad": "紧张",
            "angry": "焦虑",
            "fear": "紧张",
            "disgust": "焦虑"
        }

        # 自动检测设备（优先使用 GPU）
        self.device = 0 if torch.cuda.is_available() else -1

        # 初始化情感分析模型
        try:
            self.emotion_classifier = pipeline(
                "audio-classification",
                model="superb/wav2vec2-base-superb-er",
                device=self.device,
                model_kwargs={"cache_dir": "./models_cache"}
            )
            self.model_available = True
        except Exception as e:
            print(f"警告: 无法加载情感分析模型: {e}")
            print("将回退到规则化情感分类")
            self.emotion_classifier = None
            self.model_available = False

    def evaluate(self, audio_path: str, transcript: Optional[str] = None) -> Dict:
        """
        评估音频的情感和非语义特征

        Args:
            audio_path: 音频文件路径
            transcript: 可选的文本转录内容

        Returns:
            包含情感评估结果的字典
        """
        try:
            # 检查音频文件是否存在
            if not os.path.exists(audio_path):
                return {
                    "speech_rate": {"value": 0.0, "score": 0.0},
                    "pause": {"count": 0, "score": 0.0},
                    "emotion": {"dominant": "未知", "score": 0.0},
                    "overall_score": 0.0,
                    "suggestions": ["无法分析音频文件"]
                }

            # 读取音频文件
            try:
                audio_data, sample_rate = sf.read(audio_path)
            except Exception as e:
                return {
                    "speech_rate": {"value": 0.0, "score": 0.0},
                    "pause": {"count": 0, "score": 0.0},
                    "emotion": {"dominant": "未知", "score": 0.0},
                    "overall_score": 0.0,
                    "suggestions": [f"音频文件读取失败: {str(e)}"]
                }

            # 计算音频时长
            audio_duration = len(audio_data) / sample_rate

            # 提取音频特征
            features = self._extract_audio_features(audio_data, sample_rate)

            # 计算语速（如果有转录文本）
            speech_rate, speech_rate_score = self._calculate_speech_rate(transcript, audio_duration)

            # 计算停顿评分
            pause_score = self._calculate_pause_score(features["pause_count"])

            # 情感分类
            emotion, emotion_score = self._classify_emotion(audio_path, features, speech_rate)

            # 计算综合得分（情感分70% + 语速分30%）
            overall_score = (emotion_score * 0.7) + (speech_rate_score * 0.3)
            overall_score = max(0.0, min(10.0, overall_score))
            overall_score = round(overall_score, 2)  # 保留2位小数

            # 生成面试专属建议
            suggestions = self._generate_suggestions(features, emotion, speech_rate)

            return {
                "speech_rate": {"value": speech_rate, "score": speech_rate_score},
                "pause": {"count": features["pause_count"], "score": pause_score},
                "emotion": {"dominant": emotion, "score": emotion_score},
                "overall_score": overall_score,
                "suggestions": suggestions
            }

        except Exception as e:
            return {
                "speech_rate": {"value": 0.0, "score": 0.0},
                "pause": {"count": 0, "score": 0.0},
                "emotion": {"dominant": "未知", "score": 0.0},
                "overall_score": 0.0,
                "suggestions": [f"分析过程中出现错误: {str(e)}"]
            }

    def _extract_audio_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict:
        """
        提取音频特征

        Args:
            audio_data: 音频数据
            sample_rate: 采样率

        Returns:
            音频特征字典
        """
        # 计算音量（RMS）
        rms = np.sqrt(np.mean(np.square(audio_data)))

        # 计算停顿次数（低于阈值的部分视为停顿）
        silence_threshold = 0.01

        # 计算停顿次数（连续静音超过200ms视为一次停顿）
        pause_count = 0
        current_pause = 0
        pause_min_length = int(sample_rate * 0.2)  # 200ms

        for i in range(len(audio_data)):
            if abs(audio_data[i]) < silence_threshold:
                current_pause += 1
            else:
                if current_pause >= pause_min_length:
                    pause_count += 1
                current_pause = 0

        # 检查最后一个停顿
        if current_pause >= pause_min_length:
            pause_count += 1

        # 计算语调起伏（通过计算音频的一阶差分的标准差）
        if len(audio_data) > 1:
            pitch_variation = np.std(np.diff(audio_data))
        else:
            pitch_variation = 0

        return {
            "volume": float(rms),
            "pause_count": pause_count,
            "pitch_variation": float(pitch_variation)
        }

    def _calculate_speech_rate(self, transcript: Optional[str], audio_duration: float) -> Tuple[float, float]:
        """
        计算语速并评分（0-10分制）
        - 面试场景最优语速：3-5字/秒

        Args:
            transcript: 文本转录内容
            audio_duration: 音频时长（秒）

        Returns:
            (语速, 语速评分)
        """
        if not transcript or audio_duration <= 0:
            return 0.0, 5.0  # 默认语速和中等评分（0-10分制）

        # 计算字数（简单实现：按字符数计算，不包括空格）
        char_count = len(transcript.replace(" ", ""))
        speech_rate = char_count / audio_duration

        # 语速评分（面试场景：理想语速3-5字/秒）
        if 3 <= speech_rate <= 5:
            score = 9.0
        elif 2.5 <= speech_rate < 3 or 5 < speech_rate <= 6:
            score = 7.5
        elif 2 <= speech_rate < 2.5 or 6 < speech_rate <= 7:
            score = 6.0
        else:
            score = 4.0

        return speech_rate, score

    def _calculate_pause_score(self, pause_count: int) -> float:
        """
        计算停顿评分（0-10分制）

        Args:
            pause_count: 停顿次数

        Returns:
            停顿评分
        """
        # 停顿评分（理想停顿次数：1-3次）
        if 1 <= pause_count <= 3:
            score = 9.0
        elif pause_count == 0:
            score = 7.0
        elif pause_count == 4:
            score = 6.0
        else:
            score = 4.0

        return score

    def _classify_emotion(self, audio_path: str, features: Dict, speech_rate: float) -> Tuple[str, float]:
        """
        情感分类（0-10分制）
        - 使用 superb/wav2vec2-base-superb-er 模型
        - 失败时回退到规则化分类

        Args:
            audio_path: 音频文件路径
            features: 音频特征
            speech_rate: 语速

        Returns:
            (情感类别, 情感得分)
        """
        if self.model_available:
            try:
                # 预处理音频：转为16kHz单声道
                processed_audio_path = self._preprocess_audio(audio_path)

                if processed_audio_path:
                    try:
                        # 使用模型进行情感分析
                        results = self.emotion_classifier(processed_audio_path)

                        # 获取最高得分的情感
                        top_emotion = max(results, key=lambda x: x['score'])
                        emotion_label = top_emotion['label']
                        emotion_score = top_emotion['score'] * 10  # 转换为0-10分制

                        # 映射到面试场景情绪
                        mapped_emotion = self.EMOTION_MAP.get(emotion_label, "未知")

                        # 限制情感得分在0-10之间并保留2位小数
                        emotion_score = max(0.0, min(10.0, emotion_score))
                        emotion_score = round(emotion_score, 2)

                        return mapped_emotion, emotion_score
                    finally:
                        # 清理临时文件
                        if processed_audio_path and os.path.exists(processed_audio_path):
                            try:
                                os.remove(processed_audio_path)
                            except Exception as e:
                                print(f"删除临时文件失败: {e}")
                else:
                    # 预处理失败，回退到规则化分类
                    print("音频预处理失败，回退到规则化分类")
                    return self._rule_based_emotion_classification(features, speech_rate)

            except Exception as e:
                print(f"模型分析失败，回退到规则化分类: {e}")
                # 回退到规则化分类
                return self._rule_based_emotion_classification(features, speech_rate)
        else:
            # 回退到规则化分类
            return self._rule_based_emotion_classification(features, speech_rate)

    def _preprocess_audio(self, audio_path: str) -> Optional[str]:
        """
        音频预处理：将输入音频转为 16kHz 单声道
        - 先读原始采样率再高质量重采样

        Args:
            audio_path: 原始音频文件路径

        Returns:
            预处理后的临时音频文件路径，失败时返回 None
        """
        try:
            # 先读取原始音频（保持原始采样率）
            y, sr = librosa.load(audio_path, sr=None, mono=False)

            # 高质量重采样到16kHz
            y_resampled = librosa.resample(y, orig_sr=sr, target_sr=16000)

            # 确保是单声道
            if len(y_resampled.shape) > 1:
                y_resampled = librosa.to_mono(y_resampled)

            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_file_path = temp_file.name
            temp_file.close()

            # 保存预处理后的音频
            sf.write(temp_file_path, y_resampled, 16000)

            return temp_file_path
        except Exception as e:
            print(f"音频预处理失败: {e}")
            return None

    def _rule_based_emotion_classification(self, features: Dict, speech_rate: float) -> Tuple[str, float]:
        """
        基于规则的情感分类（回退方案）

        Args:
            features: 音频特征
            speech_rate: 语速

        Returns:
            (情感类别, 情感得分)
        """
        volume = features.get("volume", 0)
        pause_count = features.get("pause_count", 0)
        pitch_variation = features.get("pitch_variation", 0)

        # 情感分类逻辑
        scores = {
            "自信": 0,
            "紧张": 0,
            "平静": 0,
            "焦虑": 0
        }

        # 音量评分
        if 0.05 <= volume <= 0.15:
            scores["自信"] += 2.5
            scores["平静"] += 2.5
        elif volume < 0.05:
            scores["紧张"] += 2.5
        else:
            scores["焦虑"] += 2.5

        # 停顿次数评分
        if 1 <= pause_count <= 3:
            scores["自信"] += 2.5
        elif pause_count > 3:
            scores["紧张"] += 2.5
        else:
            scores["平静"] += 2.5

        # 语调变化评分
        if 0.001 <= pitch_variation <= 0.01:
            scores["自信"] += 2.5
        elif pitch_variation > 0.01:
            scores["紧张"] += 1.25
            scores["焦虑"] += 1.25
        else:
            scores["平静"] += 2.5

        # 语速评分
        if 3 <= speech_rate <= 5:
            scores["自信"] += 2.5
            scores["平静"] += 2.5
        elif speech_rate > 5:
            scores["紧张"] += 1.25
            scores["焦虑"] += 1.25
        else:
            scores["紧张"] += 2.5

        # 确定情感类别
        emotion = max(scores, key=scores.get)
        emotion_score = scores[emotion]

        # 限制情感得分在0-10之间并保留2位小数
        emotion_score = max(0.0, min(10.0, emotion_score))
        emotion_score = round(emotion_score, 2)

        return emotion, emotion_score

    def _generate_suggestions(self, features: Dict, emotion: str, speech_rate: float) -> List[str]:
        """
        生成面试专属改进建议

        Args:
            features: 音频特征
            emotion: 情感类别
            speech_rate: 语速

        Returns:
            建议列表
        """
        suggestions = []

        # 基于音量的建议
        volume = features.get("volume", 0)
        if volume < 0.05:
            suggestions.append("面试中音量偏小，建议提高音量，使回答更加清晰有力，展现自信")
        elif volume > 0.15:
            suggestions.append("面试中音量偏大，建议适当降低音量，保持平稳的语调，显得更加专业")

        # 基于停顿的建议
        pause_count = features.get("pause_count", 0)
        if pause_count > 3:
            suggestions.append(f"面试中停顿次数较多（{pause_count}次），建议减少不必要的停顿，保持回答的连贯性")
        elif pause_count == 0:
            suggestions.append("回答流畅性优秀，建议适当增加停顿，让表达更有节奏，突出重点")

        # 基于语速的建议
        if speech_rate > 5:
            suggestions.append(f"当前语速偏快（{speech_rate:.1f}字/秒），建议放慢至3-5字/秒，回答前深呼吸缓解紧张")
        elif speech_rate < 3:
            suggestions.append(f"当前语速偏慢（{speech_rate:.1f}字/秒），建议适当加快语速至3-5字/秒，保持面试节奏")
        else:
            suggestions.append(f"语速适中（{speech_rate:.1f}字/秒），继续保持良好的表达节奏")

        # 基于情感的建议
        if emotion == "紧张":
            suggestions.append("面试中表现出紧张情绪，建议提前充分准备，回答前深呼吸，保持微笑，增强自信心")
        elif emotion == "焦虑":
            suggestions.append("面试中表现出焦虑情绪，建议保持冷静，有条理地组织回答内容，聚焦于问题本身")
        elif emotion == "平静":
            suggestions.append("面试中表现平静，建议适当增加回答的热情和表现力，展现对岗位的兴趣")
        elif emotion == "自信":
            suggestions.append("面试中表现自信，继续保持良好的状态，注意保持谦逊态度")

        # 确保至少有一条建议
        if not suggestions:
            suggestions.append("继续保持良好的面试状态")

        return suggestions


# 测试代码
if __name__ == "__main__":
    """
    测试情感分析功能
    """
    evaluator = EmotionEvaluator()

    # 测试音频路径（请替换为实际的音频文件路径）
    test_audio_path = "test_audio.wav"
    test_transcript = "我是一名软件工程师，有五年的Java开发经验，熟悉Spring Boot和微服务架构"

    if os.path.exists(test_audio_path):
        result = evaluator.evaluate(test_audio_path, test_transcript)
        print("测试结果:")
        print(f"语速: {result['speech_rate']['value']:.2f}字/秒, 评分: {result['speech_rate']['score']:.1f}")
        print(f"停顿次数: {result['pause']['count']}, 评分: {result['pause']['score']:.1f}")
        print(f"情感: {result['emotion']['dominant']}, 评分: {result['emotion']['score']:.1f}")
        print(f"综合评分: {result['overall_score']:.2f}")
        print("改进建议:")
        for i, suggestion in enumerate(result['suggestions'], 1):
            print(f"{i}. {suggestion}")
    else:
        print(f"测试音频文件不存在: {test_audio_path}")
        print("请提供一个wav格式的测试音频文件")