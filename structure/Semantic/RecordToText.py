
import os
import json
import subprocess
from structure.LLM.Deepseek import chat_with_deepseek

# 配置区
WSPrompt = (
	"针对以下文本，第一段为针对一位应届大学生的面试提问题；"
	"第二段为该名大学生的回答；"
	"（若答案存在标识符AnsLiveSign为1,则加上“第三段为数据集提供的标准答案”）；"
	"请你根据该名大学生的回答，评估该学生的回答质量，并给出回答分数。"
)

# 1. 调用FunASR识别wav为文本
def run_funasr(wav_path, output_txt_path, model='paraformer-zh', funasr_cmd='funasr'):
	cmd = [funasr_cmd, '--model', model, '--input', wav_path, '--output', output_txt_path]
	subprocess.run(cmd, check=True)

# 2. 读取ASR输出文本
def read_asr_text(txt_path):
	with open(txt_path, 'r', encoding='utf-8') as f:
		return f.read().strip()

# 3. 拼接待处理文本
def build_wait_send_text(WSPrompt, question, user_ans, true_qa_ans=None):
	parts = [WSPrompt, question, user_ans]
	if true_qa_ans:
		parts.append(true_qa_ans)
	return "\n\n".join(parts)

# 4. 主流程
def main(wav_path, question, true_qa_ans=None, ans_live_sign=1):
	asr_txt_path = wav_path.replace('.wav', '_asr.txt')
	run_funasr(wav_path, asr_txt_path)
	user_ans = read_asr_text(asr_txt_path)
	wait_send_text = build_wait_send_text(WSPrompt, question, user_ans, true_qa_ans if ans_live_sign else None)
	# deepseek评估
	system_prompt = "你是面试评估专家，请严格按照评分机制输出分数和分析。分数单独输出一行，格式为：SCORE:xx"
	response = chat_with_deepseek(wait_send_text, system_prompt)
	# 解析分数
	score = None
	for line in response.splitlines():
		if line.strip().startswith('SCORE:'):
			try:
				score = int(line.strip().split(':')[1])
			except:
				pass
	result = {"text": response, "score": score}
	print(json.dumps(result, ensure_ascii=False, indent=2))
	return result

if __name__ == "__main__":
	# 示例参数
	wav_path = r"输入你的wav文件路径.wav"
	question = "请介绍一下你自己。"
	true_qa_ans = "我是某大学应届毕业生，主修计算机科学。"
	ans_live_sign = 1  # 1表示有标准答案，0表示无
	main(wav_path, question, true_qa_ans, ans_live_sign)