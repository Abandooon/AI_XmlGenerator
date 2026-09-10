"""utils/validators.py - 验证工具

提供数据验证和完整性检查功能
"""
import re
from pathlib import Path
from typing import Dict, List, Any, Union


def validate_uuid(uuid_str: str) -> bool:
    """验证UUID格式"""
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, uuid_str, re.IGNORECASE))


def validate_autosar_name(name: str) -> bool:
    """验证AUTOSAR命名规范"""
    # AUTOSAR命名规则：字母开头，可包含字母、数字、下划线、连字符
    pattern = r'^[A-Za-z][A-Za-z0-9_-]*$'
    return bool(re.match(pattern, name))


def validate_json_schema(data: Dict, schema: Dict) -> tuple[bool, List[str]]:
    """验证JSON数据是否符合Schema"""
    errors = []

    def validate_object(obj: Dict, schema_obj: Dict, path: str = ""):
        # 检查required字段
        if 'required' in schema_obj:
            for req_field in schema_obj['required']:
                if req_field not in obj:
                    errors.append(f"{path}.{req_field}: 必需字段缺失")

        # 检查properties
        if 'properties' in schema_obj:
            for field_name, field_schema in schema_obj['properties'].items():
                if field_name in obj:
                    field_path = f"{path}.{field_name}" if path else field_name
                    validate_field(obj[field_name], field_schema, field_path)

    def validate_field(value: Any, schema: Dict, path: str):
        field_type = schema.get('type')

        if field_type == 'string':
            if not isinstance(value, str):
                errors.append(f"{path}: 应为字符串类型")
            elif 'pattern' in schema:
                if not re.match(schema['pattern'], value):
                    errors.append(f"{path}: 不符合正则表达式 {schema['pattern']}")
            elif 'enum' in schema:
                if value not in schema['enum']:
                    errors.append(f"{path}: 值应为 {schema['enum']} 之一")

        elif field_type == 'number' or field_type == 'integer':
            if not isinstance(value, (int, float)):
                errors.append(f"{path}: 应为数字类型")
            elif 'minimum' in schema and value < schema['minimum']:
                errors.append(f"{path}: 值应 >= {schema['minimum']}")
            elif 'maximum' in schema and value > schema['maximum']:
                errors.append(f"{path}: 值应 <= {schema['maximum']}")

        elif field_type == 'array':
            if not isinstance(value, list):
                errors.append(f"{path}: 应为数组类型")
            elif 'items' in schema:
                for i, item in enumerate(value):
                    validate_field(item, schema['items'], f"{path}[{i}]")

        elif field_type == 'object':
            if not isinstance(value, dict):
                errors.append(f"{path}: 应为对象类型")
            else:
                validate_object(value, schema, path)

    # 开始验证
    if schema.get('type') == 'object':
        validate_object(data, schema)
    else:
        validate_field(data, schema, "root")

    return len(errors) == 0, errors


def validate_architecture_design(design: Dict) -> tuple[bool, List[str]]:
    """验证架构设计数据完整性"""
    errors = []

    # 检查必需的顶级字段
    required_fields = ['system_analysis', 'component_plan', 'interface_plan',
                       'connection_topology', 'architecture_rationale']

    for field in required_fields:
        if field not in design:
            errors.append(f"缺失必需字段: {field}")

    # 验证组件计划
    if 'component_plan' in design:
        for i, component in enumerate(design['component_plan']):
            if not isinstance(component, dict):
                errors.append(f"component_plan[{i}]: 应为对象类型")
                continue

            required_comp_fields = ['component_id', 'name', 'type', 'purpose']
            for field in required_comp_fields:
                if field not in component:
                    errors.append(f"component_plan[{i}].{field}: 必需字段缺失")

            # 验证组件名称
            if 'name' in component and not validate_autosar_name(component['name']):
                errors.append(f"component_plan[{i}].name: 不符合AUTOSAR命名规范")

    # 验证接口计划
    if 'interface_plan' in design:
        for i, interface in enumerate(design['interface_plan']):
            if not isinstance(interface, dict):
                errors.append(f"interface_plan[{i}]: 应为对象类型")
                continue

            required_intf_fields = ['interface_id', 'name', 'type', 'communication_pattern']
            for field in required_intf_fields:
                if field not in interface:
                    errors.append(f"interface_plan[{i}].{field}: 必需字段缺失")

    return len(errors) == 0, errors


def validate_arxml_structure(arxml_data: Dict) -> tuple[bool, List[str]]:
    """验证ARXML数据结构"""
    errors = []

    # 检查根元素
    if 'APPLICATION-SW-COMPONENT-TYPE' not in arxml_data:
        errors.append("缺失根元素: APPLICATION-SW-COMPONENT-TYPE")
        return False, errors

    component = arxml_data['APPLICATION-SW-COMPONENT-TYPE']

    # 检查必需字段
    required_fields = ['SHORT-NAME', 'PORTS']
    for field in required_fields:
        if field not in component:
            errors.append(f"APPLICATION-SW-COMPONENT-TYPE.{field}: 必需字段缺失")

    # 验证SHORT-NAME
    if 'SHORT-NAME' in component:
        if not validate_autosar_name(component['SHORT-NAME']):
            errors.append("SHORT-NAME: 不符合AUTOSAR命名规范")

    # 验证端口结构
    if 'PORTS' in component:
        ports = component['PORTS']

        # 验证P-PORT-PROTOTYPE
        if 'P-PORT-PROTOTYPE' in ports:
            for i, pport in enumerate(ports['P-PORT-PROTOTYPE']):
                if 'SHORT-NAME' not in pport:
                    errors.append(f"P-PORT-PROTOTYPE[{i}].SHORT-NAME: 必需字段缺失")
                if 'PROVIDED-INTERFACE-TREF' not in pport:
                    errors.append(f"P-PORT-PROTOTYPE[{i}].PROVIDED-INTERFACE-TREF: 必需字段缺失")

        # 验证R-PORT-PROTOTYPE
        if 'R-PORT-PROTOTYPE' in ports:
            for i, rport in enumerate(ports['R-PORT-PROTOTYPE']):
                if 'SHORT-NAME' not in rport:
                    errors.append(f"R-PORT-PROTOTYPE[{i}].SHORT-NAME: 必需字段缺失")
                if 'REQUIRED-INTERFACE-TREF' not in rport:
                    errors.append(f"R-PORT-PROTOTYPE[{i}].REQUIRED-INTERFACE-TREF: 必需字段缺失")

    return len(errors) == 0, errors


def validate_file_path(file_path: Union[str, Path], must_exist: bool = True) -> tuple[bool, str]:
    """验证文件路径"""
    path = Path(file_path)

    if must_exist and not path.exists():
        return False, f"文件不存在: {path}"

    if must_exist and not path.is_file():
        return False, f"路径不是文件: {path}"

    # 检查文件扩展名
    allowed_extensions = ['.json', '.yaml', '.yml', '.xml']
    if path.suffix not in allowed_extensions:
        return False, f"不支持的文件类型: {path.suffix}"

    return True, ""


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """清理和验证用户输入"""
    if not isinstance(text, str):
        return ""

    # 移除控制字符
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    # 限制长度
    if len(text) > max_length:
        text = text[:max_length]

    # 移除多余空白
    text = re.sub(r'\s+', ' ', text).strip()

    return text