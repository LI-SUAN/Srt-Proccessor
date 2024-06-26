import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QFileDialog, QPushButton, QDesktopWidget, QComboBox
import regex as re
import pyperclip
import os

class SRTProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SRT文本处理器")
        self.resize(1200, 800)  # 设置窗口大小

        self.input_text_area = QTextEdit()
        self.input_text_area.setPlaceholderText("在此处粘贴或拖动SRT文件内容")

        self.language_selector = QComboBox()
        self.language_selector.addItems(["中文", "英文"])
        self.language_selector.currentIndexChanged.connect(self.update_language)

        self.process_button = QPushButton("处理")
        self.process_button.clicked.connect(self.process_button_click)

        self.output_text_area = QTextEdit()
        self.output_text_area.setPlaceholderText("处理后的文本将显示在此处")
        self.output_text_area.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.language_selector)
        layout.addWidget(self.input_text_area)
        layout.addWidget(self.process_button)
        layout.addWidget(self.output_text_area)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # 添加拖放事件处理器
        self.input_text_area.setAcceptDrops(True)
        self.input_text_area.dragEnterEvent = self.dragEnterEvent
        self.input_text_area.dropEvent = self.dropEvent

        self.center()  # 将窗口移动到屏幕中央

    def center(self):
        # 获取屏幕尺寸
        screen = QDesktopWidget().screenGeometry()
        # 获取窗口尺寸
        size = self.geometry()
        # 计算窗口移动后的位置
        x = int((screen.width() - size.width()) / 2)
        y = int((screen.height() - size.height()) / 2)
        # 将窗口移动到屏幕中央
        self.move(x, y)

    def process_srt(self, srt_text, language):
        # 定义正则表达式模式，用于匹配SRT文本中的时间标记和对应的字幕内容
        pattern = re.compile(r'(\d+)\n(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)\n(.+?)(?=\n\n\d+|$)', re.DOTALL)
        matches = re.findall(pattern, srt_text)  # 根据正则表达式匹配SRT文本内容

        result_sentences = []  # 存储处理后的句子列表

        for i in range(len(matches)):
            index, start_time, end_time, sentence = matches[i]
            result_sentences.append(sentence)  # 将句子添加到结果列表中

        if language == "中文":
            result_sentences = self.process_chinese_subtitles(result_sentences, matches)
        else:
            result_sentences = self.process_english_subtitles(result_sentences)

        # 将处理后的文本连接成一篇文章
        result_text = ' '.join(result_sentences).replace('\n', ' ').strip()

        if language == "中文":
            result_text = self.correct_chinese_punctuation(result_text)
        else:
            result_text = self.correct_english_punctuation(result_text)

        return result_text  # 返回处理后的文本

    def process_chinese_subtitles(self, result_sentences, matches):
        for i in range(len(matches)):
            index, start_time, end_time, sentence = matches[i]
            result_sentences[i] = sentence  # 更新句子列表中的元素

            if i < len(matches) - 1:
                next_start_time = matches[i + 1][1]

                # 判断时间是否连续，根据不同情况在句子末尾添加逗号或句号
                if next_start_time == end_time:
                    result_sentences[i] += '，'  # 连续，加逗号
                else:
                    result_sentences[i] += '。'  # 不连续，加句号

        return result_sentences

    def process_english_subtitles(self, result_sentences):
        # 英文字幕的处理逻辑（无需添加标点符号）
        return result_sentences

    def correct_chinese_punctuation(self, result_text):
        # 需要修正的标点符号映射
        punctuation_mapping = {
            ' ': '，',
            '，，': '，',
            '。，': '。',
            '?，': '？',
            '?。': '？',
            '？，': '？',
            '？。': '？',
            '!，': '！',
            '!。': '！',
            '！，': '！',
            '！。': '！',
            '”。': '”',
            '"。': '"',
        }

        # 使用正则表达式找到文本中的中文标点符号，并替换为正确的标点符号
        for error, correct in punctuation_mapping.items():
            result_text = re.sub(re.escape(error) + '+', correct, result_text)

        # 修正句末的标点符号
        result_text = re.sub(r'([。])([^”’])', r'\1\n\n\2', result_text)

        return result_text

    def correct_english_punctuation(self, result_text):
        # 在所有的. ? ! " 这里添加换行符
        result_text = re.sub(r'([‘’])', r"'", result_text)
        result_text = re.sub(r'([“”])', r'"', result_text)
        result_text = re.sub(r'([.!?] )', r'\1\n\n', result_text)
        # result_text = re.sub(r'(["] )', r'\1\n\n', result_text)
        return result_text

    def open_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.input_text_area.setPlainText(content)  # 将文件内容显示在输入文本框中
        except Exception as e:
            print(f"Error opening file: {e}")

    def process_button_click(self):
        input_text = self.input_text_area.toPlainText()  # 获取输入文本框中的内容
        selected_language = self.language_selector.currentText()
        output_text = self.process_srt(input_text, selected_language)  # 处理SRT文本
        self.output_text_area.setPlainText(output_text)  # 将处理后的文本显示在输出文本框中

        # 复制结果到剪切板
        pyperclip.copy(output_text)  # 将处理后的文本复制到剪切板

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()

            # 如果是文件夹，则读取文件夹中的唯一的SRT文件
            if os.path.isdir(path):
                srt_files = [f for f in os.listdir(path) if f.lower().endswith('.srt')]
                if len(srt_files) == 1:
                    srt_file_path = os.path.join(path, srt_files[0])
                    self.open_file(srt_file_path)
                    self.process_button_click()  # 自动点击处理按钮
                    break
                else:
                    print("文件夹中没有唯一的SRT文件")
                    break

            # 如果是文件，则像以前一样处理
            elif os.path.isfile(path) and path.lower().endswith('.srt'):
                self.open_file(path)
                self.process_button_click()  # 自动点击处理按钮
                break

        # 复制结果到剪切板
        output_text = self.output_text_area.toPlainText()
        pyperclip.copy(output_text)

    def update_language(self):
        # 可以在这里添加一些语言变化时的处理逻辑
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SRTProcessor()
    window.show()
    sys.exit(app.exec_())
