"""document_processor.py - 文档处理器

处理上传的PDF、Word、图片等文档，支持Gemini API的文档处理功能
"""
import os
import time
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import google.generativeai as genai
from ..config import CONFIG
from ..utils.exceptions import LLMAPIError


class DocumentProcessor:
    """文档处理器 - 管理文档上传和处理"""

    # 支持的文件格式
    SUPPORTED_FORMATS = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }

    # 文件大小限制 (20MB)
    MAX_FILE_SIZE = 20 * 1024 * 1024

    def __init__(self):
        """初始化文档处理器"""
        self.uploaded_files = {}  # 缓存已上传的文件
        self.debug_mode = CONFIG.debug_mode

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """验证文件是否可以上传

        Args:
            file_path: 文件路径

        Returns:
            (是否有效, 错误信息)
        """
        path = Path(file_path)

        # 检查文件是否存在
        if not path.exists():
            return False, f"文件不存在: {file_path}"

        # 检查文件格式
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            supported = ', '.join(self.SUPPORTED_FORMATS.keys())
            return False, f"不支持的文件格式 {suffix}，支持格式: {supported}"

        # 检查文件大小
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            return False, f"文件太大 ({size_mb:.1f}MB)，最大支持 20MB"

        if file_size == 0:
            return False, "文件为空"

        return True, ""

    def upload_file(self, file_path: str) -> Optional[genai.File]:
        """上传文件到Gemini

        Args:
            file_path: 文件路径

        Returns:
            上传的文件对象，失败返回None
        """
        # 验证文件
        is_valid, error_msg = self.validate_file(file_path)
        if not is_valid:
            raise LLMAPIError(f"文件验证失败: {error_msg}")

        # 检查缓存
        if file_path in self.uploaded_files:
            cached_file = self.uploaded_files[file_path]
            if self.debug_mode:
                print(f"[DEBUG] 使用缓存的文件: {cached_file.name}")
            return cached_file

        try:
            path = Path(file_path)

            # 获取MIME类型
            mime_type = self.SUPPORTED_FORMATS.get(
                path.suffix.lower(),
                'application/octet-stream'
            )

            if self.debug_mode:
                print(f"[DEBUG] 上传文件: {path.name}")
                print(f"[DEBUG] MIME类型: {mime_type}")
                print(f"[DEBUG] 文件大小: {path.stat().st_size / 1024:.1f}KB")

            # 上传文件
            uploaded_file = genai.upload_file(
                path=str(path),
                mime_type=mime_type,
                display_name=path.name
            )

            # 等待文件处理完成
            max_wait = 30  # 最多等待30秒
            wait_interval = 1
            total_wait = 0

            while uploaded_file.state.name == "PROCESSING":
                if total_wait >= max_wait:
                    raise LLMAPIError(f"文件处理超时: {path.name}")

                time.sleep(wait_interval)
                total_wait += wait_interval
                uploaded_file = genai.get_file(uploaded_file.name)

                if self.debug_mode:
                    print(f"[DEBUG] 文件状态: {uploaded_file.state.name}")

            if uploaded_file.state.name == "FAILED":
                raise LLMAPIError(f"文件上传失败: {path.name}")

            # 缓存文件
            self.uploaded_files[file_path] = uploaded_file

            if self.debug_mode:
                print(f"[DEBUG] 文件上传成功: {uploaded_file.name}")
                print(f"[DEBUG] URI: {uploaded_file.uri}")

            return uploaded_file

        except Exception as e:
            raise LLMAPIError(f"上传文件失败: {str(e)}")

    def upload_multiple_files(self, file_paths: List[str]) -> List[genai.File]:
        """批量上传文件

        Args:
            file_paths: 文件路径列表

        Returns:
            上传的文件对象列表
        """
        uploaded = []

        for file_path in file_paths:
            try:
                file_obj = self.upload_file(file_path)
                if file_obj:
                    uploaded.append(file_obj)
            except Exception as e:
                if self.debug_mode:
                    print(f"[WARNING] 上传文件失败 {file_path}: {e}")
                continue

        return uploaded

    def extract_document_content(self, file_obj: genai.File) -> str:
        """提取文档内容摘要

        Args:
            file_obj: 已上传的文件对象

        Returns:
            文档内容摘要
        """
        try:
            # 使用Gemini提取文档内容
            model = genai.GenerativeModel(CONFIG.llm.model_name)

            prompt = """请分析这个文档并提取关键信息：
1. 文档类型和主要内容
2. 如果是需求文档，提取功能需求列表
3. 如果是架构图，描述架构结构
4. 如果包含AUTOSAR相关内容，提取组件和接口信息
5. 总结文档的核心要点

请用结构化的方式输出分析结果。"""

            response = model.generate_content([prompt, file_obj])

            if response and response.text:
                return response.text
            else:
                return "无法提取文档内容"

        except Exception as e:
            if self.debug_mode:
                print(f"[ERROR] 提取文档内容失败: {e}")
            return f"文档内容提取失败: {str(e)}"

    def delete_file(self, file_obj: genai.File):
        """删除已上传的文件

        Args:
            file_obj: 要删除的文件对象
        """
        try:
            genai.delete_file(file_obj.name)

            # 从缓存中移除
            for path, cached_file in list(self.uploaded_files.items()):
                if cached_file.name == file_obj.name:
                    del self.uploaded_files[path]
                    break

            if self.debug_mode:
                print(f"[DEBUG] 文件已删除: {file_obj.name}")

        except Exception as e:
            if self.debug_mode:
                print(f"[WARNING] 删除文件失败: {e}")

    def cleanup_all_files(self):
        """清理所有已上传的文件"""
        for file_obj in self.uploaded_files.values():
            self.delete_file(file_obj)
        self.uploaded_files.clear()

    def get_uploaded_files_info(self) -> List[Dict[str, Any]]:
        """获取已上传文件信息

        Returns:
            文件信息列表
        """
        files_info = []

        for path, file_obj in self.uploaded_files.items():
            files_info.append({
                'path': path,
                'name': file_obj.display_name,
                'uri': file_obj.uri,
                'state': file_obj.state.name,
                'mime_type': file_obj.mime_type
            })

        return files_info


# 全局文档处理器实例
document_processor = DocumentProcessor()