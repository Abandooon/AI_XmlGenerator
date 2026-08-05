"""document_processor.py - 文档处理器（模拟版本）

由于使用gemini代理API，代理节点不支持状态对话，实际不支持文件上传，这里提供模拟实现
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from ..config import CONFIG
from ..utils.exceptions import LLMAPIError


@dataclass
class MockFile:
    """模拟的文件对象"""
    name: str
    display_name: str
    mime_type: str
    size_bytes: int
    state: str = "ACTIVE"
    uri: str = ""


class DocumentProcessor:
    """文档处理器 - 模拟版本（不实际上传）"""

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
        self.uploaded_files = []  # 存储模拟的文件对象
        self.debug_mode = CONFIG.debug_mode

        if self.debug_mode:
            print("[DEBUG] DocumentProcessor initialized (mock mode)")

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """验证文件是否可以上传"""
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

    def get_mime_type(self, file_path: str) -> str:
        """获取文件MIME类型"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        return self.SUPPORTED_FORMATS.get(suffix, 'application/octet-stream')

    def upload_file(self, file_path: str) -> Optional[MockFile]:
        """模拟上传文件（实际只是创建一个模拟对象）"""
        # 验证文件
        is_valid, error_msg = self.validate_file(file_path)
        if not is_valid:
            raise LLMAPIError(f"文件验证失败: {error_msg}")

        path = Path(file_path)
        mime_type = self.get_mime_type(str(path))
        file_size = path.stat().st_size

        # 创建模拟的文件对象
        mock_file = MockFile(
            name=f"files/{path.stem}",
            display_name=path.name,
            mime_type=mime_type,
            size_bytes=file_size,
            state="ACTIVE",
            uri=f"mock://files/{path.stem}"
        )

        # 记录上传的文件
        self.uploaded_files.append(mock_file)

        if self.debug_mode:
            print(f"[DEBUG] Mock file uploaded: {mock_file.display_name}")

        return mock_file

    def extract_document_content(self, file_obj: MockFile) -> str:
        """提取文档内容（模拟）"""
        if hasattr(file_obj, 'display_name'):
            file_name = file_obj.display_name
            mime_type = file_obj.mime_type

            # 模拟内容提取
            if 'pdf' in mime_type.lower():
                return f"[PDF文档 {file_name}]\n模拟提取的PDF内容：包含系统需求和架构设计说明..."
            elif 'word' in mime_type.lower() or 'document' in mime_type.lower():
                return f"[Word文档 {file_name}]\n模拟提取的Word内容：详细的功能规格说明..."
            elif 'image' in mime_type.lower():
                return f"[图片 {file_name}]\n模拟的图片描述：系统架构图，显示组件间的连接关系..."
            elif 'text' in mime_type.lower() or 'plain' in mime_type.lower():
                # 对于文本文件，尝试读取实际内容
                try:
                    # 根据display_name找到原始文件路径
                    for uploaded in self.uploaded_files:
                        if uploaded == file_obj:
                            # 简单读取文本文件内容
                            return f"[文本文档 {file_name}]\n文档内容摘要..."
                except:
                    pass
                return f"[文本文档 {file_name}]\n模拟提取的文本内容..."
            else:
                return f"[文档 {file_name}]\n模拟提取的内容..."

        return "无法提取文档内容"

    def delete_file(self, file_obj: MockFile):
        """删除文件（从列表中移除）"""
        if file_obj in self.uploaded_files:
            self.uploaded_files.remove(file_obj)
            if self.debug_mode:
                print(f"[DEBUG] Mock file deleted: {file_obj.display_name}")

    def cleanup_all_files(self):
        """清理所有文件"""
        self.uploaded_files.clear()
        if self.debug_mode:
            print("[DEBUG] All mock files cleared")

    def get_uploaded_files_info(self) -> List[Dict[str, Any]]:
        """获取已上传文件信息"""
        files_info = []
        for file_obj in self.uploaded_files:
            files_info.append({
                'name': file_obj.display_name,
                'type': file_obj.mime_type,
                'size': file_obj.size_bytes,
                'state': file_obj.state
            })
        return files_info


# 全局文档处理器实例
document_processor = DocumentProcessor()